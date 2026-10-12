
import json
import re
from pathlib import Path

import engine


# ==========================================
# FLEXLANG JSON+ PLUGIN
# ==========================================

def remove_comments(source):
    """Remove #, // and /* */ comments outside strings."""

    output = []
    i = 0
    in_string = None
    escaped = False

    while i < len(source):
        char = source[i]

        if in_string:
            output.append(char)

            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = None

            i += 1
            continue

        if char in ('"', "'"):
            in_string = char
            output.append(char)
            i += 1
            continue

        # Single-line comments
        if char == "#":
            while i < len(source) and source[i] != "\n":
                i += 1
            continue

        if source.startswith("//", i):
            while i < len(source) and source[i] != "\n":
                i += 1
            continue

        # Multiline comments
        if source.startswith("/*", i):
            end = source.find("*/", i + 2)

            if end == -1:
                raise ValueError("Unclosed JSON+ block comment")

            # Preserve line numbering and spacing.
            comment = source[i:end + 2]
            output.extend("\n" if c == "\n" else " " for c in comment)
            i = end + 2
            continue

        output.append(char)
        i += 1

    if in_string:
        raise ValueError("Unclosed string in JSON+ file")

    return "".join(output)


def parse_jsonplus(source):
    """Parse JSON+ with comments and trailing commas."""

    source = remove_comments(source)

    # Convert simple single-quoted strings into JSON strings.
    # Double-quoted strings are the recommended format.
    source = convert_single_quotes(source)

    # Allow trailing commas in objects and arrays.
    source = re.sub(r",(\s*[}\]])", r"\1", source)

    return json.loads(source)


def convert_single_quotes(source):
    """Convert single-quoted strings outside double-quoted strings."""

    output = []
    i = 0
    in_double = False
    escaped = False

    while i < len(source):
        char = source[i]

        if in_double:
            output.append(char)

            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_double = False

            i += 1
            continue

        if char == '"':
            in_double = True
            output.append(char)
            i += 1
            continue

        if char == "'":
            # Find the end of this single-quoted string.
            end = i + 1
            escaped_single = False

            while end < len(source):
                current = source[end]

                if escaped_single:
                    escaped_single = False
                elif current == "\\":
                    escaped_single = True
                elif current == "'":
                    break

                end += 1

            if end >= len(source):
                raise ValueError("Unclosed single-quoted string")

            value = source[i + 1:end]
            output.append(json.dumps(value))
            i = end + 1
            continue

        output.append(char)
        i += 1

    return "".join(output)


def get_path(data, path):
    """Read a nested object path, including array indexes."""

    current = data

    for part in path.split("."):
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            if part not in current:
                raise KeyError(f"JSON+ path not found: {path}")
            current = current[part]
        else:
            raise ValueError(
                f"Cannot continue path '{path}' at '{part}'"
            )

    return current


def set_path(data, path, value):
    """Set a nested object value."""

    parts = path.split(".")
    current = data

    for index, part in enumerate(parts[:-1]):
        next_part = parts[index + 1]

        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            if part not in current:
                current[part] = (
                    [] if next_part.isdigit() else {}
                )

            current = current[part]
        else:
            raise ValueError(
                f"Cannot continue path '{path}' at '{part}'"
            )

    last = parts[-1]

    if isinstance(current, dict):
        current[last] = value
    elif isinstance(current, list):
        array_index = int(last)

        if array_index < 0 or array_index >= len(current):
            raise IndexError(
                f"Array index out of range: {array_index}"
            )

        current[array_index] = value
    else:
        raise ValueError(f"Cannot set path: {path}")


def resolve_value(text, runtime):
    """Convert FlexLang values into JSON-compatible Python values."""

    text = text.strip()

    if len(text) >= 2 and text[0] == text[-1]:
        if text[0] in ('"', "'"):
            return runtime.interpolate(text[1:-1])

    if text in runtime.variables:
        return runtime.variables[text]

    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return runtime.interpolate(text)


def get_filename(text, runtime):
    """Resolve a quoted filename."""

    value = resolve_value(text, runtime)

    if not isinstance(value, str):
        raise ValueError("Filename must be a string")

    return Path(value)


# ==========================================
# LOAD JSON+
# jsonplus.load "game.json+" as game
# ==========================================

@engine.syntax(
    r'jsonplus\.load\s+("[^"]+"|\'[^\']+\')\s+as\s+([A-Za-z_]\w*)'
)
def jsonplus_load(match, runtime):
    filename = get_filename(match.group(1), runtime)
    name = match.group(2)

    if not filename.is_file():
        raise FileNotFoundError(
            f"JSON+ file not found: {filename}"
        )

    source = filename.read_text(encoding="utf-8")
    data = parse_jsonplus(source)

    runtime.variables[name] = data

    print(f"Loaded JSON+ file: {filename}")


# ==========================================
# GET A VALUE
# jsonplus.get game "player.level" as level
# ==========================================

@engine.syntax(
    r'jsonplus\.get\s+([A-Za-z_]\w*)\s+"([^"]+)"\s+as\s+([A-Za-z_]\w*)'
)
def jsonplus_get(match, runtime):
    name = match.group(1)
    path = match.group(2)
    target = match.group(3)

    if name not in runtime.variables:
        raise ValueError(
            f"JSON+ variable '{name}' does not exist"
        )

    data = runtime.variables[name]
    result = get_path(data, path)

    runtime.variables[target] = result

    print(f"{target} = {result}")


# ==========================================
# CHANGE A VALUE
# jsonplus.set game "player.level" to 25
# ==========================================

@engine.syntax(
    r'jsonplus\.set\s+([A-Za-z_]\w*)\s+"([^"]+)"\s+to\s+(.+)'
)
def jsonplus_set(match, runtime):
    name = match.group(1)
    path = match.group(2)
    raw_value = match.group(3)

    if name not in runtime.variables:
        raise ValueError(
            f"JSON+ variable '{name}' does not exist"
        )

    data = runtime.variables[name]
    value = resolve_value(raw_value, runtime)

    set_path(data, path, value)

    print(f"Updated {path} = {value}")


# ==========================================
# SAVE JSON+
# jsonplus.save game to "game.json+"
# ==========================================

@engine.syntax(
    r'jsonplus\.save\s+([A-Za-z_]\w*)\s+to\s+("[^"]+"|\'[^\']+\')'
)
def jsonplus_save(match, runtime):
    name = match.group(1)
    filename = get_filename(match.group(2), runtime)

    if name not in runtime.variables:
        raise ValueError(
            f"JSON+ variable '{name}' does not exist"
        )

    data = runtime.variables[name]

    filename.parent.mkdir(parents=True, exist_ok=True)

    filename.write_text(
        json.dumps(data, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print(f"Saved JSON+ file: {filename}")


# ==========================================
# DISPLAY DATA
# jsonplus.show game
# ==========================================

@engine.syntax(r'jsonplus\.show\s+([A-Za-z_]\w*)')
def jsonplus_show(match, runtime):
    name = match.group(1)

    if name not in runtime.variables:
        raise ValueError(
            f"JSON+ variable '{name}' does not exist"
        )

    print(
        json.dumps(
            runtime.variables[name],
            indent=4,
            ensure_ascii=False
        )
    )


# ==========================================
# CHECK WHETHER A PATH EXISTS
# jsonplus.has game "player.level" as exists
# ==========================================

@engine.syntax(
    r'jsonplus\.has\s+([A-Za-z_]\w*)\s+"([^"]+)"\s+as\s+([A-Za-z_]\w*)'
)
def jsonplus_has(match, runtime):
    name = match.group(1)
    path = match.group(2)
    target = match.group(3)

    if name not in runtime.variables:
        raise ValueError(
            f"JSON+ variable '{name}' does not exist"
        )

    try:
        get_path(runtime.variables[name], path)
        result = True
    except (KeyError, IndexError, ValueError, TypeError):
        result = False

    runtime.variables[target] = result
    print(f"{target} = {result}")