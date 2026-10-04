import React, { useState, useEffect } from "react";
import type { EvalStatus } from "../../types";
import { triggerEvalRun, fetchEvalStatus, getExportLogUrl } from "../../api/client";

export const EvalTab: React.FC = () => {
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [evalData, setEvalData] = useState<EvalStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Polling loop for active eval run
  useEffect(() => {
    if (!activeRunId) return;

    let isMounted = true;
    const interval = setInterval(async () => {
      try {
        const status = await fetchEvalStatus(activeRunId);
        if (!isMounted) return;
        setEvalData(status);

        if (status.status === "completed" || status.status === "failed") {
          clearInterval(interval);
          setLoading(false);
        }
      } catch (err: any) {
        if (!isMounted) return;
        setError(err.message || "Failed to poll eval status");
        clearInterval(interval);
        setLoading(false);
      }
    }, 1500);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [activeRunId]);

  const handleStartEval = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await triggerEvalRun();
      setActiveRunId(res.run_id);
      setEvalData({
        run_id: res.run_id,
        status: "queued",
        progress: 0.0,
        current_step: "Initializing isolated scenarios...",
      });
    } catch (err: any) {
      setError(err.message || "Failed to trigger evaluation");
      setLoading(false);
    }
  };

  const metrics = evalData?.metrics;
  const isRunning = evalData?.status === "running" || evalData?.status === "queued";

  return (
    <div className="flex flex-col h-full bg-slate-50/50 dark:bg-slate-900/50 overflow-y-auto p-4 space-y-4">
      {/* Top Banner & Control */}
      <div className="p-4 rounded-xl bg-white dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Multi-Session Evaluation (3 Scenarios)
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Tests profile recall, memory feedback loop correction, and web research persistence.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleStartEval}
              disabled={loading || isRunning}
              className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
            >
              {isRunning ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-white animate-ping" />
                  Running...
                </>
              ) : (
                "▶ Run 3 Scenarios"
              )}
            </button>

            {evalData?.status === "completed" && (
              <a
                href={getExportLogUrl()}
                download="test_log.json"
                className="px-3 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-600 transition-colors"
              >
                📥 Export Log
              </a>
            )}
          </div>
        </div>

        {/* Progress Bar & Status */}
        {isRunning && (
          <div className="space-y-1.5 pt-2 border-t border-slate-100 dark:border-slate-700">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span className="font-mono text-[11px] truncate max-w-[80%]">
                {evalData?.current_step || "Running..."}
              </span>
              <span className="font-mono text-[11px] font-semibold text-indigo-600 dark:text-indigo-400">
                {Math.round((evalData?.progress || 0) * 100)}%
              </span>
            </div>
            <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-600 transition-all duration-300"
                style={{ width: `${Math.round((evalData?.progress || 0) * 100)}%` }}
              />
            </div>
          </div>
        )}

        {error && (
          <div className="p-2.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300">
            {error}
          </div>
        )}
      </div>

      {/* 5 Metric Cards */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
          {/* 1. Retrieval Accuracy */}
          <div className="p-3 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
            <div className="text-[10px] text-slate-400 uppercase font-medium">
              Retrieval (Hit@4)
            </div>
            <div className="text-lg font-bold text-slate-900 dark:text-slate-100 font-mono mt-0.5">
              {Math.round(metrics.hit_at_4 * 100)}%
            </div>
            <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
              All expected facts found
            </div>
          </div>

          {/* 2. MRR */}
          <div className="p-3 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
            <div className="text-[10px] text-slate-400 uppercase font-medium">
              Mean Reciprocal Rank
            </div>
            <div className="text-lg font-bold text-indigo-600 dark:text-indigo-400 font-mono mt-0.5">
              {metrics.mrr.toFixed(2)}
            </div>
            <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
              Rank of 1st relevant memory
            </div>
          </div>

          {/* 3. Stale Fact Rate */}
          <div className="p-3 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
            <div className="text-[10px] text-slate-400 uppercase font-medium">
              Stale Facts Retrieved
            </div>
            <div className={`text-lg font-bold font-mono mt-0.5 ${
              metrics.stale_count === 0 ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600"
            }`}>
              {metrics.stale_count}/{metrics.stale_total}
            </div>
            <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
              After user correction (S2)
            </div>
          </div>

          {/* 4. Tool Success Rate */}
          <div className="p-3 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
            <div className="text-[10px] text-slate-400 uppercase font-medium">
              Tool Success Rate
            </div>
            <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
              {Math.round(metrics.tool_call_success_rate * 100)}%
            </div>
            <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
              Zero execution exceptions
            </div>
          </div>

          {/* 5. Tool Selection Accuracy */}
          <div className="p-3 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 col-span-2 sm:col-span-1">
            <div className="text-[10px] text-slate-400 uppercase font-medium">
              Tool Selection Acc
            </div>
            <div className="text-lg font-bold text-sky-600 dark:text-sky-400 font-mono mt-0.5">
              {Math.round(metrics.tool_selection_accuracy * 100)}%
            </div>
            <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
              Correct tool selected
            </div>
          </div>
        </div>
      )}

      {/* Turn-by-Turn Results Table */}
      {evalData?.rows && evalData.rows.length > 0 && (
        <div className="rounded-xl bg-white dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="p-3.5 border-b border-slate-200 dark:border-slate-700 font-semibold text-xs text-slate-800 dark:text-slate-200 flex items-center justify-between">
            <span>Per-Turn Verification Log ({evalData.rows.length} turns)</span>
            <span className="font-mono text-[10px] text-slate-400">Notebook parity</span>
          </div>

          <div className="overflow-x-auto max-h-80">
            <table className="w-full text-left border-collapse text-[11px]">
              <thead className="bg-slate-50 dark:bg-slate-900/80 text-slate-500 dark:text-slate-400 font-mono sticky top-0 border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="p-2">Scen/Sess</th>
                  <th className="p-2">User Prompt</th>
                  <th className="p-2">Tools Used</th>
                  <th className="p-2 text-center">Hit</th>
                  <th className="p-2 text-center">RR</th>
                  <th className="p-2 text-center">Stale?</th>
                  <th className="p-2 text-center">Tool Sel?</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {evalData.rows.map((r, i) => (
                  <tr
                    key={i}
                    className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                  >
                    <td className="p-2 font-mono text-[10px] text-slate-600 dark:text-slate-400 whitespace-nowrap">
                      {r.scenario.slice(0, 2)} / {r.session}
                    </td>
                    <td className="p-2 text-slate-800 dark:text-slate-200 max-w-[200px] truncate" title={r.user}>
                      {r.user}
                    </td>
                    <td className="p-2 font-mono text-[10px] text-slate-500 dark:text-slate-400">
                      {r.tools_used.length > 0 ? r.tools_used.join(", ") : "-"}
                    </td>
                    <td className="p-2 text-center font-mono">
                      {r.retrieval_hit === null ? (
                        "-"
                      ) : r.retrieval_hit ? (
                        <span className="text-emerald-600 font-bold">✓</span>
                      ) : (
                        <span className="text-rose-500 font-bold">✗</span>
                      )}
                    </td>
                    <td className="p-2 text-center font-mono text-slate-600 dark:text-slate-300">
                      {r.rr ? r.rr.toFixed(2) : "-"}
                    </td>
                    <td className="p-2 text-center font-mono">
                      {r.stale_retrieved === null ? (
                        "-"
                      ) : r.stale_retrieved ? (
                        <span className="text-rose-500 font-bold">YES</span>
                      ) : (
                        <span className="text-emerald-600 font-bold">NO</span>
                      )}
                    </td>
                    <td className="p-2 text-center font-mono">
                      {r.tool_selected === null ? (
                        "-"
                      ) : r.tool_selected ? (
                        <span className="text-emerald-600 font-bold">✓</span>
                      ) : (
                        <span className="text-rose-500 font-bold">✗</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
