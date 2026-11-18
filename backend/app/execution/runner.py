import asyncio
import datetime
import math
from typing import Any, Dict, List, Optional
import numpy as np
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.evaluation import EvaluationRun, TestResult, ExecutionTrace
from app.agents.agent_factory import AgentFactory
from app.evaluators import EVALUATOR_REGISTRY
from app.utils.cost_calculator import calculate_token_cost
from app.utils.redaction import redact_sensitive_data
from app.core.logging import logger


class EvaluationRunner:
    """
    Core Execution Engine.
    Executes an agent against dataset test cases with bounded concurrency,
    evaluates outputs, records traces, and aggregates benchmark metrics.
    """
    def __init__(self, run_id: str):
        self.run_id = run_id
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    async def execute_test_case(
        self,
        test_case: Dict[str, Any],
        agent_config: Dict[str, Any],
        api_key: Optional[str],
        selected_evaluators: List[str],
        timeout_seconds: int,
        semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """Execute a single test case within concurrency limits and timeout."""
        async with semaphore:
            if self._cancelled:
                return {"status": "CANCELLED", "test_case": test_case}

            agent = AgentFactory.get_agent(agent_config, api_key=api_key)
            user_input = test_case.get("user_input", "")

            # Execute agent with timeout
            try:
                exec_result = await asyncio.wait_for(
                    agent.execute(user_input),
                    timeout=float(timeout_seconds)
                )
            except asyncio.TimeoutError:
                from app.agents.base import AgentExecutionResult
                exec_result = AgentExecutionResult(
                    final_response="",
                    error=f"Test case execution timed out after {timeout_seconds} seconds.",
                    duration_ms=timeout_seconds * 1000,
                    provider=agent_config.get("provider", "unknown"),
                    model_name=agent_config.get("model_name", "unknown")
                )
            except Exception as e:
                from app.agents.base import AgentExecutionResult
                exec_result = AgentExecutionResult(
                    final_response="",
                    error=f"Execution exception: {str(e)}",
                    duration_ms=0,
                    provider=agent_config.get("provider", "unknown"),
                    model_name=agent_config.get("model_name", "unknown")
                )

            # Evaluate outcomes
            evaluator_outcomes = {}
            test_passed = True
            primary_failure_category = None
            primary_failure_explanation = None

            for eval_name in selected_evaluators:
                evaluator = EVALUATOR_REGISTRY.get(eval_name)
                if not evaluator:
                    continue
                outcome = evaluator.evaluate(
                    test_case=test_case,
                    actual_output=exec_result.final_response,
                    actual_tool_calls=exec_result.tool_calls,
                    actual_tool_results=exec_result.tool_results,
                    duration_ms=exec_result.duration_ms,
                    error=exec_result.error
                )
                evaluator_outcomes[eval_name] = outcome.model_dump()
                if not outcome.passed:
                    test_passed = False
                    if not primary_failure_category:
                        primary_failure_category = outcome.failure_category
                        primary_failure_explanation = outcome.explanation

            # Calculate cost
            cost = calculate_token_cost(
                model_name=exec_result.model_name or agent_config.get("model_name", "mock-agent"),
                input_tokens=exec_result.input_tokens,
                output_tokens=exec_result.output_tokens
            )

            status = "PASS" if test_passed else ("ERROR" if exec_result.error else "FAIL")

            return {
                "test_case_id": test_case.get("id"),
                "test_case_identifier": test_case.get("test_case_id", "TC-UNKNOWN"),
                "name": test_case.get("name", "Unnamed Test"),
                "status": status,
                "duration_ms": exec_result.duration_ms,
                "input_tokens": exec_result.input_tokens,
                "output_tokens": exec_result.output_tokens,
                "total_tokens": exec_result.total_tokens,
                "estimated_cost": cost,
                "actual_response": exec_result.final_response,
                "actual_tool_calls": exec_result.tool_calls,
                "metrics": evaluator_outcomes,
                "failure_category": primary_failure_category,
                "failure_explanation": primary_failure_explanation,
                "trace_steps": exec_result.trace_steps,
            }

    async def run(self, api_key: Optional[str] = None, db_session: Optional[Session] = None):
        """Orchestrate entire evaluation run, persist results and update aggregate metrics."""
        external_db = db_session is not None
        db: Session = db_session if external_db else SessionLocal()
        try:
            eval_run = db.query(EvaluationRun).filter(EvaluationRun.id == self.run_id).first()
            if not eval_run:
                logger.error(f"EvaluationRun {self.run_id} not found.")
                return

            eval_run.status = "RUNNING"
            eval_run.started_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()

            agent_config = eval_run.agent_snapshot
            test_cases = eval_run.dataset_snapshot.get("test_cases", [])
            selected_evaluators = eval_run.selected_evaluators or list(EVALUATOR_REGISTRY.keys())
            concurrency = eval_run.concurrency_limit or 5
            timeout = eval_run.timeout_seconds or 30

            eval_run.total_test_cases = len(test_cases)
            db.commit()

            semaphore = asyncio.Semaphore(concurrency)
            tasks = [
                self.execute_test_case(
                    test_case=tc,
                    agent_config=agent_config,
                    api_key=api_key,
                    selected_evaluators=selected_evaluators,
                    timeout_seconds=timeout,
                    semaphore=semaphore
                )
                for tc in test_cases
            ]

            completed_results = []
            durations = []
            total_in = 0
            total_out = 0
            total_cost = 0.0
            passed_cnt = 0
            failed_cnt = 0
            error_cnt = 0

            # Execute and persist incrementally as results arrive
            for future in asyncio.as_completed(tasks):
                res = await future
                if res.get("status") == "CANCELLED":
                    break

                # Save TestResult to DB
                test_result = TestResult(
                    evaluation_run_id=eval_run.id,
                    test_case_id=res["test_case_id"],
                    test_case_identifier=res["test_case_identifier"],
                    name=res["name"],
                    status=res["status"],
                    duration_ms=res["duration_ms"],
                    input_tokens=res["input_tokens"],
                    output_tokens=res["output_tokens"],
                    total_tokens=res["total_tokens"],
                    estimated_cost=res["estimated_cost"],
                    actual_response=res["actual_response"],
                    actual_tool_calls=res["actual_tool_calls"],
                    metrics=res["metrics"],
                    failure_category=res["failure_category"],
                    failure_explanation=res["failure_explanation"]
                )
                db.add(test_result)
                db.commit()
                db.refresh(test_result)

                # Save ExecutionTrace
                trace = ExecutionTrace(
                    evaluation_run_id=eval_run.id,
                    test_result_id=test_result.id,
                    test_case_identifier=res["test_case_identifier"],
                    steps=res["trace_steps"]
                )
                db.add(trace)
                db.commit()
                db.refresh(trace)

                test_result.trace_id = trace.id
                db.commit()

                # Tally metrics
                completed_results.append(res)
                durations.append(res["duration_ms"])
                total_in += res["input_tokens"]
                total_out += res["output_tokens"]
                total_cost += res["estimated_cost"]

                if res["status"] == "PASS":
                    passed_cnt += 1
                elif res["status"] == "FAIL":
                    failed_cnt += 1
                elif res["status"] == "ERROR":
                    error_cnt += 1

                # Update live progress
                eval_run.completed_test_cases = len(completed_results)
                eval_run.passed_test_cases = passed_cnt
                eval_run.failed_test_cases = failed_cnt
                eval_run.error_count = error_cnt
                db.commit()

            if self._cancelled:
                eval_run.status = "CANCELLED"
                eval_run.completed_at = datetime.datetime.now(datetime.timezone.utc)
                db.commit()
                return

            # Compute Final Aggregate Metrics
            total_cases = len(completed_results) or 1
            success_rate = round((passed_cnt / total_cases) * 100, 2)
            avg_latency = round(float(np.mean(durations)), 2) if durations else 0.0
            p50_latency = round(float(np.percentile(durations, 50)), 2) if durations else 0.0
            p95_latency = round(float(np.percentile(durations, 95)), 2) if durations else 0.0

            # Tool calling accuracy average
            tool_sel_scores = [
                r["metrics"].get("tool_selection", {}).get("metric_value", 0.0)
                for r in completed_results if "tool_selection" in r["metrics"]
            ]
            avg_tool_accuracy = round(float(np.mean(tool_sel_scores)) * 100, 2) if tool_sel_scores else 100.0

            # JSON validity average
            json_scores = [
                r["metrics"].get("structured_output", {}).get("metric_value", 0.0)
                for r in completed_results if "structured_output" in r["metrics"]
            ]
            avg_json_validity = round(float(np.mean(json_scores)) * 100, 2) if json_scores else 100.0

            # Semantic score average
            semantic_scores = [
                r["metrics"].get("semantic", {}).get("metric_value", 0.0)
                for r in completed_results if "semantic" in r["metrics"]
            ]
            avg_semantic_score = round(float(np.mean(semantic_scores)) * 100, 2) if semantic_scores else 100.0

            # Safety pass rate
            safety_passes = [
                1 if r["metrics"].get("safety", {}).get("passed", True) else 0
                for r in completed_results if "safety" in r["metrics"]
            ]
            safety_pass_rate = round((sum(safety_passes) / len(safety_passes)) * 100, 2) if safety_passes else 100.0

            eval_run.aggregate_metrics = {
                "task_success_rate": success_rate,
                "tool_selection_accuracy": avg_tool_accuracy,
                "tool_argument_accuracy": round(float(np.mean([
                    r["metrics"].get("tool_argument", {}).get("metric_value", 1.0)
                    for r in completed_results if "tool_argument" in r["metrics"]
                ])) * 100, 2) if completed_results else 100.0,
                "structured_output_validity": avg_json_validity,
                "semantic_score": avg_semantic_score,
                "safety_pass_rate": safety_pass_rate,
                "average_latency_ms": avg_latency,
                "p50_latency_ms": p50_latency,
                "p95_latency_ms": p95_latency,
                "input_tokens": total_in,
                "output_tokens": total_out,
                "total_tokens": total_in + total_out,
                "estimated_cost_usd": round(total_cost, 6),
                "error_rate": round((error_cnt / total_cases) * 100, 2),
            }
            eval_run.status = "COMPLETED"
            eval_run.completed_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()
            logger.info(f"EvaluationRun {self.run_id} completed successfully: Success Rate {success_rate}%.")

        except Exception as e:
            logger.exception(f"EvaluationRun {self.run_id} failed: {e}")
            eval_run = db.query(EvaluationRun).filter(EvaluationRun.id == self.run_id).first()
            if eval_run:
                eval_run.status = "FAILED"
                eval_run.error_message = str(e)
                eval_run.completed_at = datetime.datetime.now(datetime.timezone.utc)
                db.commit()
        finally:
            if not external_db:
                db.close()
