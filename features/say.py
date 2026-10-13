
from engine import syntax


@syntax(r'say\s+(.+)')
def say(match, runtime):
    text = runtime.parse_value(match.group(1))
    print(runtime.interpolate(str(text)))