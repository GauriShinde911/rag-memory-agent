import sys
import subprocess
import tempfile
from langchain_core.tools import tool
from app.config import settings
from app.tools.logger import logged

MAX_OUTPUT_CHARS = 2000


@tool
@logged
def python_executor(code: str) -> str:
    """Run a short Python snippet in a separate process (5 s timeout) and return what it prints. Use print() to show results."""
    if not settings.enable_python_executor:
        return "Python code execution is disabled by server administrator."

    # NOTE: This executor provides basic process isolation with timeout and temporary cwd.
    # It is intended for demo/assignment purposes and is NOT a hardened security sandbox.
    with tempfile.TemporaryDirectory() as temp_cwd:
        try:
            p = subprocess.run(
                [sys.executable, "-c", code],
                cwd=temp_cwd,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Python execution timed out after 5.0 seconds")

    if p.returncode != 0:
        err = p.stderr.strip()
        last_err = err.splitlines()[-1] if err else "Execution failed"
        raise RuntimeError(last_err)

    out = p.stdout.strip()
    if len(out) > MAX_OUTPUT_CHARS:
        out = out[:MAX_OUTPUT_CHARS] + f"\n... [output truncated at {MAX_OUTPUT_CHARS} chars]"

    return out or "(no output)"
