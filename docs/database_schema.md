# AgentBench Database Schema Documentation

Designed with SQLAlchemy 2.0 with PostgreSQL production compatibility (and SQLite development compatibility). All primary keys are UUIDs.

---

## Entity Relationship Overview

```
users (1) ────< agents (N) ────< agent_versions (N)
  │                 │
  │                 └────< evaluation_runs (N) ────< test_results (N) ────< execution_traces (1)
  │                              │
  ├────< datasets (N) ───────────┘
  │         │
  │         ├────< dataset_versions (N)
  │         └────< test_cases (N)
  │
  └────< provider_credentials (N)
```

---

## Tables & Schemas

### 1. `users`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `email` | VARCHAR(255) | UNIQUE, INDEX | User email |
| `hashed_password` | VARCHAR(255) | NOT NULL | Argon2 password hash |
| `full_name` | VARCHAR(255) | NULLABLE | Display name |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account state |
| `is_superuser` | BOOLEAN | DEFAULT FALSE | Administrator flag |
| `created_at` | TIMESTAMPTZ | INDEX | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update timestamp |

### 2. `agents`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | Agent UUID |
| `user_id` | VARCHAR(36) | FK(users.id, CASCADE) | Owner reference |
| `name` | VARCHAR(255) | NOT NULL | Agent label |
| `agent_type` | VARCHAR(50) | NOT NULL | `direct_llm`, `langgraph`, `http` |
| `provider` | VARCHAR(50) | NOT NULL | `openai`, `gemini`, `mock` |
| `model_name` | VARCHAR(100) | NOT NULL | Target model identifier |
| `system_prompt` | TEXT | NOT NULL | System instructions |
| `temperature` | FLOAT | DEFAULT 0.2 | Sampling temperature |
| `max_output_tokens`| INT | DEFAULT 2048 | Generation limit |
| `output_format` | VARCHAR(50) | DEFAULT 'text'| `text` or `json` |
| `tools` | JSON / JSONB | DEFAULT [] | Configured tools array |
| `http_endpoint` | VARCHAR(512) | NULLABLE | External webhook URL |
| `is_sample` | BOOLEAN | DEFAULT FALSE | Baseline sample flag |

### 3. `agent_versions`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | Version UUID |
| `agent_id` | VARCHAR(36) | FK(agents.id, CASCADE) | Agent reference |
| `version_number` | INT | NOT NULL | Incrementing version index |
| `commit_message` | VARCHAR(255) | NOT NULL | Change description |
| `configuration_snapshot` | JSON / JSONB | NOT NULL | Complete frozen config |

### 4. `datasets`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | Dataset UUID |
| `user_id` | VARCHAR(36) | FK(users.id, CASCADE) | Owner reference |
| `name` | VARCHAR(255) | NOT NULL | Dataset title |
| `domain` | VARCHAR(100) | DEFAULT 'customer_support' | Evaluation domain |
| `is_sample` | BOOLEAN | DEFAULT FALSE | Seeded sample suite flag |

### 5. `test_cases`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | Test case UUID |
| `dataset_id` | VARCHAR(36) | FK(datasets.id, CASCADE)| Dataset reference |
| `test_case_id` | VARCHAR(50) | NOT NULL, INDEX | Human readable ID (e.g. TC-001) |
| `name` | VARCHAR(255) | NOT NULL | Test name |
| `user_input` | TEXT | NOT NULL | Query prompt presented to agent |
| `difficulty_level`| VARCHAR(20) | DEFAULT 'medium' | `easy`, `medium`, `hard` |
| `tags` | JSON / JSONB | DEFAULT [] | Category and skill tags |
| `expected_behavior` | TEXT | NOT NULL | Expected agent behavior |
| `expected_tool_calls`| JSON / JSONB | DEFAULT [] | Expected tools and arguments |
| `expected_output` | JSON / JSONB | DEFAULT {} | Expected keywords / JSON schema |
| `max_allowed_latency_ms` | INT | DEFAULT 3500 | Max SLA threshold |
| `evaluation_criteria` | JSON / JSONB | DEFAULT {} | Criteria configuration |

### 6. `evaluation_runs`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | Evaluation run UUID |
| `user_id` | VARCHAR(36) | FK(users.id, CASCADE) | Owner reference |
| `agent_id` | VARCHAR(36) | FK(agents.id, CASCADE) | Evaluated agent |
| `dataset_id` | VARCHAR(36) | FK(datasets.id, CASCADE)| Target dataset |
| `name` | VARCHAR(255) | NOT NULL | Evaluation title |
| `status` | VARCHAR(50) | NOT NULL, INDEX | `PENDING`, `RUNNING`, `COMPLETED`, etc. |
| `total_test_cases` | INT | DEFAULT 0 | Total test count |
| `completed_test_cases` | INT | DEFAULT 0 | Executed test count |
| `passed_test_cases` | INT | DEFAULT 0 | Passed test count |
| `failed_test_cases` | INT | DEFAULT 0 | Failed test count |
| `aggregate_metrics` | JSON / JSONB | DEFAULT {} | Success rate, latency, cost, F1 |
| `agent_snapshot` | JSON / JSONB | NOT NULL | Immutable agent snapshot |
| `dataset_snapshot` | JSON / JSONB | NOT NULL | Immutable dataset snapshot |
| `concurrency_limit` | INT | DEFAULT 5 | Parallelism bound |
| `timeout_seconds` | INT | DEFAULT 30 | Execution timeout SLA |

### 7. `test_results`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | Result UUID |
| `evaluation_run_id` | VARCHAR(36) | FK(evaluation_runs.id, CASCADE) | Run reference |
| `test_case_identifier` | VARCHAR(50) | NOT NULL | e.g. TC-001 |
| `name` | VARCHAR(255) | NOT NULL | Test case name |
| `status` | VARCHAR(20) | NOT NULL, INDEX | `PASS`, `FAIL`, `ERROR` |
| `duration_ms` | INT | DEFAULT 0 | Latency in milliseconds |
| `input_tokens` | INT | DEFAULT 0 | Prompt token count |
| `output_tokens` | INT | DEFAULT 0 | Completion token count |
| `estimated_cost` | FLOAT | DEFAULT 0.0 | Estimated cost in USD |
| `actual_response` | TEXT | NOT NULL | Agent response text |
| `actual_tool_calls` | JSON / JSONB | DEFAULT [] | Recorded tool calls |
| `metrics` | JSON / JSONB | DEFAULT {} | Evaluator outputs |
| `failure_category` | VARCHAR(100) | NULLABLE | Categorical root cause |
| `failure_explanation` | TEXT | NULLABLE | Human-readable explanation |
| `trace_id` | VARCHAR(36) | NULLABLE | Execution trace reference |

### 8. `execution_traces`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | Trace UUID |
| `evaluation_run_id` | VARCHAR(36) | FK(evaluation_runs.id, CASCADE) | Run reference |
| `test_result_id` | VARCHAR(36) | FK(test_results.id, CASCADE) | Result reference |
| `test_case_identifier`| VARCHAR(50) | NOT NULL | e.g. TC-001 |
| `steps` | JSON / JSONB | NOT NULL | Timeline steps (prompts, tool calls, results) |
| `redacted_secrets_count` | INT | DEFAULT 0 | Number of masked secret keys |

### 9. `provider_credentials`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | Credential UUID |
| `user_id` | VARCHAR(36) | FK(users.id, CASCADE) | Owner reference |
| `provider_name` | VARCHAR(50) | NOT NULL | `openai`, `gemini` |
| `key_alias` | VARCHAR(100) | NOT NULL | Friendly label |
| `encrypted_api_key` | VARCHAR(1024) | NOT NULL | AES-GCM encrypted ciphertext |
| `is_valid` | BOOLEAN | DEFAULT TRUE | Validation status |
