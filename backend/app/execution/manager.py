import asyncio
import threading
from typing import Dict, Optional
from app.execution.runner import EvaluationRunner
from app.core.logging import logger


class ExecutionManager:
    """
    Manages active evaluation runs and provides cancellation capabilities.
    Dispatches asynchronous execution tasks safely whether called from an
    async event loop or a synchronous thread.
    """
    _active_runners: Dict[str, EvaluationRunner] = {}

    @classmethod
    def start_evaluation(cls, run_id: str, api_key: Optional[str] = None) -> None:
        runner = EvaluationRunner(run_id)
        cls._active_runners[run_id] = runner

        # Launch async task
        async def _wrapper():
            try:
                await runner.run(api_key=api_key)
            except Exception as e:
                logger.error(f"Error during evaluation run {run_id}: {str(e)}", exc_info=True)
            finally:
                cls._active_runners.pop(run_id, None)

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_wrapper())
            logger.info(f"Dispatched background evaluation task on current event loop for run_id: {run_id}")
        except RuntimeError:
            # Called from a synchronous worker thread without an active event loop
            def run_in_thread():
                asyncio.run(_wrapper())

            thread = threading.Thread(target=run_in_thread, daemon=True, name=f"EvalRunner-{run_id}")
            thread.start()
            logger.info(f"Dispatched background evaluation task in dedicated thread for run_id: {run_id}")

    @classmethod
    def cancel_evaluation(cls, run_id: str) -> bool:
        runner = cls._active_runners.get(run_id)
        if runner:
            runner.cancel()
            logger.info(f"Cancellation requested for evaluation run: {run_id}")
            return True
        return False


execution_manager = ExecutionManager()
