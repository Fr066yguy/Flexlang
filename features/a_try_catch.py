
import re
import engine


TRY_START = re.compile(r"^try\s*$", re.IGNORECASE)
CATCH_LINE = re.compile(
    r"^catch(?:\s+([A-Za-z_]\w*))?\s*$",
    re.IGNORECASE,
)
END_LINE = re.compile(r"^end\s*$", re.IGNORECASE)

# Block types that can contain their own "end".
BLOCK_START = re.compile(
    r"^(?:try|repeat\b|while\b|for\b|function\b|game\.update\b)"
    r"|^if\b(?!.*\bthen\b)",
    re.IGNORECASE,
)


def parse_try(lines, start):
    depth = 1
    catch_index = None

    for index in range(start + 1, len(lines)):
        line = lines[index].strip()

        if BLOCK_START.match(line):
            depth += 1

        elif END_LINE.fullmatch(line):
            depth -= 1

            if depth == 0:
                if catch_index is None:
                    raise SyntaxError(
                        "try block is missing catch"
                    )

                match = CATCH_LINE.fullmatch(
                    lines[catch_index].strip()
                )

                error_name = match.group(1) if match else None

                return (
                    lines[start + 1:catch_index],
                    lines[catch_index + 1:index],
                    error_name,
                    index + 1,
                )

        elif depth == 1 and CATCH_LINE.fullmatch(line):
            if catch_index is not None:
                raise SyntaxError(
                    "Only one catch block is supported"
                )

            catch_index = index

    raise SyntaxError("try block is missing end")


@engine.source_handler
def handle_try_catch(source, runtime, run_line):
    lines = source.splitlines()

    if not any(TRY_START.fullmatch(line.strip()) for line in lines):
        return False

    index = 0
    normal_lines = []

    def run_normal_lines():
        if normal_lines:
            engine.run("\n".join(normal_lines), runtime)
            normal_lines.clear()

    while index < len(lines):
        if not TRY_START.fullmatch(lines[index].strip()):
            normal_lines.append(lines[index])
            index += 1
            continue

        run_normal_lines()

        try_body, catch_body, error_name, next_index = parse_try(
            lines, index
        )

        try:
            engine.run("\n".join(try_body), runtime)

        except Exception as exc:
            if error_name:
                runtime.variables[error_name] = str(exc)

            engine.run("\n".join(catch_body), runtime)

        index = next_index

    run_normal_lines()
    return True