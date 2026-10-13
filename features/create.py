
from engine import syntax

@syntax(r'create\s+([A-Za-z_][A-Za-z0-9_]*)\s+set\s+(.+)')
def create_variable(match, runtime):
    name = match.group(1)
    value = runtime.parse_value(match.group(2))

    runtime.variables[name] = value