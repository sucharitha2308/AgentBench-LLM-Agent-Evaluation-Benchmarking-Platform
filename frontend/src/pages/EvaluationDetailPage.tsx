import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  PlayCircle,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Coins,
  Cpu,
  Download,
  ShieldCheck,
  Search,
  Filter,
  Eye,
  FileText,
  StopCircle,
  ExternalLink,
  ChevronRight,
  ArrowLeft,
  X,
} from 'lucide-react';
import { apiClient } from '../services/api';
import { EvaluationRun, TestResult, ExecutionTrace } from '../types';

export const EvaluationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [run, setRun] = useState<EvaluationRun | null>(null);
  const [results, setResults] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PASS' | 'FAIL' | 'ERROR'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected test case for trace view modal
  const [selectedResult, setSelectedResult] = useState<TestResult | null>(null);
  const [trace, setTrace] = useState<ExecutionTrace | null>(null);
  const [traceLoading, setTraceLoading] = useState(false);

  const fetchRun = async () => {
    if (!id) return;
    try {
      const [runRes, resultsRes] = await Promise.all([
        apiClient.get<EvaluationRun>(`/evaluations/${id}`),
        apiClient.get<TestResult[]>(`/evaluations/${id}/results`),
      ]);
      setRun(runRes.data);
      setResults(resultsRes.data);
    } catch (err) {
      console.error('Failed to fetch evaluation details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRun();

    // Live polling if run is active
    let interval: any = null;
    if (run?.status === 'RUNNING' || run?.status === 'QUEUED') {
      interval = setInterval(fetchRun, 1500);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [id, run?.status]);

  const handleCancel = async () => {
    if (!id || !window.confirm('Cancel this active evaluation run?')) return;
    try {
      await apiClient.post(`/evaluations/${id}/cancel`);
      fetchRun();
    } catch (err) {
      alert('Failed to cancel evaluation run.');
    }
  };

  const handleDownload = async (format: 'csv' | 'json') => {
    if (!id) return;
    try {
      const res = await apiClient.get(`/reports/${id}/export?format=${format}`, {
        responseType: 'blob',
      });
      const blob = new Blob([res.data], {
        type: format === 'csv' ? 'text/csv;charset=utf-8;' : 'application/json;charset=utf-8;',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `agentbench_report_${id.slice(0, 8)}.${format}`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export evaluation report:', err);
      alert('Failed to export evaluation report.');
    }
  };

  const openTraceModal = async (result: TestResult) => {
    setSelectedResult(result);
    setTrace(null);
    setTraceLoading(true);

    if (result.trace_id) {
      try {
        const res = await apiClient.get<ExecutionTrace>(`/evaluations/traces/${result.trace_id}`);
        setTrace(res.data);
      } catch (err) {
        console.error('Failed to load trace:', err);
      } finally {
        setTraceLoading(false);
      }
    } else {
      setTraceLoading(false);
    }
  };

  const filteredResults = results.filter((r) => {
    if (statusFilter !== 'ALL' && r.status !== statusFilter) return false;
    if (
      searchQuery &&
      !r.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !r.test_case_identifier.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  if (loading && !run) {
    return (
      <div className="py-20 flex flex-col items-center justify-center space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>
        <span className="text-xs text-gray-400">Loading evaluation run...</span>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="text-center py-20 text-gray-400 text-sm">
        Evaluation run not found.
      </div>
    );
  }

  const metrics = run.aggregate_metrics || {};
  const progressPct =
    run.total_test_cases > 0
      ? Math.round((run.completed_test_cases / run.total_test_cases) * 100)
      : 0;

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/evaluations')}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-[#1E293B] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-2.5">
              <h2 className="text-lg font-bold text-white tracking-tight">{run.name}</h2>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-semibold ${
                  run.status === 'COMPLETED'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : run.status === 'RUNNING'
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 animate-pulse'
                    : run.status === 'CANCELLED'
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                }`}
              >
                {run.status}
              </span>
            </div>
            <div className="flex items-center space-x-3 text-xs text-gray-400 mt-1">
              <span>Agent: {run.agent_snapshot?.name}</span>
              <span>•</span>
              <span>Dataset: {run.dataset_snapshot?.name}</span>
              <span>•</span>
              <span>{new Date(run.created_at).toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {run.status === 'RUNNING' && (
            <button
              onClick={handleCancel}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-medium transition-colors"
            >
              <StopCircle className="w-3.5 h-3.5" />
              <span>Cancel Run</span>
            </button>
          )}

          <button
            onClick={() => handleDownload('csv')}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-[#1E293B] hover:bg-[#2D3748] text-gray-300 hover:text-white text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={() => handleDownload('json')}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-[#1E293B] hover:bg-[#2D3748] text-gray-300 hover:text-white text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* Live Progress Bar if Running */}
      {run.status === 'RUNNING' && (
        <div className="p-4 rounded-2xl bg-[#111827] border border-cyan-500/30">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="font-medium text-cyan-400 flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
              <span>Live Evaluation in Progress...</span>
            </span>
            <span className="font-mono text-gray-300">
              {run.completed_test_cases} / {run.total_test_cases} ({progressPct}%)
            </span>
          </div>
          <div className="w-full h-2 rounded-full bg-[#0B0F17] overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Aggregate Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
        <div className="p-3.5 rounded-xl bg-[#111827] border border-[#1F2937]">
          <span className="text-[10px] text-gray-500 block uppercase font-medium">Task Success</span>
          <span className="text-xl font-bold text-white font-mono mt-0.5 block">
            {metrics.task_success_rate !== undefined ? `${metrics.task_success_rate}%` : '--'}
          </span>
          <span className="text-[10px] text-emerald-400 font-mono">
            {run.passed_test_cases} passed / {run.failed_test_cases} failed
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#111827] border border-[#1F2937]">
          <span className="text-[10px] text-gray-500 block uppercase font-medium">Tool Accuracy</span>
          <span className="text-xl font-bold text-indigo-400 font-mono mt-0.5 block">
            {metrics.tool_selection_accuracy !== undefined ? `${metrics.tool_selection_accuracy}%` : '--'}
          </span>
          <span className="text-[10px] text-gray-400 font-mono">Precision/Recall F1</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#111827] border border-[#1F2937]">
          <span className="text-[10px] text-gray-500 block uppercase font-medium">JSON Validity</span>
          <span className="text-xl font-bold text-cyan-400 font-mono mt-0.5 block">
            {metrics.structured_output_validity !== undefined ? `${metrics.structured_output_validity}%` : '--'}
          </span>
          <span className="text-[10px] text-gray-400 font-mono">Schema constraints</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#111827] border border-[#1F2937]">
          <span className="text-[10px] text-gray-500 block uppercase font-medium">Avg Latency</span>
          <span className="text-xl font-bold text-white font-mono mt-0.5 block">
            {metrics.average_latency_ms ? `${metrics.average_latency_ms}ms` : '--'}
          </span>
          <span className="text-[10px] text-gray-400 font-mono">P95: {metrics.p95_latency_ms || 0}ms</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#111827] border border-[#1F2937]">
          <span className="text-[10px] text-gray-500 block uppercase font-medium">Tokens Used</span>
          <span className="text-xl font-bold text-white font-mono mt-0.5 block">
            {metrics.total_tokens ? metrics.total_tokens.toLocaleString() : '--'}
          </span>
          <span className="text-[10px] text-gray-400 font-mono">In: {metrics.input_tokens || 0}</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#111827] border border-[#1F2937]">
          <span className="text-[10px] text-gray-500 block uppercase font-medium">Estimated Cost</span>
          <span className="text-xl font-bold text-amber-400 font-mono mt-0.5 block">
            ${metrics.estimated_cost_usd !== undefined ? metrics.estimated_cost_usd : '0.00'}
          </span>
          <span className="text-[10px] text-gray-400 font-mono">USD</span>
        </div>
      </div>

      {/* Test Results Section */}
      <div className="rounded-2xl bg-[#111827] border border-[#1F2937] p-5">
        {/* Table Filters & Search */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div className="flex items-center space-x-1.5 bg-[#0B0F17] p-1 rounded-xl border border-[#1F2937]">
            {(['ALL', 'PASS', 'FAIL', 'ERROR'] as const).map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                  statusFilter === st
                    ? 'bg-[#1E293B] text-white shadow-sm'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search test case or ID..."
              className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Results Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#1F2937] text-gray-400">
                <th className="pb-3 px-3 font-medium">Test ID</th>
                <th className="pb-3 px-3 font-medium">Case Name</th>
                <th className="pb-3 px-3 font-medium">Status</th>
                <th className="pb-3 px-3 font-medium">Duration</th>
                <th className="pb-3 px-3 font-medium">Cost</th>
                <th className="pb-3 px-3 font-medium">Failure Category</th>
                <th className="pb-3 px-3 font-medium text-right">Trace Timeline</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2937]/50">
              {filteredResults.map((r) => (
                <tr key={r.id} className="hover:bg-[#1E293B]/40 transition-colors">
                  <td className="py-2.5 px-3 font-mono text-[11px] font-semibold text-indigo-400">
                    {r.test_case_identifier}
                  </td>
                  <td className="py-2.5 px-3 font-medium text-gray-200 max-w-xs truncate">{r.name}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold font-mono ${
                        r.status === 'PASS'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : r.status === 'ERROR'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {r.status === 'PASS' ? (
                        <CheckCircle2 className="w-2.5 h-2.5" />
                      ) : (
                        <XCircle className="w-2.5 h-2.5" />
                      )}
                      <span>{r.status}</span>
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-gray-400 text-[11px]">{r.duration_ms}ms</td>
                  <td className="py-2.5 px-3 font-mono text-gray-400 text-[11px]">${r.estimated_cost.toFixed(6)}</td>
                  <td className="py-2.5 px-3 text-gray-400 text-[11px]">
                    {r.failure_category ? (
                      <span className="text-rose-400 font-mono bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
                        {r.failure_category}
                      </span>
                    ) : (
                      <span className="text-gray-500">—</span>
                    )}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <button
                      onClick={() => openTraceModal(r)}
                      className="px-2.5 py-1 rounded-lg bg-indigo-600/15 hover:bg-indigo-600/30 text-indigo-300 hover:text-white text-xs font-medium transition-colors inline-flex items-center space-x-1"
                    >
                      <Eye className="w-3 h-3" />
                      <span>Trace</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Execution Trace Timeline Modal */}
      {selectedResult && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-[#1F2937] rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6 shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-[#1F2937] mb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs font-bold text-indigo-400">
                    {selectedResult.test_case_identifier}
                  </span>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.2 rounded font-semibold ${
                      selectedResult.status === 'PASS'
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : 'bg-rose-500/10 text-rose-400'
                    }`}
                  >
                    {selectedResult.status}
                  </span>
                </div>
                <h3 className="font-bold text-white text-base mt-1">{selectedResult.name}</h3>
              </div>
              <button
                onClick={() => setSelectedResult(null)}
                className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-[#1E293B]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Evaluator Breakdown Cards */}
            <div className="mb-6">
              <span className="text-[10px] uppercase font-semibold text-gray-400 tracking-wider block mb-2">
                Independent Evaluator Outcomes
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {Object.entries(selectedResult.metrics || {}).map(([key, outcome]) => (
                  <div
                    key={key}
                    className={`p-2.5 rounded-xl border text-xs ${
                      outcome.passed
                        ? 'bg-emerald-500/5 border-emerald-500/20'
                        : 'bg-rose-500/5 border-rose-500/20'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-200 capitalize">
                        {key.replace('_', ' ')}
                      </span>
                      <span
                        className={`text-[10px] font-mono font-bold ${
                          outcome.passed ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {outcome.passed ? 'PASS' : 'FAIL'}
                      </span>
                    </div>
                    <div className="text-[11px] text-gray-400 line-clamp-2 leading-tight">
                      {outcome.explanation}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Step-by-Step Execution Trace Timeline */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] uppercase font-semibold text-gray-400 tracking-wider">
                  Execution Trace Timeline
                </span>
                <span className="text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                  Secrets Redacted
                </span>
              </div>

              {traceLoading ? (
                <div className="py-8 text-center text-xs text-gray-500">Loading trace steps...</div>
              ) : trace && trace.steps.length > 0 ? (
                <div className="space-y-3 relative pl-6 before:content-[''] before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#1F2937]">
                  {trace.steps.map((step, idx) => (
                    <div key={idx} className="relative text-xs">
                      {/* Node bullet */}
                      <span className="absolute -left-6 top-1.5 w-2 h-2 rounded-full bg-indigo-500 ring-4 ring-[#111827]"></span>

                      <div className="p-3.5 rounded-xl bg-[#0B0F17] border border-[#1F2937] space-y-1.5">
                        <div className="flex items-center justify-between text-[10px] text-gray-500">
                          <span className="font-mono font-semibold text-indigo-400 uppercase">
                            {step.event_type}
                          </span>
                          <span>{new Date(step.timestamp).toLocaleTimeString()}</span>
                        </div>

                        {typeof step.content === 'string' ? (
                          <div className="text-gray-200 font-mono text-[11px] leading-relaxed whitespace-pre-wrap">
                            {step.content}
                          </div>
                        ) : (
                          <pre className="p-2.5 rounded bg-[#111827] text-[10px] font-mono text-cyan-300 overflow-x-auto">
                            {JSON.stringify(step.content, null, 2)}
                          </pre>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-[#0B0F17] text-xs text-gray-400">
                  <div className="font-semibold text-gray-300 mb-1">Final Response:</div>
                  <div className="font-mono">{selectedResult.actual_response || 'No output recorded.'}</div>
                </div>
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-[#1F2937] flex justify-end">
              <button
                onClick={() => setSelectedResult(null)}
                className="px-4 py-2 rounded-xl bg-[#1E293B] hover:bg-[#2D3748] text-white text-xs font-medium"
              >
                Close Trace
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
