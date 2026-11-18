import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Clock,
  Coins,
  Cpu,
  AlertTriangle,
  RefreshCw,
  Layers,
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
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { apiClient } from '../services/api';
import { OverviewMetrics } from '../types';

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<OverviewMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<OverviewMetrics>('/analytics/overview');
      setData(res.data);
    } catch (err) {
      console.error('Failed to load analytics overview:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Platform Analytics & Observability</h2>
          <p className="text-xs text-gray-400">
            Longitudinal reliability metrics, cost curves, model quality benchmarks, and error breakdowns
          </p>
        </div>
        <button
          onClick={fetchAnalytics}
          className="p-2 rounded-xl bg-[#1E293B] hover:bg-[#2D3748] text-gray-300 hover:text-white transition-colors"
          title="Refresh metrics"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <span className="text-[10px] text-gray-500 uppercase font-medium">Overall Pass Rate</span>
          <span className="text-2xl font-bold text-white font-mono mt-1 block">
            {data ? `${data.overall_success_rate}%` : '--'}
          </span>
          <span className="text-[11px] text-emerald-400">Reliability target: &gt;85%</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <span className="text-[10px] text-gray-500 uppercase font-medium">Average Latency</span>
          <span className="text-2xl font-bold text-white font-mono mt-1 block">
            {data ? `${data.average_latency_ms}ms` : '--'}
          </span>
          <span className="text-[11px] text-gray-400">P95: {data?.p95_latency_ms || 0}ms</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <span className="text-[10px] text-gray-500 uppercase font-medium">Tool Call Accuracy</span>
          <span className="text-2xl font-bold text-indigo-400 font-mono mt-1 block">
            {data ? `${data.average_tool_selection_accuracy}%` : '--'}
          </span>
          <span className="text-[11px] text-gray-400">F1 Decision Score</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <span className="text-[10px] text-gray-500 uppercase font-medium">Total Cost Consumed</span>
          <span className="text-2xl font-bold text-amber-400 font-mono mt-1 block">
            ${data ? data.total_estimated_cost_usd : '0.00'}
          </span>
          <span className="text-[11px] text-gray-400">
            {data?.total_tokens_consumed.toLocaleString() || 0} tokens
          </span>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Success Trend */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Evaluation Success Progression</h3>
              <p className="text-xs text-gray-400">Task completion percentage across successive evaluation runs</p>
            </div>
            <TrendingUp className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="h-64 w-full">
            {data && data.success_trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.success_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                  <XAxis dataKey="date" stroke="#6B7280" fontSize={11} tickLine={false} />
                  <YAxis domain={[0, 100]} stroke="#6B7280" fontSize={11} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', fontSize: '12px' }} />
                  <Area type="monotone" dataKey="success_rate" name="Success %" stroke="#6366F1" fill="#6366F1" fillOpacity={0.2} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-gray-500">
                No runs recorded yet.
              </div>
            )}
          </div>
        </div>

        {/* Model Accuracy Comparison */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Model Tier Performance</h3>
              <p className="text-xs text-gray-400">Average benchmark task success rate by model</p>
            </div>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="h-64 w-full">
            {data && data.model_comparison_overview.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.model_comparison_overview} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                  <XAxis dataKey="model" stroke="#6B7280" fontSize={11} tickLine={false} />
                  <YAxis domain={[0, 100]} stroke="#6B7280" fontSize={11} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey="avg_success_rate" name="Avg Success %" fill="#06B6D4" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-gray-500">
                No model comparison data available.
              </div>
            )}
          </div>
        </div>

        {/* Failure Breakdown */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Failure Category Distribution</h3>
              <p className="text-xs text-gray-400">Classified root causes for failed evaluations</p>
            </div>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="h-64 w-full">
            {data && data.failure_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.failure_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                  <XAxis dataKey="category" stroke="#6B7280" fontSize={10} angle={-15} textAnchor="end" tickLine={false} />
                  <YAxis stroke="#6B7280" fontSize={11} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey="count" name="Failure Count" fill="#F43F5E" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-emerald-400">
                Zero failure categories identified across runs.
              </div>
            )}
          </div>
        </div>

        {/* Latency Progression */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Execution Latency Over Time</h3>
              <p className="text-xs text-gray-400">Average response time (ms) per evaluation run</p>
            </div>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="h-64 w-full">
            {data && data.success_trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.success_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                  <XAxis dataKey="date" stroke="#6B7280" fontSize={11} tickLine={false} />
                  <YAxis stroke="#6B7280" fontSize={11} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', fontSize: '12px' }} />
                  <Area type="monotone" dataKey="avg_latency" name="Latency (ms)" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.15} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-gray-500">
                No latency history recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
