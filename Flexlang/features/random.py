
import random as random_module
import re
import engine


# ==========================================
# FLEXLANG RANDOM PLUGIN
# ==========================================

def resolve_value(text, runtime):
    """Convert a FlexLang value into a Python value."""
    text = text.strip()

    # Quoted strings
    if (
        len(text) >= 2
        and text[0] == text[-1]
        and text[0] in ("'", '"')
    ):
        return runtime.interpolate(text[1:-1])

    # Existing variables
    if text in runtime.variables:
        return runtime.variables[text]

    # Boolean values
    if text.lower() == "true":
        return True

    if text.lower() == "false":
        return False

    # Integers and decimals
    try:
        return int(text)
    except ValueError:
        pass

    try:
        return float(text)
    except ValueError:
        pass

    # Fall back to interpolated text
    return runtime.interpolate(text)


def store_value(name, result, runtime):
    """Store a result in the FlexLang runtime."""
    runtime.variables[name] = result
    print(f"{name} = {result}")


# ==========================================
# RANDOM INTEGER
# ==========================================

@engine.syntax(
    r'random\s+number\s+(-?\d+)\s+to\s+(-?\d+)'
)
def random_number(match, runtime):
    minimum = int(match.group(1))
    maximum = int(match.group(2))

    if minimum > maximum:
        raise ValueError(
            "The minimum cannot be greater than the maximum"
        )

    result = random_module.randint(minimum, maximum)
    print(result)

    runtime.variables["random_result"] = result


# ==========================================
# RANDOM DECIMAL
# ==========================================

@engine.syntax(
    r'random\s+decimal\s+(-?\d+(?:\.\d+)?)\s+to\s+(-?\d+(?:\.\d+)?)'
)
def random_decimal(match, runtime):
    minimum = float(match.group(1))
    maximum = float(match.group(2))

    if minimum > maximum:
        raise ValueError(
            "The minimum cannot be greater than the maximum"
        )

    result = random_module.uniform(minimum, maximum)

    print(result)
    runtime.variables["random_result"] = result


# ==========================================
# RANDOM BOOLEAN
# ==========================================

@engine.syntax(r'random\s+boolean')
def random_boolean(match, runtime):
    result = random_module.choice([True, False])

    print(result)
    runtime.variables["random_result"] = result


# ==========================================
# RANDOM CHOICE
# Supports quoted choices:
# random choose "Red" "Blue" "Green"
# ==========================================

@engine.syntax(r'random\s+choose\s+(.+)')
def random_choose(match, runtime):
    text = match.group(1).strip()

    choices = re.findall(
        r'"([^"]*)"|\'([^\']*)\'',
        text
    )

    choices = [
        double_quoted if double_quoted else single_quoted
        for double_quoted, single_quoted in choices
    ]

    if not choices:
        raise ValueError(
            'Provide choices in quotes, e.g. '
            'random choose "Red" "Blue" "Green"'
        )

    result = random_module.choice(choices)

    print(result)
    runtime.variables["random_result"] = result


# ==========================================
# RANDOM VARIABLE
# random set damage to 10 to 25
# ==========================================

@engine.syntax(
    r'random\s+set\s+([A-Za-z_][A-Za-z0-9_]*)\s+to\s+(-?\d+)\s+to\s+(-?\d+)'
)
def random_set_integer(match, runtime):
    name = match.group(1)
    minimum = int(match.group(2))
    maximum = int(match.group(3))

    if minimum > maximum:
        raise ValueError(
            "The minimum cannot be greater than the maximum"
        )

    result = random_module.randint(minimum, maximum)
    store_value(name, result, runtime)


# ==========================================
# RANDOM DECIMAL VARIABLE
# random set luck to decimal 0 to 1
# ==========================================

@engine.syntax(
    r'random\s+set\s+([A-Za-z_][A-Za-z0-9_]*)\s+to\s+decimal\s+(-?\d+(?:\.\d+)?)\s+to\s+(-?\d+(?:\.\d+)?)'
)
def random_set_decimal(match, runtime):
    name = match.group(1)
    minimum = float(match.group(2))
    maximum = float(match.group(3))

    if minimum > maximum:
        raise ValueError(
            "The minimum cannot be greater than the maximum"
        )

    result = random_module.uniform(minimum, maximum)
    store_value(name, result, runtime)


# ==========================================
# RANDOM CHOICE VARIABLE
# random set loot to choose "Sword" "Bow" "Staff"
# ==========================================

@engine.syntax(
    r'random\s+set\s+([A-Za-z_][A-Za-z0-9_]*)\s+to\s+choose\s+(.+)'
)
def random_set_choice(match, runtime):
    name = match.group(1)
    text = match.group(2)

    choices = re.findall(
        r'"([^"]*)"|\'([^\']*)\'',
        text
    )

    choices = [
        double_quoted if double_quoted else single_quoted
        for double_quoted, single_quoted in choices
    ]

    if not choices:
        raise ValueError(
            'Provide quoted choices, e.g. '
            'random set loot to choose "Sword" "Bow"'
        )

    store_value(
        name,
        random_module.choice(choices),
        runtime
    )


# ==========================================
# RANDOM EVENT
# Prints a random event from the supplied choices.
# ==========================================

@engine.syntax(r'random\s+event\s+(.+)')
def random_event(match, runtime):
    text = match.group(1)

    choices = re.findall(
        r'"([^"]*)"|\'([^\']*)\'',
        text
    )

    choices = [
        double_quoted if double_quoted else single_quoted
        for double_quoted, single_quoted in choices
    ]

    if not choices:
        raise ValueError(
            'Provide events in quotes, e.g. '
            'random event "Storm" "Treasure"'
        )

    result = random_module.choice(choices)

    print(f"Random event: {result}")
    runtime.variables["random_event"] = result


print("FlexLang random plugin loaded!")