import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  PlayCircle,
  Clock,
  Coins,
  CheckCircle2,
  XCircle,
  PlusCircle,
  Search,
  ArrowUpRight,
  Filter,
} from 'lucide-react';
import { apiClient } from '../services/api';
import { EvaluationRun } from '../types';

export const EvaluationsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchRuns = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<EvaluationRun[]>('/evaluations');
      setRuns(res.data);
    } catch (err) {
      console.error('Failed to load evaluation runs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const filteredRuns = runs.filter((r) =>
    r.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Evaluation Runs</h2>
          <p className="text-xs text-gray-400">
            Inspect historical test executions, live runs, and aggregate benchmark scores
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by run name..."
              className="w-full bg-[#111827] border border-[#1F2937] rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            onClick={() => navigate('/evaluations/new')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-all shadow-md shadow-indigo-600/20"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Launch Run</span>
          </button>
        </div>
      </div>

      {/* Runs Table */}
      <div className="rounded-2xl bg-[#111827] border border-[#1F2937] p-5 shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#1F2937] text-gray-400">
                <th className="pb-3 px-3 font-medium">Run Name</th>
                <th className="pb-3 px-3 font-medium">Agent</th>
                <th className="pb-3 px-3 font-medium">Status</th>
                <th className="pb-3 px-3 font-medium">Success Rate</th>
                <th className="pb-3 px-3 font-medium">Tool Accuracy</th>
                <th className="pb-3 px-3 font-medium">Avg Latency</th>
                <th className="pb-3 px-3 font-medium">Cost</th>
                <th className="pb-3 px-3 font-medium text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2937]/50">
              {filteredRuns.length > 0 ? (
                filteredRuns.map((r) => {
                  const m = r.aggregate_metrics || {};
                  return (
                    <tr key={r.id} className="hover:bg-[#1E293B]/40 transition-colors">
                      <td className="py-3 px-3 font-medium text-white">{r.name}</td>
                      <td className="py-3 px-3 text-gray-300">
                        {r.agent_snapshot?.name || 'Agent'}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            r.status === 'COMPLETED'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : r.status === 'RUNNING'
                              ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 animate-pulse'
                              : r.status === 'CANCELLED'
                              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-mono font-semibold text-emerald-400">
                        {m.task_success_rate !== undefined ? `${m.task_success_rate}%` : '--'}
                      </td>
                      <td className="py-3 px-3 font-mono text-indigo-300">
                        {m.tool_selection_accuracy !== undefined ? `${m.tool_selection_accuracy}%` : '--'}
                      </td>
                      <td className="py-3 px-3 font-mono text-gray-300">
                        {m.average_latency_ms ? `${m.average_latency_ms}ms` : '--'}
                      </td>
                      <td className="py-3 px-3 font-mono text-amber-400">
                        ${m.estimated_cost_usd !== undefined ? m.estimated_cost_usd : '0.00'}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <Link
                          to={`/evaluations/${r.id}`}
                          className="px-2.5 py-1 rounded-lg bg-indigo-600/15 hover:bg-indigo-600/30 text-indigo-300 hover:text-white font-medium text-xs transition-colors inline-flex items-center space-x-1"
                        >
                          <span>Inspect</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-gray-500">
                    No evaluation runs found matching your search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
