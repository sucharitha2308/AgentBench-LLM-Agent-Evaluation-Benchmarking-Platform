import React, { useEffect, useState } from 'react';
import {
  Key,
  Shield,
  CheckCircle2,
  AlertCircle,
  Trash2,
  ExternalLink,
  User,
  Server,
  Zap,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../services/api';
import { ProviderCredential } from '../types';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [credentials, setCredentials] = useState<ProviderCredential[]>([]);
  const [loading, setLoading] = useState(true);

  // New Credential Form
  const [providerName, setProviderName] = useState<'openai' | 'gemini'>('openai');
  const [keyAlias, setKeyAlias] = useState('Primary Key');
  const [apiKey, setApiKey] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const fetchCredentials = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<ProviderCredential[]>('/agents/credentials');
      setCredentials(res.data);
    } catch (err) {
      console.error('Failed to load credentials:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCredentials();
  }, []);

  const handleSaveKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) return;
    setSubmitting(true);
    setTestResult(null);

    try {
      await apiClient.post('/agents/credentials', {
        provider_name: providerName,
        key_alias: keyAlias,
        api_key: apiKey.trim(),
      });
      setApiKey('');
      setKeyAlias('Primary Key');
      fetchCredentials();
      alert(`Successfully saved and encrypted ${providerName.toUpperCase()} API key.`);
    } catch (err: any) {
      alert(err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to save credential.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteKey = async (id: string) => {
    if (!window.confirm('Delete this provider credential?')) return;
    try {
      await apiClient.delete(`/agents/credentials/${id}`);
      fetchCredentials();
    } catch (err) {
      alert('Failed to delete credential.');
    }
  };

  const testKeyConnection = async (prov: string) => {
    setTestResult(null);
    try {
      const model = prov === 'openai' ? 'gpt-4o-mini' : 'gemini-1.5-flash';
      const res = await apiClient.post('/agents/test-connection', {
        provider: prov,
        model_name: model,
      });
      setTestResult({
        provider: prov,
        success: res.data.success,
        message: res.data.message,
        latency_ms: res.data.latency_ms,
      });
    } catch (err: any) {
      setTestResult({
        provider: prov,
        success: false,
        message: err.response?.data?.error?.message || err.response?.data?.detail || 'Connection test failed.',
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Settings & Provider Credentials</h2>
        <p className="text-xs text-gray-400 mt-1">
          Manage your account profile, configure external LLM API credentials, and review encryption policies
        </p>
      </div>

      {/* User Profile Card */}
      <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937]">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm">{user?.full_name || 'AI Engineer'}</h3>
            <span className="text-xs text-gray-400">{user?.email}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-4 border-t border-[#1F2937] text-xs">
          <div>
            <span className="text-gray-500 block">User ID</span>
            <span className="font-mono text-gray-300 text-[11px] truncate block">{user?.id}</span>
          </div>
          <div>
            <span className="text-gray-500 block">Account Status</span>
            <span className="text-emerald-400 font-semibold">Active</span>
          </div>
          <div>
            <span className="text-gray-500 block">Password Security</span>
            <span className="text-cyan-400 font-mono text-[11px]">Argon2 Hashed</span>
          </div>
        </div>
      </div>

      {/* Provider API Key Management */}
      <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <Key className="w-4 h-4 text-indigo-400" />
              <h3 className="font-bold text-white text-sm">LLM Provider API Keys</h3>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Keys are encrypted at rest with AES-GCM. Raw credentials are never stored in plaintext or exposed in API responses.
            </p>
          </div>
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px] font-mono">
            <Shield className="w-3.5 h-3.5 text-indigo-400" />
            <span>Encrypted at Rest</span>
          </div>
        </div>

        {/* Add Key Form */}
        <form onSubmit={handleSaveKey} className="p-4 rounded-xl bg-[#0B0F17] border border-[#1F2937] space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-medium text-gray-300 mb-1">Provider</label>
              <select
                value={providerName}
                onChange={(e: any) => setProviderName(e.target.value)}
                className="w-full bg-[#111827] border border-[#1F2937] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="openai">OpenAI (GPT-4o, GPT-4o-mini)</option>
                <option value="gemini">Google Gemini (Gemini 1.5 Pro, Flash)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-gray-300 mb-1">Key Label / Alias</label>
              <input
                type="text"
                value={keyAlias}
                onChange={(e) => setKeyAlias(e.target.value)}
                placeholder="e.g. Production Key"
                className="w-full bg-[#111827] border border-[#1F2937] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-gray-300 mb-1">API Secret Key</label>
              <input
                type="password"
                required
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-... or AIza..."
                className="w-full bg-[#111827] border border-[#1F2937] rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submitting || !apiKey}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 disabled:opacity-40"
            >
              {submitting ? 'Encrypting & Saving...' : 'Save & Encrypt API Key'}
            </button>
          </div>
        </form>

        {/* Existing Keys Table */}
        <div>
          <span className="text-[10px] uppercase font-semibold text-gray-400 tracking-wider block mb-2">
            Active Configured Credentials ({credentials.length})
          </span>

          {credentials.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#1F2937] text-gray-400">
                    <th className="pb-2.5 px-3 font-medium">Provider</th>
                    <th className="pb-2.5 px-3 font-medium">Label</th>
                    <th className="pb-2.5 px-3 font-medium">Masked Key</th>
                    <th className="pb-2.5 px-3 font-medium">Status</th>
                    <th className="pb-2.5 px-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1F2937]/50">
                  {credentials.map((cred) => (
                    <tr key={cred.id} className="hover:bg-[#1E293B]/40 transition-colors">
                      <td className="py-2.5 px-3 font-mono text-white uppercase font-semibold">
                        {cred.provider_name}
                      </td>
                      <td className="py-2.5 px-3 text-gray-300">{cred.key_alias}</td>
                      <td className="py-2.5 px-3 font-mono text-gray-400 text-[11px]">{cred.masked_key}</td>
                      <td className="py-2.5 px-3">
                        <span className="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded text-[10px] font-medium inline-flex items-center space-x-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Valid</span>
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right space-x-2">
                        <button
                          onClick={() => testKeyConnection(cred.provider_name)}
                          className="px-2 py-1 rounded bg-[#1E293B] hover:bg-[#2D3748] text-gray-300 hover:text-white text-[11px] transition-colors"
                        >
                          Verify
                        </button>
                        <button
                          onClick={() => handleDeleteKey(cred.id)}
                          className="p-1 rounded text-gray-400 hover:text-rose-400 transition-colors"
                          title="Delete credential"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-[#0B0F17] text-xs text-gray-500 text-center">
              No custom API keys configured. Evaluation runs without keys will automatically execute in deterministic Mock Demo Mode.
            </div>
          )}
        </div>

        {/* Test Result Callout */}
        {testResult && (
          <div
            className={`p-3.5 rounded-xl border text-xs ${
              testResult.success
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
            }`}
          >
            <div className="flex items-center space-x-2 font-semibold">
              {testResult.success ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
              <span>{testResult.provider.toUpperCase()} Verification Result</span>
            </div>
            <p className="mt-1 text-[11px] leading-relaxed">{testResult.message}</p>
            {testResult.latency_ms && (
              <span className="block text-[10px] font-mono text-gray-400 mt-1">
                Roundtrip: {testResult.latency_ms}ms
              </span>
            )}
          </div>
        )}
      </div>

      {/* Platform Architecture & Infrastructure Info */}
      <div className="p-6 rounded-2xl bg-[#111827] border border-[#1F2937] space-y-4">
        <div className="flex items-center space-x-2 text-white font-bold text-sm">
          <Server className="w-4 h-4 text-cyan-400" />
          <span>System Environment & Infrastructure</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-[#0B0F17] border border-[#1F2937]">
            <span className="text-gray-500 block text-[10px]">API Engine</span>
            <span className="font-semibold text-white">FastAPI 0.163</span>
          </div>
          <div className="p-3 rounded-xl bg-[#0B0F17] border border-[#1F2937]">
            <span className="text-gray-500 block text-[10px]">Database ORM</span>
            <span className="font-semibold text-white">SQLAlchemy 2.0</span>
          </div>
          <div className="p-3 rounded-xl bg-[#0B0F17] border border-[#1F2937]">
            <span className="text-gray-500 block text-[10px]">Worker Broker</span>
            <span className="font-semibold text-white">Celery & AsyncIO</span>
          </div>
          <div className="p-3 rounded-xl bg-[#0B0F17] border border-[#1F2937]">
            <span className="text-gray-500 block text-[10px]">Frontend Tooling</span>
            <span className="font-semibold text-white">Vite + React TS</span>
          </div>
        </div>
      </div>
    </div>
  );
};
