export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  agent_type: 'direct_llm' | 'langgraph' | 'http';
  provider: 'openai' | 'gemini' | 'mock';
  model_name: string;
  system_prompt: string;
  temperature: number;
  max_output_tokens: number;
  output_format: 'text' | 'json';
  tools: Array<{
    name: string;
    description: string;
    parameters?: Record<string, any>;
  }>;
  http_endpoint?: string;
  is_sample: boolean;
  created_at: string;
  updated_at: string;
  versions_count?: number;
}

export interface AgentVersion {
  id: string;
  agent_id: string;
  version_number: number;
  commit_message: string;
  configuration_snapshot: Record<string, any>;
  created_at: string;
}

export interface TestCase {
  id: string;
  dataset_id: string;
  test_case_id: string;
  name: string;
  description?: string;
  user_input: string;
  difficulty_level: 'easy' | 'medium' | 'hard';
  tags: string[];
  expected_behavior: string;
  expected_tool_calls: Array<{
    tool_name: string;
    arguments: Record<string, any>;
  }>;
  expected_output: Record<string, any>;
  max_allowed_latency_ms: number;
  evaluation_criteria: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Dataset {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  domain: string;
  is_sample: boolean;
  test_case_count: number;
  created_at: string;
  updated_at: string;
}

export interface TestResult {
  id: string;
  evaluation_run_id: string;
  test_case_id?: string;
  test_case_identifier: string;
  name: string;
  status: 'PASS' | 'FAIL' | 'ERROR';
  duration_ms: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost: number;
  actual_response: string;
  actual_tool_calls: Array<{
    tool_name: string;
    arguments: Record<string, any>;
  }>;
  metrics: Record<string, {
    metric_name: string;
    metric_value: number;
    passed: boolean;
    explanation: string;
    evidence: Record<string, any>;
    failure_category?: string;
  }>;
  failure_category?: string;
  failure_explanation?: string;
  trace_id?: string;
  created_at: string;
}

export interface ExecutionTrace {
  id: string;
  evaluation_run_id: string;
  test_result_id?: string;
  test_case_identifier: string;
  steps: Array<{
    timestamp: string;
    event_type: string;
    content: any;
  }>;
  redacted_secrets_count: number;
  created_at: string;
}

export interface EvaluationRun {
  id: string;
  user_id: string;
  agent_id: string;
  dataset_id: string;
  name: string;
  status: 'PENDING' | 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  total_test_cases: number;
  completed_test_cases: number;
  passed_test_cases: number;
  failed_test_cases: number;
  error_count: number;
  aggregate_metrics: {
    task_success_rate?: number;
    tool_selection_accuracy?: number;
    tool_argument_accuracy?: number;
    structured_output_validity?: number;
    semantic_score?: number;
    safety_pass_rate?: number;
    average_latency_ms?: number;
    p50_latency_ms?: number;
    p95_latency_ms?: number;
    input_tokens?: number;
    output_tokens?: number;
    total_tokens?: number;
    estimated_cost_usd?: number;
    error_rate?: number;
  };
  agent_snapshot: Record<string, any>;
  dataset_snapshot: Record<string, any>;
  concurrency_limit: number;
  timeout_seconds: number;
  selected_evaluators: string[];
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface MetricDelta {
  metric_name: string;
  value_a: number;
  value_b: number;
  delta: number;
  percentage_change: number;
  winner: 'A' | 'B' | 'TIE';
}

export interface RunComparison {
  run_a: EvaluationRun;
  run_b: EvaluationRun;
  metric_comparisons: MetricDelta[];
  test_differences: Array<{
    test_case_identifier: string;
    name: string;
    status_a: string;
    status_b: string;
    status_differs: boolean;
    latency_a_ms: number;
    latency_b_ms: number;
    latency_delta_ms: number;
    failure_category_a?: string;
    failure_category_b?: string;
  }>;
  summary: string;
}

export interface RegressionAnalysis {
  baseline_run_id: string;
  current_run_id: string;
  total_regressions: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  regressed_cases: Array<{
    test_case_identifier: string;
    name: string;
    previous_status: string;
    current_status: string;
    previous_latency_ms: number;
    current_latency_ms: number;
    failure_category?: string;
    failure_explanation?: string;
  }>;
  metric_degradations: Array<{
    metric: string;
    baseline: string;
    current: string;
    degradation: string;
  }>;
  recommendation: string;
}

export interface OverviewMetrics {
  total_agents: number;
  total_datasets: number;
  total_evaluation_runs: number;
  total_test_cases_executed: number;
  overall_success_rate: number;
  overall_failure_rate: number;
  average_latency_ms: number;
  p95_latency_ms: number;
  total_tokens_consumed: number;
  total_estimated_cost_usd: number;
  average_tool_selection_accuracy: number;
  average_json_validity_rate: number;
  recent_runs: Array<{
    id: string;
    name: string;
    agent_name: string;
    status: string;
    success_rate: number;
    created_at: string;
    total_cases: number;
    passed: number;
    failed: number;
  }>;
  success_trend: Array<{
    run_name: string;
    success_rate: number;
    avg_latency: number;
    date: string;
  }>;
  failure_distribution: Array<{
    category: string;
    count: number;
  }>;
  model_comparison_overview: Array<{
    model: string;
    avg_success_rate: number;
    runs_count: number;
  }>;
}

export interface ProviderCredential {
  id: string;
  provider_name: string;
  key_alias: string;
  is_valid: boolean;
  last_verified_at?: string;
  created_at: string;
  masked_key: string;
}
