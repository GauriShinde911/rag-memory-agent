export interface HealthStatus {
  status: string;
  embeddings: "loading" | "ready" | "error" | string;
  llm: "configured" | "missing_key" | string;
  provider: string;
  model: string;
}

export interface RetrievedMemory {
  id: string | null;
  text: string;
  distance: number;
  metadata?: {
    version?: number;
    session_id?: string;
    created_at?: string;
  };
}

export interface ToolCallRecord {
  tool: string;
  args: Record<string, any> | any[] | string;
  success: boolean;
  output?: string | null;
  error?: string | null;
  latency_s: number;
}

export interface MemoryOpRecord {
  op: "add" | "update" | "delete" | string;
  id?: string | null;
  text?: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  retrieved?: RetrievedMemory[];
  tool_calls?: ToolCallRecord[];
  memory_ops?: MemoryOpRecord[];
  skipped_ops?: any[];
  timestamp: string;
  isError?: boolean;
}

export interface MemoryItem {
  id: string;
  text: string;
  version: number;
  session_id: string;
  created_at: string;
  updated_at?: string | null;
}

export interface LiveMetrics {
  total_calls: number;
  successful_calls: number;
  success_rate: number;
  by_tool: Record<string, { calls: number; success: number }>;
  recent_calls: ToolCallRecord[];
}

export interface EvalMetricSummary {
  metric: string;
  value: string;
  score: number;
}

export interface EvalTurnRow {
  scenario: string;
  session: string;
  user: string;
  reply: string;
  n_tool_calls: number;
  tool_ok: number;
  tools_used: string[];
  retrieved: string[];
  memory_ops: any[];
  retrieval_hit: boolean | null;
  rr: number;
  stale_retrieved: boolean | null;
  tool_selected: boolean | null;
}

export interface EvalMetrics {
  hit_at_4: number;
  mrr: number;
  stale_fact_rate: number;
  stale_count: number;
  stale_total: number;
  tool_call_success_rate: number;
  tool_selection_accuracy: number;
  summary_table: EvalMetricSummary[];
}

export interface EvalStatus {
  run_id: string;
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  current_step?: string | null;
  metrics?: EvalMetrics | null;
  summary_table?: EvalMetricSummary[] | null;
  rows?: EvalTurnRow[] | null;
  error?: string | null;
}
