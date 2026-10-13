
from engine import syntax
import ast
import operator
import re

BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate(node, runtime):
    if isinstance(node, ast.Constant):
        if type(node.value) in (int, float):
            return node.value
        raise ValueError("Only numbers are allowed")

    if isinstance(node, ast.Name):
        if node.id not in runtime.variables:
            raise ValueError(f"Unknown variable '{node.id}'")
        value = runtime.variables[node.id]
        if type(value) not in (int, float):
            raise ValueError(f"'{node.id}' must be a number")
        return value

    if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPS:
        left = evaluate(node.left, runtime)
        right = evaluate(node.right, runtime)

        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
            raise ValueError("Cannot divide by zero")

        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponent is too large")

        result = BINARY_OPS[type(node.op)](left, right)

        if isinstance(result, (int, float)) and abs(result) > 1e100:
            raise ValueError("Result is too large")

        return result

    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
        return UNARY_OPS[type(node.op)](evaluate(node.operand, runtime))

    raise ValueError("Unsupported math expression")


def calculate(expression, runtime):
    # Translate FlexLang's ^ exponent symbol to Python's **.
    expression = expression.replace("^", "**")

    # Parse expression without executing Python code.
    tree = ast.parse(expression, mode="eval")
    return evaluate(tree.body, runtime)


@syntax(r'([A-Za-z_]\w*)\s*=\s*(.+)')
def assign_math(match, runtime):
    name = match.group(1)
    expression = match.group(2)

    # Support numbers, existing variables, and arithmetic.
    result = calculate(expression, runtime)
    runtime.variables[name] = result
    print(f"{name} = {result}")


@syntax(r'add\s+(.+?)\s+and\s+(.+)')
def add_values(match, runtime):
    left = calculate(match.group(1), runtime)
    right = calculate(match.group(2), runtime)
    print(left + right)