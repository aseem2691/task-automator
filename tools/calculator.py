import ast
import operator

from langchain_core.tools import tool

# Safe math operators only
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPERATORS[type(node.op)](_eval(node.operand))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely. Supports +, -, *, /, %, **, //.

    Args:
        expression: A math expression like "2 + 3 * 4" or "(100 - 25) / 3".
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval(tree.body)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"
