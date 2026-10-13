
import subprocess
import sys
from pathlib import Path

import engine


# ==========================================
# FLEXLANG TERMINAL PLUGIN
# ==========================================

@engine.syntax(r'terminal\.clear')
def terminal_clear(match, runtime):
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="", flush=True)


@engine.syntax(r'terminal\.title\s+(.+)')
def terminal_title(match, runtime):
    """Set the terminal window title."""
    title = runtime.interpolate(
        engine.FlexRuntime.parse_value(match.group(1))
    )
    print(f"\033]0;{title}\007", end="", flush=True)


@engine.syntax(r'terminal\.line')
def terminal_line(match, runtime):
    """Print a separator."""
    print("-" * 40)


@engine.syntax(r'terminal\.pause')
def terminal_pause(match, runtime):
    """Wait for the user to press Enter."""
    input("Press Enter to continue...")


@engine.syntax(r'terminal\.input\s+([A-Za-z_]\w*)\s+"([^"]*)"')
def terminal_input(match, runtime):
    """Read input and store it as a string."""
    name = match.group(1)
    prompt = runtime.interpolate(match.group(2))
    runtime.variables[name] = input(prompt)


@engine.syntax(r'terminal\.number\s+([A-Za-z_]\w*)\s+"([^"]*)"')
def terminal_number(match, runtime):
    """Read and validate a number."""
    name = match.group(1)
    prompt = runtime.interpolate(match.group(2))

    while True:
        answer = input(prompt)

        try:
            if "." in answer:
                value = float(answer)
            else:
                value = int(answer)

            runtime.variables[name] = value
            break

        except ValueError:
            print("Please enter a valid number.")


@engine.syntax(r'terminal\.write\s+(.+)')
def terminal_write(match, runtime):
    """Print text without automatically adding a newline."""
    text = engine.FlexRuntime.parse_value(match.group(1))
    print(runtime.interpolate(str(text)), end="", flush=True)


@engine.syntax(r'terminal\.command\s+"([^"]*)"')
def terminal_command(match, runtime):
    """
    Run a system command.
    Only use commands you trust.
    """
    command = runtime.interpolate(match.group(1))

    if sys.platform == "win32":
        result = subprocess.run(
            ["cmd", "/c", command],
            check=False
        )
    else:
        result = subprocess.run(
            command,
            shell=True,
            check=False
        )

    runtime.variables["terminal_exit_code"] = result.returncode


print("FlexLang terminal plugin loaded!")