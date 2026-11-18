import React, { useEffect, useState } from 'react';
import {
  Database,
  Plus,
  Download,
  Upload,
  Trash2,
  Tag,
  Clock,
  Layers,
  ChevronRight,
  Code,
  FileJson,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { apiClient } from '../services/api';
import { Dataset, TestCase } from '../types';

export const DatasetsPage: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTestCase, setActiveTestCase] = useState<TestCase | null>(null);

  // Add test case modal
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [tcId, setTcId] = useState('');
  const [tcName, setTcName] = useState('');
  const [tcInput, setTcInput] = useState('');
  const [tcBehavior, setTcBehavior] = useState('');
  const [tcDifficulty, setTcDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [tcTags, setTcTags] = useState('tool_calling, support');
  const [tcExpectedTools, setTcExpectedTools] = useState('');
  const [tcMaxLatency, setTcMaxLatency] = useState(3500);

  // Import JSON Modal
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [importJsonText, setImportJsonText] = useState('');
  const [importStatus, setImportStatus] = useState<string | null>(null);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<Dataset[]>('/datasets');
      setDatasets(res.data);
      if (res.data.length > 0 && !selectedDataset) {
        setSelectedDataset(res.data[0]);
      }
    } catch (err) {
      console.error('Failed to load datasets:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTestCases = async (datasetId: string) => {
    try {
      const res = await apiClient.get<TestCase[]>(`/datasets/${datasetId}/test-cases`);
      setTestCases(res.data);
      if (res.data.length > 0) {
        setActiveTestCase(res.data[0]);
      } else {
        setActiveTestCase(null);
      }
    } catch (err) {
      console.error('Failed to load test cases:', err);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  useEffect(() => {
    if (selectedDataset) {
      fetchTestCases(selectedDataset.id);
    }
  }, [selectedDataset]);

  const handleExport = async () => {
    if (!selectedDataset) return;
    try {
      const res = await apiClient.get(`/datasets/${selectedDataset.id}/export`);
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedDataset.name.replace(/\s+/g, '_')}_dataset.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to export dataset.');
    }
  };

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDataset) return;
    setImportStatus(null);
    try {
      const parsed = JSON.parse(importJsonText);
      const res = await apiClient.post(`/datasets/${selectedDataset.id}/import`, parsed);
      setImportStatus(`Successfully imported ${res.data.imported_count} test cases.`);
      fetchTestCases(selectedDataset.id);
      setTimeout(() => {
        setIsImportModalOpen(false);
        setImportJsonText('');
        setImportStatus(null);
      }, 1500);
    } catch (err: any) {
      setImportStatus(`Import error: ${err.message || 'Invalid JSON format'}`);
    }
  };

  const handleAddTestCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDataset) return;

    let expectedToolsParsed = [];
    if (tcExpectedTools.trim()) {
      try {
        expectedToolsParsed = JSON.parse(tcExpectedTools);
      } catch {
        // Fallback simple tool name list
        expectedToolsParsed = tcExpectedTools.split(',').map((t) => ({
          tool_name: t.trim(),
          arguments: {},
        }));
      }
    }

    const payload = {
      test_case_id: tcId,
      name: tcName,
      user_input: tcInput,
      expected_behavior: tcBehavior,
      difficulty_level: tcDifficulty,
      tags: tcTags.split(',').map((t) => t.trim()).filter(Boolean),
      expected_tool_calls: expectedToolsParsed,
      expected_output: {},
      max_allowed_latency_ms: tcMaxLatency,
      evaluation_criteria: { require_task_success: true },
    };

    try {
      await apiClient.post(`/datasets/${selectedDataset.id}/test-cases`, payload);
      setIsAddModalOpen(false);
      fetchTestCases(selectedDataset.id);
      // Reset
      setTcId('');
      setTcName('');
      setTcInput('');
      setTcBehavior('');
      setTcExpectedTools('');
    } catch (err: any) {
      alert(err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to add test case.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">Evaluation Datasets & Ground Truth Suites</h2>
          <p className="text-xs text-gray-400">
            Define repeatable test cases, expected tool calls, JSON schemas, and acceptance criteria
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-[#1E293B] hover:bg-[#2D3748] text-gray-300 hover:text-white text-xs font-medium transition-colors"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Import JSON</span>
          </button>
          <button
            onClick={handleExport}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-[#1E293B] hover:bg-[#2D3748] text-gray-300 hover:text-white text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </button>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-all shadow-md shadow-indigo-600/20"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Test Case</span>
          </button>
        </div>
      </div>

      {/* Dataset Selection Tabs */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-2 border-b border-[#1F2937]">
        {datasets.map((d) => (
          <button
            key={d.id}
            onClick={() => setSelectedDataset(d)}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-medium transition-all whitespace-nowrap ${
              selectedDataset?.id === d.id
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                : 'bg-[#111827] text-gray-400 hover:text-gray-200 hover:bg-[#1E293B]'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>{d.name}</span>
            <span
              className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                selectedDataset?.id === d.id ? 'bg-indigo-700 text-white' : 'bg-[#0B0F17] text-gray-400'
              }`}
            >
              {d.test_case_count || testCases.length}
            </span>
          </button>
        ))}
      </div>

      {/* Main Content: Split Test Cases Table + Inspection Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Test Cases Table */}
        <div className="lg:col-span-2 rounded-2xl bg-[#111827] border border-[#1F2937] p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3 px-2">
            <span className="text-xs font-semibold text-gray-300">
              Test Cases ({testCases.length})
            </span>
            <span className="text-[11px] text-gray-500 font-mono">
              Domain: {selectedDataset?.domain || 'e-commerce'}
            </span>
          </div>

          <div className="overflow-x-auto flex-1 max-h-[600px] overflow-y-auto">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 bg-[#111827] border-b border-[#1F2937]">
                <tr className="text-gray-400">
                  <th className="py-2.5 px-3 font-medium">ID</th>
                  <th className="py-2.5 px-3 font-medium">Test Case Name</th>
                  <th className="py-2.5 px-3 font-medium">Difficulty</th>
                  <th className="py-2.5 px-3 font-medium">Expected Tools</th>
                  <th className="py-2.5 px-3 font-medium">Max SLA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F2937]/50">
                {testCases.map((tc) => {
                  const isSelected = activeTestCase?.id === tc.id;
                  return (
                    <tr
                      key={tc.id}
                      onClick={() => setActiveTestCase(tc)}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? 'bg-indigo-600/15 text-white' : 'hover:bg-[#1E293B]/40 text-gray-300'
                      }`}
                    >
                      <td className="py-2.5 px-3 font-mono text-[11px] font-semibold text-indigo-400">
                        {tc.test_case_id}
                      </td>
                      <td className="py-2.5 px-3 font-medium truncate max-w-[200px]">{tc.name}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-medium uppercase font-mono ${
                            tc.difficulty_level === 'easy'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : tc.difficulty_level === 'medium'
                              ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {tc.difficulty_level}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-gray-400">
                        {tc.expected_tool_calls && tc.expected_tool_calls.length > 0 ? (
                          tc.expected_tool_calls.map((t) => t.tool_name).join(', ')
                        ) : (
                          <span className="text-gray-500 italic">None (Direct answer)</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-gray-400">
                        {tc.max_allowed_latency_ms}ms
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Test Case Inspector */}
        <div className="rounded-2xl bg-[#111827] border border-[#1F2937] p-5 flex flex-col justify-between">
          {activeTestCase ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-[#1F2937] pb-3">
                <div>
                  <span className="font-mono text-xs font-bold text-indigo-400">
                    {activeTestCase.test_case_id}
                  </span>
                  <h3 className="font-semibold text-white text-sm mt-0.5">{activeTestCase.name}</h3>
                </div>
                <span className="text-[10px] font-mono uppercase bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded border border-indigo-500/20">
                  {activeTestCase.difficulty_level}
                </span>
              </div>

              <div>
                <label className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                  User Prompt / Input
                </label>
                <div className="p-3 rounded-xl bg-[#0B0F17] border border-[#1F2937] text-xs text-gray-200 leading-relaxed font-mono">
                  "{activeTestCase.user_input}"
                </div>
              </div>

              <div>
                <label className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                  Expected Behavior
                </label>
                <p className="text-xs text-gray-300 leading-relaxed">
                  {activeTestCase.expected_behavior || 'Direct response satisfying constraints.'}
                </p>
              </div>

              <div>
                <label className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                  Expected Tool Calls & Arguments
                </label>
                <pre className="p-3 rounded-xl bg-[#0B0F17] border border-[#1F2937] text-[11px] font-mono text-cyan-300 overflow-x-auto">
                  {JSON.stringify(activeTestCase.expected_tool_calls, null, 2)}
                </pre>
              </div>

              {activeTestCase.expected_output && Object.keys(activeTestCase.expected_output).length > 0 && (
                <div>
                  <label className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                    Expected Output Specifications / Schema
                  </label>
                  <pre className="p-3 rounded-xl bg-[#0B0F17] border border-[#1F2937] text-[11px] font-mono text-emerald-300 overflow-x-auto max-h-40">
                    {JSON.stringify(activeTestCase.expected_output, null, 2)}
                  </pre>
                </div>
              )}

              <div>
                <label className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider block mb-1.5">
                  Tags
                </label>
                <div className="flex flex-wrap gap-1">
                  {activeTestCase.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] bg-[#1E293B] text-gray-300 px-2 py-0.5 rounded border border-gray-700"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-gray-500">
              Select a test case to inspect expectations and schemas.
            </div>
          )}
        </div>
      </div>

      {/* Add Test Case Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-[#1F2937] rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6 shadow-2xl">
            <h3 className="font-bold text-white text-sm mb-4">Add Test Case to Dataset</h3>
            <form onSubmit={handleAddTestCase} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Test Case ID</label>
                  <input
                    type="text"
                    required
                    value={tcId}
                    onChange={(e) => setTcId(e.target.value)}
                    placeholder="e.g. TC-031"
                    className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Difficulty</label>
                  <select
                    value={tcDifficulty}
                    onChange={(e: any) => setTcDifficulty(e.target.value)}
                    className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-medium mb-1">Name</label>
                <input
                  type="text"
                  required
                  value={tcName}
                  onChange={(e) => setTcName(e.target.value)}
                  placeholder="e.g. Verify cancelled order refund"
                  className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-medium mb-1">User Input / Prompt</label>
                <textarea
                  required
                  rows={2}
                  value={tcInput}
                  onChange={(e) => setTcInput(e.target.value)}
                  placeholder="What user asks the agent..."
                  className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-medium mb-1">Expected Behavior</label>
                <textarea
                  rows={2}
                  value={tcBehavior}
                  onChange={(e) => setTcBehavior(e.target.value)}
                  placeholder="Detailed description of what the agent should do..."
                  className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-medium mb-1">
                  Expected Tool Calls (JSON Array or tool names)
                </label>
                <input
                  type="text"
                  value={tcExpectedTools}
                  onChange={(e) => setTcExpectedTools(e.target.value)}
                  placeholder='e.g. [{"tool_name": "get_order", "arguments": {"order_id": "ORD-1001"}}]'
                  className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Tags (comma-separated)</label>
                  <input
                    type="text"
                    value={tcTags}
                    onChange={(e) => setTcTags(e.target.value)}
                    className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Max Latency SLA (ms)</label>
                  <input
                    type="number"
                    value={tcMaxLatency}
                    onChange={(e) => setTcMaxLatency(parseInt(e.target.value) || 3500)}
                    className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-[#1F2937]">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-[#1E293B] text-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium"
                >
                  Save Test Case
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Import JSON Modal */}
      {isImportModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-[#1F2937] rounded-2xl w-full max-w-lg p-6 shadow-2xl">
            <h3 className="font-bold text-white text-sm mb-1">Import Test Cases from JSON</h3>
            <p className="text-xs text-gray-400 mb-3">
              Paste standard AgentBench dataset JSON with a "test_cases" array.
            </p>

            {importStatus && (
              <div className="p-3 mb-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs">
                {importStatus}
              </div>
            )}

            <form onSubmit={handleImport} className="space-y-4">
              <textarea
                required
                rows={10}
                value={importJsonText}
                onChange={(e) => setImportJsonText(e.target.value)}
                placeholder='{ "test_cases": [ { "test_case_id": "TC-100", "name": "...", "user_input": "..." } ] }'
                className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl p-3 text-[11px] font-mono text-white focus:outline-none focus:border-indigo-500"
              />

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setIsImportModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-[#1E293B] text-gray-300 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium"
                >
                  Parse & Import
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
