import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Bot,
  Database,
  PlayCircle,
  GitCompare,
  TrendingDown,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Zap,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, setCollapsed }) => {
  const navItems = [
    { name: 'Overview', to: '/', icon: LayoutDashboard },
    { name: 'Agents', to: '/agents', icon: Bot },
    { name: 'Datasets', to: '/datasets', icon: Database },
    { name: 'Evaluations', to: '/evaluations', icon: PlayCircle },
    { name: 'Model Comparison', to: '/compare', icon: GitCompare },
    { name: 'Regression Testing', to: '/regression', icon: TrendingDown },
    { name: 'Analytics', to: '/analytics', icon: BarChart3 },
    { name: 'Settings', to: '/settings', icon: Settings },
  ];

  return (
    <aside
      className={`h-screen bg-[#0B0F17] border-r border-[#1F2937] flex flex-col transition-all duration-300 z-30 sticky top-0 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-[#1F2937]">
        {!collapsed && (
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg text-white tracking-tight">AgentBench</span>
              <span className="text-[10px] block font-mono uppercase tracking-wider text-indigo-400 font-semibold">
                v1.0 • Platform
              </span>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="w-full flex justify-center">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Zap className="w-5 h-5 text-white" />
            </div>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={`p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-[#1E293B] transition-colors ${
            collapsed ? 'hidden' : 'block'
          }`}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 shadow-sm'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-[#111827]'
                } ${collapsed ? 'justify-center' : 'space-x-3'}`
              }
              title={collapsed ? item.name : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Status Card */}
      {!collapsed && (
        <div className="p-3 m-3 rounded-xl bg-[#111827] border border-[#1F2937]/80 text-xs">
          <div className="flex items-center space-x-2 text-emerald-400 mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span className="font-semibold">Engine Ready</span>
          </div>
          <p className="text-gray-400 text-[11px] leading-relaxed">
            Deterministic mock & live API evaluators operational.
          </p>
        </div>
      )}

      {/* Collapsed expand button at bottom */}
      {collapsed && (
        <div className="p-3 flex justify-center border-t border-[#1F2937]">
          <button
            onClick={() => setCollapsed(false)}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-[#1E293B]"
            title="Expand sidebar"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </aside>
  );
};
