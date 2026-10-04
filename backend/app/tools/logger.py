import functools
import time
import threading
from collections import deque
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional

# Request-scoped collector for per-turn tool execution trace
current_turn_tools: ContextVar[Optional[List[Dict[str, Any]]]] = ContextVar(
    "current_turn_tools", default=None
)


class GlobalToolStore:
    """Thread-safe store for aggregate live tool metrics across all requests."""

    def __init__(self, max_recent: int = 100):
        self._lock = threading.Lock()
        self.total_calls = 0
        self.successful_calls = 0
        self.by_tool: Dict[str, Dict[str, int]] = {}
        self.recent_calls = deque(maxlen=max_recent)

    def record(self, call_data: Dict[str, Any]) -> None:
        tool_name = call_data.get("tool", "unknown")
        success = bool(call_data.get("success", False))

        with self._lock:
            self.total_calls += 1
            if success:
                self.successful_calls += 1

            if tool_name not in self.by_tool:
                self.by_tool[tool_name] = {"calls": 0, "success": 0}
            self.by_tool[tool_name]["calls"] += 1
            if success:
                self.by_tool[tool_name]["success"] += 1

            self.recent_calls.append(call_data)

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            rate = (
                round(self.successful_calls / self.total_calls, 4)
                if self.total_calls > 0
                else 1.0
            )
            return {
                "total_calls": self.total_calls,
                "successful_calls": self.successful_calls,
                "success_rate": rate,
                "by_tool": {k: dict(v) for k, v in self.by_tool.items()},
                "recent_calls": list(self.recent_calls),
            }

    def clear(self) -> None:
        with self._lock:
            self.total_calls = 0
            self.successful_calls = 0
            self.by_tool.clear()
            self.recent_calls.clear()


global_tool_store = GlobalToolStore()


def logged(fn: Callable) -> Callable:
    """Decorator recording tool call arguments, success status, output and latency."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        rec: Dict[str, Any] = {
            "tool": fn.__name__,
            "args": kwargs if kwargs else (list(args) if args else {}),
        }
        try:
            out = fn(*args, **kwargs)
            rec["success"] = True
            rec["output"] = str(out)[:200]
            rec["error"] = None
            return out
        except Exception as e:
            rec["success"] = False
            rec["output"] = None
            rec["error"] = f"{type(e).__name__}: {e}"
            raise e
        finally:
            rec["latency_s"] = round(time.time() - t0, 3)

            # 1. Append to request-scoped collector if active
            turn_collector = current_turn_tools.get()
            if turn_collector is not None:
                turn_collector.append(rec)

            # 2. Append to aggregate store for live metrics
            global_tool_store.record(rec)

    return wrapper
