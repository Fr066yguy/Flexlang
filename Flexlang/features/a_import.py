
import re
import sys
from pathlib import Path

import engine


IMPORT_LINE = re.compile(
    r"""^\s*import\s+(['"])(.+?)\1\s*(?:#.*)?$""",
    re.IGNORECASE,
)

MAX_FILE_BYTES = 1024 * 1024
MAX_IMPORT_DEPTH = 32


def get_project_root():
    # The first .flx argument is the main program.
    if len(sys.argv) > 1:
        main_file = Path(sys.argv[1]).expanduser()

        if main_file.suffix.lower() == ".flx":
            return main_file.resolve().parent

    return Path.cwd().resolve()


def expand_source(source, base_dir, root_dir, stack, imported):
    """Replace import statements with their module source."""
    output = []

    for line in source.splitlines():
        match = IMPORT_LINE.fullmatch(line)

        if not match:
            output.append(line)
            continue

        relative_name = match.group(2).strip()
        module_path = Path(relative_name)

        if module_path.is_absolute():
            raise ValueError("Absolute import paths are not allowed")

        if module_path.suffix.lower() != ".flx":
            raise ValueError("Only .flx files can be imported")

        path = (base_dir / module_path).resolve()

        # Keep imports inside the main project's directory.
        try:
            path.relative_to(root_dir)
        except ValueError:
            raise ValueError(
                f"Import is outside the project folder: {relative_name}"
            )

        # Check the active chain before the already-imported cache.
        if path in stack:
            chain = " -> ".join(
                str(item.name) for item in stack + [path]
            )
            raise ValueError(f"Circular import detected: {chain}")

        # Import each module only once per import pass.
        if path in imported:
            continue

        if not path.is_file():
            raise FileNotFoundError(
                f"Cannot find imported file: {relative_name}"
            )

        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(
                f"Imported file exceeds 1 MB: {relative_name}"
            )

        if len(stack) >= MAX_IMPORT_DEPTH:
            raise ValueError("Maximum import depth of 32 exceeded")

        module_source = path.read_text(encoding="utf-8")

        expanded_module = expand_source(
            module_source,
            path.parent,
            root_dir,
            stack + [path],
            imported,
        )

        imported.add(path)
        output.append(expanded_module)

    return "\n".join(output)


@engine.source_handler
def handle_imports(source, runtime, run_line):
    # Don't intercept programs that don't use imports.
    if not any(IMPORT_LINE.fullmatch(line) for line in source.splitlines()):
        return False

    try:
        root_dir = get_project_root()
        main_file = None

        if len(sys.argv) > 1:
            candidate = Path(sys.argv[1]).expanduser()

            if candidate.suffix.lower() == ".flx":
                main_file = candidate.resolve()

        stack = [main_file] if main_file else []

        expanded = expand_source(
            source,
            root_dir,
            root_dir,
            stack,
            set(),
        )

    except Exception as exc:
        print(f"FlexLang import error: {exc}")
        return True

    # Run the expanded program using the same runtime and variables.
    engine.run(expanded, runtime)
    return True