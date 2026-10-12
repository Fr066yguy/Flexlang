
import re
import pygame
import engine


# ==========================================
# FLEXLANG 2D GAME ENGINE
# ==========================================

def get_state(runtime):
    if not hasattr(runtime, "game2d"):
        runtime.game2d = {
            "title": "FlexLang Game",
            "width": 800,
            "height": 600,
            "background": (32, 40, 56),
            "players": {},
            "fps": 60,
            "update_source": "",
        }

    return runtime.game2d


def parse_color(text, runtime):
    text = runtime.interpolate(text.strip())

    if text.startswith("#"):
        text = text[1:]

    if len(text) == 3:
        text = "".join(char * 2 for char in text)

    if len(text) != 6:
        raise ValueError("Color must be #RRGGBB or #RGB")

    try:
        return tuple(
            int(text[index:index + 2], 16)
            for index in (0, 2, 4)
        )
    except ValueError:
        raise ValueError(f"Invalid color: {text}")


def get_player(name, runtime):
    players = get_state(runtime)["players"]

    if name not in players:
        raise ValueError(f"Player '{name}' does not exist")

    return players[name]


# ==========================================
# WINDOW COMMANDS
# ==========================================

@engine.syntax(r'window\.new\s+"([^"]+)"\s+(\d+)\s+(\d+)')
def window_new(match, runtime):
    state = get_state(runtime)

    state["title"] = match.group(1)
    state["width"] = int(match.group(2))
    state["height"] = int(match.group(3))

    if state["width"] < 1 or state["height"] < 1:
        raise ValueError("Window dimensions must be positive")


@engine.syntax(r'window\.background\s+(.+)')
def window_background(match, runtime):
    get_state(runtime)["background"] = parse_color(
        match.group(1), runtime
    )


# ==========================================
# PLAYER COMMANDS
# ==========================================

@engine.syntax(r'player\.new\s+"([^"]+)"\s+(-?\d+)\s+(-?\d+)')
def player_new(match, runtime):
    name = match.group(1)

    get_state(runtime)["players"][name] = {
        "x": float(match.group(2)),
        "y": float(match.group(3)),
        "width": 40,
        "height": 40,
        "color": (0, 255, 136),
    }


@engine.syntax(r'player\.color\s+"([^"]+)"\s+(.+)')
def player_color(match, runtime):
    player = get_player(match.group(1), runtime)
    player["color"] = parse_color(match.group(2), runtime)


@engine.syntax(r'player\.size\s+"([^"]+)"\s+(\d+)\s+(\d+)')
def player_size(match, runtime):
    player = get_player(match.group(1), runtime)

    player["width"] = int(match.group(2))
    player["height"] = int(match.group(3))


@engine.syntax(
    r'player\.move\s+"([^"]+)"\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)'
)
def player_move(match, runtime):
    player = get_player(match.group(1), runtime)

    player["x"] += float(match.group(2))
    player["y"] += float(match.group(3))


# ==========================================
# KEYBOARD INPUT
# ==========================================

KEY_MAP = {
    "a": pygame.K_a,
    "b": pygame.K_b,
    "c": pygame.K_c,
    "d": pygame.K_d,
    "e": pygame.K_e,
    "f": pygame.K_f,
    "g": pygame.K_g,
    "h": pygame.K_h,
    "i": pygame.K_i,
    "j": pygame.K_j,
    "k": pygame.K_k,
    "l": pygame.K_l,
    "m": pygame.K_m,
    "n": pygame.K_n,
    "o": pygame.K_o,
    "p": pygame.K_p,
    "q": pygame.K_q,
    "r": pygame.K_r,
    "s": pygame.K_s,
    "t": pygame.K_t,
    "u": pygame.K_u,
    "v": pygame.K_v,
    "w": pygame.K_w,
    "x": pygame.K_x,
    "y": pygame.K_y,
    "z": pygame.K_z,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "space": pygame.K_SPACE,
    "enter": pygame.K_RETURN,
    "escape": pygame.K_ESCAPE,
}


@engine.syntax(r'input\.key\s+"([^"]+)"\s+([A-Za-z]+)')
def input_key(match, runtime):
    player_name = match.group(1)
    key_name = match.group(2).lower()

    if key_name not in KEY_MAP:
        raise ValueError(f"Unknown key: {key_name}")

    # The game loop refreshes these variables every frame.
    pressed_keys = getattr(runtime, "_game_pressed_keys", None)

    pressed = (
        bool(pressed_keys[KEY_MAP[key_name]])
        if pressed_keys is not None
        else False
    )

    runtime.variables["key_" + key_name] = pressed
    runtime.variables[
        "key_" + player_name + "_" + key_name
    ] = pressed


# ==========================================
# FPS COMMAND
# ==========================================

@engine.syntax(r'game\.fps\s+(\d+)')
def game_fps(match, runtime):
    fps = int(match.group(1))

    if not 1 <= fps <= 1000:
        raise ValueError("FPS must be between 1 and 1000")

    get_state(runtime)["fps"] = fps


# ==========================================
# CONDITION EVALUATOR
# ==========================================

def evaluate_condition(condition, runtime):
    condition = condition.strip()

    for operator in ("==", "!=", ">=", "<=", ">", "<"):
        parts = condition.split(operator, 1)

        if len(parts) != 2:
            continue

        left_text = parts[0].strip()
        right_text = parts[1].strip()

        def resolve(text):
            if text in runtime.variables:
                return runtime.variables[text]

            if (
                len(text) >= 2
                and text[0] == text[-1]
                and text[0] in ('"', "'")
            ):
                return runtime.interpolate(text[1:-1])

            if text.lower() == "true":
                return True

            if text.lower() == "false":
                return False

            if text.lower() == "none":
                return None

            try:
                return int(text)
            except ValueError:
                pass

            try:
                return float(text)
            except ValueError:
                pass

            return runtime.interpolate(text)

        left = resolve(left_text)
        right = resolve(right_text)

        if operator == "==":
            return left == right
        if operator == "!=":
            return left != right
        if operator == ">":
            return left > right
        if operator == "<":
            return left < right
        if operator == ">=":
            return left >= right
        if operator == "<=":
            return left <= right

    value = runtime.variables.get(condition, condition)

    if isinstance(value, bool):
        return value

    if str(value).lower() == "true":
        return True

    if str(value).lower() == "false":
        return False

    raise ValueError(f"Invalid condition: {condition}")


# ==========================================
# GAME UPDATE BLOCK
# ==========================================

@engine.source_handler
def game_update_block(source, runtime, run_lines):
    lines = source.splitlines()
    start = None

    for index, line in enumerate(lines):
        if line.strip().lower() == "game.update":
            start = index
            break

    if start is None:
        return False

    depth = 1
    end = None

    for index in range(start + 1, len(lines)):
        line = lines[index].strip().lower()

        if line == "game.update":
            depth += 1
        elif line == "end":
            depth -= 1

            if depth == 0:
                end = index
                break

    if end is None:
        raise ValueError(
            "game.update is missing its closing end"
        )

    update_lines = lines[start + 1:end]
    get_state(runtime)["update_source"] = "\n".join(update_lines)

    remaining = lines[:start] + lines[end + 1:]
    remaining_source = "\n".join(remaining)

    if remaining_source.strip():
        engine.run(remaining_source, runtime)

    return True


# ==========================================
# UPDATE INTERPRETER
# Handles single-line if/then commands.
# ==========================================

def execute_update(source, runtime):
    for original_line in source.splitlines():
        line = original_line.strip()

        if not line or line.startswith("#"):
            continue

        match = re.fullmatch(
            r'if\s+(.+?)\s+then\s+(.+)',
            line,
            re.IGNORECASE
        )

        if match:
            try:
                if evaluate_condition(match.group(1), runtime):
                    engine.run(
                        match.group(2),
                        runtime,
                        _skip_source_handlers=True
                    )
            except Exception as error:
                print(f"Game update error: {error}")

            continue

        if line.lower() == "end":
            continue

        engine.run(
            line,
            runtime,
            _skip_source_handlers=True
        )


# ==========================================
# GAME LOOP
# ==========================================

@engine.syntax(r'game\.start')
def game_start(match, runtime):
    state = get_state(runtime)

    pygame.init()

    try:
        screen = pygame.display.set_mode(
            (state["width"], state["height"])
        )
        pygame.display.set_caption(state["title"])

        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)
        running = True

        while running:
            # Process window and keyboard events first.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    running = False

            if not running:
                break

            # Refresh input state every frame.
            pygame.event.pump()
            runtime._game_pressed_keys = pygame.key.get_pressed()

            # Execute FlexLang game logic.
            execute_update(state["update_source"], runtime)

            # Keep players inside the window.
            for player in state["players"].values():
                max_x = max(
                    0, state["width"] - player["width"]
                )
                max_y = max(
                    0, state["height"] - player["height"]
                )

                player["x"] = max(
                    0, min(player["x"], max_x)
                )
                player["y"] = max(
                    0, min(player["y"], max_y)
                )

            # Draw the scene.
            screen.fill(state["background"])

            for player in state["players"].values():
                pygame.draw.rect(
                    screen,
                    player["color"],
                    pygame.Rect(
                        round(player["x"]),
                        round(player["y"]),
                        player["width"],
                        player["height"]
                    )
                )

            help_surface = font.render(
                "WASD / Arrows: Move    ESC: Quit",
                True,
                (240, 240, 245)
            )
            screen.blit(help_surface, (12, 12))

            pygame.display.flip()
            clock.tick(state["fps"])

    finally:
        if hasattr(runtime, "_game_pressed_keys"):
            del runtime._game_pressed_keys

        pygame.quit()

    print("FlexLang game closed.")