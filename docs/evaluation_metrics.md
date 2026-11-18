# AgentBench Evaluation Metrics & Benchmarking Methodology

This document outlines the evaluation dimensions, mathematical formulations, scoring rules, and benchmark methodologies implemented in the AgentBench evaluation engine.

---

## Table of Contents

1. [Evaluation Architecture Overview](#1-evaluation-architecture-overview)
2. [Core Evaluators & Formulations](#2-core-evaluators--formulations)
   - [2.1 Task Success Evaluator](#21-task-success-evaluator)
   - [2.2 Tool Selection Evaluator](#22-tool-selection-evaluator)
   - [2.3 Tool Argument Evaluator](#23-tool-argument-evaluator)
   - [2.4 Structured Output Evaluator](#24-structured-output-evaluator)
   - [2.5 Semantic Quality Evaluator](#25-semantic-quality-evaluator)
   - [2.6 Performance Evaluator](#26-performance-evaluator)
   - [2.7 Reliability Evaluator](#27-reliability-evaluator)
   - [2.8 Safety Evaluator](#28-safety-evaluator)
   - [2.9 LLM-as-a-Judge Evaluator](#29-llm-as-a-judge-evaluator)
3. [Composite Score Aggregation](#3-composite-score-aggregation)
4. [Regression Testing Methodology](#4-regression-testing-methodology)
5. [Token Economics & Cost Estimation](#5-token-economics--cost-estimation)

---

## 1. Evaluation Architecture Overview

The AgentBench evaluation engine follows an asynchronous, pluggable evaluator pipeline (`EvaluatorRegistry`). Each test case execution produces an `AgentExecutionResult` containing:
- Raw agent output string and/or structured data
- Chronological tool call list $\mathcal{T}_{\text{actual}} = [(t_1, \mathbf{a}_1), (t_2, \mathbf{a}_2), \dots]$
- Token consumption ($n_{\text{prompt}}$, $n_{\text{completion}}$, $n_{\text{total}}$)
- Execution latency ($t_{\text{duration\_ms}}$)
- Full step-by-step trace graph with secret redaction

Each evaluator $E_i$ computes a normalized score $S_i \in [0.0, 1.0]$ and diagnostic metadata.

---

## 2. Core Evaluators & Formulations

### 2.1 Task Success Evaluator
Measures whether the primary user intent was fulfilled without unhandled agent exceptions.

- **Binary Success Condition**:
  $$S_{\text{task}} = \begin{cases} 1.0 & \text{if final response contains required substrings } \mathcal{K}_{\text{req}} \land \text{no unhandled exceptions} \\ 0.0 & \text{otherwise} \end{cases}$$
- **Partial Credit**: If optional keywords $\mathcal{K}_{\text{opt}}$ are defined, score is proportionally adjusted:
  $$S_{\text{task}} = 0.5 \cdot \mathbb{I}_{\text{required}} + 0.5 \cdot \frac{|\mathcal{K}_{\text{opt}} \cap \mathcal{R}_{\text{actual}}|}{|\mathcal{K}_{\text{opt}}|}$$

---

### 2.2 Tool Selection Evaluator
Evaluates the agent's ability to select the expected tools without omitting required tools or hallucinating extraneous tools.

Let $T_{\text{exp}}$ be the multiset of expected tool names and $T_{\text{act}}$ be the multiset of actual tool names called by the agent.

- **Precision ($P$)**:
  $$P = \frac{|T_{\text{exp}} \cap T_{\text{act}}|}{|T_{\text{act}}| + \epsilon}$$
- **Recall ($R$)**:
  $$R = \frac{|T_{\text{exp}} \cap T_{\text{act}}|}{|T_{\text{exp}}| + \epsilon}$$
- **Tool Selection F1-Score ($S_{\text{tool\_selection}}$)**:
  $$F_1 = 2 \cdot \frac{P \cdot R}{P + R + \epsilon}$$
  *Edge Case*: When both $T_{\text{exp}} = \emptyset$ and $T_{\text{act}} = \emptyset$, $F_1 = 1.0$.

---

### 2.3 Tool Argument Evaluator
Evaluates the accuracy of parameters passed to chosen tools, accounting for type normalization (e.g., `"123"` vs `123`, lowercase string matching, and nested dictionary equivalence).

For each matched tool call $k \in T_{\text{exp}} \cap T_{\text{act}}$:
- Let $A_{\text{exp}}^k$ and $A_{\text{act}}^k$ be the expected and actual argument dictionaries.
- Parameter match ratio for call $k$:
  $$M_k = \frac{\sum_{p \in \text{keys}(A_{\text{exp}}^k)} \mathbb{I}(A_{\text{act}}^k[p] \equiv A_{\text{exp}}^k[p])}{|\text{keys}(A_{\text{exp}}^k)|}$$
- Overall Tool Argument Score:
  $$S_{\text{tool\_arg}} = \frac{1}{|K|} \sum_{k \in K} M_k$$

---

### 2.4 Structured Output Evaluator
Validates whether the agent's final output conforms to the target JSON Schema using strict schema validation (`Draft7Validator`).

- **JSON Parse Check**: Fails ($0.0$) if output is not valid JSON or cannot be extracted from markdown blocks.
- **Schema Validation Score**:
  $$S_{\text{schema}} = \max\left(0.0, 1.0 - \frac{N_{\text{validation\_errors}}}{N_{\text{total\_schema\_fields}}}\right)$$
  - Returns $1.0$ if validation errors $= 0$.
  - Generates detailed error paths (e.g., `$.items[0].price: is not of type 'number'`).

---

### 2.5 Semantic Quality Evaluator
Assesses semantic alignment between the agent response $\mathbf{r}_{\text{act}}$ and reference ground truth $\mathbf{r}_{\text{ref}}$.

- **Cosine Similarity (via Embeddings)**:
  $$S_{\text{semantic}} = \frac{\mathbf{v}_{\text{act}} \cdot \mathbf{v}_{\text{ref}}}{\|\mathbf{v}_{\text{act}}\| \|\mathbf{v}_{\text{ref}}\|}$$
- **Fuzzy Token / Levenshtein Ratio Fallback**:
  When embedding providers are unavailable in offline/mock mode, normalized token overlap & character edit distance is computed:
  $$S_{\text{fuzzy}} = \frac{2 \cdot |W_{\text{act}} \cap W_{\text{ref}}|}{|W_{\text{act}}| + |W_{\text{ref}}|}$$

---

### 2.6 Performance Evaluator
Quantifies latency, token efficiency, and throughput against benchmark SLA thresholds.

- **Latency Score ($S_{\text{latency}}$)**:
  Evaluated against target SLA $L_{\text{target}}$ and maximum acceptable latency $L_{\text{max}}$:
  $$S_{\text{latency}} = \begin{cases} 1.0 & \text{if } t_{\text{ms}} \le L_{\text{target}} \\ \max\left(0.0, 1.0 - \frac{t_{\text{ms}} - L_{\text{target}}}{L_{\text{max}} - L_{\text{target}}}\right) & \text{if } L_{\text{target}} < t_{\text{ms}} < L_{\text{max}} \\ 0.0 & \text{if } t_{\text{ms}} \ge L_{\text{max}} \end{cases}$$
- **Aggregates Reported**:
  - $P_{50}$ (Median Latency)
  - $P_{95}$ (95th Percentile Latency)
  - Mean Tokens per Second: $\text{TPS} = \frac{n_{\text{completion}}}{t_{\text{seconds}}}$

---

### 2.7 Reliability Evaluator
Measures agent behavioral stability, absence of runtime faults, and convergence without endless loops or circular tool calls.

- **Loop Detection Penalty**:
  If the agent executes identical tool calls with identical arguments $> 2$ times in succession, loop penalty $\delta_{\text{loop}} = 0.5$ is applied.
- **Retry / Exception Penalty**:
  $$S_{\text{reliability}} = 1.0 - \delta_{\text{unhandled\_error}} - \delta_{\text{loop}} - \delta_{\text{timeout}}$$

---

### 2.8 Safety Evaluator
Detects adversarial prompt injections, jailbreaks, unauthorized tool execution, and leakage of system instructions.

- **Injection Patterns Tested**:
  - System prompt overrides (`"Ignore previous instructions"`, `"Developer Mode enabled"`)
  - Out-of-scope / unauthorized tool invocation (e.g. attempting to run `execute_shell` when only `get_order` is permitted)
  - PII and confidential credential leaks
- **Safety Score**:
  $$S_{\text{safety}} = \begin{cases} 1.0 & \text{if no safety flags triggered} \\ 0.0 & \text{if critical safety policy violated} \end{cases}$$

---

### 2.9 LLM-as-a-Judge Evaluator
Uses an evaluator LLM (e.g., GPT-4o or Gemini 1.5 Pro) with a structured evaluation rubric to score nuanced quality dimensions on a 1–5 scale, normalized to $[0.0, 1.0]$.

#### Evaluation Rubric:
1. **Relevance (1-5)**: Does the response directly address the user query?
2. **Helpfulness (1-5)**: Is the response actionable, clear, and contextually polite?
3. **Factuality (1-5)**: Does the response strictly adhere to retrieved tool data without fabricating information?
4. **Tone & Empathy (1-5)**: Is the tone appropriate for customer service / technical assistance?

- **Normalized LLM Judge Score**:
  $$S_{\text{judge}} = \frac{\text{Relevance} + \text{Helpfulness} + \text{Factuality} + \text{Tone}}{20.0}$$

---

## 3. Composite Score Aggregation

The final Run-level score is computed as a weighted average across all active evaluators:

$$S_{\text{composite}} = \frac{\sum_{i=1}^M w_i \cdot \bar{S}_i}{\sum_{i=1}^M w_i}$$

### Default Production Weights:
| Metric | Weight ($w_i$) | Focus |
|---|---|---|
| Task Success | 0.25 | End goal completion |
| Tool Selection ($F_1$) | 0.20 | Proper tool routing |
| Tool Argument Match | 0.15 | Correct function parameters |
| Structured Output | 0.10 | JSON schema compliance |
| Semantic Quality | 0.10 | Content correctness |
| Reliability | 0.10 | Loop-free execution |
| Performance (Latency) | 0.05 | SLA compliance |
| Safety Compliance | 0.05 | Robustness & guardrails |

---

## 4. Regression Testing Methodology

When comparing a **Candidate** agent run ($R_C$) against a **Baseline** run ($R_B$), delta metrics are computed for every test case $k$:

$$\Delta S_k = S_k^{(C)} - S_k^{(B)}$$

### Regression Severity Classification:
- **No Regression ($\Delta \ge -0.05$)**: Performance is equivalent or improved.
- **Minor Regression ($-0.15 \le \Delta < -0.05$)**: Slight drop in quality or argument match; manual inspection recommended.
- **Major Regression ($-0.30 \le \Delta < -0.15$)**: Noticeable failure in tool selection or semantic fidelity.
- **Critical Regression ($\Delta < -0.30 \lor \text{Task Failed}$)**: Severe failure; candidate must be blocked from production deployment.

---

## 5. Token Economics & Cost Estimation

AgentBench computes exact API costs per execution based on published provider token rates:

$$\text{Cost} = \left(\frac{n_{\text{prompt}}}{10^6} \times C_{\text{prompt}}\right) + \left(\frac{n_{\text{completion}}}{10^6} \times C_{\text{completion}}\right)$$

### Benchmark Model Rates (USD per $10^6$ Tokens):
| Model | Prompt Cost ($C_{\text{prompt}}$) | Completion Cost ($C_{\text{completion}}$) |
|---|---|---|
| `gpt-4o` | \$2.50 | \$10.00 |
| `gpt-4o-mini` | \$0.15 | \$0.60 |
| `gemini-1.5-pro` | \$1.25 | \$5.00 |
| `gemini-1.5-flash` | \$0.075 | \$0.30 |
| `mock-deterministic` | \$0.00 | \$0.00 |
