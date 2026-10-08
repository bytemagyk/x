import pygame
from constants import *

FONT_SIZE = 20
MSG_LINES = 6

def init_fonts():
    pygame.font.init()
    return {
        'small': pygame.font.SysFont('monospace', FONT_SIZE),
        'med':   pygame.font.SysFont('monospace', FONT_SIZE + 4),
        'big':   pygame.font.SysFont('monospace', 28),
        'title': pygame.font.SysFont('monospace', 48, bold=True),
    }


def draw_text(surf, fonts, text, x, y, color=WHITE, size='small'):
    s = fonts[size].render(str(text), True, color)
    surf.blit(s, (x, y))
    return s.get_height()


def draw_bar(surf, x, y, w, h, val, max_val, color, bg=DGRAY):
    pygame.draw.rect(surf, bg, (x, y, w, h))
    if max_val > 0:
        fill = int(w * val / max_val)
        pygame.draw.rect(surf, color, (x, y, fill, h))
    pygame.draw.rect(surf, GRAY, (x, y, w, h), 1)


def draw_hud(surf, fonts, player):
    x, y = SIDEBAR_X + 8, 8
    lh = FONT_SIZE + 3

    draw_text(surf, fonts, f"{player.cls_name}  Depth:{player.depth}", x, y, YELLOW, 'med')
    y += lh + 6

    draw_text(surf, fonts, f"HP: {player.stats.hp}/{player.stats.max_hp}", x, y, WHITE)
    y += lh
    draw_bar(surf, x, y, PANEL_W - 20, 10, player.stats.hp, player.stats.max_hp, RED)
    y += 14

    draw_text(surf, fonts, f"EXP: {player.stats.exp}/{player.stats.exp_next}  Lv:{player.stats.lvl}", x, y, GREEN)
    y += lh
    draw_bar(surf, x, y, PANEL_W - 20, 8, player.stats.exp, player.stats.exp_next, BLUE)
    y += 12

    draw_text(surf, fonts, f"STR:{player.stats.str_}  DEX:{player.stats.dex}  Gold:{player.gold}", x, y, YELLOW)
    y += lh

    hunger_color = {
        'full': GREEN, 'hungry': YELLOW, 'starving': RED
    }.get(player.hunger_state, WHITE)
    draw_text(surf, fonts, f"Hunger: {player.hunger_state.upper()}", x, y, hunger_color)
    y += lh + 4

    # Equipment
    draw_text(surf, fonts, "── Equipment ──", x, y, GRAY)
    y += lh
    wname = player.weapon.display_name() if player.weapon else "none"
    aname = player.armor.display_name() if player.armor else "none"
    draw_text(surf, fonts, f"W: {wname[:22]}", x, y, YELLOW)
    y += lh
    draw_text(surf, fonts, f"A: {aname[:22]}", x, y, BLUE)
    y += lh
    if player.ring1:
        draw_text(surf, fonts, f"R1:{player.ring1.display_name()[:20]}", x, y, PURPLE)
        y += lh
    if player.ring2:
        draw_text(surf, fonts, f"R2:{player.ring2.display_name()[:20]}", x, y, PURPLE)
        y += lh
    if player.missile_slot:
        draw_text(surf, fonts, f"M: {player.missile_slot.display_name()[:20]}", x, y, ORANGE)
        y += lh

    # Buffs
    if player.stats.buffs:
        y += 4
        draw_text(surf, fonts, "── Buffs ──", x, y, GRAY)
        y += lh
        for buff, turns in player.stats.buffs.items():
            col = RED if buff in ('poison','bleed','paralysis') else CYAN
            draw_text(surf, fonts, f"{buff}({turns})", x, y, col)
            y += lh

    return y


def draw_messages(surf, fonts, messages, y_start):
    recent = messages[-MSG_LINES:]
    y = y_start
    for i, msg in enumerate(recent):
        alpha = 255 - (len(recent) - 1 - i) * 40
        col = (min(255, alpha), min(255, alpha), min(255, alpha))
        draw_text(surf, fonts, msg[:55], SIDEBAR_X + 8, y, col)
        y += FONT_SIZE + 3


def draw_map(surf, fonts, dungeon, player, cam_x, cam_y, sprites=None):
    sprites = sprites or {}
    wall_spr  = sprites.get('wall')
    floor_spr = sprites.get('floor')
    view_w = SIDEBAR_X // TILE_SIZE
    view_h = SCREEN_H // TILE_SIZE

    for sx in range(view_w + 1):
        for sy in range(view_h + 1):
            mx = sx + cam_x
            my = sy + cam_y
            if not (0 <= mx < dungeon.width and 0 <= my < dungeon.height):
                continue
            px = sx * TILE_SIZE
            py = sy * TILE_SIZE

            if dungeon.lit[mx][my]:
                tile = dungeon.tiles[mx][my]
                color = TILE_COLORS.get(tile, BLACK)
                if tile == WALL and wall_spr:
                    surf.blit(wall_spr, (px, py))
                elif tile == FLOOR and floor_spr:
                    surf.blit(floor_spr, (px, py))
                else:
                    pygame.draw.rect(surf, color, (px, py, TILE_SIZE, TILE_SIZE))
                # Trap indicator
                if (mx, my) in dungeon.traps and tile == FLOOR:
                    pygame.draw.rect(surf, (180, 50, 50), (px+12, py+12, 8, 8))
                char = TILE_CHARS.get(tile, '?')
                if tile not in (WALL, FLOOR):
                    draw_text(surf, fonts, char, px + 8, py + 8, _dim(color, 1.4))
            elif dungeon.visited[mx][my]:
                tile = dungeon.tiles[mx][my]
                color = _dim(TILE_COLORS.get(tile, BLACK), 0.4)
                if tile == WALL and wall_spr:
                    dark = wall_spr.copy()
                    dark.set_alpha(80)
                    surf.blit(dark, (px, py))
                elif tile == FLOOR and floor_spr:
                    dark = floor_spr.copy()
                    dark.set_alpha(80)
                    surf.blit(dark, (px, py))
                else:
                    pygame.draw.rect(surf, color, (px, py, TILE_SIZE, TILE_SIZE))
                    char = TILE_CHARS.get(tile, '?')
                    draw_text(surf, fonts, char, px + 8, py + 8, _dim(color, 0.6))
            else:
                pygame.draw.rect(surf, BLACK, (px, py, TILE_SIZE, TILE_SIZE))

    # Items
    for ix, iy, item in dungeon.items:
        if dungeon.lit[ix][iy]:
            sx = (ix - cam_x) * TILE_SIZE
            sy = (iy - cam_y) * TILE_SIZE
            if 0 <= sx < SIDEBAR_X and 0 <= sy < SCREEN_H:
                draw_text(surf, fonts, item.char, sx + 8, sy + 8, item.color)

    # Enemies
    for enemy in dungeon.enemies:
        if not enemy.is_alive():
            continue
        show = dungeon.lit[enemy.x][enemy.y]
        if not show and player.stats.has_buff('mind_vision'):
            show = True
        if show:
            sx = (enemy.x - cam_x) * TILE_SIZE
            sy = (enemy.y - cam_y) * TILE_SIZE
            if 0 <= sx < SIDEBAR_X and 0 <= sy < SCREEN_H:
                pygame.draw.rect(surf, (80, 20, 20), (sx, sy, TILE_SIZE, TILE_SIZE))
                sprite = (sprites or {}).get(enemy.name)
                if sprite:
                    surf.blit(sprite, (sx, sy))
                else:
                    draw_text(surf, fonts, enemy.char, sx + 8, sy + 8, enemy.color)
                # HP bar
                draw_bar(surf, sx, sy + TILE_SIZE - 4, TILE_SIZE, 4,
                         enemy.stats.hp, enemy.stats.max_hp, RED, (40, 0, 0))

    # Player
    px = (player.x - cam_x) * TILE_SIZE
    py = (player.y - cam_y) * TILE_SIZE
    player_spr = sprites.get('player')
    if player_spr:
        surf.blit(player_spr, (px, py))
    else:
        pygame.draw.rect(surf, (30, 60, 120), (px, py, TILE_SIZE, TILE_SIZE))
        draw_text(surf, fonts, '@', px + 8, py + 8, WHITE)


def _dim(color, factor):
    return tuple(min(255, max(0, int(c * factor))) for c in color)


def draw_inventory(surf, fonts, player, selected=0):
    surf.fill((20, 20, 30))
    draw_text(surf, fonts, "INVENTORY  (E=use/equip  D=drop  ESC=close)", 20, 10, YELLOW, 'med')
    draw_text(surf, fonts, f"Gold: {player.gold}", 20, 36, YELLOW)

    items = player.inventory
    for i, item in enumerate(items):
        y = 60 + i * 22
        bg = (50, 50, 80) if i == selected else (20, 20, 30)
        pygame.draw.rect(surf, bg, (10, y, SCREEN_W - PANEL_W - 20, 20))
        equipped = item in [player.weapon, player.armor, player.ring1, player.ring2, player.missile_slot]
        eq_str = " [E]" if equipped else ""
        draw_text(surf, fonts, f"{chr(97+i)}) {item.display_name()}{eq_str}", 16, y + 2, item.color)

    # Item detail
    if 0 <= selected < len(items):
        item = items[selected]
        dx = SCREEN_W - PANEL_W + 10
        dy = 60
        draw_text(surf, fonts, item.display_name(), dx, dy, item.color, 'med')
        dy += 24
        if hasattr(item, 'min_dmg'):
            draw_text(surf, fonts, f"Damage: {item.min_dmg+item.level}-{item.max_dmg+item.level}", dx, dy, WHITE)
            dy += 18
        if hasattr(item, 'defense'):
            draw_text(surf, fonts, f"Defense: {item.dr()}", dx, dy, WHITE)
            dy += 18
        if hasattr(item, 'nutrition'):
            draw_text(surf, fonts, f"Nutrition: {item.nutrition}", dx, dy, WHITE)
            dy += 18
        if hasattr(item, 'charges'):
            draw_text(surf, fonts, f"Charges: {item.charges}/{item.max_charges}", dx, dy, WHITE)
            dy += 18
        if item.cursed and item.identified:
            draw_text(surf, fonts, "CURSED", dx, dy, RED)


def draw_class_select(surf, fonts):
    surf.fill(BLACK)
    draw_text(surf, fonts, "PIXEL DUNGEON", SCREEN_W//2 - 180, 80, YELLOW, 'title')
    draw_text(surf, fonts, "Choose your class:", SCREEN_W//2 - 120, 180, WHITE, 'big')
    classes = list(CLASSES_INFO.items())
    for i, (name, desc) in enumerate(classes):
        y = 240 + i * 80
        col = YELLOW if i == 0 else WHITE
        draw_text(surf, fonts, f"{i+1}. {name}", SCREEN_W//2 - 200, y, col, 'med')
        draw_text(surf, fonts, desc, SCREEN_W//2 - 200, y + 22, GRAY)
    draw_text(surf, fonts, "Press 1-4 to select", SCREEN_W//2 - 120, 580, GRAY)


CLASSES_INFO = {
    'Warrior':  "High HP & STR. Starts with Short Sword & Mail Armor.",
    'Mage':     "Starts with a Wand of Magic Missile. Identifies wands on use.",
    'Rogue':    "High DEX. Detects traps. Starts with Dagger.",
    'Huntress': "Ranged specialist. Starts with Boomerang.",
}


def draw_game_over(surf, fonts, player, won=False):
    surf.fill(BLACK)
    msg = "YOU WIN!" if won else "YOU DIED"
    col = YELLOW if won else RED
    draw_text(surf, fonts, msg, SCREEN_W//2 - 120, 150, col, 'title')
    draw_text(surf, fonts, f"Class: {player.cls_name}  Depth: {player.depth}", SCREEN_W//2-150, 260, WHITE, 'med')
    draw_text(surf, fonts, f"Level: {player.stats.lvl}  Gold: {player.gold}", SCREEN_W//2-150, 295, YELLOW, 'med')
    draw_text(surf, fonts, f"Turns: {player.turns}", SCREEN_W//2-150, 330, WHITE, 'med')
    draw_text(surf, fonts, "Press R to restart or Q to quit", SCREEN_W//2-160, 420, GRAY, 'med')


CONTROLS = [
    ("Movement",  "Arrow keys  or  H J K L"),
    ("Diagonal",  "Y U B N"),
    ("Pick up",   "G"),
    ("Inventory", "I  or  Tab"),
    ("Use/Equip", "E  (in inventory)"),
    ("Drop",      "D  (in inventory)"),
    ("Throw",     "T  — nearest visible enemy"),
    ("Stairs down", ">  or  Period"),
    ("Stairs up",   "<  or  Comma"),
    ("Wait/Rest",   "S"),
    ("Settings",    "F1"),
    ("Close menu",  "ESC"),
]

def draw_settings(surf, fonts):
    surf.fill((15, 15, 25))
    draw_text(surf, fonts, "SETTINGS", SCREEN_W // 2 - 80, 40, YELLOW, 'big')
    draw_text(surf, fonts, "Controls", SCREEN_W // 2 - 55, 90, GRAY, 'med')
    pygame.draw.line(surf, DGRAY, (SCREEN_W // 2 - 200, 115), (SCREEN_W // 2 + 200, 115), 1)

    for i, (action, keys) in enumerate(CONTROLS):
        y = 128 + i * 30
        draw_text(surf, fonts, action, SCREEN_W // 2 - 220, y, WHITE)
        draw_text(surf, fonts, keys,   SCREEN_W // 2 + 10,  y, CYAN)

    draw_text(surf, fonts, "ESC — back", SCREEN_W // 2 - 40, SCREEN_H - 40, GRAY)


def draw_depth_transition(surf, fonts, depth):
    surf.fill(BLACK)
    draw_text(surf, fonts, f"Depth {depth}", SCREEN_W//2 - 80, SCREEN_H//2 - 20, YELLOW, 'big')
    pygame.display.flip()
    pygame.time.wait(800)
