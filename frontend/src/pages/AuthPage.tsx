import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, ShieldCheck, ArrowRight, Lock, Mail, User as UserIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const AuthPage: React.FC = () => {
  const { login, register, loginAsDemo } = useAuth();
  const navigate = useNavigate();

  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        await register(email, password, fullName);
      } else {
        await login(email, password);
      }
      navigate('/');
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Authentication failed. Please verify your credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      await loginAsDemo();
      navigate('/');
    } catch (err: any) {
      setError('Could not connect to demo account. Please ensure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 mb-4 shadow-xl shadow-indigo-500/20">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">AgentBench</h1>
          <p className="text-sm text-gray-400 mt-1">
            LLM Agent Evaluation, Benchmarking & Observability
          </p>
        </div>

        {/* Auth Card */}
        <div className="bg-[#111827] border border-[#1F2937] rounded-2xl p-6 sm:p-8 shadow-2xl">
          {/* Quick Demo Login Option */}
          <div className="mb-6 pb-6 border-b border-[#1F2937]">
            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600/20 via-cyan-500/10 to-indigo-600/20 border border-indigo-500/40 hover:border-indigo-500/80 text-indigo-300 hover:text-white font-medium text-sm flex items-center justify-center space-x-2 transition-all group"
            >
              <SparklesIcon className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
              <span>Sign in with 1-Click Demo Engineer Account</span>
            </button>
            <p className="text-[11px] text-gray-400 text-center mt-2">
              Pre-configured with sample customer-support agent and 30 benchmark test cases.
            </p>
          </div>

          {/* Form Tabs */}
          <div className="flex rounded-lg bg-[#0B0F17] p-1 mb-6 border border-[#1F2937]">
            <button
              type="button"
              onClick={() => { setIsRegister(false); setError(null); }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
                !isRegister ? 'bg-[#1E293B] text-white shadow-sm' : 'text-gray-400 hover:text-white'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setIsRegister(true); setError(null); }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
                isRegister ? 'bg-[#1E293B] text-white shadow-sm' : 'text-gray-400 hover:text-white'
              }`}
            >
              Create Account
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs leading-relaxed">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1.5">Full Name</label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Alex Mercer"
                    className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl pl-9 pr-3.5 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl pl-9 pr-3.5 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-[#0B0F17] border border-[#1F2937] rounded-xl pl-9 pr-3.5 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/30 disabled:opacity-50 mt-2"
            >
              <span>{loading ? 'Processing...' : isRegister ? 'Register & Continue' : 'Sign In'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </div>

        <div className="flex items-center justify-center space-x-2 text-gray-400 text-xs mt-6">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Argon2 Security • AES-GCM Encrypted Credentials</span>
        </div>
      </div>
    </div>
  );
};

const SparklesIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);
