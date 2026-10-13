
import random
import pygame
import engine


# ==========================================
# SNAKE GAME PLUGIN
# ==========================================

def get_snake_state(runtime):
    if not hasattr(runtime, "snake_game"):
        runtime.snake_game = {
            "cell": 20,
            "snake": [(10, 10), (9, 10), (8, 10)],
            "direction": (1, 0),
            "next_direction": (1, 0),
            "food": (15, 10),
            "score": 0,
            "game_over": False,
            "move_timer": 0,
            "move_delay": 0.12,
            "last_time": 0,
        }
    return runtime.snake_game


@engine.syntax(r'snake\.new(?:\s+(\d+)\s+(\d+))?')
def snake_new(match, runtime):
    state = get_snake_state(runtime)
    game = engine.get_state(runtime) if hasattr(engine, "get_state") else None

    width = int(match.group(1) or 800)
    height = int(match.group(2) or 600)

    state["cell"] = 20
    state["snake"] = [(5, 5), (4, 5), (3, 5)]
    state["direction"] = (1, 0)
    state["next_direction"] = (1, 0)
    state["score"] = 0
    state["game_over"] = False
    state["move_timer"] = 0
    state["last_time"] = 0
    state["width"] = width
    state["height"] = height
    state["food"] = random_food(state)


def random_food(state):
    cols = max(1, state["width"] // state["cell"])
    rows = max(1, state["height"] // state["cell"])

    free = [
        (x, y)
        for x in range(cols)
        for y in range(rows)
        if (x, y) not in state["snake"]
    ]

    return random.choice(free) if free else None


@engine.syntax(r'snake\.speed\s+(\d+(?:\.\d+)?)')
def snake_speed(match, runtime):
    speed = float(match.group(1))
    if speed <= 0:
        raise ValueError("Snake speed must be positive")

    get_snake_state(runtime)["move_delay"] = 1 / speed


@engine.syntax(r'snake\.start')
def snake_start(match, runtime):
    state = get_snake_state(runtime)
    cell = state["cell"]

    pygame.init()

    try:
        screen = pygame.display.set_mode(
            (state["width"], state["height"])
        )
        pygame.display.set_caption("FlexLang Snake")

        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 30)
        small_font = pygame.font.Font(None, 22)

        state["last_time"] = pygame.time.get_ticks() / 1000
        running = True

        while running:
            dt = clock.tick(60) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    elif event.key == pygame.K_UP:
                        if state["direction"] != (0, 1):
                            state["next_direction"] = (0, -1)

                    elif event.key == pygame.K_DOWN:
                        if state["direction"] != (0, -1):
                            state["next_direction"] = (0, 1)

                    elif event.key == pygame.K_LEFT:
                        if state["direction"] != (1, 0):
                            state["next_direction"] = (-1, 0)

                    elif event.key == pygame.K_RIGHT:
                        if state["direction"] != (-1, 0):
                            state["next_direction"] = (1, 0)

                    elif event.key == pygame.K_SPACE:
                        if state["game_over"]:
                            state["snake"] = [
                                (5, 5), (4, 5), (3, 5)
                            ]
                            state["direction"] = (1, 0)
                            state["next_direction"] = (1, 0)
                            state["score"] = 0
                            state["game_over"] = False
                            state["food"] = random_food(state)
                            state["move_timer"] = 0

            if not state["game_over"]:
                state["move_timer"] += dt

                while (
                    state["move_timer"] >= state["move_delay"]
                    and not state["game_over"]
                ):
                    state["move_timer"] -= state["move_delay"]
                    state["direction"] = state["next_direction"]

                    dx, dy = state["direction"]
                    hx, hy = state["snake"][0]
                    new_head = (hx + dx, hy + dy)

                    cols = state["width"] // cell
                    rows = state["height"] // cell

                    eating = new_head == state["food"]
                    body = (
                        state["snake"]
                        if eating
                        else state["snake"][:-1]
                    )

                    if (
                        new_head[0] < 0
                        or new_head[1] < 0
                        or new_head[0] >= cols
                        or new_head[1] >= rows
                        or new_head in body
                    ):
                        state["game_over"] = True
                        break

                    state["snake"].insert(0, new_head)

                    if eating:
                        state["score"] += 1
                        state["food"] = random_food(state)

                        if state["food"] is None:
                            state["game_over"] = True
                    else:
                        state["snake"].pop()

            # Draw background and grid.
            screen.fill((12, 18, 28))

            for x in range(0, state["width"], cell):
                pygame.draw.line(
                    screen, (23, 31, 44),
                    (x, 0), (x, state["height"])
                )

            for y in range(0, state["height"], cell):
                pygame.draw.line(
                    screen, (23, 31, 44),
                    (0, y), (state["width"], y)
                )

            # Draw food.
            if state["food"] is not None:
                fx, fy = state["food"]
                pygame.draw.rect(
                    screen, (255, 75, 95),
                    (fx * cell + 2, fy * cell + 2,
                     cell - 4, cell - 4),
                    border_radius=5
                )

            # Draw snake.
            for index, (sx, sy) in enumerate(state["snake"]):
                snake_color = (
                    (0, 255, 150)
                    if index == 0
                    else (0, max(90, 200 - index), 110)
                )

                pygame.draw.rect(
                    screen,
                    snake_color,
                    (sx * cell + 1, sy * cell + 1,
                     cell - 2, cell - 2),
                    border_radius=4
                )

            score_text = font.render(
                f"Score: {state['score']}",
                True, (240, 245, 255)
            )
            screen.blit(score_text, (12, 10))

            controls = small_font.render(
                "ARROWS: Move    SPACE: Restart after game over    ESC: Quit",
                True, (160, 175, 195)
            )
            screen.blit(
                controls,
                (12, state["height"] - 25)
            )

            if state["game_over"]:
                overlay = pygame.Surface(
                    (state["width"], state["height"]),
                    pygame.SRCALPHA
                )
                overlay.fill((0, 0, 0, 165))
                screen.blit(overlay, (0, 0))

                title = font.render(
                    "GAME OVER",
                    True, (255, 80, 100)
                )
                restart = small_font.render(
                    "Press SPACE to play again",
                    True, (255, 255, 255)
                )

                screen.blit(
                    title,
                    title.get_rect(
                        center=(
                            state["width"] // 2,
                            state["height"] // 2 - 20
                        )
                    )
                )
                screen.blit(
                    restart,
                    restart.get_rect(
                        center=(
                            state["width"] // 2,
                            state["height"] // 2 + 18
                        )
                    )
                )

            pygame.display.flip()

    finally:
        pygame.quit()

    print("Snake closed.")