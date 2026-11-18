from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db, get_current_user
from app.models.user import User
from app.models.credential import ProviderCredential
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentVersionResponse,
    ConnectionTestRequest, ConnectionTestResponse
)
from app.schemas.evaluation import CredentialCreate, CredentialResponse
from app.services.agent_service import AgentService
from app.core.security import encrypt_secret, decrypt_secret
from app.core.errors import NotFoundException

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    agent_in: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register and configure a new AI agent."""
    return AgentService.create_agent(db, current_user.id, agent_in)


@router.get("", response_model=List[AgentResponse])
def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all agents available to the current user."""
    return AgentService.list_agents(db, current_user.id)


# Test connection and Credential Management must precede /{id} to prevent path parameter shadowing
@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_provider_connection(
    test_req: ConnectionTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test connectivity to an LLM provider with user's stored or provided key."""
    # If no key passed explicitly in payload, look up user's stored credential
    if not test_req.api_key and test_req.provider in ["openai", "gemini"]:
        cred = db.query(ProviderCredential).filter(
            ProviderCredential.user_id == current_user.id,
            ProviderCredential.provider_name == test_req.provider,
            ProviderCredential.is_valid == True
        ).first()
        if cred:
            test_req.api_key = decrypt_secret(cred.encrypted_api_key)

    return await AgentService.test_connection(test_req)


@router.post("/credentials", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
def save_provider_credential(
    cred_in: CredentialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Store encrypted API key for a provider."""
    # Check if credential already exists for this provider
    existing = db.query(ProviderCredential).filter(
        ProviderCredential.user_id == current_user.id,
        ProviderCredential.provider_name == cred_in.provider_name
    ).first()

    enc_key = encrypt_secret(cred_in.api_key)
    if existing:
        existing.encrypted_api_key = enc_key
        existing.key_alias = cred_in.key_alias
        existing.is_valid = True
        db.commit()
        db.refresh(existing)
        target = existing
    else:
        cred = ProviderCredential(
            user_id=current_user.id,
            provider_name=cred_in.provider_name,
            key_alias=cred_in.key_alias,
            encrypted_api_key=enc_key,
            is_valid=True
        )
        db.add(cred)
        db.commit()
        db.refresh(cred)
        target = cred

    masked = f"{cred_in.api_key[:4]}...{cred_in.api_key[-4:]}" if len(cred_in.api_key) > 8 else "***"
    return CredentialResponse(
        id=target.id,
        provider_name=target.provider_name,
        key_alias=target.key_alias,
        is_valid=target.is_valid,
        last_verified_at=target.last_verified_at,
        created_at=target.created_at,
        masked_key=masked
    )


@router.get("/credentials", response_model=List[CredentialResponse])
def list_credentials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List configured provider credentials (raw secrets are strictly redacted)."""
    creds = db.query(ProviderCredential).filter(ProviderCredential.user_id == current_user.id).all()
    results = []
    for c in creds:
        dec = decrypt_secret(c.encrypted_api_key)
        masked = f"{dec[:4]}...{dec[-4:]}" if len(dec) > 8 else "***"
        results.append(CredentialResponse(
            id=c.id,
            provider_name=c.provider_name,
            key_alias=c.key_alias,
            is_valid=c.is_valid,
            last_verified_at=c.last_verified_at,
            created_at=c.created_at,
            masked_key=masked
        ))
    return results


@router.delete("/credentials/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credential(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a stored provider credential."""
    cred = db.query(ProviderCredential).filter(
        ProviderCredential.id == id,
        ProviderCredential.user_id == current_user.id
    ).first()
    if not cred:
        raise NotFoundException("ProviderCredential", id)
    db.delete(cred)
    db.commit()
    return None


@router.get("/{id}", response_model=AgentResponse)
def get_agent(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a specific agent."""
    return AgentService.get_agent(db, id, current_user.id)


@router.put("/{id}", response_model=AgentResponse)
def update_agent(
    id: str,
    agent_in: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update agent configuration and create version checkpoint."""
    return AgentService.update_agent(db, id, current_user.id, agent_in)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an agent and its version history."""
    AgentService.delete_agent(db, id, current_user.id)
    return None


@router.get("/{id}/versions", response_model=List[AgentVersionResponse])
def get_agent_versions(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve immutable configuration version history for an agent."""
    return AgentService.get_agent_versions(db, id, current_user.id)
