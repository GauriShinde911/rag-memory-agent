import React, { useState } from "react";
import type { RetrievedMemory, ToolCallRecord, MemoryOpRecord } from "../../types";

interface ExplainabilityChipsProps {
  retrieved?: RetrievedMemory[];
  toolCalls?: ToolCallRecord[];
  memoryOps?: MemoryOpRecord[];
  skippedOps?: any[];
}

export const ExplainabilityChips: React.FC<ExplainabilityChipsProps> = ({
  retrieved = [],
  toolCalls = [],
  memoryOps = [],
  skippedOps = [],
}) => {
  const [activeAccordion, setActiveAccordion] = useState<"retrieved" | "tools" | "memory" | null>(null);

  const toggleAccordion = (type: "retrieved" | "tools" | "memory") => {
    setActiveAccordion((prev) => (prev === type ? null : type));
  };

  const hasRetrieved = retrieved.length > 0;
  const hasTools = toolCalls.length > 0;
  const hasOps = memoryOps.length > 0 || skippedOps.length > 0;

  if (!hasRetrieved && !hasTools && !hasOps) {
    return null;
  }

  return (
    <div className="mt-3 pt-2.5 border-t border-slate-200/70 dark:border-slate-800/80 text-xs">
      {/* Chip buttons row */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Retrieved Memories Chip */}
        {hasRetrieved && (
          <button
            onClick={() => toggleAccordion("retrieved")}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium border transition-colors ${
              activeAccordion === "retrieved"
                ? "bg-amber-100 dark:bg-amber-950/70 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-700"
                : "bg-slate-100 dark:bg-slate-800/70 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200/60 dark:hover:bg-slate-700/60"
            }`}
          >
            <span>🔍 Retrieved</span>
            <span className="px-1 py-0.2 rounded-full text-[10px] bg-amber-500/20 text-amber-700 dark:text-amber-300 font-mono">
              {retrieved.length}
            </span>
          </button>
        )}

        {/* Tools Executed Chip */}
        {hasTools && (
          <button
            onClick={() => toggleAccordion("tools")}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium border transition-colors ${
              activeAccordion === "tools"
                ? "bg-sky-100 dark:bg-sky-950/70 text-sky-800 dark:text-sky-300 border-sky-300 dark:border-sky-700"
                : "bg-slate-100 dark:bg-slate-800/70 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200/60 dark:hover:bg-slate-700/60"
            }`}
          >
            <span>🛠️ Tools</span>
            <span className="font-mono text-[10px] text-sky-600 dark:text-sky-400">
              {toolCalls.map((t) => (t.success ? "✓" : "✗")).join("")}
            </span>
          </button>
        )}

        {/* Memory Ops Chip */}
        {hasOps && (
          <button
            onClick={() => toggleAccordion("memory")}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium border transition-colors ${
              activeAccordion === "memory"
                ? "bg-emerald-100 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700"
                : "bg-slate-100 dark:bg-slate-800/70 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200/60 dark:hover:bg-slate-700/60"
            }`}
          >
            <span>🧠 Memory</span>
            <div className="flex items-center gap-1">
              {memoryOps.map((op, idx) => {
                if (op.op === "add")
                  return (
                    <span
                      key={idx}
                      className="px-1 py-0.2 rounded text-[10px] bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 font-mono"
                    >
                      +add
                    </span>
                  );
                if (op.op === "update")
                  return (
                    <span
                      key={idx}
                      className="px-1 py-0.2 rounded text-[10px] bg-amber-500/20 text-amber-700 dark:text-amber-300 font-mono"
                    >
                      ↺upd
                    </span>
                  );
                if (op.op === "delete")
                  return (
                    <span
                      key={idx}
                      className="px-1 py-0.2 rounded text-[10px] bg-rose-500/20 text-rose-700 dark:text-rose-300 font-mono"
                    >
                      ✕del
                    </span>
                  );
                return null;
              })}
              {skippedOps.length > 0 && (
                <span className="px-1 py-0.2 rounded text-[10px] bg-slate-300 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-mono">
                  {skippedOps.length} skipped
                </span>
              )}
            </div>
          </button>
        )}
      </div>

      {/* Accordion contents */}
      {activeAccordion === "retrieved" && (
        <div className="mt-2.5 p-3 rounded-lg bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200/70 dark:border-amber-800/50 space-y-2">
          <div className="text-[11px] font-semibold text-amber-900 dark:text-amber-300">
            Retrieved from Chroma Vector DB (Cosine Distance, 0 = Identical):
          </div>
          <div className="space-y-1.5">
            {retrieved.map((m, idx) => (
              <div
                key={idx}
                className="p-2 rounded bg-white/80 dark:bg-slate-900/80 border border-amber-200/50 dark:border-amber-800/40 text-[11px]"
              >
                <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 font-mono text-[10px] mb-1">
                  <span>ID: {m.id || "n/a"}</span>
                  <span className="font-semibold text-amber-700 dark:text-amber-400">
                    dist: {m.distance.toFixed(4)}
                  </span>
                </div>
                <div className="text-slate-800 dark:text-slate-200 font-sans">
                  {m.text}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeAccordion === "tools" && (
        <div className="mt-2.5 p-3 rounded-lg bg-sky-50/70 dark:bg-sky-950/30 border border-sky-200/70 dark:border-sky-800/50 space-y-2">
          <div className="text-[11px] font-semibold text-sky-900 dark:text-sky-300">
            Tools Executed via LangGraph ReAct Loop:
          </div>
          <div className="space-y-1.5">
            {toolCalls.map((t, idx) => (
              <div
                key={idx}
                className="p-2 rounded bg-white/80 dark:bg-slate-900/80 border border-sky-200/50 dark:border-sky-800/40 text-[11px] space-y-1"
              >
                <div className="flex items-center justify-between font-mono text-[10px]">
                  <span className="font-semibold text-sky-700 dark:text-sky-400 flex items-center gap-1.5">
                    {t.success ? (
                      <span className="text-emerald-500">✓</span>
                    ) : (
                      <span className="text-rose-500">✗</span>
                    )}
                    {t.tool}
                  </span>
                  <span className="text-slate-400">{t.latency_s}s</span>
                </div>
                <div className="text-slate-600 dark:text-slate-400 font-mono text-[10px] truncate">
                  Args: {JSON.stringify(t.args)}
                </div>
                {t.output && (
                  <div className="text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-slate-950 p-1.5 rounded font-mono text-[10px] break-all">
                    Output: {t.output}
                  </div>
                )}
                {t.error && (
                  <div className="text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 p-1.5 rounded font-mono text-[10px]">
                    Error: {t.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeAccordion === "memory" && (
        <div className="mt-2.5 p-3 rounded-lg bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200/70 dark:border-emerald-800/50 space-y-2">
          <div className="text-[11px] font-semibold text-emerald-900 dark:text-emerald-300">
            Memory Feedback Loop Mutations (LLM JSON Extraction):
          </div>
          <div className="space-y-1.5">
            {memoryOps.map((op, idx) => (
              <div
                key={idx}
                className="p-2 rounded bg-white/80 dark:bg-slate-900/80 border border-emerald-200/50 dark:border-emerald-800/40 text-[11px] space-y-1"
              >
                <div className="flex items-center justify-between font-mono text-[10px]">
                  <span
                    className={`font-semibold uppercase ${
                      op.op === "add"
                        ? "text-emerald-600 dark:text-emerald-400"
                        : op.op === "update"
                        ? "text-amber-600 dark:text-amber-400"
                        : "text-rose-600 dark:text-rose-400"
                    }`}
                  >
                    [{op.op}] {op.id ? `ID: ${op.id}` : ""}
                  </span>
                </div>
                {op.text && (
                  <div className="text-slate-800 dark:text-slate-200 font-sans">
                    {op.text}
                  </div>
                )}
              </div>
            ))}
            {skippedOps.map((sk, idx) => (
              <div
                key={`sk-${idx}`}
                className="p-2 rounded bg-amber-50 dark:bg-amber-950/30 border border-amber-300/40 text-[10px] text-amber-800 dark:text-amber-300 space-y-0.5"
              >
                <div className="font-semibold font-mono">⚠️ Skipped Operation:</div>
                <div>{sk.reason || JSON.stringify(sk)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
