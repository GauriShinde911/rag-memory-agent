import React, { useState, useRef, useEffect } from "react";
import type { ChatMessage } from "../../types";
import { ExplainabilityChips } from "./ExplainabilityChips";

interface ChatContainerProps {
  messages: ChatMessage[];
  loading: boolean;
  onSendMessage: (text: string) => void;
  onSelectPrompt: (text: string) => void;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  loading,
  onSendMessage,
  onSelectPrompt,
}) => {
  const [inputText, setInputText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;
    onSendMessage(inputText.trim());
    setInputText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const samplePrompts = [
    "I'm writing a paper on transformer-based time-series forecasting. Due 15 October.",
    "My cloud GPU budget is $50 per month.",
    "Correction: my GPU budget was raised to $80 per month, not $50.",
    "There are 16 days left and I read 4 papers a day. How many in total?",
    "Search the web for what FAISS is and save a one-line summary to your memory.",
    "Use Python to compute how many months a $400 GPU purchase lasts with an $80/mo budget.",
  ];

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 max-w-lg mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-2xl font-bold mb-4 border border-indigo-500/20">
              Ω
            </div>
            <h2 className="text-base font-semibold text-slate-800 dark:text-slate-200 mb-1">
              Personal Research Assistant
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
              Ask questions, teach facts across sessions, calculate formulas, or run Python code.
            </p>

            <div className="w-full space-y-2 text-left">
              <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider px-1">
                Suggested Prompts
              </div>
              <div className="grid grid-cols-1 gap-2">
                {samplePrompts.slice(0, 4).map((p, i) => (
                  <button
                    key={i}
                    onClick={() => onSelectPrompt(p)}
                    className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 hover:bg-indigo-50/70 dark:hover:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80 text-left text-xs text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-300 transition-all hover:border-indigo-300 dark:hover:border-indigo-700"
                  >
                    "{p}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "assistant" && (
                <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white text-xs font-bold shrink-0 mt-0.5 shadow-sm">
                  Ω
                </div>
              )}

              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 text-xs sm:text-sm leading-relaxed shadow-sm ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white rounded-tr-none"
                    : msg.isError
                    ? "bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-200 border border-rose-200 dark:border-rose-800 rounded-tl-none"
                    : "bg-slate-100 dark:bg-slate-800/90 text-slate-800 dark:text-slate-200 border border-slate-200/60 dark:border-slate-700/70 rounded-tl-none"
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {msg.role === "assistant" && (
                  <ExplainabilityChips
                    retrieved={msg.retrieved}
                    toolCalls={msg.tool_calls}
                    memoryOps={msg.memory_ops}
                    skippedOps={msg.skipped_ops}
                  />
                )}
              </div>
            </div>
          ))
        )}

        {loading && (
          <div className="flex gap-3 justify-start items-center">
            <div className="w-7 h-7 rounded-lg bg-indigo-600/70 flex items-center justify-center text-white text-xs font-bold shrink-0 animate-pulse">
              Ω
            </div>
            <div className="p-3.5 rounded-2xl rounded-tl-none bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" />
              <span
                className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce"
                style={{ animationDelay: "0.15s" }}
              />
              <span
                className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce"
                style={{ animationDelay: "0.3s" }}
              />
              <span className="text-xs text-slate-500 dark:text-slate-400 font-mono ml-1">
                Reasoning & retrieving...
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90">
        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Enter to send, Shift+Enter for newline)"
            className="flex-1 p-2.5 max-h-32 text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 border border-slate-300 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none transition-all"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !inputText.trim()}
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-md transition-colors flex items-center justify-center shrink-0"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
};
