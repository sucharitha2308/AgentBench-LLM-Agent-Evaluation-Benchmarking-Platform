# AgentBench REST API Documentation

Base Endpoint: `/api/v1`  
Interactive OpenAPI Documentation: `http://localhost:8000/docs`

---

## 1. Authentication (`/api/v1/auth`)

### `POST /auth/register`
Create a new user account.
- **Request Body**:
  ```json
  {
    "email": "engineer@company.com",
    "password": "StrongPassword123!",
    "full_name": "Senior AI Engineer"
  }
  ```
- **Response**: `201 Created` with User object (password omitted).

### `POST /auth/login`
Authenticate and obtain JWT access and refresh tokens.
- **Request Body**:
  ```json
  {
    "email": "engineer@company.com",
    "password": "StrongPassword123!"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "token_type": "bearer"
  }
  ```

### `POST /auth/refresh`
Refresh an expired access token using a valid refresh token.

### `GET /auth/me`
Retrieve currently authenticated user profile. Requires `Authorization: Bearer <token>`.

---

## 2. Agent Management (`/api/v1/agents`)

### `GET /agents`
List all agents owned by user plus sample baseline agents.

### `POST /agents`
Register a new agent configuration.
- **Parameters**: `name`, `description`, `agent_type` (`direct_llm`, `langgraph`, `http`), `provider` (`mock`, `openai`, `gemini`), `model_name`, `system_prompt`, `temperature`, `max_output_tokens`, `output_format` (`text`, `json`), `tools` list.

### `GET /agents/{id}`
Retrieve details for a single agent.

### `PUT /agents/{id}`
Update agent configuration. Automatically creates a new version checkpoint in `agent_versions`.

### `DELETE /agents/{id}`
Delete custom agent and its associated version history.

### `GET /agents/{id}/versions`
Retrieve immutable configuration history snapshots for this agent.

### `POST /agents/test-connection`
Probe external LLM provider connectivity and measure roundtrip response latency.

### `POST /agents/credentials`
Store and encrypt provider API key (AES-GCM at rest).

---

## 3. Dataset Management (`/api/v1/datasets`)

### `GET /datasets`
List all available evaluation datasets.

### `POST /datasets`
Create a new evaluation dataset.

### `GET /datasets/{id}/test-cases`
List test cases contained within the dataset.

### `POST /datasets/{id}/test-cases`
Add a ground-truth test case to the dataset with expected tool calls, JSON schemas, and latency SLAs.

### `GET /datasets/{id}/export`
Export the complete dataset into standard AgentBench JSON format.

### `POST /datasets/{id}/import`
Bulk import test cases from a JSON payload.

---

## 4. Evaluations & Tracing (`/api/v1/evaluations`)

### `POST /evaluations`
Launch an evaluation run.
- **Request Body**:
  ```json
  {
    "agent_id": "agent-uuid",
    "dataset_id": "dataset-uuid",
    "name": "GPT-4o Customer Support Benchmark",
    "concurrency_limit": 5,
    "timeout_seconds": 30,
    "selected_evaluators": ["task_success", "tool_selection", "tool_argument", "structured_output", "performance"]
  }
  ```

### `GET /evaluations/{id}`
Fetch evaluation run progress, status (`QUEUED`, `RUNNING`, `COMPLETED`, `CANCELLED`), and aggregate metrics.

### `POST /evaluations/{id}/cancel`
Cancel an active ongoing evaluation run safely.

### `GET /evaluations/{id}/results`
Retrieve individual test results, status (`PASS`, `FAIL`, `ERROR`), duration, token count, cost, and failure categories.

### `GET /evaluations/traces/{trace_id}`
Retrieve full timeline execution steps for a specific test execution (prompts, agent decisions, tool execution, tool output, final response with redacted secrets).

### `GET /evaluations/regression/analyze`
Analyze performance regressions between baseline run and candidate run.

---

## 5. Analytics & Reports (`/api/v1/analytics`, `/api/v1/reports`)

### `GET /analytics/overview`
Platform-wide evaluation KPIs, success rate trends, and failure category distribution.

### `POST /analytics/compare`
Side-by-side benchmarking comparison of two evaluation runs with metric deltas and winner indicators.

### `GET /reports/{run_id}`
Executive evaluation report with recommendations and breakdown.

### `GET /reports/{run_id}/export?format=csv`
Download evaluation report in CSV or JSON format.

---

## 6. Health Endpoints

- `GET /health` - API liveness probe.
- `GET /ready` - Database connection readiness probe.
