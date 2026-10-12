
import re
import engine


def get_list(runtime, name):
    value = runtime.variables.get(name)

    if not isinstance(value, list):
        raise ValueError(f"'{name}' is not a list")

    return value


def get_value(runtime, raw):
    return runtime.parse_value(runtime.interpolate(raw.strip()))


def list_command(pattern):
    def register(function):
        @engine.syntax(pattern)
        def handler(match, runtime):
            try:
                function(match, runtime)
            except Exception as exc:
                print(f"FlexLang list error: {exc}")

        return handler
    return register


@list_command(r"list\.create\s+([A-Za-z_]\w*)")
def create_list(match, runtime):
    name = match.group(1)
    runtime.variables[name] = []
    print(f"Created list: {name}")


@list_command(r"list\.add\s+([A-Za-z_]\w*)\s+(.+)")
def add_item(match, runtime):
    name, raw = match.groups()
    get_list(runtime, name).append(get_value(runtime, raw))
    print(f"Added item to {name}")


@list_command(r"list\.show\s+([A-Za-z_]\w*)")
def show_list(match, runtime):
    name = match.group(1)
    items = get_list(runtime, name)
    print(f"{name} = {items}")


@list_command(r"list\.length\s+([A-Za-z_]\w*)")
def list_length(match, runtime):
    name = match.group(1)
    print(len(get_list(runtime, name)))


@list_command(
    r"list\.length\s+([A-Za-z_]\w*)\s+into\s+([A-Za-z_]\w*)"
)
def list_length_into(match, runtime):
    name, target = match.groups()
    runtime.variables[target] = len(get_list(runtime, name))
    print(f"{target} = {runtime.variables[target]}")


@list_command(
    r"list\.get\s+([A-Za-z_]\w*)\s+(\d+)\s+into\s+([A-Za-z_]\w*)"
)
def get_item(match, runtime):
    name, index, target = match.groups()
    items = get_list(runtime, name)
    index = int(index)

    if index >= len(items):
        raise IndexError(f"Index {index} is out of range")

    runtime.variables[target] = items[index]
    print(f"{target} = {items[index]}")


@list_command(
    r"list\.set\s+([A-Za-z_]\w*)\s+(\d+)\s+(.+)"
)
def set_item(match, runtime):
    name, index, raw = match.groups()
    items = get_list(runtime, name)
    index = int(index)

    if index >= len(items):
        raise IndexError(f"Index {index} is out of range")

    items[index] = get_value(runtime, raw)
    print(f"Updated {name}[{index}]")


@list_command(
    r"list\.remove\s+([A-Za-z_]\w*)\s+(\d+)"
)
def remove_item(match, runtime):
    name, index = match.groups()
    items = get_list(runtime, name)
    index = int(index)

    if index >= len(items):
        raise IndexError(f"Index {index} is out of range")

    removed = items.pop(index)
    print(f"Removed {removed} from {name}")


@list_command(r"list\.clear\s+([A-Za-z_]\w*)")
def clear_list(match, runtime):
    name = match.group(1)
    get_list(runtime, name).clear()
    print(f"Cleared list: {name}")