import React, { useState } from "react";
import type { MemoryItem } from "../../types";

interface MemoryTabProps {
  memories: MemoryItem[];
  loading: boolean;
  onRefresh: () => void;
  onUpdate: (id: string, text: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  lastChangedIds?: string[];
}

export const MemoryTab: React.FC<MemoryTabProps> = ({
  memories,
  loading,
  onRefresh,
  onUpdate,
  onDelete,
  lastChangedIds = [],
}) => {
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const filtered = memories.filter(
    (m) =>
      m.text.toLowerCase().includes(search.toLowerCase()) ||
      m.id.toLowerCase().includes(search.toLowerCase()) ||
      m.session_id.toLowerCase().includes(search.toLowerCase())
  );

  const startEdit = (item: MemoryItem) => {
    setEditingId(item.id);
    setEditText(item.text);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditText("");
  };

  const handleSaveEdit = async (id: string) => {
    if (!editText.trim()) return;
    setActionLoading(true);
    try {
      await onUpdate(id, editText.trim());
      setEditingId(null);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this memory fact?")) return;
    setActionLoading(true);
    try {
      await onDelete(id);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50/50 dark:bg-slate-900/50">
      {/* Search & Actions Bar */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 flex gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search vector memory..."
          className="flex-1 px-3 py-1.5 text-xs bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500 text-slate-800 dark:text-slate-200"
        />
        <button
          onClick={onRefresh}
          disabled={loading}
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
          title="Refresh memory facts"
        >
          {loading ? "..." : "🔄"}
        </button>
      </div>

      {/* Memory facts count */}
      <div className="px-4 py-2 text-[11px] font-medium text-slate-500 dark:text-slate-400 flex items-center justify-between">
        <span>{filtered.length} stored facts (Chroma)</span>
        {lastChangedIds.length > 0 && (
          <span className="text-emerald-600 dark:text-emerald-400 font-mono">
            {lastChangedIds.length} modified this turn
          </span>
        )}
      </div>

      {/* Memory List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filtered.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">
            No memories found. Converse with the agent to store durable facts.
          </div>
        ) : (
          filtered.map((item) => {
            const isHighlighted = lastChangedIds.includes(item.id);
            const isEditing = editingId === item.id;

            return (
              <div
                key={item.id}
                className={`p-3.5 rounded-xl border text-xs transition-all ${
                  isHighlighted
                    ? "bg-emerald-50/80 dark:bg-emerald-950/40 border-emerald-400/80 dark:border-emerald-700 ring-2 ring-emerald-500/20"
                    : "bg-white dark:bg-slate-800/90 border-slate-200 dark:border-slate-700/80 hover:border-slate-300 dark:hover:border-slate-600"
                }`}
              >
                {/* Header tags */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5 font-mono text-[10px]">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">
                      [{item.id}]
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-bold border border-indigo-200 dark:border-indigo-800">
                      v{item.version}
                    </span>
                    <span className="text-slate-400">sess: {item.session_id}</span>
                  </div>

                  <div className="flex items-center gap-1">
                    {!isEditing && (
                      <>
                        <button
                          onClick={() => startEdit(item)}
                          disabled={actionLoading}
                          className="px-2 py-0.5 text-[10px] text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(item.id)}
                          disabled={actionLoading}
                          className="px-2 py-0.5 text-[10px] text-slate-500 hover:text-rose-600 dark:hover:text-rose-400 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* Content or Edit Form */}
                {isEditing ? (
                  <div className="space-y-2 mt-1">
                    <textarea
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      rows={2}
                      className="w-full p-2 text-xs bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 border border-slate-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                    <div className="flex justify-end gap-1.5">
                      <button
                        onClick={cancelEdit}
                        disabled={actionLoading}
                        className="px-2.5 py-1 text-[11px] text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-md"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleSaveEdit(item.id)}
                        disabled={actionLoading}
                        className="px-2.5 py-1 text-[11px] bg-indigo-600 hover:bg-indigo-700 text-white rounded-md font-medium"
                      >
                        {actionLoading ? "Saving..." : "Save (v+1)"}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-slate-800 dark:text-slate-200 font-sans leading-relaxed">
                    {item.text}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
