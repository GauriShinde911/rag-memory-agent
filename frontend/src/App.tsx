import React, { useState, useEffect, useCallback } from "react";
import type {
  HealthStatus,
  ChatMessage,
  MemoryItem,
  LiveMetrics,
} from "./types";
import {
  fetchHealth,
  createSession,
  sendChatMessage,
  fetchMemories,
  updateMemoryFact,
  deleteMemoryFact,
  fetchLiveMetrics,
} from "./api/client";
import { Header } from "./components/Header";
import { Toast } from "./components/Toast";
import { ChatContainer } from "./components/chat/ChatContainer";
import { MemoryTab } from "./components/panels/MemoryTab";
import { ToolsTab } from "./components/panels/ToolsTab";
import { EvalTab } from "./components/panels/EvalTab";

export const App: React.FC = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [sessionId, setSessionId] = useState<string>("init_session");
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Active right-side tab
  const [activeTab, setActiveTab] = useState<"memory" | "tools" | "eval">("memory");

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  // Memory & Tools state
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [lastChangedIds, setLastChangedIds] = useState<string[]>([]);
  const [toolMetrics, setToolMetrics] = useState<LiveMetrics | null>(null);
  const [toolsLoading, setToolsLoading] = useState(false);

  // Dark mode effect
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  // Load Health, initial session, and data
  const loadInitialData = useCallback(async () => {
    try {
      const h = await fetchHealth();
      setHealth(h);
    } catch (e) {
      console.error("Health check error", e);
    }

    try {
      const sess = await createSession();
      setSessionId(sess.session_id);
    } catch (e) {
      console.error("Session creation error", e);
    }

    refreshMemories();
    refreshTools();
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Periodic health check
  useEffect(() => {
    const timer = setInterval(async () => {
      try {
        const h = await fetchHealth();
        setHealth(h);
      } catch (e) {
        // silent fail
      }
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const refreshMemories = async () => {
    setMemoryLoading(true);
    try {
      const data = await fetchMemories();
      setMemories(data.memories);
    } catch (e) {
      console.error("Failed to load memories", e);
    } finally {
      setMemoryLoading(false);
    }
  };

  const refreshTools = async () => {
    setToolsLoading(true);
    try {
      const m = await fetchLiveMetrics();
      setToolMetrics(m);
    } catch (e) {
      console.error("Failed to load tool metrics", e);
    } finally {
      setToolsLoading(false);
    }
  };

  // Handler: Start New Session
  const handleNewSession = async () => {
    try {
      const sess = await createSession();
      setSessionId(sess.session_id);
      setMessages([]);
      setLastChangedIds([]);
      setToastMessage("Short-term memory cleared, long-term memory kept.");
      refreshMemories();
    } catch (err: any) {
      setToastMessage(`Failed to reset session: ${err.message}`);
    }
  };

  // Handler: Send Message
  const handleSendMessage = async (text: string) => {
    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setChatLoading(true);

    try {
      const res = await sendChatMessage(sessionId, text);
      const aiMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: res.reply,
        retrieved: res.retrieved,
        tool_calls: res.tool_calls,
        memory_ops: res.memory_ops,
        skipped_ops: res.skipped_ops,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, aiMsg]);

      // Highlight modified memory IDs
      if (res.memory_ops && res.memory_ops.length > 0) {
        const changed = res.memory_ops
          .map((op: any) => op.id)
          .filter(Boolean);
        setLastChangedIds(changed);
      }

      // Refresh memory list and tools telemetry
      refreshMemories();
      refreshTools();
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: `Error: ${err.message || "Failed to communicate with assistant."}`,
        isError: true,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setChatLoading(false);
    }
  };

  // Handler: Manual Memory Updates
  const handleUpdateMemory = async (id: string, text: string) => {
    await updateMemoryFact(id, text);
    refreshMemories();
    setToastMessage(`Memory [${id}] updated to next version.`);
  };

  const handleDeleteMemory = async (id: string) => {
    await deleteMemoryFact(id);
    refreshMemories();
    setToastMessage(`Memory [${id}] removed from vector store.`);
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-100 dark:bg-slate-950 font-sans">
      <Header
        sessionId={sessionId}
        health={health}
        onNewSession={handleNewSession}
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode((prev) => !prev)}
      />

      {/* Main split view */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Left Column: Chat Area */}
        <div className="w-full md:w-[58%] lg:w-[60%] h-full flex flex-col">
          <ChatContainer
            messages={messages}
            loading={chatLoading}
            onSendMessage={handleSendMessage}
            onSelectPrompt={handleSendMessage}
          />
        </div>

        {/* Right Column: Tabbed Inspector */}
        <div className="w-full md:w-[42%] lg:w-[40%] h-full flex flex-col bg-white dark:bg-slate-900 border-t md:border-t-0 md:border-l border-slate-200 dark:border-slate-800">
          {/* Tab Navigation */}
          <div className="flex border-b border-slate-200 dark:border-slate-800 px-4 pt-3 bg-slate-50/70 dark:bg-slate-900/70">
            <button
              onClick={() => setActiveTab("memory")}
              className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === "memory"
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                  : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <span>🧠 Memory</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-200 dark:bg-slate-800 font-mono">
                {memories.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab("tools")}
              className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === "tools"
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                  : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <span>🛠️ Tools</span>
              {toolMetrics && toolMetrics.total_calls > 0 && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 font-mono">
                  {Math.round(toolMetrics.success_rate * 100)}%
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("eval")}
              className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === "eval"
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                  : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <span>📊 Evaluation</span>
              <span className="text-[9px] uppercase px-1 rounded bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 font-mono">
                3 Scen
              </span>
            </button>
          </div>

          {/* Active Tab Panel */}
          <div className="flex-1 overflow-hidden">
            {activeTab === "memory" && (
              <MemoryTab
                memories={memories}
                loading={memoryLoading}
                onRefresh={refreshMemories}
                onUpdate={handleUpdateMemory}
                onDelete={handleDeleteMemory}
                lastChangedIds={lastChangedIds}
              />
            )}
            {activeTab === "tools" && (
              <ToolsTab
                metrics={toolMetrics}
                loading={toolsLoading}
                onRefresh={refreshTools}
              />
            )}
            {activeTab === "eval" && <EvalTab />}
          </div>
        </div>
      </div>

      {/* Toast Notification */}
      <Toast message={toastMessage} onClose={() => setToastMessage(null)} />
    </div>
  );
};

export default App;
