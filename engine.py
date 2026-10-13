
from pathlib import Path
import importlib.util
import re
import sys


# Make sure plugins importing "engine" use this same module.
sys.modules["engine"] = sys.modules[__name__]


# ==========================================
# FLEXLANG RUNTIME
# ==========================================

class FlexRuntime:
    def __init__(self):
        self.variables = {}

    def interpolate(self, text):
        """Replace {variable} placeholders with stored values."""

        def replace(match):
            name = match.group(1)

            if name not in self.variables:
                raise ValueError(
                    f"Variable '{name}' does not exist"
                )

            return str(self.variables[name])

        return re.sub(
            r"\{([A-Za-z_][A-Za-z0-9_]*)\}",
            replace,
            text
        )

    @staticmethod
    def parse_value(text):
        """Convert quoted strings and numbers into values."""
        text = text.strip()

        if (
            len(text) >= 2
            and text[0] == text[-1]
            and text[0] in ('"', "'")
        ):
            return text[1:-1]

        try:
            return int(text)
        except ValueError:
            pass

        try:
            return float(text)
        except ValueError:
            pass

        return text


# ==========================================
# FEATURE REGISTRY
# ==========================================

SYNTAX = []
SOURCE_HANDLERS = []

# Controls whether plugin loading messages are shown.
QUIET_STARTUP = False


def source_handler(function):
    SOURCE_HANDLERS.append(function)
    return function


def syntax(pattern):
    """Register a FlexLang syntax handler."""

    compiled_pattern = re.compile(pattern, re.IGNORECASE)

    def register(function):
        SYNTAX.append((compiled_pattern, function))
        return function

    return register


# ==========================================
# AUTOMATIC PLUGIN LOADER
# ==========================================

def load_features():
    """Load every Python plugin from the features folder."""

    folder = Path(__file__).parent / "features"
    folder.mkdir(parents=True, exist_ok=True)

    SYNTAX.clear()
    SOURCE_HANDLERS.clear()

    for file in sorted(folder.glob("*.py")):
        if file.name.startswith("_"):
            continue

        if file.name == "__init__.py":
            continue

        module_name = f"flexlang_feature_{file.stem}"

        spec = importlib.util.spec_from_file_location(
            module_name,
            file
        )

        if spec is None or spec.loader is None:
            if not QUIET_STARTUP:
                print(f"Could not load plugin: {file.name}")
            continue

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)

            if not QUIET_STARTUP:
                print(f"Loaded feature: {file.stem}")

        except Exception as error:
            print(f"Plugin error in {file.name}: {error}")


# ==========================================
# FLEXLANG INTERPRETER
# ==========================================

def run(source, runtime=None, _skip_source_handlers=False):
    if runtime is None:
        runtime = FlexRuntime()

    # Allow plugins to process complete source blocks.
    if not _skip_source_handlers:
        for handler in SOURCE_HANDLERS:
            try:
                handled = handler(
                    source,
                    runtime,
                    lambda line: run(line, runtime, True)
                )

                if handled:
                    return

            except Exception as error:
                print(f"FlexLang block error: {error}")
                return

    # Execute normal single-line syntax.
    for line_number, line in enumerate(source.splitlines(), 1):
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        # Ignore the mute directive if it reaches the interpreter.
        if line.lower() == "--mutestart":
            continue

        matched = False

        for pattern, function in SYNTAX:
            match = pattern.fullmatch(line)

            if match:
                try:
                    function(match, runtime)
                except Exception as error:
                    print(f"Line {line_number}: {error}")

                matched = True
                break

        if not matched:
            print(
                f"Line {line_number}: "
                f"Unknown syntax: {line}"
            )


# ==========================================
# PROGRAM START
# ==========================================

def main():
    global QUIET_STARTUP

    filename = Path(sys.argv[1]) if len(sys.argv) >= 2 else None
    source = None

    # Read the program first so we can check its startup setting.
    if filename is not None and filename.is_file():
        try:
            source = filename.read_text(encoding="utf-8")

        except OSError as error:
            print(f"Could not read program: {error}")
            return

    # Enable quiet startup if the directive appears in the file.
    QUIET_STARTUP = (
        source is not None
        and any(
            line.strip().lower() == "--mutestart"
            for line in source.splitlines()
        )
    )

    if not QUIET_STARTUP:
        print("FlexLang starting...")

    # Load plugins normally, but suppress their loading messages
    # when --Mutestart is enabled.
    load_features()

    if filename is None:
        if not QUIET_STARTUP:
            print()
            print("Usage:")
            print("  python engine.py hello.flx")
        return

    if not filename.is_file():
        print(f"File not found: {filename}")
        return

    # Remove the directive before running the program.
    source = "\n".join(
        line
        for line in source.splitlines()
        if line.strip().lower() != "--mutestart"
    )

    run(source)


if __name__ == "__main__":
    main()