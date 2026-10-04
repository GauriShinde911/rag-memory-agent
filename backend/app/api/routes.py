import os
import uuid
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse

from app.config import settings, PROJECT_ROOT
from app.memory.long_term import LongTermMemory, get_embeddings_status
from app.agent.assistant import Assistant
from app.tools.logger import global_tool_store
from app.eval.runner import run_evaluation
from app.api.schemas import (
    HealthResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    ChatRequest,
    ChatResponse,
    MemoryListResponse,
    MemoryItem,
    UpdateMemoryRequest,
    LiveMetricsResponse,
    EvalRunResponse,
    EvalStatusResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# State holders for live sessions and eval runs
_live_ltm: Optional[LongTermMemory] = None
_sessions: Dict[str, Assistant] = {}
_eval_runs: Dict[str, Dict[str, Any]] = {}


def get_live_ltm() -> LongTermMemory:
    """Retrieve or initialize the primary persistent LTM for live chat."""
    global _live_ltm
    if _live_ltm is None:
        _live_ltm = LongTermMemory(
            collection=settings.collection_name,
            persist_dir=settings.persist_dir,
            reset=False,
        )
    return _live_ltm


def get_or_create_assistant(session_id: str) -> Assistant:
    """Get active session assistant or initialize a new one."""
    if session_id not in _sessions:
        ltm = get_live_ltm()
        _sessions[session_id] = Assistant(ltm=ltm, session_id=session_id)
        logger.info(f"Initialized new assistant session '{session_id}'")
    return _sessions[session_id]


# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
@router.get("/health", response_model=HealthResponse)
def health_check():
    """Report backend readiness, embedding status, and LLM configuration."""
    emb_status = get_embeddings_status()
    llm_configured = "configured" if settings.is_llm_configured() else "missing_key"
    return HealthResponse(
        status="ok",
        embeddings=emb_status,
        llm=llm_configured,
        provider=settings.llm_provider,
        model=settings.llm_model,
    )


# -----------------------------------------------------------------------------
# Sessions
# -----------------------------------------------------------------------------
@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(req: CreateSessionRequest):
    """Start a new session: clears short-term memory buffer while preserving long-term memory."""
    sess_id = req.session_id or f"live_{datetime.now().strftime('%H%M%S')}"

    if sess_id in _sessions:
        # Existing session: clear sliding-window buffer
        _sessions[sess_id].stm.clear()
        message = "Existing session reset: short-term memory cleared, long-term memory kept."
    else:
        # Brand new session
        _sessions[sess_id] = Assistant(ltm=get_live_ltm(), session_id=sess_id)
        message = "New session created: short-term memory fresh, long-term memory kept."

    logger.info(f"Session {sess_id}: {message}")
    return CreateSessionResponse(session_id=sess_id, message=message)


# -----------------------------------------------------------------------------
# Chat
# -----------------------------------------------------------------------------
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Run an interactive turn with retrieval, tool execution, and memory feedback."""
    bot = get_or_create_assistant(req.session_id)
    try:
        res = bot.ask(req.message)
        return ChatResponse(
            reply=res["reply"],
            retrieved=res["retrieved"],
            tool_calls=res["tool_calls"],
            memory_ops=res["memory_ops"],
            skipped_ops=res.get("skipped_ops", []),
        )
    except Exception as e:
        logger.error(f"Chat turn failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Turn execution failed: {str(e)}")


# -----------------------------------------------------------------------------
# Memory Management
# -----------------------------------------------------------------------------
@router.get("/memory", response_model=MemoryListResponse)
def list_memories(search: Optional[str] = Query(default=None)):
    """Retrieve all long-term memory facts stored in Chroma."""
    ltm = get_live_ltm()
    items = ltm.all()

    if search and search.strip():
        q = search.strip().lower()
        items = [i for i in items if q in i["text"].lower() or q in i["id"].lower()]

    # Sort descending by updated_at or created_at
    items.sort(key=lambda x: x.get("updated_at") or x.get("created_at") or "", reverse=True)
    return MemoryListResponse(memories=items, total=len(items))


@router.patch("/memory/{memory_id}")
def update_memory(memory_id: str, req: UpdateMemoryRequest):
    """Manually edit a memory fact from the UI (increments version)."""
    ltm = get_live_ltm()
    res_id = ltm.update(memory_id, req.text.strip())
    if not res_id:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")

    updated = ltm.get_by_id(res_id)
    return {"status": "updated", "memory": updated}


@router.delete("/memory/{memory_id}")
def delete_memory(memory_id: str):
    """Manually delete a memory fact from the UI."""
    ltm = get_live_ltm()
    res_id = ltm.delete(memory_id)
    if not res_id:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")
    return {"status": "deleted", "id": res_id}


# -----------------------------------------------------------------------------
# Tools Live Metrics
# -----------------------------------------------------------------------------
@router.get("/metrics/live", response_model=LiveMetricsResponse)
def get_live_metrics():
    """Retrieve cumulative tool execution metrics and success rate."""
    return global_tool_store.get_metrics()


# -----------------------------------------------------------------------------
# Evaluation Harness
# -----------------------------------------------------------------------------
def _execute_eval_background(run_id: str):
    """Worker function executing eval scenarios in a background thread."""
    def progress_callback(progress: float, step: str):
        if run_id in _eval_runs:
            _eval_runs[run_id]["progress"] = progress
            _eval_runs[run_id]["current_step"] = step

    try:
        _eval_runs[run_id]["status"] = "running"
        results = run_evaluation(progress_callback=progress_callback)
        _eval_runs[run_id].update({
            "status": "completed",
            "progress": 1.0,
            "current_step": "Complete",
            "metrics": results["metrics"],
            "summary_table": results["metrics"]["summary_table"],
            "rows": results["rows"],
            "completed_at": results["completed_at"],
        })
    except Exception as e:
        logger.error(f"Eval run {run_id} failed: {e}", exc_info=True)
        _eval_runs[run_id].update({
            "status": "failed",
            "error": str(e),
            "current_step": f"Error: {e}",
        })


@router.post("/eval/run", response_model=EvalRunResponse)
def start_evaluation():
    """Trigger execution of the 3 multi-session test scenarios in the background."""
    run_id = f"eval_{uuid.uuid4().hex[:8]}"
    _eval_runs[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "progress": 0.0,
        "current_step": "Queued",
        "metrics": None,
        "summary_table": None,
        "rows": None,
        "error": None,
    }

    thread = threading.Thread(target=_execute_eval_background, args=(run_id,), daemon=True)
    thread.start()

    return EvalRunResponse(
        run_id=run_id,
        status="queued",
        message="Evaluation started in background.",
    )


@router.get("/eval/{run_id}", response_model=EvalStatusResponse)
def get_eval_status(run_id: str):
    """Poll status and retrieve results of an evaluation run."""
    run_data = _eval_runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail=f"Eval run '{run_id}' not found")
    return EvalStatusResponse(**run_data)


# -----------------------------------------------------------------------------
# Export Log
# -----------------------------------------------------------------------------
@router.get("/export/log")
def export_log():
    """Download test_log.json produced by evaluation runs."""
    log_path = PROJECT_ROOT / "test_log.json"
    if not log_path.exists():
        raise HTTPException(
            status_code=404,
            detail="test_log.json not found. Run an evaluation scenario first.",
        )
    return FileResponse(
        path=str(log_path),
        filename="test_log.json",
        media_type="application/json",
    )
