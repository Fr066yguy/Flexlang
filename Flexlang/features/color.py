
from engine import syntax
import re

COLORS = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "gray": "90",
    "grey": "90",
    "bright_red": "91",
    "bright_green": "92",
    "bright_yellow": "93",
    "bright_blue": "94",
    "bright_magenta": "95",
    "bright_cyan": "96",
    "bright_white": "97",
    "reset": "0",
}


@syntax(r'color\s+([A-Za-z_]+)\s+(.+)')
def color_command(match, runtime):
    color_name = match.group(1).lower()
    message = match.group(2).strip()

    if color_name not in COLORS:
        available = ", ".join(COLORS.keys())
        raise ValueError(
            f"Unknown color '{color_name}'. "
            f"Available colors: {available}"
        )

    # Remove surrounding quotes and interpolate variables.
    if (
        len(message) >= 2
        and message[0] == message[-1]
        and message[0] in ("'", '"')
    ):
        message = message[1:-1]

    message = runtime.interpolate(message)

    print(f"\033[{COLORS[color_name]}m{message}\033[0m")