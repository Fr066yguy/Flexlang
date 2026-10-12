
from engine import source_handler
import re


def get_value(text, runtime):
    text = text.strip()

    if (
        len(text) >= 2
        and text[0] == text[-1]
        and text[0] in ("'", '"')
    ):
        return runtime.interpolate(text[1:-1])

    if text in runtime.variables:
        return runtime.variables[text]

    if text == "True":
        return True
    if text == "False":
        return False

    try:
        return runtime.parse_value(text)
    except (ValueError, TypeError):
        raise ValueError(f"Unknown value: {text}")


def evaluate(condition, runtime):
    condition = condition.strip()

    for operator in (" or ", " and "):
        if operator in condition:
            left, right = condition.split(operator, 1)

            if operator == " or ":
                return (
                    evaluate(left, runtime)
                    or evaluate(right, runtime)
                )

            return (
                evaluate(left, runtime)
                and evaluate(right, runtime)
            )

    if condition.startswith("not "):
        return not evaluate(condition[4:], runtime)

    for operator in ("==", "!=", ">=", "<=", ">", "<"):
        if operator in condition:
            left_text, right_text = condition.split(
                operator, 1
            )

            left = get_value(left_text, runtime)
            right = get_value(right_text, runtime)

            if operator == "==":
                return left == right
            if operator == "!=":
                return left != right
            if operator == ">":
                return left > right
            if operator == "<":
                return left < right
            if operator == ">=":
                return left >= right
            if operator == "<=":
                return left <= right

    value = get_value(condition, runtime)

    if isinstance(value, bool):
        return value

    raise ValueError(
        f"Condition must be True or False: {condition}"
    )


def parse_block(lines, start=0):
    nodes = []
    i = start

    while i < len(lines):
        line = lines[i].strip()

        if not line or line.startswith("#"):
            i += 1
            continue

        if line in ("else", "end"):
            return nodes, i, line

        # FOR LOOP
        if line.startswith("for "):
            match = re.fullmatch(
                r"for\s+([A-Za-z_]\w*)\s*=\s*(.+?)"
                r"\s+to\s+(.+?)(?:\s+step\s+(.+))?",
                line
            )

            if not match:
                raise ValueError(
                    f"Invalid for loop at line {i + 1}. "
                    "Use: for i = 0 to 10"
                )

            name = match.group(1)
            start_text = match.group(2).strip()
            end_text = match.group(3).strip()
            step_text = match.group(4)

            body, stop_index, stop = parse_block(
                lines, i + 1
            )

            if stop != "end":
                raise ValueError(
                    f"Missing 'end' for loop at line {i + 1}"
                )

            nodes.append((
                "for",
                name,
                start_text,
                end_text,
                step_text,
                body
            ))

            i = stop_index + 1
            continue

        # IF BLOCK
        if line.startswith("if "):
            condition = line[3:].strip()

            # Keep existing one-line if syntax working.
            if " then " in condition:
                nodes.append(("line", line))
                i += 1
                continue

            if condition.endswith(" then"):
                condition = condition[:-5].strip()

            if not condition:
                raise ValueError(
                    f"Missing condition at line {i + 1}"
                )

            yes_nodes, stop_index, stop = parse_block(
                lines, i + 1
            )

            no_nodes = []

            if stop == "else":
                no_nodes, stop_index, stop = parse_block(
                    lines, stop_index + 1
                )

            if stop != "end":
                raise ValueError(
                    f"Missing 'end' for if at line {i + 1}"
                )

            nodes.append((
                "if", condition, yes_nodes, no_nodes
            ))

            i = stop_index + 1
            continue

        nodes.append(("line", line))
        i += 1

    return nodes, i, None


def execute_nodes(nodes, runtime, execute_line):
    for node in nodes:
        if node[0] == "line":
            execute_line(node[1])

        elif node[0] == "if":
            _, condition, yes_nodes, no_nodes = node

            if evaluate(condition, runtime):
                execute_nodes(
                    yes_nodes, runtime, execute_line
                )
            else:
                execute_nodes(
                    no_nodes, runtime, execute_line
                )

        elif node[0] == "for":
            (
                _, name, start_text, end_text,
                step_text, body
            ) = node

            start = get_value(start_text, runtime)
            end = get_value(end_text, runtime)

            if (
                isinstance(start, bool)
                or isinstance(end, bool)
                or not isinstance(start, (int, float))
                or not isinstance(end, (int, float))
            ):
                raise ValueError(
                    "For loop start and end must be numbers."
                )

            if step_text is not None:
                step = get_value(step_text, runtime)

                if (
                    isinstance(step, bool)
                    or not isinstance(step, (int, float))
                ):
                    raise ValueError(
                        "For loop step must be a number."
                    )
            else:
                step = 1 if start <= end else -1

            if step == 0:
                raise ValueError(
                    "For loop step cannot be zero."
                )

            if start < end and step < 0:
                raise ValueError(
                    "Step must be positive when counting up."
                )

            if start > end and step > 0:
                raise ValueError(
                    "Step must be negative when counting down."
                )

            current = start
            iterations = 0

            while (
                current <= end
                if step > 0
                else current >= end
            ):
                runtime.variables[name] = current

                execute_nodes(
                    body, runtime, execute_line
                )

                current += step
                iterations += 1

                if iterations > 1_000_000:
                    raise ValueError(
                        "For loop exceeded 1,000,000 iterations."
                    )


@source_handler
def multiline(source, runtime, execute_line):
    lines = source.splitlines()

    nodes, index, stop = parse_block(lines)

    if stop is not None:
        raise ValueError(
            f"Unexpected '{stop}' at line {index + 1}"
        )

    execute_nodes(nodes, runtime, execute_line)
    return True