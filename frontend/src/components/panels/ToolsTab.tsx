import React from "react";
import type { LiveMetrics } from "../../types";

interface ToolsTabProps {
  metrics: LiveMetrics | null;
  loading: boolean;
  onRefresh: () => void;
}

export const ToolsTab: React.FC<ToolsTabProps> = ({
  metrics,
  loading,
  onRefresh,
}) => {
  const successPct = metrics ? Math.round(metrics.success_rate * 100) : 100;
  const toolList = ["calculator", "web_search", "python_executor"];

  return (
    <div className="flex flex-col h-full bg-slate-50/50 dark:bg-slate-900/50">
      {/* Metrics Banner */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
            Live Tool Telemetry
          </h2>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
          >
            {loading ? "..." : "🔄 Refresh"}
          </button>
        </div>

        {/* Metric Cards Row */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="p-3 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
            <div className="text-[10px] text-slate-400 font-medium uppercase">
              Total Invocations
            </div>
            <div className="text-lg font-bold text-slate-900 dark:text-slate-100 font-mono mt-0.5">
              {metrics?.total_calls || 0}
            </div>
          </div>
          <div className="p-3 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
            <div className="text-[10px] text-slate-400 font-medium uppercase">
              Success Rate
            </div>
            <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
              {successPct}%
            </div>
          </div>
        </div>

        {/* Tool Breakdown */}
        <div className="grid grid-cols-3 gap-1.5 text-center text-xs">
          {toolList.map((t) => {
            const data = metrics?.by_tool[t] || { calls: 0, success: 0 };
            return (
              <div
                key={t}
                className="p-2 rounded-lg bg-slate-100/80 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60"
              >
                <div className="font-mono text-[10px] text-slate-500 dark:text-slate-400 truncate">
                  {t.replace("_", " ")}
                </div>
                <div className="font-semibold text-slate-800 dark:text-slate-200 font-mono mt-0.5">
                  {data.success}/{data.calls}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Calls Log */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
        <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
          Recent Invocations
        </div>

        {!metrics || metrics.recent_calls.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">
            No tool calls logged yet. Ask the agent to calculate something, search the web, or run Python code.
          </div>
        ) : (
          [...metrics.recent_calls].reverse().map((call, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl bg-white dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700/80 text-xs space-y-1.5"
            >
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  {call.success ? (
                    <span className="text-emerald-500">✓</span>
                  ) : (
                    <span className="text-rose-500">✗</span>
                  )}
                  {call.tool}
                </span>
                <span className="text-slate-400 text-[10px]">
                  {call.latency_s}s
                </span>
              </div>

              <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 break-all bg-slate-50 dark:bg-slate-900 p-1.5 rounded">
                Args: {JSON.stringify(call.args)}
              </div>

              {call.output && (
                <div className="text-[10px] font-mono text-slate-700 dark:text-slate-300 break-all">
                  Result: {call.output}
                </div>
              )}

              {call.error && (
                <div className="text-[10px] font-mono text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 p-1.5 rounded">
                  Error: {call.error}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
