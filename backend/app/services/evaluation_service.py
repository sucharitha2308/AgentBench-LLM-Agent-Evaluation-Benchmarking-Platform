import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.evaluation import EvaluationRun, TestResult, ExecutionTrace
from app.models.agent import Agent
from app.models.dataset import Dataset, TestCase
from app.models.credential import ProviderCredential
from app.schemas.evaluation import EvaluationCreate
from app.core.errors import NotFoundException, ForbiddenException, BadRequestException
from app.core.security import decrypt_secret
from app.execution.manager import execution_manager


class EvaluationService:
    @staticmethod
    def list_runs(db: Session, user_id: str) -> List[EvaluationRun]:
        return db.query(EvaluationRun).filter(
            EvaluationRun.user_id == user_id
        ).order_by(EvaluationRun.created_at.desc()).all()

    @staticmethod
    def get_run(db: Session, run_id: str, user_id: str) -> EvaluationRun:
        run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if not run:
            raise NotFoundException("EvaluationRun", run_id)
        if run.user_id != user_id:
            raise ForbiddenException()
        return run

    @staticmethod
    def create_run(db: Session, user_id: str, run_in: EvaluationCreate) -> EvaluationRun:
        agent = db.query(Agent).filter(Agent.id == run_in.agent_id).first()
        if not agent:
            raise NotFoundException("Agent", run_in.agent_id)

        dataset = db.query(Dataset).filter(Dataset.id == run_in.dataset_id).first()
        if not dataset:
            raise NotFoundException("Dataset", run_in.dataset_id)

        test_cases = db.query(TestCase).filter(TestCase.dataset_id == dataset.id).all()
        if not test_cases:
            raise BadRequestException("Cannot run evaluation on an empty dataset. Add test cases first.")

        # Build immutable agent snapshot
        agent_snapshot = {
            "id": agent.id,
            "name": agent.name,
            "agent_type": agent.agent_type,
            "provider": agent.provider,
            "model_name": agent.model_name,
            "system_prompt": agent.system_prompt,
            "temperature": agent.temperature,
            "max_output_tokens": agent.max_output_tokens,
            "output_format": agent.output_format,
            "tools": agent.tools,
            "http_endpoint": agent.http_endpoint
        }

        # Build immutable dataset snapshot
        dataset_snapshot = {
            "id": dataset.id,
            "name": dataset.name,
            "domain": dataset.domain,
            "test_cases": [
                {
                    "id": tc.id,
                    "test_case_id": tc.test_case_id,
                    "name": tc.name,
                    "description": tc.description,
                    "user_input": tc.user_input,
                    "difficulty_level": tc.difficulty_level,
                    "tags": tc.tags,
                    "expected_behavior": tc.expected_behavior,
                    "expected_tool_calls": tc.expected_tool_calls,
                    "expected_output": tc.expected_output,
                    "max_allowed_latency_ms": tc.max_allowed_latency_ms,
                    "evaluation_criteria": tc.evaluation_criteria
                }
                for tc in test_cases
            ]
        }

        # Fetch decrypted API key if user has stored credentials for this provider
        decrypted_key = None
        if agent.provider in ["openai", "gemini"]:
            cred = db.query(ProviderCredential).filter(
                ProviderCredential.user_id == user_id,
                ProviderCredential.provider_name == agent.provider,
                ProviderCredential.is_valid == True
            ).first()
            if cred:
                decrypted_key = decrypt_secret(cred.encrypted_api_key)

        eval_run = EvaluationRun(
            user_id=user_id,
            agent_id=agent.id,
            dataset_id=dataset.id,
            name=run_in.name,
            status="QUEUED",
            total_test_cases=len(test_cases),
            completed_test_cases=0,
            passed_test_cases=0,
            failed_test_cases=0,
            error_count=0,
            aggregate_metrics={},
            agent_snapshot=agent_snapshot,
            dataset_snapshot=dataset_snapshot,
            concurrency_limit=run_in.concurrency_limit,
            timeout_seconds=run_in.timeout_seconds,
            selected_evaluators=run_in.selected_evaluators
        )
        db.add(eval_run)
        db.commit()
        db.refresh(eval_run)

        # Dispatch background execution
        execution_manager.start_evaluation(eval_run.id, api_key=decrypted_key)

        return eval_run

    @staticmethod
    def cancel_run(db: Session, run_id: str, user_id: str) -> EvaluationRun:
        run = EvaluationService.get_run(db, run_id, user_id)
        if run.status in ["COMPLETED", "FAILED", "CANCELLED"]:
            return run
        
        execution_manager.cancel_evaluation(run_id)
        run.status = "CANCELLED"
        run.completed_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def get_run_results(db: Session, run_id: str, user_id: str) -> List[TestResult]:
        EvaluationService.get_run(db, run_id, user_id)
        return db.query(TestResult).filter(
            TestResult.evaluation_run_id == run_id
        ).order_by(TestResult.created_at.asc()).all()

    @staticmethod
    def get_run_traces(db: Session, run_id: str, user_id: str) -> List[ExecutionTrace]:
        EvaluationService.get_run(db, run_id, user_id)
        return db.query(ExecutionTrace).filter(
            ExecutionTrace.evaluation_run_id == run_id
        ).order_by(ExecutionTrace.created_at.asc()).all()

    @staticmethod
    def get_trace_by_id(db: Session, trace_id: str, user_id: str) -> ExecutionTrace:
        trace = db.query(ExecutionTrace).filter(ExecutionTrace.id == trace_id).first()
        if not trace:
            raise NotFoundException("ExecutionTrace", trace_id)
        EvaluationService.get_run(db, trace.evaluation_run_id, user_id)
        return trace
