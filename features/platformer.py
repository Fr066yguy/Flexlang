
import re
import engine


def get_world(runtime):
    if not hasattr(runtime, "platformer_world"):
        runtime.platformer_world = {
            "width": 800,
            "height": 450,
            "background": "#182438",
            "player": None,
            "platforms": [],
            "coins": [],
            "enemies": [],
        }
    return runtime.platformer_world


@engine.syntax(r'platformer\.window\s+(\d+)\s+(\d+)')
def set_window(match, runtime):
    world = get_world(runtime)
    world["width"] = max(320, min(1920, int(match.group(1))))
    world["height"] = max(240, min(1080, int(match.group(2))))


@engine.syntax(r'platformer\.background\s+"(#[0-9a-fA-F]{6})"')
def set_background(match, runtime):
    get_world(runtime)["background"] = match.group(1)


@engine.syntax(
    r'platformer\.player\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+"(#[0-9a-fA-F]{6})"'
)
def set_player(match, runtime):
    world = get_world(runtime)
    world["player"] = {
        "x": int(match.group(1)),
        "y": int(match.group(2)),
        "w": int(match.group(3)),
        "h": int(match.group(4)),
        "color": match.group(5),
    }


@engine.syntax(
    r'platformer\.platform\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+"(#[0-9a-fA-F]{6})"'
)
def add_platform(match, runtime):
    get_world(runtime)["platforms"].append({
        "x": int(match.group(1)),
        "y": int(match.group(2)),
        "w": int(match.group(3)),
        "h": int(match.group(4)),
        "color": match.group(5),
    })


@engine.syntax(
    r'platformer\.coin\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+"(#[0-9a-fA-F]{6})"'
)
def add_coin(match, runtime):
    get_world(runtime)["coins"].append({
        "x": int(match.group(1)),
        "y": int(match.group(2)),
        "size": int(match.group(3)),
        "color": match.group(4),
    })


@engine.syntax(
    r'platformer\.enemy\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+"(#[0-9a-fA-F]{6})"'
)
def add_enemy(match, runtime):
    get_world(runtime)["enemies"].append({
        "x": int(match.group(1)),
        "y": int(match.group(2)),
        "w": int(match.group(3)),
        "h": int(match.group(4)),
        "color": match.group(5),
    })


@engine.syntax(r'platformer\.start')
def start_platformer(match, runtime):
    import pygame

    world = get_world(runtime)
    pygame.init()

    width = world["width"]
    height = world["height"]
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("FlexLang Platformer")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 26)

    background = world["background"]
    platforms = [dict(p) for p in world["platforms"]]
    coins = [dict(c, collected=False) for c in world["coins"]]
    enemies = [dict(e, direction=1, start_x=e["x"]) for e in world["enemies"]]

    player = dict(world["player"]) if world["player"] else {
        "x": 50, "y": 50, "w": 32, "h": 42, "color": "#4da6ff"
    }

    px, py = float(player["x"]), float(player["y"])
    pw, ph = player["w"], player["h"]
    speed_y = 0.0
    speed_x = 0.0
    on_ground = False
    score = 0
    alive = True
    game_over = False
    jump_requested = False

    def color(value):
        return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))

    def rect_hits(a, b):
        return a.colliderect(b)

    player_rect = pygame.Rect(int(px), int(py), pw, ph)

    while alive:
        dt = min(clock.tick(60) / 16.6667, 2.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                alive = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    jump_requested = True
                elif event.key == pygame.K_ESCAPE:
                    alive = False
                elif event.key == pygame.K_r and game_over:
                    px, py = float(player["x"]), float(player["y"])
                    speed_y = 0
                    score = 0
                    game_over = False
                    for coin in coins:
                        coin["collected"] = False

        keys = pygame.key.get_pressed()
        if not game_over:
            speed_x = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                speed_x -= 4.5
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                speed_x += 4.5

            px += speed_x * dt
            px = max(0, min(width - pw, px))

            player_rect = pygame.Rect(round(px), round(py), pw, ph)

            # Horizontal collision with platforms
            for platform in platforms:
                wall = pygame.Rect(
                    platform["x"], platform["y"],
                    platform["w"], platform["h"]
                )
                if rect_hits(player_rect, wall):
                    if speed_x > 0:
                        px = wall.left - pw
                    elif speed_x < 0:
                        px = wall.right
                    player_rect.x = round(px)

            if jump_requested and on_ground:
                speed_y = -12.5
                on_ground = False
            jump_requested = False

            speed_y = min(speed_y + 0.55 * dt, 14)
            old_bottom = py + ph
            py += speed_y * dt
            player_rect = pygame.Rect(round(px), round(py), pw, ph)
            on_ground = False

            for platform in platforms:
                floor = pygame.Rect(
                    platform["x"], platform["y"],
                    platform["w"], platform["h"]
                )
                if rect_hits(player_rect, floor):
                    if speed_y >= 0 and old_bottom <= floor.top + 8:
                        py = floor.top - ph
                        speed_y = 0
                        on_ground = True
                    elif speed_y < 0:
                        py = floor.bottom
                        speed_y = 0
                    player_rect.y = round(py)

            # Collect coins
            for coin in coins:
                if coin["collected"]:
                    continue
                size = coin["size"]
                coin_rect = pygame.Rect(
                    coin["x"], coin["y"], size, size
                )
                if rect_hits(player_rect, coin_rect):
                    coin["collected"] = True
                    score += 1

            # Enemies patrol back and forth
            for enemy in enemies:
                enemy["x"] += enemy["direction"] * 1.5 * dt
                if abs(enemy["x"] - enemy["start_x"]) > 65:
                    enemy["direction"] *= -1

                enemy_rect = pygame.Rect(
                    round(enemy["x"]), enemy["y"],
                    enemy["w"], enemy["h"]
                )
                if rect_hits(player_rect, enemy_rect):
                    game_over = True

            if py > height + 100:
                game_over = True

        screen.fill(color(background))

        for platform in platforms:
            pygame.draw.rect(
                screen, color(platform["color"]),
                (platform["x"], platform["y"],
                 platform["w"], platform["h"])
            )

        for coin in coins:
            if not coin["collected"]:
                size = coin["size"]
                pygame.draw.circle(
                    screen, color(coin["color"]),
                    (coin["x"] + size // 2, coin["y"] + size // 2),
                    size // 2
                )

        for enemy in enemies:
            pygame.draw.rect(
                screen, color(enemy["color"]),
                (round(enemy["x"]), enemy["y"],
                 enemy["w"], enemy["h"])
            )

        pygame.draw.rect(
            screen, color(player["color"]),
            (round(px), round(py), pw, ph),
            border_radius=4,
        )

        score_text = font.render(f"Coins: {score}", True, (255, 255, 255))
        screen.blit(score_text, (12, 10))

        if game_over:
            overlay = font.render(
                "GAME OVER  -  Press R to restart or ESC to exit",
                True, (255, 255, 255)
            )
            screen.blit(
                overlay,
                (max(8, width // 2 - overlay.get_width() // 2), height // 2)
            )

        pygame.display.flip()

    pygame.quit()
    print(f"Platformer closed. Coins collected: {score}")