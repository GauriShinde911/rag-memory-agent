from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    embeddings: str = "ready"  # "loading" | "ready" | "error"
    llm: str = "configured"    # "configured" | "missing_key"
    provider: str
    model: str


class CreateSessionRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Optional custom session identifier")


class CreateSessionResponse(BaseModel):
    session_id: str
    message: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class RetrievedMemory(BaseModel):
    id: Optional[str] = None
    text: str
    distance: float
    metadata: Dict[str, Any] = {}


class ToolCallRecord(BaseModel):
    tool: str
    args: Union[Dict[str, Any], List[Any], str] = {}
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    latency_s: float


class MemoryOpRecord(BaseModel):
    op: str
    id: Optional[str] = None
    text: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    retrieved: List[RetrievedMemory]
    tool_calls: List[ToolCallRecord]
    memory_ops: List[MemoryOpRecord]
    skipped_ops: List[Dict[str, Any]] = []


class MemoryItem(BaseModel):
    id: str
    text: str
    version: int
    session_id: str
    created_at: str
    updated_at: Optional[str] = None


class MemoryListResponse(BaseModel):
    memories: List[MemoryItem]
    total: int


class UpdateMemoryRequest(BaseModel):
    text: str


class LiveMetricsResponse(BaseModel):
    total_calls: int
    successful_calls: int
    success_rate: float
    by_tool: Dict[str, Any]
    recent_calls: List[Dict[str, Any]]


class EvalRunResponse(BaseModel):
    run_id: str
    status: str
    message: str


class EvalStatusResponse(BaseModel):
    run_id: str
    status: str  # "queued", "running", "completed", "failed"
    progress: float
    current_step: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    summary_table: Optional[List[Dict[str, Any]]] = None
    rows: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
