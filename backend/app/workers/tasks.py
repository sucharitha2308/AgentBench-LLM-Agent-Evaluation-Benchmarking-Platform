import asyncio
from typing import Optional
from app.workers.celery_app import celery_app
from app.execution.runner import EvaluationRunner
from app.core.logging import logger


@celery_app.task(name="app.workers.tasks.execute_evaluation_run", bind=True, max_retries=2)
def execute_evaluation_run(self, run_id: str, api_key: Optional[str] = None):
    """Celery background worker task for running evaluations."""
    logger.info(f"Celery worker received evaluation task: {run_id}")
    try:
        runner = EvaluationRunner(run_id)
        asyncio.run(runner.run(api_key=api_key))
        return {"status": "SUCCESS", "run_id": run_id}
    except Exception as exc:
        logger.exception(f"Celery evaluation task failed: {exc}")
        raise self.retry(exc=exc, countdown=10)
