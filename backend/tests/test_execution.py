import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.dataset import Dataset, TestCase
from app.models.evaluation import EvaluationRun, TestResult
from app.execution.runner import EvaluationRunner
from app.services.comparison_service import ComparisonService
from app.services.regression_service import RegressionService


@pytest.mark.asyncio
async def test_evaluation_execution_pipeline(db_session: Session, test_user):
    """Scenario 13 & 14: Evaluation execution pipeline & background job processing"""
    # 1. Setup test agent
    agent = Agent(
        user_id=test_user.id,
        name="Mock Support Agent",
        provider="mock",
        model_name="mock-agent",
        agent_type="direct_llm",
        system_prompt="Support assistant",
        tools=[{"name": "get_order"}]
    )
    db_session.add(agent)

    # 2. Setup test dataset with 2 cases
    dataset = Dataset(
        user_id=test_user.id,
        name="Mini Evaluation Dataset",
        domain="support"
    )
    db_session.add(dataset)
    db_session.commit()

    tc1 = TestCase(
        dataset_id=dataset.id,
        test_case_id="TC-01",
        name="Lookup ORD-1001",
        user_input="Where is order ORD-1001?",
        expected_tool_calls=[{"tool_name": "get_order", "arguments": {"order_id": "ORD-1001"}}],
        expected_output={"contains_keywords": ["ORD-1001", "Shipped"]},
        evaluation_criteria={"require_tool_selection": True}
    )
    tc2 = TestCase(
        dataset_id=dataset.id,
        test_case_id="TC-02",
        name="General return policy",
        user_input="What is the return policy?",
        expected_tool_calls=[],
        expected_output={"contains_keywords": ["30 days", "policy"]},
        evaluation_criteria={"require_tool_selection": True}
    )
    db_session.add_all([tc1, tc2])
    db_session.commit()

    # 3. Create evaluation run
    eval_run = EvaluationRun(
        user_id=test_user.id,
        agent_id=agent.id,
        dataset_id=dataset.id,
        name="Pipeline Verification Run",
        status="PENDING",
        selected_evaluators=["task_success", "tool_selection", "performance", "reliability"],
        agent_snapshot={
            "id": agent.id,
            "name": agent.name,
            "provider": "mock",
            "model_name": "mock-agent",
            "agent_type": "direct_llm",
            "tools": agent.tools
        },
        dataset_snapshot={
            "id": dataset.id,
            "name": dataset.name,
            "test_cases": [
                {
                    "id": tc1.id,
                    "test_case_id": tc1.test_case_id,
                    "name": tc1.name,
                    "user_input": tc1.user_input,
                    "expected_tool_calls": tc1.expected_tool_calls,
                    "expected_output": tc1.expected_output,
                    "max_allowed_latency_ms": 3000,
                    "evaluation_criteria": tc1.evaluation_criteria
                },
                {
                    "id": tc2.id,
                    "test_case_id": tc2.test_case_id,
                    "name": tc2.name,
                    "user_input": tc2.user_input,
                    "expected_tool_calls": tc2.expected_tool_calls,
                    "expected_output": tc2.expected_output,
                    "max_allowed_latency_ms": 3000,
                    "evaluation_criteria": tc2.evaluation_criteria
                }
            ]
        }
    )
    db_session.add(eval_run)
    db_session.commit()
    db_session.refresh(eval_run)

    # 4. Execute runner
    runner = EvaluationRunner(eval_run.id)
    await runner.run(db_session=db_session)

    # 5. Verify results
    db_session.refresh(eval_run)
    assert eval_run.status == "COMPLETED"
    assert eval_run.total_test_cases == 2
    assert eval_run.completed_test_cases == 2
    assert eval_run.passed_test_cases >= 1
    assert "task_success_rate" in eval_run.aggregate_metrics

    # Verify individual results & traces exist
    results = db_session.query(TestResult).filter(TestResult.evaluation_run_id == eval_run.id).all()
    assert len(results) == 2
    for r in results:
        assert r.trace_id is not None
        assert r.duration_ms >= 0


def test_run_comparison_service(db_session: Session, test_user):
    """Scenario 15: Run Comparison and Delta Analysis"""
    # Create mock Run A (80% success)
    run_a = EvaluationRun(
        user_id=test_user.id,
        agent_id="agent-1",
        dataset_id="dataset-1",
        name="Run A Baseline",
        status="COMPLETED",
        total_test_cases=10,
        completed_test_cases=10,
        passed_test_cases=8,
        failed_test_cases=2,
        aggregate_metrics={
            "task_success_rate": 80.0,
            "tool_selection_accuracy": 85.0,
            "average_latency_ms": 400.0,
            "total_tokens": 1500,
            "estimated_cost_usd": 0.003
        },
        agent_snapshot={"name": "Agent Alpha", "model_name": "mock-a"},
        dataset_snapshot={"name": "Support Suite"}
    )
    # Create mock Run B (90% success)
    run_b = EvaluationRun(
        user_id=test_user.id,
        agent_id="agent-2",
        dataset_id="dataset-1",
        name="Run B Candidate",
        status="COMPLETED",
        total_test_cases=10,
        completed_test_cases=10,
        passed_test_cases=9,
        failed_test_cases=1,
        aggregate_metrics={
            "task_success_rate": 90.0,
            "tool_selection_accuracy": 92.0,
            "average_latency_ms": 350.0,
            "total_tokens": 1400,
            "estimated_cost_usd": 0.0028
        },
        agent_snapshot={"name": "Agent Beta", "model_name": "mock-b"},
        dataset_snapshot={"name": "Support Suite"}
    )
    db_session.add_all([run_a, run_b])
    db_session.commit()

    comparison = ComparisonService.compare_runs(db_session, test_user.id, run_a.id, run_b.id)
    assert comparison.run_a.id == run_a.id
    assert comparison.run_b.id == run_b.id
    
    # Task success rate delta check
    succ_delta = next(m for m in comparison.metric_comparisons if m.metric_name == "task_success_rate")
    assert succ_delta.delta == 10.0
    assert succ_delta.winner == "B"
    assert "Agent Beta" in comparison.summary


def test_regression_detection_service(db_session: Session, test_user):
    """Scenario 16: Regression Detection between Baseline and Current Runs"""
    run_baseline = EvaluationRun(
        user_id=test_user.id,
        agent_id="agent-base",
        dataset_id="dataset-1",
        name="Baseline Run",
        status="COMPLETED",
        total_test_cases=2,
        passed_test_cases=2,
        failed_test_cases=0,
        aggregate_metrics={"task_success_rate": 100.0, "average_latency_ms": 200.0},
        agent_snapshot={"name": "Baseline Agent"},
        dataset_snapshot={"name": "Support"}
    )
    run_current = EvaluationRun(
        user_id=test_user.id,
        agent_id="agent-curr",
        dataset_id="dataset-1",
        name="Current Run",
        status="COMPLETED",
        total_test_cases=2,
        passed_test_cases=1,
        failed_test_cases=1,
        aggregate_metrics={"task_success_rate": 50.0, "average_latency_ms": 300.0},
        agent_snapshot={"name": "Current Agent"},
        dataset_snapshot={"name": "Support"}
    )
    db_session.add_all([run_baseline, run_current])
    db_session.commit()

    # Baseline: TC-01 passed, TC-02 passed
    b_tr1 = TestResult(
        evaluation_run_id=run_baseline.id,
        test_case_identifier="TC-01",
        name="Order status",
        status="PASS",
        duration_ms=180
    )
    b_tr2 = TestResult(
        evaluation_run_id=run_baseline.id,
        test_case_identifier="TC-02",
        name="Refund check",
        status="PASS",
        duration_ms=220
    )
    # Current: TC-01 passed, TC-02 REGRESSED to FAIL
    c_tr1 = TestResult(
        evaluation_run_id=run_current.id,
        test_case_identifier="TC-01",
        name="Order status",
        status="PASS",
        duration_ms=210
    )
    c_tr2 = TestResult(
        evaluation_run_id=run_current.id,
        test_case_identifier="TC-02",
        name="Refund check",
        status="FAIL",
        duration_ms=390,
        failure_category="tool_argument_mismatch",
        failure_explanation="Failed argument binding"
    )
    db_session.add_all([b_tr1, b_tr2, c_tr1, c_tr2])
    db_session.commit()

    analysis = RegressionService.analyze_regressions(
        db_session, test_user.id, run_baseline.id, run_current.id, threshold_pct=5.0
    )
    assert analysis.total_regressions == 1
    assert analysis.regressed_cases[0]["test_case_identifier"] == "TC-02"
    assert analysis.regressed_cases[0]["failure_category"] == "tool_argument_mismatch"
    assert analysis.severity in ["MEDIUM", "HIGH", "CRITICAL"]
