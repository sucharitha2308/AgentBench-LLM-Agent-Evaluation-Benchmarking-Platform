from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.agent import Agent, AgentVersion
from app.schemas.agent import AgentCreate, AgentUpdate, ConnectionTestRequest, ConnectionTestResponse
from app.core.errors import NotFoundException, ForbiddenException
from app.providers.provider_factory import ProviderFactory


class AgentService:
    @staticmethod
    def list_agents(db: Session, user_id: str) -> List[Agent]:
        # Return user's agents plus sample agents
        return db.query(Agent).filter(
            (Agent.user_id == user_id) | (Agent.is_sample == True)
        ).order_by(Agent.created_at.desc()).all()

    @staticmethod
    def get_agent(db: Session, agent_id: str, user_id: str) -> Agent:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise NotFoundException("Agent", agent_id)
        if agent.user_id != user_id and not agent.is_sample:
            raise ForbiddenException()
        return agent

    @staticmethod
    def create_agent(db: Session, user_id: str, agent_in: AgentCreate) -> Agent:
        agent = Agent(
            user_id=user_id,
            name=agent_in.name,
            description=agent_in.description,
            agent_type=agent_in.agent_type,
            provider=agent_in.provider,
            model_name=agent_in.model_name,
            system_prompt=agent_in.system_prompt,
            temperature=agent_in.temperature,
            max_output_tokens=agent_in.max_output_tokens,
            output_format=agent_in.output_format,
            tools=agent_in.tools,
            http_endpoint=agent_in.http_endpoint,
            is_sample=False
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)

        # Create version 1 snapshot
        version = AgentVersion(
            agent_id=agent.id,
            version_number=1,
            commit_message="Initial configuration",
            configuration_snapshot=agent_in.model_dump()
        )
        db.add(version)
        db.commit()
        return agent

    @staticmethod
    def update_agent(db: Session, agent_id: str, user_id: str, agent_in: AgentUpdate) -> Agent:
        agent = AgentService.get_agent(db, agent_id, user_id)
        if agent.is_sample and agent.user_id != user_id:
            raise ForbiddenException("Sample baseline agent cannot be modified directly. Create a copy.")

        update_data = agent_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)

        db.commit()
        db.refresh(agent)

        # Increment version snapshot
        last_version = db.query(AgentVersion).filter(AgentVersion.agent_id == agent.id).order_by(AgentVersion.version_number.desc()).first()
        next_ver = (last_version.version_number + 1) if last_version else 1
        
        version = AgentVersion(
            agent_id=agent.id,
            version_number=next_ver,
            commit_message=f"Configuration update v{next_ver}",
            configuration_snapshot={
                "name": agent.name,
                "agent_type": agent.agent_type,
                "provider": agent.provider,
                "model_name": agent.model_name,
                "system_prompt": agent.system_prompt,
                "temperature": agent.temperature,
                "max_output_tokens": agent.max_output_tokens,
                "tools": agent.tools,
                "output_format": agent.output_format
            }
        )
        db.add(version)
        db.commit()
        return agent

    @staticmethod
    def delete_agent(db: Session, agent_id: str, user_id: str) -> None:
        agent = AgentService.get_agent(db, agent_id, user_id)
        if agent.is_sample and agent.user_id != user_id:
            raise ForbiddenException("Sample agents cannot be deleted.")
        db.delete(agent)
        db.commit()

    @staticmethod
    def get_agent_versions(db: Session, agent_id: str, user_id: str) -> List[AgentVersion]:
        AgentService.get_agent(db, agent_id, user_id)
        return db.query(AgentVersion).filter(AgentVersion.agent_id == agent_id).order_by(AgentVersion.version_number.desc()).all()

    @staticmethod
    async def test_connection(test_req: ConnectionTestRequest) -> ConnectionTestResponse:
        provider = ProviderFactory.get_provider(
            provider_name=test_req.provider,
            model_name=test_req.model_name,
            api_key=test_req.api_key
        )
        result = await provider.test_connection()
        return ConnectionTestResponse(
            success=result.get("success", False),
            provider=test_req.provider,
            model_name=test_req.model_name,
            message=result.get("message", "Connection verified"),
            latency_ms=result.get("latency_ms", 0),
            raw_response=str(result)
        )
