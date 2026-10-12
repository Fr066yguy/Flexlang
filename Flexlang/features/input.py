
from engine import syntax

@syntax(r'input\s+([A-Za-z_]\w*)\s+(.+)')
def input_command(match, runtime):
    name = match.group(1)
    prompt = match.group(2).strip()

    # Remove surrounding quotes from the prompt.
    if (
        len(prompt) >= 2
        and prompt[0] == prompt[-1]
        and prompt[0] in ("'", '"')
    ):
        prompt = prompt[1:-1]

    prompt = runtime.interpolate(prompt)

    answer = input(prompt)

    runtime.variables[name] = answer