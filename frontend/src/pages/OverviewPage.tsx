import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Bot,
  Database,
  PlayCircle,
  CheckCircle2,
  Clock,
  Coins,
  ArrowUpRight,
  TrendingUp,
  AlertTriangle,
  Plus,
  RefreshCw,
  Cpu,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { apiClient } from '../services/api';
import { OverviewMetrics } from '../types';

export const OverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<OverviewMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<OverviewMetrics>('/analytics/overview');
      setData(res.data);
    } catch (err) {
      console.error('Failed to load overview analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-[#111827] to-[#111827] border border-[#1F2937]">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Agent Evaluation & Observability</h2>
          <p className="text-sm text-gray-400 mt-1 max-w-xl">
            Evaluate, test, and benchmark LLM agent workflows against deterministic ground truth test suites.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchOverview}
            disabled={loading}
            className="p-2 rounded-xl bg-[#1E293B] hover:bg-[#2D3748] text-gray-300 hover:text-white transition-colors"
            title="Refresh metrics"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => navigate('/evaluations/new')}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-all shadow-md shadow-indigo-600/25"
          >
            <PlayCircle className="w-4 h-4" />
            <span>Launch Evaluation</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs font-medium">Task Success Rate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {data ? `${data.overall_success_rate}%` : '--'}
          </div>
          <div className="text-[11px] text-gray-400 mt-1">
            Across {data?.total_test_cases_executed || 0} executed test cases
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs font-medium">Avg Execution Latency</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {data ? `${data.average_latency_ms}ms` : '--'}
          </div>
          <div className="text-[11px] text-gray-400 mt-1">
            P95: {data?.p95_latency_ms || 0}ms
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs font-medium">Tool Calling Accuracy</span>
            <Cpu className="w-4 h-4 text-violet-400" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {data ? `${data.average_tool_selection_accuracy}%` : '--'}
          </div>
          <div className="text-[11px] text-gray-400 mt-1">
            JSON Schema: {data?.average_json_validity_rate || 100}%
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs font-medium">Total Tokens / Cost</span>
            <Coins className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {data ? `${data.total_tokens_consumed.toLocaleString()} tok` : '--'}
          </div>
          <div className="text-[11px] text-gray-400 mt-1">
            Estimated ${data?.total_estimated_cost_usd || '0.00'} USD
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Success Trend AreaChart */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937] flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Evaluation Success Trend</h3>
              <p className="text-xs text-gray-400">Success rate (%) progression across evaluation runs</p>
            </div>
            <TrendingUp className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="h-64 w-full flex-1">
            {data && data.success_trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.success_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="successGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366F1" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#6366F1" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                  <XAxis dataKey="date" stroke="#6B7280" fontSize={11} tickLine={false} />
                  <YAxis domain={[0, 100]} stroke="#6B7280" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="success_rate" name="Success %" stroke="#6366F1" strokeWidth={2} fillOpacity={1} fill="url(#successGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-gray-500">
                No evaluation trend history recorded yet. Run an evaluation to visualize trends.
              </div>
            )}
          </div>
        </div>

        {/* Failure Category BarChart */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937] flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Failure Distribution</h3>
              <p className="text-xs text-gray-400">Classification of errors and evaluation failures</p>
            </div>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="h-64 w-full flex-1">
            {data && data.failure_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.failure_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                  <XAxis dataKey="category" stroke="#6B7280" fontSize={10} angle={-15} textAnchor="end" tickLine={false} />
                  <YAxis stroke="#6B7280" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" name="Failed Cases" fill="#F43F5E" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-xs text-emerald-400 space-y-1">
                <CheckCircle2 className="w-8 h-8 text-emerald-500/80 mb-1" />
                <span>Zero failure categories detected!</span>
                <span className="text-gray-500 text-[11px]">All evaluated test cases have passed.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Evaluations Table */}
      <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Recent Evaluation Runs</h3>
            <p className="text-xs text-gray-400">Latest benchmark executions and performance metrics</p>
          </div>
          <Link
            to="/evaluations"
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center space-x-1"
          >
            <span>View All</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#1F2937] text-gray-400">
                <th className="pb-3 font-medium">Evaluation Run</th>
                <th className="pb-3 font-medium">Agent</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Cases</th>
                <th className="pb-3 font-medium">Success Rate</th>
                <th className="pb-3 font-medium">Date</th>
                <th className="pb-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2937]/50">
              {data && data.recent_runs.length > 0 ? (
                data.recent_runs.map((r) => (
                  <tr key={r.id} className="hover:bg-[#1E293B]/40 transition-colors">
                    <td className="py-3 font-medium text-white">{r.name}</td>
                    <td className="py-3 text-gray-300">{r.agent_name}</td>
                    <td className="py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          r.status === 'COMPLETED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : r.status === 'RUNNING'
                            ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="py-3 text-gray-400">
                      <span className="text-emerald-400">{r.passed}</span> / {r.total_cases}
                    </td>
                    <td className="py-3 font-mono text-indigo-300 font-medium">
                      {r.success_rate}%
                    </td>
                    <td className="py-3 text-gray-400">
                      {new Date(r.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 text-right">
                      <Link
                        to={`/evaluations/${r.id}`}
                        className="text-xs text-indigo-400 hover:text-white font-medium px-2 py-1 rounded bg-indigo-600/10 hover:bg-indigo-600/30 transition-colors"
                      >
                        Inspect Traces
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-500">
                    No evaluation runs found. Click "Launch Evaluation" to begin.
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
