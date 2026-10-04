import re
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from app.config import settings, PROJECT_ROOT
from app.memory.long_term import LongTermMemory
from app.agent.assistant import Assistant
from app.eval.scenarios import SCENARIOS

logger = logging.getLogger(__name__)


def compute_metrics(
    rows: List[Dict[str, Any]],
    all_tool_calls: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compute the 5 notebook evaluation metrics from row records and tool calls."""
    # 1. Retrieval accuracy (Hit@4)
    probe_rows = [r for r in rows if r.get("retrieval_hit") is not None]
    if probe_rows:
        hits = sum(1 for r in probe_rows if r["retrieval_hit"])
        hit_at_4 = round(hits / len(probe_rows), 4)
        mrr = round(sum(r.get("rr", 0.0) for r in probe_rows) / len(probe_rows), 4)
    else:
        hits = 0
        hit_at_4 = 0.0
        mrr = 0.0

    # 2. Stale facts retrieved
    stale_rows = [r for r in rows if r.get("stale_retrieved") is not None]
    if stale_rows:
        stale_count = sum(1 for r in stale_rows if r["stale_retrieved"])
        stale_total = len(stale_rows)
        stale_rate = round(stale_count / stale_total, 4)
    else:
        stale_count = 0
        stale_total = 0
        stale_rate = 0.0

    # 3. Tool call success rate
    if all_tool_calls is not None:
        tool_total = len(all_tool_calls)
        tool_ok = sum(1 for c in all_tool_calls if c.get("success", False))
    else:
        tool_total = sum(r.get("n_tool_calls", 0) for r in rows)
        tool_ok = sum(r.get("tool_ok", 0) for r in rows)
    tool_success_rate = round(tool_ok / tool_total, 4) if tool_total > 0 else 1.0

    # 4. Tool selection accuracy
    tool_sel_rows = [r for r in rows if r.get("tool_selected") is not None]
    if tool_sel_rows:
        sel_hits = sum(1 for r in tool_sel_rows if r["tool_selected"])
        tool_selection_acc = round(sel_hits / len(tool_sel_rows), 4)
        sel_total = len(tool_sel_rows)
    else:
        sel_hits = 0
        sel_total = 0
        tool_selection_acc = 0.0

    summary_table = [
        {
            "metric": "Retrieval accuracy (Hit@4, all expected facts retrieved)",
            "value": f"{hit_at_4:.0%} ({hits}/{len(probe_rows)})" if probe_rows else "n/a",
            "score": hit_at_4,
        },
        {
            "metric": "Mean Reciprocal Rank of first relevant memory",
            "value": f"{mrr:.2f}",
            "score": mrr,
        },
        {
            "metric": "Stale facts retrieved after correction",
            "value": f"{stale_count}/{stale_total}" if stale_total > 0 else "n/a",
            "score": stale_rate,
        },
        {
            "metric": "Tool-call success rate (no exception)",
            "value": f"{tool_success_rate:.0%} ({tool_ok}/{tool_total})" if tool_total > 0 else "n/a",
            "score": tool_success_rate,
        },
        {
            "metric": "Correct tool selected when required",
            "value": f"{tool_selection_acc:.0%} ({sel_hits}/{sel_total})" if sel_total > 0 else "n/a",
            "score": tool_selection_acc,
        },
    ]

    return {
        "hit_at_4": hit_at_4,
        "mrr": mrr,
        "stale_fact_rate": stale_rate,
        "stale_count": stale_count,
        "stale_total": stale_total,
        "tool_call_success_rate": tool_success_rate,
        "tool_selection_accuracy": tool_selection_acc,
        "summary_table": summary_table,
    }


def run_evaluation(
    scenarios: Optional[List[Dict[str, Any]]] = None,
    k: int = 4,
    pause_seconds: Optional[float] = None,
    agent_factory: Optional[Callable[[LongTermMemory, str], Assistant]] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    export_files: bool = True,
) -> Dict[str, Any]:
    """Execute multi-session evaluation scenarios and compute metrics."""
    scenarios = scenarios or SCENARIOS
    pause = (
        pause_seconds
        if pause_seconds is not None
        else settings.eval_pause_seconds
    )

    total_turns = sum(
        len(sess.get("turns", []))
        for sc in scenarios
        for sess in sc.get("sessions", [])
    )
    current_turn_idx = 0

    rows: List[Dict[str, Any]] = []
    transcript: List[Dict[str, Any]] = []
    all_tool_calls: List[Dict[str, Any]] = []

    for sc_idx, sc in enumerate(scenarios):
        sc_name = sc["name"]
        # Isolated Chroma collection per scenario, clean reset at start
        coll_name = "eval_" + re.sub(r"\W+", "_", sc_name).lower().strip("_")

        logger.info(f"Starting Scenario '{sc_name}' on collection '{coll_name}'")
        # Clean start for this scenario
        LongTermMemory(collection=coll_name, reset=True)

        for sess in sc["sessions"]:
            sess_id = sess["id"]
            # Re-open collection from disk = new session, fresh STM buffer
            ltm = LongTermMemory(collection=coll_name, reset=False)

            if agent_factory:
                bot = agent_factory(ltm, sess_id)
            else:
                bot = Assistant(ltm, session_id=sess_id, k=k)

            for turn in sess["turns"]:
                user_msg = turn["user"]
                current_turn_idx += 1
                if progress_callback and total_turns > 0:
                    progress_callback(
                        round(current_turn_idx / total_turns, 2),
                        f"[{sc_name}] Session {sess_id}: {user_msg[:30]}...",
                    )

                res = bot.ask(user_msg)
                turn_tools = res["tool_calls"]
                all_tool_calls.extend(turn_tools)

                docs = [m["text"].lower() for m in res["retrieved"]]
                joined_docs = " || ".join(docs)

                row: Dict[str, Any] = {
                    "scenario": sc_name,
                    "session": sess_id,
                    "user": user_msg,
                    "reply": res["reply"],
                    "n_tool_calls": len(turn_tools),
                    "tool_ok": sum(1 for c in turn_tools if c.get("success", False)),
                    "tools_used": [c.get("tool", "") for c in turn_tools],
                    "retrieved": [m["text"] for m in res["retrieved"]],
                    "memory_ops": res["memory_ops"],
                    "retrieval_hit": None,
                    "rr": 0.0,
                    "stale_retrieved": None,
                    "tool_selected": None,
                }

                # Metric 1: Retrieval probe check
                if "expect_memory" in turn:
                    expected = [e.lower() for e in turn["expect_memory"]]
                    row["retrieval_hit"] = all(e in joined_docs for e in expected)
                    ranks = [
                        i + 1
                        for i, d in enumerate(docs)
                        if any(e in d for e in expected)
                    ]
                    row["rr"] = round(1.0 / ranks[0], 4) if ranks else 0.0

                # Metric 2: Stale fact check after correction
                if "forbid_memory" in turn:
                    forbidden = [f.lower() for f in turn["forbid_memory"]]
                    row["stale_retrieved"] = any(f in joined_docs for f in forbidden)

                # Metric 3: Tool selection check
                if "expect_tool" in turn:
                    exp_tool = turn["expect_tool"]
                    row["tool_selected"] = exp_tool in row["tools_used"]

                rows.append(row)
                transcript.append(dict(row))

                if pause > 0:
                    time.sleep(pause)

    # Compute final metrics
    metrics = compute_metrics(rows, all_tool_calls)

    result_payload = {
        "metrics": metrics,
        "rows": rows,
        "transcript": transcript,
        "tool_log": all_tool_calls,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    if export_files:
        try:
            log_path = PROJECT_ROOT / "test_log.json"
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(result_payload, f, indent=2)
            logger.info(f"Saved evaluation results to {log_path}")
        except Exception as e:
            logger.error(f"Failed to export test_log.json: {e}")

    return result_payload
