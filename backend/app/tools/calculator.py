import ast
import math
import operator
from langchain_core.tools import tool
from app.tools.logger import logged

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
}

_FUNCS = {
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "abs": abs,
    "round": round,
}


def _eval(node):
    """Safely evaluate AST node against strictly allowed operations and math functions."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FUNCS
    ):
        return _FUNCS[node.func.id](*[_eval(a) for a in node.args])
    raise ValueError("Unsupported or unsafe expression")


@tool
@logged
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression exactly, e.g. '(16*4)+3**2' or 'sqrt(144)'. Use for ALL arithmetic."""
    try:
        cleaned = expression.strip().strip("'\"`")
        tree = ast.parse(cleaned, mode="eval")
        result = _eval(tree.body)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(result)
    except Exception as e:
        raise ValueError(f"Calculator evaluation failed: {e}")
