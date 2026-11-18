import pytest
from fastapi.testclient import TestClient
from app.models.user import User


def test_user_registration(client: TestClient):
    """Scenario 1: User Registration"""
    payload = {
        "email": "newuser@agentbench.ai",
        "password": "Password123!",
        "full_name": "New Benchmarker"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@agentbench.ai"
    assert data["full_name"] == "New Benchmarker"
    assert "hashed_password" not in data
    assert "password" not in data

    # Test duplicate registration rejection
    dup_res = client.post("/api/v1/auth/register", json=payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["error"]["message"]


def test_user_authentication(client: TestClient, test_user: User):
    """Scenario 2: User Authentication & Token Generation"""
    # Valid login
    login_payload = {
        "email": test_user.email,
        "password": "securepassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # Invalid login
    bad_login = {
        "email": test_user.email,
        "password": "wrongpassword"
    }
    bad_res = client.post("/api/v1/auth/login", json=bad_login)
    assert bad_res.status_code == 401


def test_protected_routes(client: TestClient, auth_headers: dict):
    """Scenario 3: Protected Routes Access Control"""
    # Unauthorized access without header
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401

    # Authorized access with valid JWT
    auth_res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert auth_res.status_code == 200
    assert auth_res.json()["email"] == "test_engineer@agentbench.ai"


def test_cross_user_authorization(client: TestClient, auth_headers: dict, other_auth_headers: dict):
    """Scenario 18: Cross-user authorization and isolation"""
    # User A creates an agent
    create_res = client.post(
        "/api/v1/agents",
        json={
            "name": "User A Private Agent",
            "provider": "mock",
            "model_name": "mock-agent",
            "agent_type": "direct_llm",
            "tools": []
        },
        headers=auth_headers
    )
    assert create_res.status_code == 201
    agent_id = create_res.json()["id"]

    # User B attempts to access User A's private agent -> 403 Forbidden
    cross_res = client.get(f"/api/v1/agents/{agent_id}", headers=other_auth_headers)
    assert cross_res.status_code == 403

    # User B attempts to delete User A's private agent -> 403 Forbidden
    delete_res = client.delete(f"/api/v1/agents/{agent_id}", headers=other_auth_headers)
    assert delete_res.status_code == 403
