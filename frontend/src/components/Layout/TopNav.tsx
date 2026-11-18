import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { PlusCircle, LogOut, Sparkles } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const TopNav: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/') return 'Overview';
    if (path.startsWith('/agents')) return 'Agent Management';
    if (path.startsWith('/datasets')) return 'Dataset & Test Cases';
    if (path === '/evaluations/new') return 'New Evaluation';
    if (path.startsWith('/evaluations')) return 'Evaluation Runs';
    if (path.startsWith('/compare')) return 'Model Benchmarking';
    if (path.startsWith('/regression')) return 'Regression Analysis';
    if (path.startsWith('/analytics')) return 'Analytics & Metrics';
    if (path.startsWith('/settings')) return 'Settings & Credentials';
    return 'Dashboard';
  };

  return (
    <header className="h-16 bg-[#0B0F17]/90 backdrop-blur-md border-b border-[#1F2937] px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Title & Mode */}
      <div className="flex items-center space-x-4">
        <h1 className="text-xl font-semibold text-white tracking-tight">{getPageTitle()}</h1>
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>FastAPI Live</span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-4">
        {/* New Evaluation CTA */}
        <button
          onClick={() => navigate('/evaluations/new')}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-all shadow-md shadow-indigo-600/20"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Evaluation</span>
        </button>

        {/* User Badge & Logout */}
        <div className="flex items-center space-x-3 pl-3 border-l border-[#1F2937]">
          <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-xs font-bold text-indigo-400">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
          </div>
          <div className="hidden md:block text-left text-xs">
            <div className="text-gray-200 font-medium leading-none">{user?.full_name || 'Engineer'}</div>
            <div className="text-gray-400 text-[11px] truncate max-w-[120px] mt-0.5">{user?.email}</div>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-gray-400 hover:text-rose-400 hover:bg-[#1E293B] transition-colors"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
