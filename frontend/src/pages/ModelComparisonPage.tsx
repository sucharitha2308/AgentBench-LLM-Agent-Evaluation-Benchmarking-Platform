import React, { useEffect, useState } from 'react';
import {
  GitCompare,
  Trophy,
  TrendingUp,
  ArrowRight,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RefreshCw,
  Scale,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { apiClient } from '../services/api';
import { EvaluationRun, RunComparison } from '../types';

export const ModelComparisonPage: React.FC = () => {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [runIdA, setRunIdA] = useState('');
  const [runIdB, setRunIdB] = useState('');
  const [comparison, setComparison] = useState<RunComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    const fetchRuns = async () => {
      try {
        setInitialLoading(true);
        const res = await apiClient.get<EvaluationRun[]>('/evaluations');
        const completed = res.data.filter((r) => r.status === 'COMPLETED');
        setRuns(completed);

        if (completed.length >= 2) {
          setRunIdA(completed[0].id);
          setRunIdB(completed[1].id);
        } else if (completed.length === 1) {
          setRunIdA(completed[0].id);
        }
      } catch (err) {
        console.error('Failed to load runs:', err);
      } finally {
        setInitialLoading(false);
      }
    };
    fetchRuns();
  }, []);

  const runComparison = async () => {
    if (!runIdA || !runIdB) return;
    try {
      setLoading(true);
      const res = await apiClient.post<RunComparison>('/analytics/compare', {
        run_id_a: runIdA,
        run_id_b: runIdB,
      });
      setComparison(res.data);
    } catch (err: any) {
      alert(err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to compare evaluation runs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (runIdA && runIdB && runIdA !== runIdB) {
      runComparison();
    }
  }, [runIdA, runIdB]);

  // Chart data for visual comparison
  const chartData = comparison
    ? [
        {
          name: 'Task Success %',
          AgentA: comparison.run_a.aggregate_metrics.task_success_rate || 0,
          AgentB: comparison.run_b.aggregate_metrics.task_success_rate || 0,
        },
        {
          name: 'Tool Accuracy %',
          AgentA: comparison.run_a.aggregate_metrics.tool_selection_accuracy || 0,
          AgentB: comparison.run_b.aggregate_metrics.tool_selection_accuracy || 0,
        },
        {
          name: 'JSON Validity %',
          AgentA: comparison.run_a.aggregate_metrics.structured_output_validity || 0,
          AgentB: comparison.run_b.aggregate_metrics.structured_output_validity || 0,
        },
        {
          name: 'Safety %',
          AgentA: comparison.run_a.aggregate_metrics.safety_pass_rate || 100,
          AgentB: comparison.run_b.aggregate_metrics.safety_pass_rate || 100,
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">Model & Agent Benchmarking Comparison</h2>
        <p className="text-xs text-gray-400">
          Compare two distinct models or agent configurations under identical evaluation test datasets
        </p>
      </div>

      {/* Selectors Bar */}
      <div className="p-4 rounded-2xl bg-[#111827] border border-[#1F2937] flex flex-col md:flex-row md:items-center gap-4">
        <div className="flex-1">
          <label className="block text-[10px] font-semibold text-indigo-400 uppercase tracking-wider mb-1">
            Agent A (Baseline)
          </label>
          <select
            value={runIdA}
            onChange={(e) => setRunIdA(e.target.value)}
            className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="">Select baseline evaluation run...</option>
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.agent_snapshot?.provider} • {r.agent_snapshot?.model_name})
              </option>
            ))}
          </select>
        </div>

        <div className="hidden md:flex items-center justify-center pt-4">
          <div className="w-8 h-8 rounded-full bg-[#1E293B] border border-gray-700 flex items-center justify-center text-xs font-bold text-gray-400">
            VS
          </div>
        </div>

        <div className="flex-1">
          <label className="block text-[10px] font-semibold text-cyan-400 uppercase tracking-wider mb-1">
            Agent B (Challenger)
          </label>
          <select
            value={runIdB}
            onChange={(e) => setRunIdB(e.target.value)}
            className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="">Select challenger evaluation run...</option>
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.agent_snapshot?.provider} • {r.agent_snapshot?.model_name})
              </option>
            ))}
          </select>
        </div>

        <div className="md:pt-4">
          <button
            onClick={runComparison}
            disabled={!runIdA || !runIdB || runIdA === runIdB || loading}
            className="w-full md:w-auto px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all disabled:opacity-40"
          >
            {loading ? 'Comparing...' : 'Compare Runs'}
          </button>
        </div>
      </div>

      {comparison && (
        <div className="space-y-6">
          {/* Executive Summary Card */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-indigo-950/30 via-[#111827] to-[#111827] border border-indigo-500/20 flex items-start space-x-3.5">
            <div className="p-2.5 rounded-xl bg-indigo-600/20 text-indigo-400 mt-0.5">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-sm">Benchmarking Outcome</h3>
              <p className="text-xs text-gray-300 mt-1 leading-relaxed">{comparison.summary}</p>
            </div>
          </div>

          {/* Side-by-side Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 rounded-2xl bg-[#111827] border border-indigo-500/30">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono font-bold uppercase text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
                  Agent A
                </span>
                <span className="text-xs text-gray-400 font-mono">
                  {comparison.run_a.agent_snapshot?.model_name}
                </span>
              </div>
              <h4 className="font-bold text-white text-base">{comparison.run_a.agent_snapshot?.name}</h4>
              <div className="grid grid-cols-3 gap-2 mt-4 text-center">
                <div className="p-2 rounded-lg bg-[#0B0F17]">
                  <span className="text-[10px] text-gray-500 block">Success Rate</span>
                  <span className="font-mono font-bold text-sm text-emerald-400">
                    {comparison.run_a.aggregate_metrics.task_success_rate || 0}%
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-[#0B0F17]">
                  <span className="text-[10px] text-gray-500 block">Avg Latency</span>
                  <span className="font-mono font-bold text-sm text-white">
                    {comparison.run_a.aggregate_metrics.average_latency_ms || 0}ms
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-[#0B0F17]">
                  <span className="text-[10px] text-gray-500 block">Est. Cost</span>
                  <span className="font-mono font-bold text-sm text-amber-400">
                    ${comparison.run_a.aggregate_metrics.estimated_cost_usd || 0}
                  </span>
                </div>
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-[#111827] border border-cyan-500/30">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono font-bold uppercase text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded">
                  Agent B
                </span>
                <span className="text-xs text-gray-400 font-mono">
                  {comparison.run_b.agent_snapshot?.model_name}
                </span>
              </div>
              <h4 className="font-bold text-white text-base">{comparison.run_b.agent_snapshot?.name}</h4>
              <div className="grid grid-cols-3 gap-2 mt-4 text-center">
                <div className="p-2 rounded-lg bg-[#0B0F17]">
                  <span className="text-[10px] text-gray-500 block">Success Rate</span>
                  <span className="font-mono font-bold text-sm text-emerald-400">
                    {comparison.run_b.aggregate_metrics.task_success_rate || 0}%
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-[#0B0F17]">
                  <span className="text-[10px] text-gray-500 block">Avg Latency</span>
                  <span className="font-mono font-bold text-sm text-white">
                    {comparison.run_b.aggregate_metrics.average_latency_ms || 0}ms
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-[#0B0F17]">
                  <span className="text-[10px] text-gray-500 block">Est. Cost</span>
                  <span className="font-mono font-bold text-sm text-amber-400">
                    ${comparison.run_b.aggregate_metrics.estimated_cost_usd || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Visual BarChart Comparison */}
          <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937]">
            <h3 className="text-sm font-semibold text-white mb-1">Side-by-Side Performance Comparison</h3>
            <p className="text-xs text-gray-400 mb-4">Direct metric comparison between Agent A and Agent B</p>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                  <XAxis dataKey="name" stroke="#6B7280" fontSize={11} tickLine={false} />
                  <YAxis domain={[0, 100]} stroke="#6B7280" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  <Bar dataKey="AgentA" name={comparison.run_a.agent_snapshot?.name || 'Agent A'} fill="#6366F1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="AgentB" name={comparison.run_b.agent_snapshot?.name || 'Agent B'} fill="#06B6D4" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Metric Deltas Table */}
          <div className="rounded-2xl bg-[#111827] border border-[#1F2937] p-5">
            <h3 className="text-sm font-semibold text-white mb-3">Detailed Metric Breakdown & Deltas</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#1F2937] text-gray-400">
                    <th className="pb-3 px-3 font-medium">Metric</th>
                    <th className="pb-3 px-3 font-medium">Agent A</th>
                    <th className="pb-3 px-3 font-medium">Agent B</th>
                    <th className="pb-3 px-3 font-medium">Delta</th>
                    <th className="pb-3 px-3 font-medium">% Change</th>
                    <th className="pb-3 px-3 font-medium text-right">Winner</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1F2937]/50">
                  {comparison.metric_comparisons.map((m) => (
                    <tr key={m.metric_name} className="hover:bg-[#1E293B]/40 transition-colors">
                      <td className="py-2.5 px-3 font-medium text-gray-200 capitalize">
                        {m.metric_name.replace(/_/g, ' ')}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-gray-300">{m.value_a}</td>
                      <td className="py-2.5 px-3 font-mono text-gray-300">{m.value_b}</td>
                      <td className="py-2.5 px-3 font-mono">
                        <span className={m.delta > 0 ? 'text-cyan-400' : m.delta < 0 ? 'text-rose-400' : 'text-gray-400'}>
                          {m.delta > 0 ? `+${m.delta}` : m.delta}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono">
                        <span className={m.percentage_change > 0 ? 'text-cyan-400' : m.percentage_change < 0 ? 'text-rose-400' : 'text-gray-400'}>
                          {m.percentage_change > 0 ? `+${m.percentage_change}%` : `${m.percentage_change}%`}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <span
                          className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                            m.winner === 'A'
                              ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                              : m.winner === 'B'
                              ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                              : 'bg-gray-800 text-gray-400'
                          }`}
                        >
                          {m.winner === 'TIE' ? 'TIE' : `Agent ${m.winner}`}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Test Differences Table */}
          {comparison.test_differences.length > 0 && (
            <div className="rounded-2xl bg-[#111827] border border-[#1F2937] p-5">
              <h3 className="text-sm font-semibold text-white mb-3">Test-Level Outcome Differences</h3>
              <div className="overflow-x-auto max-h-80 overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-[#111827] border-b border-[#1F2937]">
                    <tr className="text-gray-400">
                      <th className="py-2.5 px-3 font-medium">Test ID</th>
                      <th className="py-2.5 px-3 font-medium">Test Case</th>
                      <th className="py-2.5 px-3 font-medium">Status (A)</th>
                      <th className="py-2.5 px-3 font-medium">Status (B)</th>
                      <th className="py-2.5 px-3 font-medium">Latency Delta</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1F2937]/50">
                    {comparison.test_differences.map((td) => (
                      <tr
                        key={td.test_case_identifier}
                        className={td.status_differs ? 'bg-amber-500/5' : 'hover:bg-[#1E293B]/40'}
                      >
                        <td className="py-2.5 px-3 font-mono text-indigo-400 font-semibold">
                          {td.test_case_identifier}
                        </td>
                        <td className="py-2.5 px-3 text-gray-300 truncate max-w-xs">{td.name}</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`font-mono text-[10px] px-1.5 py-0.5 rounded font-bold ${
                              td.status_a === 'PASS' ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
                            }`}
                          >
                            {td.status_a}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`font-mono text-[10px] px-1.5 py-0.5 rounded font-bold ${
                              td.status_b === 'PASS' ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
                            }`}
                          >
                            {td.status_b}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-gray-400 text-[11px]">
                          {td.latency_delta_ms > 0 ? `+${td.latency_delta_ms}ms` : `${td.latency_delta_ms}ms`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
