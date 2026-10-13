import pygame
from constants import *

FONT_SIZE = 20
MSG_LINES = 6
QUICKSLOT_COUNT = 4
MINIMAP_SIZE = 120  # px square in sidebar

def init_fonts():
    pygame.font.init()
    return {
        'small': pygame.font.SysFont('monospace', FONT_SIZE),
        'med':   pygame.font.SysFont('monospace', FONT_SIZE + 4),
        'big':   pygame.font.SysFont('monospace', 28),
        'title': pygame.font.SysFont('monospace', 48, bold=True),
        'tiny':  pygame.font.SysFont('monospace', FONT_SIZE - 4),
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


# ── HUD ───────────────────────────────────────────────────────────────────────
def draw_hud(surf, fonts, player):
    x, y = SIDEBAR_X + 8, 8
    lh = FONT_SIZE + 4

    draw_text(surf, fonts, f"{player.cls_name}  Depth:{player.depth}", x, y, YELLOW, 'med')
    y += lh + 4

    draw_text(surf, fonts, f"HP: {player.stats.hp}/{player.stats.max_hp}", x, y, WHITE)
    y += lh
    draw_bar(surf, x, y, PANEL_W - 20, 12, player.stats.hp, player.stats.max_hp, RED)
    y += 16

    draw_text(surf, fonts, f"EXP: {player.stats.exp}/{player.stats.exp_next}  Lv:{player.stats.lvl}", x, y, GREEN)
    y += lh
    draw_bar(surf, x, y, PANEL_W - 20, 8, player.stats.exp, player.stats.exp_next, BLUE)
    y += 14

    draw_text(surf, fonts, f"STR:{player.stats.str_}  DEX:{player.stats.dex}  Gold:{player.gold}", x, y, YELLOW)
    y += lh

    hunger_color = {'full': GREEN, 'hungry': YELLOW, 'starving': RED}.get(player.hunger_state, WHITE)
    draw_text(surf, fonts, f"Hunger: {player.hunger_state.upper()}", x, y, hunger_color)
    y += lh + 4

    draw_text(surf, fonts, "── Equipment ──", x, y, GRAY)
    y += lh
    wname = player.weapon.display_name() if player.weapon else "none"
    aname = player.armor.display_name()  if player.armor  else "none"
    draw_text(surf, fonts, f"W: {wname[:24]}", x, y, YELLOW); y += lh
    draw_text(surf, fonts, f"A: {aname[:24]}", x, y, BLUE);   y += lh
    if player.ring1:
        draw_text(surf, fonts, f"R1:{player.ring1.display_name()[:22]}", x, y, PURPLE); y += lh
    if player.ring2:
        draw_text(surf, fonts, f"R2:{player.ring2.display_name()[:22]}", x, y, PURPLE); y += lh
    if player.missile_slot:
        draw_text(surf, fonts, f"M: {player.missile_slot.display_name()[:22]}", x, y, ORANGE); y += lh

    if player.stats.buffs:
        y += 4
        draw_text(surf, fonts, "── Buffs ──", x, y, GRAY); y += lh
        for buff, turns in player.stats.buffs.items():
            col = RED if buff in ('poison','bleed','paralysis') else CYAN
            draw_text(surf, fonts, f"{buff}({turns})", x, y, col); y += lh

    return y


# ── Mini-map ──────────────────────────────────────────────────────────────────
def draw_minimap(surf, fonts, dungeon, player, y_start):
    mx = SIDEBAR_X + (PANEL_W - MINIMAP_SIZE) // 2
    my = y_start + 8
    pygame.draw.rect(surf, (10, 10, 20), (mx, my, MINIMAP_SIZE, MINIMAP_SIZE))
    pygame.draw.rect(surf, DGRAY, (mx, my, MINIMAP_SIZE, MINIMAP_SIZE), 1)

    cell_w = MINIMAP_SIZE / dungeon.width
    cell_h = MINIMAP_SIZE / dungeon.height

    for rx in range(dungeon.width):
        for ry in range(dungeon.height):
            if not dungeon.visited[rx][ry]:
                continue
            tile = dungeon.tiles[rx][ry]
            if tile == WALL:
                col = (50, 40, 35)
            elif tile in (STAIRS_DOWN, STAIRS_UP):
                col = YELLOW
            elif tile == DOOR:
                col = BROWN
            elif tile == WATER:
                col = DBLUE
            else:
                col = (80, 70, 60)
            px = int(mx + rx * cell_w)
            py = int(my + ry * cell_h)
            pygame.draw.rect(surf, col, (px, py, max(1, int(cell_w)), max(1, int(cell_h))))

    # Player dot
    ppx = int(mx + player.x * cell_w)
    ppy = int(my + player.y * cell_h)
    pygame.draw.rect(surf, WHITE, (ppx, ppy, max(2, int(cell_w)+1), max(2, int(cell_h)+1)))

    draw_text(surf, fonts, "Map", mx, my - FONT_SIZE - 2, GRAY, 'tiny')
    return my + MINIMAP_SIZE + 8


# ── Messages ──────────────────────────────────────────────────────────────────
def draw_messages(surf, fonts, messages, y_start):
    recent = messages[-MSG_LINES:]
    y = y_start
    for i, msg in enumerate(recent):
        alpha = 255 - (len(recent) - 1 - i) * 38
        col = (min(255,alpha), min(255,alpha), min(255,alpha))
        draw_text(surf, fonts, msg[:52], SIDEBAR_X + 8, y, col)
        y += FONT_SIZE + 4


# ── Quickslot bar ─────────────────────────────────────────────────────────────
SLOT_SIZE = 56

def draw_quickslots(surf, fonts, player):
    bar_w = QUICKSLOT_COUNT * (SLOT_SIZE + 4) + 4
    bx = (SIDEBAR_X - bar_w) // 2
    by = SCREEN_H - SLOT_SIZE - 8
    for i in range(QUICKSLOT_COUNT):
        sx = bx + i * (SLOT_SIZE + 4)
        item = player.quickslots[i] if i < len(player.quickslots) else None
        bg = (40, 40, 60) if item else (25, 25, 35)
        pygame.draw.rect(surf, bg, (sx, by, SLOT_SIZE, SLOT_SIZE))
        pygame.draw.rect(surf, GRAY, (sx, by, SLOT_SIZE, SLOT_SIZE), 1)
        draw_text(surf, fonts, str(i+1), sx+2, by+2, DGRAY, 'tiny')
        if item:
            draw_text(surf, fonts, item.char, sx+18, by+14, item.color, 'med')
            draw_text(surf, fonts, item.name[:6], sx+2, by+SLOT_SIZE-18, GRAY, 'tiny')


# ── Floating damage numbers ───────────────────────────────────────────────────
class FloatText:
    def __init__(self, text, x, y, color=RED):
        self.text  = text
        self.x     = float(x)
        self.y     = float(y)
        self.color = color
        self.life  = 40  # frames

    def update(self):
        self.y  -= 0.8
        self.life -= 1

    def alive(self):
        return self.life > 0

    def draw(self, surf, fonts, cam_x, cam_y):
        sx = int((self.x - cam_x) * TILE_SIZE + TILE_SIZE // 2)
        sy = int((self.y - cam_y) * TILE_SIZE)
        alpha = min(255, self.life * 8)
        col = tuple(min(255, c) for c in self.color)
        s = fonts['small'].render(self.text, True, col)
        s.set_alpha(alpha)
        surf.blit(s, (sx - s.get_width()//2, sy))


# ── Tooltip ───────────────────────────────────────────────────────────────────
def draw_tooltip(surf, fonts, item, mx, my):
    lines = [item.display_name()]
    if hasattr(item, 'min_dmg'):
        lines.append(f"Dmg: {item.min_dmg+item.level}-{item.max_dmg+item.level}")
    if hasattr(item, 'defense'):
        lines.append(f"DEF: {item.dr()}")
    if hasattr(item, 'charges'):
        lines.append(f"Charges: {item.charges}/{item.max_charges}")
    if hasattr(item, 'nutrition'):
        lines.append(f"Nutrition: {item.nutrition}")
    if item.cursed and item.identified:
        lines.append("CURSED")

    pad = 6
    w = max(fonts['tiny'].size(l)[0] for l in lines) + pad*2
    h = len(lines) * (FONT_SIZE - 2) + pad*2
    tx = min(mx + 12, SCREEN_W - w - 4)
    ty = min(my + 12, SCREEN_H - h - 4)
    pygame.draw.rect(surf, (20, 20, 40), (tx, ty, w, h))
    pygame.draw.rect(surf, GRAY, (tx, ty, w, h), 1)
    for i, line in enumerate(lines):
        col = item.color if i == 0 else WHITE
        draw_text(surf, fonts, line, tx+pad, ty+pad+i*(FONT_SIZE-2), col, 'tiny')


# ── Map ───────────────────────────────────────────────────────────────────────
ROOM_TINTS = {
    'treasure': (60, 50, 10),
    'shop':     (10, 40, 60),
    'garden':   (10, 50, 10),
    'armory':   (50, 20, 10),
    'library':  (30, 10, 50),
    'boss':     (60, 10, 10),
}

def draw_map(surf, fonts, dungeon, player, cam_x, cam_y, sprites=None, float_texts=None):
    sprites     = sprites or {}
    float_texts = float_texts or []
    wall_spr    = sprites.get('wall')
    floor_spr   = sprites.get('floor')
    view_w = SIDEBAR_X // TILE_SIZE
    view_h = SCREEN_H  // TILE_SIZE

    for sx in range(view_w + 1):
        for sy in range(view_h + 1):
            mx = sx + cam_x
            my = sy + cam_y
            if not (0 <= mx < dungeon.width and 0 <= my < dungeon.height):
                continue
            px = sx * TILE_SIZE
            py = sy * TILE_SIZE

            if dungeon.lit[mx][my]:
                tile  = dungeon.tiles[mx][my]
                color = TILE_COLORS.get(tile, BLACK)

                # Secret door looks like wall until searched
                if (mx, my) in dungeon.secret_doors:
                    if wall_spr: surf.blit(wall_spr, (px, py))
                    else: pygame.draw.rect(surf, TILE_COLORS[WALL], (px, py, TILE_SIZE, TILE_SIZE))
                    continue

                if tile == WALL and wall_spr:
                    surf.blit(wall_spr, (px, py))
                elif tile == FLOOR and floor_spr:
                    surf.blit(floor_spr, (px, py))
                    # Room tint overlay for special rooms
                    room = dungeon.room_at(mx, my)
                    if room and room.kind in ROOM_TINTS:
                        tint = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        r,g,b = ROOM_TINTS[room.kind]
                        tint.fill((r, g, b, 60))
                        surf.blit(tint, (px, py))
                else:
                    pygame.draw.rect(surf, color, (px, py, TILE_SIZE, TILE_SIZE))

                # Trap indicator
                if (mx, my) in dungeon.traps:
                    pygame.draw.rect(surf, (180, 50, 50), (px+TILE_SIZE//2-4, py+TILE_SIZE//2-4, 8, 8))

                # Dew drop
                if (mx, my) in dungeon.dew_drops:
                    pygame.draw.circle(surf, CYAN, (px+TILE_SIZE//2, py+TILE_SIZE//2), 4)

                if tile not in (WALL, FLOOR):
                    char = TILE_CHARS.get(tile, '?')
                    draw_text(surf, fonts, char, px+TILE_SIZE//4, py+TILE_SIZE//4, _dim(color, 1.4))

            elif dungeon.visited[mx][my]:
                tile  = dungeon.tiles[mx][my]
                color = _dim(TILE_COLORS.get(tile, BLACK), 0.4)
                if (mx, my) in dungeon.secret_doors:
                    if wall_spr:
                        d = wall_spr.copy(); d.set_alpha(80); surf.blit(d, (px, py))
                    else:
                        pygame.draw.rect(surf, color, (px, py, TILE_SIZE, TILE_SIZE))
                    continue
                if tile == WALL and wall_spr:
                    d = wall_spr.copy(); d.set_alpha(80); surf.blit(d, (px, py))
                elif tile == FLOOR and floor_spr:
                    d = floor_spr.copy(); d.set_alpha(80); surf.blit(d, (px, py))
                else:
                    pygame.draw.rect(surf, color, (px, py, TILE_SIZE, TILE_SIZE))
                    char = TILE_CHARS.get(tile, '?')
                    draw_text(surf, fonts, char, px+TILE_SIZE//4, py+TILE_SIZE//4, _dim(color, 0.6))
            else:
                pygame.draw.rect(surf, BLACK, (px, py, TILE_SIZE, TILE_SIZE))

    # Items
    for ix, iy, item in dungeon.items:
        if dungeon.lit[ix][iy]:
            sx = (ix - cam_x) * TILE_SIZE
            sy = (iy - cam_y) * TILE_SIZE
            if 0 <= sx < SIDEBAR_X and 0 <= sy < SCREEN_H:
                draw_text(surf, fonts, item.char, sx+TILE_SIZE//4, sy+TILE_SIZE//4, item.color)

    # Enemies
    for enemy in dungeon.enemies:
        if not enemy.is_alive():
            continue
        show = dungeon.lit[enemy.x][enemy.y] or player.stats.has_buff('mind_vision')
        if show:
            sx = (enemy.x - cam_x) * TILE_SIZE
            sy = (enemy.y - cam_y) * TILE_SIZE
            if 0 <= sx < SIDEBAR_X and 0 <= sy < SCREEN_H:
                pygame.draw.rect(surf, (80, 20, 20), (sx, sy, TILE_SIZE, TILE_SIZE))
                spr = sprites.get(enemy.name)
                if spr:
                    surf.blit(spr, (sx, sy))
                else:
                    draw_text(surf, fonts, enemy.char, sx+TILE_SIZE//4, sy+TILE_SIZE//4, enemy.color)
                draw_bar(surf, sx, sy+TILE_SIZE-5, TILE_SIZE, 5,
                         enemy.stats.hp, enemy.stats.max_hp, RED, (40,0,0))

    # Player
    ppx = (player.x - cam_x) * TILE_SIZE
    ppy = (player.y - cam_y) * TILE_SIZE
    player_spr = sprites.get('player')
    if player_spr:
        surf.blit(player_spr, (ppx, ppy))
    else:
        pygame.draw.rect(surf, (30, 60, 120), (ppx, ppy, TILE_SIZE, TILE_SIZE))
        draw_text(surf, fonts, '@', ppx+TILE_SIZE//4, ppy+TILE_SIZE//4, WHITE)

    # Floating damage numbers
    for ft in float_texts:
        ft.draw(surf, fonts, cam_x, cam_y)


def _dim(color, factor):
    return tuple(min(255, max(0, int(c * factor))) for c in color)


# ── Inventory ─────────────────────────────────────────────────────────────────
def draw_inventory(surf, fonts, player, selected=0):
    surf.fill((20, 20, 30))
    draw_text(surf, fonts, "INVENTORY  (E=use/equip  D=drop  Q=quickslot  ESC=close)", 20, 10, YELLOW, 'med')
    draw_text(surf, fonts, f"Gold: {player.gold}", 20, 38, YELLOW)

    items = player.inventory
    for i, item in enumerate(items):
        y = 65 + i * 26
        bg = (50, 50, 80) if i == selected else (20, 20, 30)
        pygame.draw.rect(surf, bg, (10, y, SCREEN_W - PANEL_W - 20, 24))
        equipped = item in [player.weapon, player.armor, player.ring1, player.ring2, player.missile_slot]
        qs_idx = next((j for j,s in enumerate(player.quickslots) if s is item), None)
        tag = f" [E]" if equipped else (f" [Q{qs_idx+1}]" if qs_idx is not None else "")
        draw_text(surf, fonts, f"{chr(97+i)}) {item.display_name()}{tag}", 16, y+3, item.color)

    # Detail panel
    if 0 <= selected < len(items):
        item = items[selected]
        dx = SCREEN_W - PANEL_W + 10
        dy = 65
        draw_text(surf, fonts, item.display_name(), dx, dy, item.color, 'med'); dy += 28
        if hasattr(item, 'min_dmg'):
            draw_text(surf, fonts, f"Damage: {item.min_dmg+item.level}-{item.max_dmg+item.level}", dx, dy, WHITE); dy += 22
        if hasattr(item, 'defense'):
            draw_text(surf, fonts, f"Defense: {item.dr()}", dx, dy, WHITE); dy += 22
        if hasattr(item, 'nutrition'):
            draw_text(surf, fonts, f"Nutrition: {item.nutrition}", dx, dy, WHITE); dy += 22
        if hasattr(item, 'charges'):
            draw_text(surf, fonts, f"Charges: {item.charges}/{item.max_charges}", dx, dy, WHITE); dy += 22
        if item.cursed and item.identified:
            draw_text(surf, fonts, "CURSED", dx, dy, RED)


# ── Class select ──────────────────────────────────────────────────────────────
def draw_class_select(surf, fonts):
    surf.fill(BLACK)
    draw_text(surf, fonts, "PIXEL DUNGEON", SCREEN_W//2 - 200, 80, YELLOW, 'title')
    draw_text(surf, fonts, "Choose your class:", SCREEN_W//2 - 130, 180, WHITE, 'big')
    for i, (name, desc) in enumerate(CLASSES_INFO.items()):
        y = 250 + i * 90
        col = YELLOW if i == 0 else WHITE
        draw_text(surf, fonts, f"{i+1}. {name}", SCREEN_W//2 - 220, y, col, 'med')
        draw_text(surf, fonts, desc, SCREEN_W//2 - 220, y+26, GRAY)
    draw_text(surf, fonts, "Press 1-4 to select", SCREEN_W//2 - 130, 640, GRAY)


CLASSES_INFO = {
    'Warrior':  "High HP & STR. Starts with Short Sword & Mail Armor.",
    'Mage':     "Starts with a Wand of Magic Missile. Identifies wands on use.",
    'Rogue':    "High DEX. Detects traps. Starts with Dagger.",
    'Huntress': "Ranged specialist. Starts with Boomerang.",
}


# ── Game over ─────────────────────────────────────────────────────────────────
def draw_game_over(surf, fonts, player, won=False):
    surf.fill(BLACK)
    msg = "YOU WIN!" if won else "YOU DIED"
    col = YELLOW if won else RED
    draw_text(surf, fonts, msg, SCREEN_W//2 - 130, 150, col, 'title')
    draw_text(surf, fonts, f"Class: {player.cls_name}  Depth: {player.depth}", SCREEN_W//2-160, 270, WHITE, 'med')
    draw_text(surf, fonts, f"Level: {player.stats.lvl}  Gold: {player.gold}", SCREEN_W//2-160, 305, YELLOW, 'med')
    draw_text(surf, fonts, f"Turns: {player.turns}", SCREEN_W//2-160, 340, WHITE, 'med')
    draw_text(surf, fonts, "Press R to restart or Q to quit", SCREEN_W//2-170, 430, GRAY, 'med')


# ── Settings ──────────────────────────────────────────────────────────────────
CONTROLS = [
    ("Movement",    "Arrow keys  or  H J K L"),
    ("Diagonal",    "Y U B N"),
    ("Pick up",     "G"),
    ("Inventory",   "I  or  Tab"),
    ("Use/Equip",   "E  (in inventory)"),
    ("Drop",        "D  (in inventory)"),
    ("Quickslot",   "Q  (in inventory) — assign to slot 1-4"),
    ("Use slot",    "1 2 3 4"),
    ("Throw",       "T  — nearest visible enemy"),
    ("Search",      "F  — find secret doors"),
    ("Stairs down", ">  or  Period"),
    ("Stairs up",   "<  or  Comma"),
    ("Wait/Rest",   "S"),
    ("Settings",    "F1"),
    ("Close menu",  "ESC"),
]

def draw_settings(surf, fonts):
    surf.fill((15, 15, 25))
    draw_text(surf, fonts, "SETTINGS", SCREEN_W//2 - 80, 40, YELLOW, 'big')
    draw_text(surf, fonts, "Controls", SCREEN_W//2 - 60, 90, GRAY, 'med')
    pygame.draw.line(surf, DGRAY, (SCREEN_W//2-220, 118), (SCREEN_W//2+220, 118), 1)
    for i, (action, keys) in enumerate(CONTROLS):
        y = 130 + i * 30
        draw_text(surf, fonts, action, SCREEN_W//2 - 220, y, WHITE)
        draw_text(surf, fonts, keys,   SCREEN_W//2 + 10,  y, CYAN)
    draw_text(surf, fonts, "ESC — back", SCREEN_W//2 - 50, SCREEN_H - 44, GRAY)


# ── Depth transition ──────────────────────────────────────────────────────────
def draw_depth_transition(surf, fonts, depth):
    surf.fill(BLACK)
    draw_text(surf, fonts, f"Depth {depth}", SCREEN_W//2 - 80, SCREEN_H//2 - 20, YELLOW, 'big')
    pygame.display.flip()
    pygame.time.wait(800)
