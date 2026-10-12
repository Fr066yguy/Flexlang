
from engine import syntax
import time
import re

@syntax(r'sleep\s+(.+)')
def sleep_command(match, runtime):
    value = match.group(1).strip()

    # Allow numbers or variables.
    if value in runtime.variables:
        value = runtime.variables[value]

    try:
        seconds = float(value)
    except (ValueError, TypeError):
        raise ValueError(
            "Sleep duration must be a number or numeric variable."
        )

    if seconds < 0:
        raise ValueError("Sleep duration cannot be negative.")

    if seconds > 3600:
        raise ValueError("Maximum sleep duration is 3600 seconds.")

    time.sleep(seconds)