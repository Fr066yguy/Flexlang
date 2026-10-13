
from engine import syntax
import re


@syntax(r'toNumber\(\s*([A-Za-z_]\w*)\s*\)')
def to_number(match, runtime):
    name = match.group(1)

    if name not in runtime.variables:
        raise ValueError(f"Unknown variable '{name}'")

    value = runtime.variables[name]

    if isinstance(value, bool):
        raise ValueError("Cannot convert True or False to a number")

    try:
        text = str(value).strip()

        if not text:
            raise ValueError("Cannot convert empty text to a number")

        # Keep whole numbers as integers.
        if re.fullmatch(r'[+-]?\d+', text):
            result = int(text)
        else:
            result = float(text)

        runtime.variables[name] = result

    except (ValueError, TypeError):
        raise ValueError(
            f"Cannot convert {value!r} to a number"
        )