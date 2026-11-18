from fastapi.testclient import TestClient


def test_dataset_creation(client: TestClient, auth_headers: dict):
    """Scenario 5: Dataset Creation"""
    payload = {
        "name": "E-Commerce Refund Test Suite",
        "description": "Evaluation cases for testing refund policies",
        "domain": "customer_support"
    }
    response = client.post("/api/v1/datasets", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "E-Commerce Refund Test Suite"
    assert data["domain"] == "customer_support"


def test_test_case_creation_and_export(client: TestClient, auth_headers: dict):
    """Scenario 6: Test Case Creation, Validation, and JSON Export"""
    # Create dataset first
    ds_res = client.post(
        "/api/v1/datasets",
        json={"name": "Tools Test Dataset", "domain": "support"},
        headers=auth_headers
    )
    dataset_id = ds_res.json()["id"]

    # Add test case
    tc_payload = {
        "test_case_id": "TC-999",
        "name": "Verify order refund status",
        "description": "Test case for order 1002 refund verification",
        "user_input": "Is order ORD-1002 refundable?",
        "difficulty_level": "medium",
        "tags": ["refunds", "tool_calling"],
        "expected_behavior": "Call check_refund_eligibility for ORD-1002",
        "expected_tool_calls": [
            {"tool_name": "check_refund_eligibility", "arguments": {"order_id": "ORD-1002"}}
        ],
        "expected_output": {"contains_keywords": ["eligible", "ORD-1002"]},
        "max_allowed_latency_ms": 3000,
        "evaluation_criteria": {"require_tool_selection": True}
    }
    tc_res = client.post(f"/api/v1/datasets/{dataset_id}/test-cases", json=tc_payload, headers=auth_headers)
    assert tc_res.status_code == 201
    tc_data = tc_res.json()
    assert tc_data["test_case_id"] == "TC-999"

    # Export dataset to JSON
    export_res = client.get(f"/api/v1/datasets/{dataset_id}/export", headers=auth_headers)
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert len(export_data["test_cases"]) == 1
    assert export_data["test_cases"][0]["test_case_id"] == "TC-999"
