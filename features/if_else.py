
import re
from engine import syntax, source_handler, run


def get_value(text, runtime):
    text = text.strip()

    if len(text) >= 2 and text[0] == text[-1]:
        if text[0] in ("'", '"'):
            return runtime.interpolate(text[1:-1])

    if text in runtime.variables:
        return runtime.variables[text]

    if text == "True":
        return True
    if text == "False":
        return False

    try:
        return int(text)
    except ValueError:
        pass

    try:
        return float(text)
    except ValueError:
        pass

    raise ValueError(f"Unknown value: {text}")


def evaluate(condition, runtime):
    condition = condition.strip()

    for op in ("==", "!=", ">=", "<=", ">", "<"):
        parts = condition.split(op, 1)

        if len(parts) == 2:
            left = get_value(parts[0], runtime)
            right = get_value(parts[1], runtime)

            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == ">":
                return left > right
            if op == "<":
                return left < right
            if op == ">=":
                return left >= right
            if op == "<=":
                return left <= right

    value = get_value(condition, runtime)

    if isinstance(value, bool):
        return value

    raise ValueError(f"Invalid condition: {condition}")


# Single-line syntax:
# if score > 10 then say "Winner"

@syntax(r'if\s+(.+?)\s+then\s+(.+)')
def if_then(match, runtime):
    if evaluate(match.group(1), runtime):
        run(match.group(2), runtime)


# Block syntax:
# if score > 10
#     say "Winner"
# else
#     say "Try again"
# end

@source_handler
def if_block(source, runtime, run_line):
    lines = source.splitlines()

    if not any(
        re.match(r'^\s*if\s+(.+?)\s*$', line)
        and " then " not in line
        for line in lines
    ):
        return False

    def execute_block(block_lines):
        index = 0

        while index < len(block_lines):
            line = block_lines[index]
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                index += 1
                continue

            if re.match(r'^if\s+(.+)$', stripped) and " then " not in stripped:
                condition = stripped[3:].strip()
                index += 1

                true_lines = []
                false_lines = []
                active = true_lines
                depth = 1

                while index < len(block_lines):
                    current = block_lines[index].strip()

                    if re.match(r'^if\s+(.+)$', current) and " then " not in current:
                        depth += 1

                    if current == "end":
                        depth -= 1

                        if depth == 0:
                            break

                    if depth == 1 and current == "else":
                        active = false_lines
                        index += 1
                        continue

                    if depth > 0:
                        active.append(block_lines[index])

                    index += 1

                if depth != 0:
                    raise ValueError("Missing 'end' for if block.")

                if evaluate(condition, runtime):
                    execute_block(true_lines)
                else:
                    execute_block(false_lines)

                index += 1
                continue

            if stripped == "else" or stripped == "end":
                raise ValueError(f"Unexpected '{stripped}' in block.")

            run_line(line)
            index += 1

    # Only handle if blocks here. The game2d plugin must extract its
    # game.update body before that body is executed each frame.
    execute_block(lines)
    return True