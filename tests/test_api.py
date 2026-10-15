import pytest
import jwt
import redis as sync_redis

from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import SECRET_KEY, ALGORITHM
from app.services.rate_limit import RATE_LIMITS, REDIS_URL

# This creates a virtual "browser" that talks directly to your FastAPI app
client_context = TestClient(app)
client = client_context.__enter__()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def generate_test_token(role: str) -> str:
    """Helper function to mock JWTs for our tests."""
    return jwt.encode({"role": role}, SECRET_KEY, algorithm=ALGORITHM)

def test_reject_unauthenticated_request(client):
    # ACT: Try to execute a tool without a Bearer token
    response = client.post(
        "/v1/execute-tool",
        json={"tool_name": "query_database", "arguments": {"table_name": "users", "limit": 10}}
    )
    
    # ASSERT: The API should block it completely
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}

def test_rbac_security_block(client):
    # ARRANGE: Create a token for a 'guest' who has no permissions
    token = generate_test_token("guest")
    
    # ACT: Attempt to query the database
    response = client.post(
        "/v1/execute-tool",
        headers={"Authorization": f"Bearer {token}"},
        json={"tool_name": "query_database", "arguments": {"table_name": "users", "limit": 10}}
    )
    
    # ASSERT: The API should forbid the action based on role
    assert response.status_code == 403
    assert "RBAC Blocked" in response.json()["detail"]

def test_successful_tool_execution(client):
    # ARRANGE: Create an 'admin' token
    token = generate_test_token("admin")
    
    # ACT: Send a perfectly formatted request
    response = client.post(
        "/v1/execute-tool",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tool_name": "send_email", 
            "arguments": {"recipient": "test@domain.com", "subject": "Test", "body": "Data"}
        }
    )
    
    # ASSERT: The API should permit it and return the validated arguments
    assert response.status_code == 200
    assert response.json()["status"] == "permitted"
    assert response.json()["tool"] == "send_email"

def test_reject_invalid_jwt(client):
    response = client.post(
        "/v1/execute-tool",
        headers={"Authorization": "Bearer invalid.token.value"},
        json={
            "tool_name": "query_database",
            "arguments": {"table_name": "users", "limit": 10},
        },
    )

    assert response.status_code == 401

def test_reject_unknown_tool(client):
    token = generate_test_token("admin")

    response = client.post(
        "/v1/execute-tool",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tool_name": "nonexistent_tool",
            "arguments": {},
        },
    )

    assert response.status_code == 404
    assert "Unrecognized tool" in response.json()["detail"]

def test_reject_malformed_arguments(client):
    token = generate_test_token("admin")

    response = client.post(
        "/v1/execute-tool",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tool_name": "send_email",
            "arguments": {
                "recipient": "test@domain.com",
                "subject": "Test",
                # Required "body" field is missing.
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]

def test_rate_limit_enforcement(client, monkeypatch):
    token = generate_test_token("admin")
    redis_key = "rate_limit:admin"

    # Lower the limit so the test needs only two requests.
    monkeypatch.setitem(RATE_LIMITS, "admin", 1)

    # Reset only this test's counter.
    with sync_redis.Redis.from_url(REDIS_URL) as redis_client:
        redis_client.delete(redis_key)

        try:
            headers = {"Authorization": f"Bearer {token}"}
            payload = {
                "tool_name": "send_email",
                "arguments": {
                    "recipient": "test@domain.com",
                    "subject": "Test",
                    "body": "Data",
                },
            }

            first_response = client.post(
                "/v1/execute-tool",
                headers=headers,
                json=payload,
            )

            second_response = client.post(
                "/v1/execute-tool",
                headers=headers,
                json=payload,
            )

            assert first_response.status_code == 200
            assert second_response.status_code == 429

        finally:
            redis_client.delete(redis_key)