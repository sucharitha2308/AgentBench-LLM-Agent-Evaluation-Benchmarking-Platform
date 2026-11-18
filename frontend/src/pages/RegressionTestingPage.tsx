import React, { useEffect, useState } from 'react';
import {
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldAlert,
  ArrowRight,
  Info,
  Sparkles,
} from 'lucide-react';
import { apiClient } from '../services/api';
import { EvaluationRun, RegressionAnalysis } from '../types';

export const RegressionTestingPage: React.FC = () => {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [baselineRunId, setBaselineRunId] = useState('');
  const [currentRunId, setCurrentRunId] = useState('');
  const [threshold, setThreshold] = useState(5.0);
  const [analysis, setAnalysis] = useState<RegressionAnalysis | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchRuns = async () => {
      try {
        const res = await apiClient.get<EvaluationRun[]>('/evaluations');
        const completed = res.data.filter((r) => r.status === 'COMPLETED');
        setRuns(completed);

        if (completed.length >= 2) {
          // Assume older run is baseline, newer run is current
          setBaselineRunId(completed[1].id);
          setCurrentRunId(completed[0].id);
        } else if (completed.length === 1) {
          setBaselineRunId(completed[0].id);
          setCurrentRunId(completed[0].id);
        }
      } catch (err) {
        console.error('Failed to load runs:', err);
      }
    };
    fetchRuns();
  }, []);

  const runAnalysis = async () => {
    if (!baselineRunId || !currentRunId) return;
    try {
      setLoading(true);
      const res = await apiClient.get<RegressionAnalysis>('/evaluations/regression/analyze', {
        params: {
          baseline_run_id: baselineRunId,
          current_run_id: currentRunId,
          threshold_pct: threshold,
        },
      });
      setAnalysis(res.data);
    } catch (err: any) {
      alert(err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to analyze regression.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (baselineRunId && currentRunId) {
      runAnalysis();
    }
  }, [baselineRunId, currentRunId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">Regression Testing & Quality Guardrails</h2>
        <p className="text-xs text-gray-400">
          Detect functional performance degradations, newly failing test cases, and latency spikes across agent versions
        </p>
      </div>

      {/* Selectors Bar */}
      <div className="p-4 rounded-2xl bg-[#111827] border border-[#1F2937] flex flex-col md:flex-row md:items-center gap-4">
        <div className="flex-1">
          <label className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Baseline Reference Run
          </label>
          <select
            value={baselineRunId}
            onChange={(e) => setBaselineRunId(e.target.value)}
            className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="">Select baseline run...</option>
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.aggregate_metrics.task_success_rate || 0}% success • {new Date(r.created_at).toLocaleDateString()})
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1">
          <label className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Current Candidate Run
          </label>
          <select
            value={currentRunId}
            onChange={(e) => setCurrentRunId(e.target.value)}
            className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="">Select current candidate run...</option>
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.aggregate_metrics.task_success_rate || 0}% success • {new Date(r.created_at).toLocaleDateString()})
              </option>
            ))}
          </select>
        </div>

        <div className="w-full md:w-36">
          <label className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Tolerance ({threshold}%)
          </label>
          <input
            type="number"
            min={1}
            max={20}
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value) || 5.0)}
            className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="md:pt-4">
          <button
            onClick={runAnalysis}
            disabled={!baselineRunId || !currentRunId || loading}
            className="w-full md:w-auto px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all disabled:opacity-40"
          >
            {loading ? 'Analyzing...' : 'Detect Regressions'}
          </button>
        </div>
      </div>

      {analysis && (
        <div className="space-y-6">
          {/* Severity & Recommendation Card */}
          <div
            className={`p-5 rounded-2xl border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 ${
              analysis.severity === 'LOW'
                ? 'bg-emerald-500/5 border-emerald-500/30 text-emerald-300'
                : analysis.severity === 'MEDIUM'
                ? 'bg-amber-500/5 border-amber-500/30 text-amber-300'
                : 'bg-rose-500/5 border-rose-500/30 text-rose-300'
            }`}
          >
            <div className="flex items-start space-x-3.5">
              <div
                className={`p-2.5 rounded-xl ${
                  analysis.severity === 'LOW' ? 'bg-emerald-500/20' : 'bg-rose-500/20'
                }`}
              >
                {analysis.severity === 'LOW' ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : (
                  <AlertTriangle className="w-5 h-5" />
                )}
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-sm">Regression Risk:</span>
                  <span className="font-mono uppercase font-bold text-xs px-2 py-0.5 rounded bg-black/40">
                    {analysis.severity} SEVERITY
                  </span>
                  <span className="text-xs">
                    ({analysis.total_regressions} test case regressions)
                  </span>
                </div>
                <p className="text-xs text-gray-300 mt-1.5 leading-relaxed max-w-2xl">
                  {analysis.recommendation}
                </p>
              </div>
            </div>
          </div>

          {/* Metric Degradations */}
          {analysis.metric_degradations.length > 0 && (
            <div className="p-5 rounded-2xl bg-[#111827] border border-[#1F2937]">
              <h3 className="text-sm font-semibold text-white mb-3">Metric Degradations Exceeding Tolerance</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {analysis.metric_degradations.map((d, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-[#0B0F17] border border-[#1F2937] text-xs">
                    <span className="text-gray-400 block font-medium mb-1">{d.metric}</span>
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-gray-300">Baseline: {d.baseline}</span>
                      <span className="text-rose-400 font-bold">{d.degradation}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Regressed Test Cases Table */}
          <div className="rounded-2xl bg-[#111827] border border-[#1F2937] p-5">
            <h3 className="text-sm font-semibold text-white mb-1">Regressed Test Cases</h3>
            <p className="text-xs text-gray-400 mb-4">
              Test cases that passed in the baseline run, but failed or errored in the candidate run
            </p>

            {analysis.regressed_cases.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[#1F2937] text-gray-400">
                      <th className="pb-3 px-3 font-medium">Test ID</th>
                      <th className="pb-3 px-3 font-medium">Test Case</th>
                      <th className="pb-3 px-3 font-medium">Baseline Status</th>
                      <th className="pb-3 px-3 font-medium">Candidate Status</th>
                      <th className="pb-3 px-3 font-medium">Failure Category</th>
                      <th className="pb-3 px-3 font-medium">Explanation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1F2937]/50">
                    {analysis.regressed_cases.map((rc) => (
                      <tr key={rc.test_case_identifier} className="bg-rose-500/5">
                        <td className="py-2.5 px-3 font-mono font-bold text-rose-400">
                          {rc.test_case_identifier}
                        </td>
                        <td className="py-2.5 px-3 font-medium text-gray-200">{rc.name}</td>
                        <td className="py-2.5 px-3">
                          <span className="text-emerald-400 font-mono text-[10px] bg-emerald-500/10 px-1.5 py-0.5 rounded font-bold">
                            {rc.previous_status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="text-rose-400 font-mono text-[10px] bg-rose-500/10 px-1.5 py-0.5 rounded font-bold">
                            {rc.current_status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[11px] text-rose-300">
                          {rc.failure_category || 'unknown'}
                        </td>
                        <td className="py-2.5 px-3 text-gray-400 text-[11px] max-w-sm truncate">
                          {rc.failure_explanation || 'Failed acceptance criteria.'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 flex flex-col items-center justify-center space-y-1 text-xs text-emerald-400">
                <CheckCircle2 className="w-8 h-8 text-emerald-500/80 mb-1" />
                <span>Zero test cases regressed!</span>
                <span className="text-gray-500 text-[11px]">
                  All previously passing functional test cases maintained passing status.
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
