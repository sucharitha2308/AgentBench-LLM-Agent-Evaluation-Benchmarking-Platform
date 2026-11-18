# AgentBench System Architecture

## 1. Overview & Architectural Principles

AgentBench is a modular, high-reliability platform engineered to evaluate, benchmark, debug, and monitor LLM-powered AI agents. It provides deterministic test harness capabilities, model-independent provider abstractions, automated multi-dimensional evaluation criteria, and execution tracing with automated credential redaction.

```
                      ┌──────────────────────────────────────┐
                      │    Presentation Layer (React + Vite)  │
                      │  Overview • Agents • Datasets • Trace │
                      └──────────────────┬───────────────────┘
                                         │ REST API (JSON)
                                         ▼
                      ┌──────────────────────────────────────┐
                      │      API Gateway (FastAPI v0.110+)   │
                      │  Auth • Rate Limiting • Validation    │
                      └──────────────────┬───────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
┌─────────────────┐            ┌───────────────────┐            ┌──────────────────┐
│ Services Layer  │            │ Agent Execution   │            │ Evaluation Engine│
│ • Auth Service  │            │ • Direct LLM      │            │ • Task Success   │
│ • Agent Service │◄───────────┤ • LangGraph       ├───────────►│ • Tool Selection │
│ • Dataset Svc   │            │ • External HTTP   │            │ • Arguments Acc. │
│ • Analytics Svc │            │ • Tool Registry   │            │ • JSON Schema    │
│ • Regression    │            └─────────┬─────────┘            │ • Latency / Cost │
└────────┬────────┘                      │                      │ • Safety Check   │
         │                               ▼                      └──────────────────┘
         │                     ┌───────────────────┐
         │                     │ Provider Layer    │
         │                     │ • OpenAI Provider │
         │                     │ • Gemini Provider │
         │                     │ • Mock Provider   │
         │                     └───────────────────┘
         ▼                               │
┌──────────────────────────────┐         │
│ Data Layer                   │         ▼
│ • PostgreSQL (SQLAlchemy 2.0)│ ┌──────────────────────────────┐
│ • Redis Cache / Celery Broker│ │ External LLM APIs (Encrypted)│
└──────────────────────────────┘ └──────────────────────────────┘
```

## 2. Layer Descriptions

### Layer 1: Presentation Layer (Frontend)
- **Framework**: React 18 with Vite and TypeScript.
- **Styling**: Tailwind CSS with dark SaaS aesthetic (dark navy/charcoal `#0B0F17`, indigo/cyan accents).
- **State Management**: TanStack Query (React Query) and native Context API.
- **Visualizations**: Recharts AreaChart, BarChart, and responsive timeline trace viewer.

### Layer 2: API Gateway Layer (FastAPI)
- Base URL `/api/v1` with automatic OpenAPI/Swagger documentation at `/docs`.
- Argon2 password verification and stateless JWT token authentication with configurable rotation.
- Dependency injection for database transactions and authenticated user context.

### Layer 3: Application Services
- **AuthService**: User onboarding, login, JWT issuance and refresh.
- **AgentService**: Agent lifecycle, configuration checkpoints (versions), connection probing.
- **DatasetService**: Dataset catalog, test cases, JSON import/export, dataset versioning.
- **EvaluationService**: Execution dispatch, progress tracking, run cancellation.
- **ComparisonService**: Model benchmarking, metric deltas, test-level differences, metric winner allocation.
- **RegressionService**: Automated degradation detection, severity rating, AI recommendations.
- **AnalyticsService**: System-wide KPIs, cost aggregation, success trends, failure categorization.
- **ReportService**: Executive report generation, CSV and JSON exports.

### Layer 4: Agent Execution & Tool Sandbox
- **Agent Adapters**: Base adapter pattern supporting Direct LLM agents, LangGraph orchestration, and external HTTP agents with SSRF prevention.
- **Tool Registry**: Deterministic controlled sandbox (`get_order`, `check_refund_eligibility`, `search_products`, `get_weather`).
- Unrestricted Python execution and arbitrary shell commands are strictly disallowed.

### Layer 5: LLM Provider Layer
- Unified `BaseLLMProvider` interface returning normalized `ProviderResponse` with `ProviderToolCall` and token usage metrics.
- Native integration with official `openai` and `google-genai` SDKs.
- Deterministic `MockProvider` for instant demo mode and automated offline testing.

### Layer 6: Multi-Dimensional Evaluation Engine
- Independent evaluator modules computing numeric scores, pass/fail status, categorical failure classification, and evidence payloads.

### Layer 7: Persistence & Background Processing
- SQLAlchemy 2.0 with PostgreSQL (and zero-config SQLite support for instant local runs).
- Redis queue and Celery worker integration with in-process async background manager fallback.
