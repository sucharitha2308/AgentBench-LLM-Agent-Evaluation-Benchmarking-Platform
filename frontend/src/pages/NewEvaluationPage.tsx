import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bot,
  Database,
  Sliders,
  CheckCircle2,
  PlayCircle,
  Shield,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Zap,
} from 'lucide-react';
import { apiClient } from '../services/api';
import { Agent, Dataset } from '../types';

const EVALUATOR_OPTIONS = [
  { id: 'task_success', name: 'Task Success Evaluator', description: 'Checks overall goal completion against expected behaviors and answers.' },
  { id: 'tool_selection', name: 'Tool Selection Evaluator', description: 'Calculates precision, recall, and F1 score for tool call decisions.' },
  { id: 'tool_argument', name: 'Tool Argument Evaluator', description: 'Validates exact and normalized parameter values passed to tools.' },
  { id: 'structured_output', name: 'Structured JSON Output Evaluator', description: 'Enforces JSON schema validation, required fields, and types.' },
  { id: 'semantic', name: 'Semantic Response Evaluator', description: 'Measures keyword presence, semantic relevance, and factual grounding.' },
  { id: 'performance', name: 'Performance & SLA Evaluator', description: 'Measures latency against SLA ceilings and tracks token consumption.' },
  { id: 'reliability', name: 'Reliability & Error Isolation', description: 'Detects provider exceptions, tool crashes, and unexpected timeouts.' },
  { id: 'safety', name: 'Safety & Policy Compliance', description: 'Checks for unauthorized tool execution, prompt injection, and leaks.' },
  { id: 'llm_judge', name: 'LLM-as-a-Judge Evaluator', description: 'Qualitative scoring of clarity, tone, and empathy.' },
];

export const NewEvaluationPage: React.FC = () => {
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);

  // Form State
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [runName, setRunName] = useState('');
  const [selectedEvaluators, setSelectedEvaluators] = useState<string[]>([
    'task_success',
    'tool_selection',
    'tool_argument',
    'structured_output',
    'semantic',
    'performance',
    'reliability',
    'safety',
  ]);
  const [concurrency, setConcurrency] = useState(5);
  const [timeoutSeconds, setTimeoutSeconds] = useState(30);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [agentsRes, datasetsRes] = await Promise.all([
          apiClient.get<Agent[]>('/agents'),
          apiClient.get<Dataset[]>('/datasets'),
        ]);
        setAgents(agentsRes.data);
        setDatasets(datasetsRes.data);

        if (agentsRes.data.length > 0) setSelectedAgentId(agentsRes.data[0].id);
        if (datasetsRes.data.length > 0) setSelectedDatasetId(datasetsRes.data[0].id);
      } catch (err) {
        console.error('Failed to load agents or datasets:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const selectedAgent = agents.find((a) => a.id === selectedAgentId);
  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId);

  useEffect(() => {
    if (selectedAgent && selectedDataset && !runName) {
      setRunName(`${selectedAgent.name} on ${selectedDataset.name}`);
    }
  }, [selectedAgent, selectedDataset]);

  const toggleEvaluator = (id: string) => {
    if (selectedEvaluators.includes(id)) {
      setSelectedEvaluators(selectedEvaluators.filter((e) => e !== id));
    } else {
      setSelectedEvaluators([...selectedEvaluators, id]);
    }
  };

  const handleLaunch = async () => {
    if (!selectedAgentId || !selectedDatasetId) return;
    setIsSubmitting(true);
    try {
      const payload = {
        agent_id: selectedAgentId,
        dataset_id: selectedDatasetId,
        name: runName || `${selectedAgent?.name} Evaluation`,
        selected_evaluators: selectedEvaluators,
        concurrency_limit: concurrency,
        timeout_seconds: timeoutSeconds,
      };
      const res = await apiClient.post('/evaluations', payload);
      navigate(`/evaluations/${res.data.id}`);
    } catch (err: any) {
      alert(err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to start evaluation.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Stepper Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Configure Evaluation Run</h2>
        <p className="text-xs text-gray-400 mt-1">
          Follow the step-by-step workflow to benchmark your agent against ground truth datasets.
        </p>

        {/* Steps */}
        <div className="grid grid-cols-5 gap-2 mt-6">
          {[
            { num: 1, label: 'Select Agent' },
            { num: 2, label: 'Select Dataset' },
            { num: 3, label: 'Evaluators' },
            { num: 4, label: 'Parameters' },
            { num: 5, label: 'Review & Run' },
          ].map((s) => (
            <div
              key={s.num}
              onClick={() => s.num < step && setStep(s.num)}
              className={`p-2.5 rounded-xl border text-center transition-all ${
                s.num === step
                  ? 'bg-indigo-600/10 border-indigo-500/40 text-indigo-400 font-semibold'
                  : s.num < step
                  ? 'bg-[#111827] border-[#1F2937] text-gray-300 cursor-pointer'
                  : 'bg-[#0B0F17] border-[#1F2937] text-gray-600'
              }`}
            >
              <div className="text-[10px] uppercase font-mono">Step {s.num}</div>
              <div className="text-xs truncate font-medium">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-[#111827] border border-[#1F2937] rounded-2xl p-6 shadow-xl min-h-[360px] flex flex-col justify-between">
        {/* Step 1: Select Agent */}
        {step === 1 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white">Choose Agent for Evaluation</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgentId(agent.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    selectedAgentId === agent.id
                      ? 'bg-indigo-600/15 border-indigo-500 text-white shadow-md shadow-indigo-500/10'
                      : 'bg-[#0B0F17] border-[#1F2937] text-gray-300 hover:border-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm">{agent.name}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1E293B] text-cyan-400">
                      {agent.provider.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 line-clamp-2 mb-3">{agent.description}</p>
                  <div className="text-[11px] font-mono text-gray-500 flex items-center space-x-3">
                    <span>Model: {agent.model_name}</span>
                    <span>Tools: {agent.tools?.length || 0}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Select Dataset */}
        {step === 2 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white">Choose Target Benchmark Dataset</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {datasets.map((d) => (
                <div
                  key={d.id}
                  onClick={() => setSelectedDatasetId(d.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    selectedDatasetId === d.id
                      ? 'bg-indigo-600/15 border-indigo-500 text-white shadow-md shadow-indigo-500/10'
                      : 'bg-[#0B0F17] border-[#1F2937] text-gray-300 hover:border-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm">{d.name}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
                      {d.test_case_count} Test Cases
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 line-clamp-2 mb-3">{d.description}</p>
                  <span className="text-[11px] font-mono text-gray-500">Domain: {d.domain}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Select Evaluators */}
        {step === 3 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white">Select Automated Evaluators</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto pr-1">
              {EVALUATOR_OPTIONS.map((ev) => {
                const isChecked = selectedEvaluators.includes(ev.id);
                return (
                  <label
                    key={ev.id}
                    className={`flex items-start space-x-3 p-3 rounded-xl border cursor-pointer transition-colors ${
                      isChecked
                        ? 'bg-indigo-600/10 border-indigo-500/50'
                        : 'bg-[#0B0F17] border-[#1F2937] opacity-60 hover:opacity-100'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleEvaluator(ev.id)}
                      className="mt-1 rounded bg-[#0B0F17] border-gray-700 text-indigo-600 focus:ring-indigo-500"
                    />
                    <div>
                      <div className="text-xs font-semibold text-white">{ev.name}</div>
                      <div className="text-[11px] text-gray-400 mt-0.5">{ev.description}</div>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>
        )}

        {/* Step 4: Concurrency & Parameters */}
        {step === 4 && (
          <div className="space-y-6 max-w-lg">
            <h3 className="text-sm font-semibold text-white">Execution Parameters</h3>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1.5">
                Evaluation Run Name
              </label>
              <input
                type="text"
                value={runName}
                onChange={(e) => setRunName(e.target.value)}
                className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-gray-300 font-medium">Concurrency Limit</span>
                <span className="font-mono text-indigo-400">{concurrency} parallel workers</span>
              </div>
              <input
                type="range"
                min={1}
                max={15}
                value={concurrency}
                onChange={(e) => setConcurrency(parseInt(e.target.value))}
                className="w-full accent-indigo-500"
              />
              <span className="text-[11px] text-gray-500">
                Number of test cases processed concurrently.
              </span>
            </div>

            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-gray-300 font-medium">Per-Test Timeout</span>
                <span className="font-mono text-indigo-400">{timeoutSeconds} seconds</span>
              </div>
              <input
                type="range"
                min={5}
                max={90}
                step={5}
                value={timeoutSeconds}
                onChange={(e) => setTimeoutSeconds(parseInt(e.target.value))}
                className="w-full accent-indigo-500"
              />
              <span className="text-[11px] text-gray-500">
                Upper bound before a test case is safely failed as a timeout error.
              </span>
            </div>
          </div>
        )}

        {/* Step 5: Review & Run */}
        {step === 5 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white">Review Configuration Summary</h3>
            <div className="p-4 rounded-xl bg-[#0B0F17] border border-[#1F2937] space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Run Name:</span>
                <span className="font-medium text-white">{runName}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Agent:</span>
                <span className="font-medium text-indigo-400">
                  {selectedAgent?.name} ({selectedAgent?.provider} • {selectedAgent?.model_name})
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Dataset:</span>
                <span className="font-medium text-emerald-400">
                  {selectedDataset?.name} ({selectedDataset?.test_case_count} test cases)
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Selected Evaluators:</span>
                <span className="font-mono text-cyan-400">{selectedEvaluators.length} active</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Worker Concurrency:</span>
                <span className="font-mono text-gray-200">{concurrency} workers</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Timeout Threshold:</span>
                <span className="font-mono text-gray-200">{timeoutSeconds}s</span>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between pt-6 border-t border-[#1F2937] mt-6">
          <button
            type="button"
            disabled={step === 1}
            onClick={() => setStep(step - 1)}
            className="flex items-center space-x-1 px-4 py-2 rounded-xl bg-[#1E293B] hover:bg-[#2D3748] text-gray-300 text-xs font-medium disabled:opacity-30 disabled:pointer-events-none"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Previous</span>
          </button>

          {step < 5 ? (
            <button
              type="button"
              onClick={() => setStep(step + 1)}
              className="flex items-center space-x-1 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md shadow-indigo-600/30"
            >
              <span>Next Step</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              type="button"
              disabled={isSubmitting}
              onClick={handleLaunch}
              className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 disabled:opacity-50"
            >
              <PlayCircle className="w-4 h-4" />
              <span>{isSubmitting ? 'Dispatching...' : 'Launch Evaluation Run'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
