
import re
import engine


# ==========================================
# FLEXLANG FUNCTIONS PLUGIN
# No core engine modifications required.
# ==========================================

FUNCTION_HEADER = re.compile(
    r"^\s*function\s+([A-Za-z_]\w*)\s*\((.*?)\)\s*$",
    re.IGNORECASE
)

RETURN_LINE = re.compile(
    r"^\s*return(?:\s+(.*))?$",
    re.IGNORECASE
)

IDENTIFIER = re.compile(r"^[A-Za-z_]\w*$")


def split_arguments(text):
    """Split arguments while respecting strings and nested calls."""
    parts = []
    current = []
    depth = 0
    quote = None
    escaped = False

    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue

        if char == "\\" and quote:
            current.append(char)
            escaped = True
            continue

        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue

        if char in ('"', "'"):
            quote = char
            current.append(char)
        elif char in "([{":
            depth += 1
            current.append(char)
        elif char in ")]}":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)

    if current or text.strip():
        parts.append("".join(current).strip())

    return parts


def get_functions(runtime):
    if not hasattr(runtime, "_flexlang_functions"):
        runtime._flexlang_functions = {}
    return runtime._flexlang_functions


def evaluate_argument(expression, runtime):
    """Resolve a parameter from a variable, string, or number."""
    expression = expression.strip()

    if expression in runtime.variables:
        return runtime.variables[expression]

    # Allow interpolated string arguments.
    if (
        len(expression) >= 2
        and expression[0] == expression[-1]
        and expression[0] in ('"', "'")
    ):
        value = engine.FlexRuntime.parse_value(expression)
        if isinstance(value, str):
            return runtime.interpolate(value)
        return value

    return engine.FlexRuntime.parse_value(expression)


def evaluate_return(expression, runtime):
    """Resolve the expression returned by a function."""
    expression = expression.strip()

    if expression in runtime.variables:
        return runtime.variables[expression]

    return evaluate_argument(expression, runtime)


def execute_function(name, argument_text, runtime):
    functions = get_functions(runtime)

    if name not in functions:
        raise NameError(f"Function '{name}' does not exist.")

    parameters, body = functions[name]

    arguments = (
        split_arguments(argument_text)
        if argument_text.strip()
        else []
    )

    if len(arguments) != len(parameters):
        raise TypeError(
            f"{name}() expects {len(parameters)} argument(s), "
            f"but received {len(arguments)}."
        )

    values = [
        evaluate_argument(argument, runtime)
        for argument in arguments
    ]

    # Create a local variable scope.
    caller_variables = runtime.variables
    local_variables = caller_variables.copy()
    local_variables.update(zip(parameters, values))
    runtime.variables = local_variables

    try:
        lines = body.splitlines()
        executable_lines = []
        return_expression = None

        # Find a top-level return and stop before executing it.
        # Nested returns inside if/else are not supported yet.
        depth = 0

        for line in lines:
            stripped = line.strip()

            if RETURN_LINE.fullmatch(stripped) and depth == 0:
                match = RETURN_LINE.fullmatch(stripped)
                return_expression = match.group(1)
                break

            if re.match(r"^(if|for|while)\b", stripped):
                depth += 1
            elif stripped == "end" and depth > 0:
                depth -= 1

            executable_lines.append(line)

        if executable_lines:
            engine.run("\n".join(executable_lines), runtime)

        if return_expression is None:
            return None

        return evaluate_return(return_expression, runtime)

    finally:
        # Do not leak function-local variables into the caller.
        runtime.variables = caller_variables


def find_calls_outside_strings(line):
    """Find simple function-call expressions outside quoted strings."""
    functions = get_functions_from_current_runtime()

    # This function is replaced below with a runtime-aware version.
    return []


def replace_function_calls(line, runtime):
    """Replace function calls with their computed literal results."""
    functions = get_functions(runtime)
    output = []
    index = 0
    quote = None
    escaped = False

    while index < len(line):
        char = line[index]

        if escaped:
            output.append(char)
            escaped = False
            index += 1
            continue

        if char == "\\" and quote:
            output.append(char)
            escaped = True
            index += 1
            continue

        if quote:
            output.append(char)
            if char == quote:
                quote = None
            index += 1
            continue

        if char in ('"', "'"):
            quote = char
            output.append(char)
            index += 1
            continue

        # Match an identifier followed by an opening parenthesis.
        match = re.match(r"[A-Za-z_]\w*\s*\(", line[index:])

        if not match:
            output.append(char)
            index += 1
            continue

        name_and_open = match.group(0)
        name = name_and_open.split("(")[0].strip()

        if name not in functions:
            output.append(char)
            index += 1
            continue

        opening = index + name_and_open.rfind("(")
        depth = 1
        inner_quote = None
        inner_escaped = False
        end = opening + 1

        while end < len(line) and depth:
            current = line[end]

            if inner_escaped:
                inner_escaped = False
            elif current == "\\" and inner_quote:
                inner_escaped = True
            elif inner_quote:
                if current == inner_quote:
                    inner_quote = None
            elif current in ('"', "'"):
                inner_quote = current
            elif current == "(":
                depth += 1
            elif current == ")":
                depth -= 1

            end += 1

        if depth != 0:
            output.append(char)
            index += 1
            continue

        arguments = line[opening + 1:end - 1]
        value = execute_function(name, arguments, runtime)

        if isinstance(value, str):
            # Preserve the result as a string literal.
            import json
            replacement = json.dumps(value)
        elif value is None:
            replacement = "null"
        else:
            replacement = str(value)

        output.append(replacement)
        index = end

    return "".join(output)


def get_functions_from_current_runtime():
    # Compatibility placeholder; not used by the runtime-aware scanner.
    return {}


def functions_source(source, runtime, execute_line):
    """Register function definitions and expand calls before execution."""
    lines = source.splitlines()
    remaining = []
    index = 0
    found_definition = False
    functions = get_functions(runtime)

    # First pass: collect all function definitions.
    while index < len(lines):
        line = lines[index]
        match = FUNCTION_HEADER.fullmatch(line)

        if not match:
            remaining.append(line)
            index += 1
            continue

        found_definition = True
        name, parameter_text = match.groups()

        parameters = (
            split_arguments(parameter_text)
            if parameter_text.strip()
            else []
        )

        if any(not IDENTIFIER.fullmatch(p) for p in parameters):
            print(f"Function error: invalid parameter in {name}()")
            return True

        if len(parameters) != len(set(parameters)):
            print(f"Function error: duplicate parameter in {name}()")
            return True

        body = []
        index += 1
        depth = 1

        while index < len(lines):
            current = lines[index]
            stripped = current.strip()

            if FUNCTION_HEADER.fullmatch(current):
                depth += 1
            elif re.match(r"^(if|for|while)\b", stripped):
                depth += 1
            elif stripped.lower() == "end":
                depth -= 1

                if depth == 0:
                    break

            body.append(current)
            index += 1

        if depth != 0:
            print(f"Function error: missing 'end' for {name}()")
            return True

        functions[name] = (parameters, "\n".join(body))
        index += 1

    # Second pass: expand function calls in ordinary statements.
    # This also supports calls inside function bodies.
    transformed = [
        replace_function_calls(line, runtime)
        for line in remaining
    ]

    transformed_source = "\n".join(transformed).strip()

    if found_definition or transformed_source != "\n".join(remaining).strip():
        if transformed_source:
            # Re-enter the interpreter so other block plugins can work.
            engine.run(transformed_source, runtime)
        return True

    return False


engine.source_handler(functions_source)

print("FlexLang functions plugin loaded.")