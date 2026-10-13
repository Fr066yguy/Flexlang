
from engine import syntax
import ast
import operator
import re

COMPARISONS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
}


def get_value(text, runtime):
    text = text.strip()

    # Quoted text
    if (
        len(text) >= 2
        and text[0] == text[-1]
        and text[0] in ("'", '"')
    ):
        return runtime.interpolate(text[1:-1])

    # Number
    try:
        return int(text)
    except ValueError:
        pass

    try:
        return float(text)
    except ValueError:
        pass

    # Variable
    if re.fullmatch(r"[A-Za-z_]\w*", text):
        if text not in runtime.variables:
            raise ValueError(f"Unknown variable '{text}'")
        return runtime.variables[text]

    raise ValueError(f"Invalid comparison value: {text}")


@syntax(
    r'compare\s+(.+?)\s*(==|!=|>=|<=|>|<)\s*(.+)'
)
def compare(match, runtime):
    left_text = match.group(1)
    symbol = match.group(2)
    right_text = match.group(3)

    left = get_value(left_text, runtime)
    right = get_value(right_text, runtime)

    # Don't allow ordering comparisons between unlike types.
    if symbol not in ("==", "!=") and type(left) != type(right):
        if not (
            isinstance(left, (int, float))
            and isinstance(right, (int, float))
        ):
            raise ValueError("Cannot compare these value types")

    result = COMPARISONS[symbol](left, right)

    print(f"{left} {symbol} {right} -> {result}")
    runtime.variables["comparison"] = result