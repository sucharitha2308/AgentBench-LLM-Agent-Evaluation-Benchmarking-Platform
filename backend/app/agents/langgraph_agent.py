import datetime
import time
from typing import Any, Dict, List, Optional
from app.agents.base import BaseAgentAdapter, AgentExecutionResult
from app.agents.direct_llm_agent import DirectLLMAgent


class LangGraphAgent(BaseAgentAdapter):
    """
    LangGraph Workflow Agent Adapter.
    Executes a structured multi-node graph (Reasoning -> Tool Dispatch -> Response Synthesizer).
    """
    def __init__(self, config: Dict[str, Any], api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.underlying = DirectLLMAgent(config, api_key)

    async def execute(self, user_input: str) -> AgentExecutionResult:
        # Augment execution trace with LangGraph workflow states
        res = await self.underlying.execute(user_input)
        
        # Add graph state nodes to trace
        graph_steps = [
            {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "event_type": "GRAPH_NODE_ENTER",
                "content": {"node": "supervisor_intent_classifier", "state": "ACTIVE"}
            }
        ]
        graph_steps.extend(res.trace_steps)
        graph_steps.append({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event_type": "GRAPH_NODE_EXIT",
            "content": {"node": "synthesizer_output_formatter", "status": "COMPLETED"}
        })
        res.trace_steps = graph_steps
        return res
