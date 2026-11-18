import React, { useEffect, useState } from 'react';
import {
  Bot,
  Plus,
  Settings2,
  Trash2,
  Play,
  Cpu,
  History,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Wrench,
  Sparkles,
} from 'lucide-react';
import { apiClient } from '../services/api';
import { Agent, AgentVersion } from '../types';

const AVAILABLE_TOOLS = [
  { name: 'get_order', description: 'Retrieve order status and carrier tracking details by order_id' },
  { name: 'check_refund_eligibility', description: 'Check return window and refund eligibility for an order' },
  { name: 'search_products', description: 'Search the store inventory and catalog matching user queries' },
  { name: 'get_weather', description: 'Check current weather conditions for delivery delay estimates' },
];

export const AgentsPage: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  // Create / Edit modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [agentType, setAgentType] = useState<'direct_llm' | 'langgraph' | 'http'>('direct_llm');
  const [provider, setProvider] = useState<'openai' | 'gemini' | 'mock'>('mock');
  const [modelName, setModelName] = useState('mock-agent');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(2048);
  const [outputFormat, setOutputFormat] = useState<'text' | 'json'>('text');
  const [selectedTools, setSelectedTools] = useState<string[]>(['get_order', 'check_refund_eligibility', 'search_products', 'get_weather']);
  const [httpEndpoint, setHttpEndpoint] = useState('');

  // Version History Modal
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  const [agentVersions, setAgentVersions] = useState<AgentVersion[]>([]);
  const [historyAgentName, setHistoryAgentName] = useState('');

  // Test Connection Modal
  const [testModalOpen, setTestModalOpen] = useState(false);
  const [testingProvider, setTestingProvider] = useState('');
  const [testingModel, setTestingModel] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<Agent[]>('/agents');
      setAgents(res.data);
    } catch (err) {
      console.error('Failed to load agents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const openCreateModal = () => {
    setEditingAgent(null);
    setName('');
    setDescription('');
    setAgentType('direct_llm');
    setProvider('mock');
    setModelName('mock-agent');
    setSystemPrompt('You are a helpful customer support assistant.');
    setTemperature(0.2);
    setMaxTokens(2048);
    setOutputFormat('text');
    setSelectedTools(['get_order', 'check_refund_eligibility', 'search_products', 'get_weather']);
    setHttpEndpoint('');
    setIsModalOpen(true);
  };

  const openEditModal = (agent: Agent) => {
    setEditingAgent(agent);
    setName(agent.name);
    setDescription(agent.description || '');
    setAgentType(agent.agent_type);
    setProvider(agent.provider);
    setModelName(agent.model_name);
    setSystemPrompt(agent.system_prompt);
    setTemperature(agent.temperature);
    setMaxTokens(agent.max_output_tokens);
    setOutputFormat(agent.output_format);
    setSelectedTools(agent.tools.map((t) => t.name));
    setHttpEndpoint(agent.http_endpoint || '');
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const toolsPayload = selectedTools.map((tName) => {
      const match = AVAILABLE_TOOLS.find((t) => t.name === tName);
      return {
        name: tName,
        description: match?.description || '',
        parameters: { param: 'string' },
      };
    });

    const payload = {
      name,
      description,
      agent_type: agentType,
      provider,
      model_name: modelName,
      system_prompt: systemPrompt,
      temperature,
      max_output_tokens: maxTokens,
      output_format: outputFormat,
      tools: toolsPayload,
      http_endpoint: agentType === 'http' ? httpEndpoint : undefined,
    };

    try {
      if (editingAgent) {
        await apiClient.put(`/agents/${editingAgent.id}`, payload);
      } else {
        await apiClient.post('/agents', payload);
      }
      setIsModalOpen(false);
      fetchAgents();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save agent configuration.');
    }
  };

  const handleDelete = async (agent: Agent) => {
    if (!window.confirm(`Are you sure you want to delete agent "${agent.name}"?`)) return;
    try {
      await apiClient.delete(`/agents/${agent.id}`);
      fetchAgents();
    } catch (err: any) {
      alert(err.response?.data?.error?.message || err.response?.data?.detail || 'Sample baseline agents cannot be deleted.');
    }
  };

  const viewHistory = async (agent: Agent) => {
    try {
      setHistoryAgentName(agent.name);
      const res = await apiClient.get<AgentVersion[]>(`/agents/${agent.id}/versions`);
      setAgentVersions(res.data);
      setHistoryModalOpen(true);
    } catch (err) {
      alert('Failed to load version history.');
    }
  };

  const runConnectionTest = async (prov: string, model: string) => {
    setTestingProvider(prov);
    setTestingModel(model);
    setTestResult(null);
    setTestModalOpen(true);
    setTesting(true);

    try {
      const res = await apiClient.post('/agents/test-connection', {
        provider: prov,
        model_name: model,
      });
      setTestResult(res.data);
    } catch (err: any) {
      setTestResult({
        success: false,
        message: err.response?.data?.error?.message || err.response?.data?.detail || 'Connection test failed. Check API key in Settings.',
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top action bar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Registered Agents</h2>
          <p className="text-xs text-gray-400">Configure AI models, tool bindings, system prompts, and architectures</p>
        </div>
        <button
          onClick={openCreateModal}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-all shadow-md shadow-indigo-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>Register New Agent</span>
        </button>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="rounded-2xl bg-[#111827] border border-[#1F2937] p-5 flex flex-col justify-between hover:border-gray-700 transition-all shadow-sm group"
          >
            <div>
              {/* Card Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2.5">
                  <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white text-sm group-hover:text-indigo-300 transition-colors">
                      {agent.name}
                    </h3>
                    <div className="flex items-center space-x-2 mt-0.5">
                      <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/20">
                        {agent.provider.toUpperCase()}
                      </span>
                      <span className="text-[10px] text-gray-400 font-mono">
                        {agent.model_name}
                      </span>
                    </div>
                  </div>
                </div>

                {agent.is_sample && (
                  <span className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    Sample Baseline
                  </span>
                )}
              </div>

              {/* Description */}
              <p className="text-xs text-gray-400 line-clamp-2 mb-4 leading-relaxed">
                {agent.description || 'No description provided.'}
              </p>

              {/* Parameters Summary */}
              <div className="grid grid-cols-3 gap-2 p-2.5 rounded-xl bg-[#0B0F17] border border-[#1F2937] text-center text-xs mb-4">
                <div>
                  <span className="text-[10px] text-gray-500 block">Arch</span>
                  <span className="font-mono text-gray-300 text-[11px] capitalize">
                    {agent.agent_type.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-gray-500 block">Temp</span>
                  <span className="font-mono text-gray-300 text-[11px]">{agent.temperature}</span>
                </div>
                <div>
                  <span className="text-[10px] text-gray-500 block">Format</span>
                  <span className="font-mono text-gray-300 text-[11px] uppercase">
                    {agent.output_format}
                  </span>
                </div>
              </div>

              {/* Tools chips */}
              <div className="mb-4">
                <span className="text-[10px] uppercase font-semibold text-gray-500 block mb-1.5">
                  Available Tools ({agent.tools?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {agent.tools && agent.tools.length > 0 ? (
                    agent.tools.map((t, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono bg-[#1E293B] text-gray-300 px-2 py-0.5 rounded border border-gray-700 flex items-center space-x-1"
                      >
                        <Wrench className="w-2.5 h-2.5 text-indigo-400" />
                        <span>{t.name}</span>
                      </span>
                    ))
                  ) : (
                    <span className="text-[11px] text-gray-500 italic">No tools bound</span>
                  )}
                </div>
              </div>
            </div>

            {/* Card Actions */}
            <div className="pt-3 border-t border-[#1F2937] flex items-center justify-between">
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => runConnectionTest(agent.provider, agent.model_name)}
                  className="px-2.5 py-1 rounded-lg text-xs bg-[#1E293B] hover:bg-[#2D3748] text-gray-300 hover:text-white transition-colors"
                  title="Test LLM connection"
                >
                  Test
                </button>
                <button
                  onClick={() => viewHistory(agent)}
                  className="px-2.5 py-1 rounded-lg text-xs bg-[#1E293B] hover:bg-[#2D3748] text-gray-300 hover:text-white transition-colors flex items-center space-x-1"
                  title="View configuration versions"
                >
                  <History className="w-3 h-3" />
                  <span>v1</span>
                </button>
              </div>

              <div className="flex items-center space-x-1">
                <button
                  onClick={() => openEditModal(agent)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-[#1E293B] transition-colors"
                  title="Edit agent"
                >
                  <Settings2 className="w-4 h-4" />
                </button>
                {!agent.is_sample && (
                  <button
                    onClick={() => handleDelete(agent)}
                    className="p-1.5 rounded-lg text-gray-400 hover:text-rose-400 hover:bg-[#1E293B] transition-colors"
                    title="Delete agent"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-[#1F2937] rounded-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white mb-4">
              {editingAgent ? 'Edit Agent Configuration' : 'Register New AI Agent'}
            </h3>

            <form onSubmit={handleSave} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-300 font-medium mb-1">Agent Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. GPT-4o Support Assistant"
                  className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-medium mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  placeholder="Describe agent purpose and domain..."
                  className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Provider</label>
                  <select
                    value={provider}
                    onChange={(e: any) => {
                      const p = e.target.value;
                      setProvider(p);
                      if (p === 'openai') setModelName('gpt-4o-mini');
                      else if (p === 'gemini') setModelName('gemini-1.5-flash');
                      else setModelName('mock-agent');
                    }}
                    className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="mock">Deterministic Mock (Demo / Offline)</option>
                    <option value="openai">OpenAI API</option>
                    <option value="gemini">Google Gemini API</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-300 font-medium mb-1">Model Name</label>
                  <input
                    type="text"
                    required
                    value={modelName}
                    onChange={(e) => setModelName(e.target.value)}
                    placeholder="e.g. gpt-4o, gemini-1.5-pro, mock-agent"
                    className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Agent Architecture</label>
                  <select
                    value={agentType}
                    onChange={(e: any) => setAgentType(e.target.value)}
                    className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="direct_llm">Direct LLM Tool-Calling Agent</option>
                    <option value="langgraph">LangGraph Orchestrated Agent</option>
                    <option value="http">External HTTP Agent</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-300 font-medium mb-1">Output Format</label>
                  <select
                    value={outputFormat}
                    onChange={(e: any) => setOutputFormat(e.target.value)}
                    className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="text">Natural Language Text</option>
                    <option value="json">Structured JSON Output</option>
                  </select>
                </div>
              </div>

              {agentType === 'http' && (
                <div>
                  <label className="block text-gray-300 font-medium mb-1">External HTTP Endpoint</label>
                  <input
                    type="url"
                    required
                    value={httpEndpoint}
                    onChange={(e) => setHttpEndpoint(e.target.value)}
                    placeholder="https://api.myagent.com/v1/run"
                    className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-gray-300 font-medium mb-1">System Instructions / Prompt</label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  rows={3}
                  className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white font-mono text-[11px] focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-medium mb-1">
                    Temperature ({temperature})
                  </label>
                  <input
                    type="range"
                    min="0.0"
                    max="1.5"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full accent-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Max Output Tokens</label>
                  <input
                    type="number"
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(parseInt(e.target.value) || 2048)}
                    className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-1.5 text-white font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Tool Selection Checkboxes */}
              <div>
                <label className="block text-gray-300 font-medium mb-2">Authorized Mock Tools</label>
                <div className="space-y-2">
                  {AVAILABLE_TOOLS.map((t) => (
                    <label
                      key={t.name}
                      className="flex items-start space-x-2.5 p-2 rounded-xl bg-[#0B0F17] border border-[#1F2937] cursor-pointer hover:border-gray-700"
                    >
                      <input
                        type="checkbox"
                        checked={selectedTools.includes(t.name)}
                        onChange={(e) => {
                          if (e.target.checked) setSelectedTools([...selectedTools, t.name]);
                          else setSelectedTools(selectedTools.filter((name) => name !== t.name));
                        }}
                        className="mt-0.5 rounded border-gray-700 bg-gray-900 text-indigo-600 focus:ring-indigo-500"
                      />
                      <div>
                        <div className="font-mono text-indigo-400 font-semibold">{t.name}</div>
                        <div className="text-[11px] text-gray-400">{t.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-[#1F2937]">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-[#1E293B] hover:bg-[#2D3748] text-gray-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-md shadow-indigo-600/30"
                >
                  Save Agent
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Version History Modal */}
      {historyModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-[#1F2937] rounded-2xl w-full max-w-lg p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#1F2937]">
              <div>
                <h3 className="font-bold text-white text-sm">Version History: {historyAgentName}</h3>
                <p className="text-[11px] text-gray-400">Immutable configuration snapshots</p>
              </div>
              <button
                onClick={() => setHistoryModalOpen(false)}
                className="text-gray-400 hover:text-white text-xs"
              >
                Close
              </button>
            </div>

            <div className="space-y-3 max-h-80 overflow-y-auto">
              {agentVersions.map((v) => (
                <div key={v.id} className="p-3 rounded-xl bg-[#0B0F17] border border-[#1F2937] text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-indigo-400">Version {v.version_number}</span>
                    <span className="text-[10px] text-gray-500">
                      {new Date(v.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-gray-300 text-[11px] mb-2">{v.commit_message}</p>
                  <pre className="p-2 rounded bg-[#111827] text-[10px] font-mono text-gray-400 overflow-x-auto">
                    {JSON.stringify(v.configuration_snapshot, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Test Connection Modal */}
      {testModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-[#1F2937] rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <h3 className="font-bold text-white text-sm mb-1">LLM Provider Connectivity Test</h3>
            <p className="text-xs text-gray-400 mb-4">
              Testing {testingProvider.toUpperCase()} ({testingModel})
            </p>

            {testing ? (
              <div className="py-8 flex flex-col items-center justify-center space-y-2">
                <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>
                <span className="text-xs text-gray-400">Pinging provider endpoint...</span>
              </div>
            ) : testResult ? (
              <div
                className={`p-4 rounded-xl border mb-4 text-xs ${
                  testResult.success
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                }`}
              >
                <div className="flex items-center space-x-2 font-semibold mb-1">
                  {testResult.success ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-rose-400" />
                  )}
                  <span>{testResult.success ? 'Connection Successful' : 'Connection Failed'}</span>
                </div>
                <p className="text-[11px] leading-relaxed mt-1">{testResult.message}</p>
                {testResult.latency_ms && (
                  <div className="mt-2 text-[10px] font-mono text-gray-400">
                    Roundtrip Latency: {testResult.latency_ms}ms
                  </div>
                )}
              </div>
            ) : null}

            <div className="flex justify-end">
              <button
                onClick={() => setTestModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-[#1E293B] hover:bg-[#2D3748] text-white text-xs font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
