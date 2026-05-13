"""
Calculator Tool
===============
Safely evaluates mathematical expressions using Python's ``ast`` module.
**Never** uses ``eval()`` — only literal numbers and basic arithmetic
operators (+, -, *, /, **, %) are permitted.
"""

import ast
import operator
from typing import Union

from langchain_core.tools import tool


# Allowed binary operators
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}

# Allowed unary operators
_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST) -> Union[int, float]:
    """
    Recursively evaluate an AST node containing only numeric literals
    and whitelisted operators.

    Args:
        node: An ``ast`` node produced by ``ast.parse(expr, mode='eval')``.

    Returns:
        The numeric result of the expression.

    Raises:
        ValueError: If the expression contains disallowed operations.
    """
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _OPERATORS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _safe_eval(node.operand)
        return _UNARY_OPERATORS[op_type](operand)

    raise ValueError(
        f"Unsupported expression element: {type(node).__name__}. "
        "Only numbers and basic math operators are allowed."
    )


@tool
def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression and return the result.
    Use this tool when the user asks you to calculate, compute, or
    solve a math problem. Supports: +, -, *, /, **, %, //.

    Args:
        expression: A mathematical expression string (e.g., "2 + 3 * 4").

    Returns:
        The result of the calculation as a formatted string.
    """
    try:
        # Parse the expression into an AST
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree)

        # Format nicely: drop .0 for whole numbers
        if isinstance(result, float) and result.is_integer():
            result = int(result)

        return f"🔢 {expression.strip()} = {result}"

    except ZeroDivisionError:
        return "❌ Math error: Division by zero is not allowed."
    except (ValueError, SyntaxError) as exc:
        return (
            f"❌ Could not evaluate '{expression}'. "
            f"Please use a valid math expression. ({exc})"
        )
    except Exception as exc:
        return f"⚠️ Calculation error: {exc}"
