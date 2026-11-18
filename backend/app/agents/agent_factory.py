from typing import Any, Dict, Optional
from app.agents.base import BaseAgentAdapter
from app.agents.direct_llm_agent import DirectLLMAgent
from app.agents.langgraph_agent import LangGraphAgent
from app.agents.http_agent import HttpAgent
from app.core.errors import BadRequestException


class AgentFactory:
    @staticmethod
    def get_agent(config: Dict[str, Any], api_key: Optional[str] = None) -> BaseAgentAdapter:
        agent_type = config.get("agent_type", "direct_llm").lower()
        if agent_type == "direct_llm":
            return DirectLLMAgent(config, api_key)
        elif agent_type == "langgraph":
            return LangGraphAgent(config, api_key)
        elif agent_type == "http":
            return HttpAgent(config, api_key)
        else:
            raise BadRequestException(f"Unsupported agent type: '{agent_type}'. Supported: direct_llm, langgraph, http")
