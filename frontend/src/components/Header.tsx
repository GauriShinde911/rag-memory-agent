import React from "react";
import type { HealthStatus } from "../types";

interface HeaderProps {
  sessionId: string;
  health: HealthStatus | null;
  onNewSession: () => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  sessionId,
  health,
  onNewSession,
  darkMode,
  onToggleDarkMode,
}) => {
  const getHealthBadge = () => {
    if (!health) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
          Connecting...
        </span>
      );
    }
    if (health.embeddings === "loading") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
          Loading embeddings...
        </span>
      );
    }
    if (health.llm === "missing_key") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
          Missing API Key
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
        Live & Ready
      </span>
    );
  };

  return (
    <header className="h-16 px-6 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur sticky top-0 z-40 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-base shadow-md shadow-indigo-500/20">
          Ω
        </div>
        <div>
          <h1 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            RAG Memory Agent
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
              Viva Edition
            </span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Vector long-term memory & self-correcting feedback loop
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Session ID Badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800/80 text-xs font-mono text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
          <span className="text-slate-400 font-sans">Session:</span>
          <span className="font-semibold text-indigo-600 dark:text-indigo-400">{sessionId}</span>
        </div>

        {/* Model Badge */}
        {health && (
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800/80 text-xs font-mono text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            <span className="text-slate-400 font-sans">Model:</span>
            <span>{health.model}</span>
          </div>
        )}

        {/* Health status */}
        {getHealthBadge()}

        {/* New Session Button */}
        <button
          onClick={onNewSession}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 border border-indigo-200 dark:border-indigo-800/80 transition-colors shadow-sm"
          title="Clear short-term memory buffer while preserving long-term vector DB"
        >
          <span>✨ New Session</span>
        </button>

        {/* Dark/Light toggle */}
        <button
          onClick={onToggleDarkMode}
          className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title="Toggle light/dark theme"
        >
          {darkMode ? "☀️" : "🌙"}
        </button>
      </div>
    </header>
  );
};
