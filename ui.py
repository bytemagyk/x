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


def _item_sprite(item, sprites):
    itype = item.itype
    name = item.name.lower()
    if itype == POTION:
        potion_colors = {
            'healing': 'r',
            'strength': 'y',
            'paralysis': 'b',
            'levitation': 'b',
            'invisibility': 'b',
            'toxic gas': 'g',
            'liquid flame': 'r',
            'frost': 'b',
            'mind vision': 'b',
            'experience': 'y',
            'haste': 'y',
            'mana': 'b',
        }
        return sprites.get(f"potion_{potion_colors.get(item.true_name, 'r')}")
    if itype == GOLD:
        return sprites.get('gold')
    if itype == WEAPON:
        sprite_names = {
            'dagger': 'dagger',
            'hand axe': 'axe',
            'battle axe': 'axe',
            'greataxe': 'axe',
            'short sword': 'sword_iron',
            'long sword': 'sword_steel',
            'mace': 'mace',
            'spear': 'spear',
            'glaive': 'spear',
            'war hammer': 'warhammer',
        }
        return sprites.get(sprite_names.get(name))
    if itype == ARMOR:
        armor_sprites = {
            'cloth armor': 'chest_leather',
            'leather armor': 'chest_leather',
            'mail armor': 'chest_iron',
            'scale armor': 'chest_iron',
            'plate armor': 'chest_gold',
            'warrior armor': 'chest_gold',
        }
        return sprites.get(armor_sprites.get(name))
    if itype == MISSILE:
        return sprites.get('bow')
    if itype == SCROLL:
        scroll_sprites = {
            'enchant weapon': 'scroll_fire',
            'terror': 'scroll_fire',
            'psionic blast': 'scroll_fire',
            'remove curse': 'scroll_heal',
            'lullaby': 'scroll_heal',
            'upgrade': 'scroll_ice',
            'enchant armor': 'scroll_ice',
        }
        return sprites.get(scroll_sprites.get(item.true_name, 'scroll_arcane'))
    if itype == WAND:
        wand_sprites = {
            'magic missile': 'staff_arcane',
            'disintegration': 'staff_arcane',
            'firebolt': 'wand_fire',
            'frost': 'wand_ice',
            'lightning': 'wand_light',
            'blast wave': 'wand_light',
            'venom': 'wand_nature',
            'corrosion': 'wand_nature',
            'living earth': 'wand_nature',
            'warding': 'wand_nature',
            'regrowth': 'wand_nature',
            'transfusion': 'wand_nature',
        }
        return sprites.get(wand_sprites.get(item.effect, 'wand_arcane'))
    return None


def _blit_sprite(surf, sprite, x, y, size):
    if sprite:
        if sprite.get_size() != (size, size):
            sprite = pygame.transform.scale(sprite, (size, size))
        surf.blit(sprite, (x, y))
        return True
    return False


def _draw_item_sprite(surf, item, sprites, x, y, size):
    return _blit_sprite(surf, _item_sprite(item, sprites), x, y, size)


def _tile_sprite(sprites, tile, x, y, tick):
    if tile == WALL:
        if (x * 17 + y * 31) % 37 == 0:
            return sprites.get(f"wall_torch_{(tick // 300) % 2}")
        variants = ('wall_brick', 'wall_brick_b', 'wall_cracked', 'wall_mossy')
        return sprites.get(variants[(x * 17 + y * 31) % len(variants)])
    if tile == FLOOR:
        variants = ('floor_stone', 'floor_stone_b', 'floor_cracked',
                    'floor_mossy', 'floor_wet')
        return sprites.get(variants[(x * 13 + y * 29) % len(variants)])
    if tile == DOOR:
        return sprites.get('door')
    if tile == STAIRS_UP:
        return sprites.get('stairs_up')
    if tile == STAIRS_DOWN:
        return sprites.get('stairs_down')
    if tile == WATER:
        return sprites.get(f"water_{(tick // 220) % 4}")
    if tile == GRASS:
        variants = ('grass', 'grass_b', 'grass_flowers',
                    'grass_tall', 'grass_tall_b')
        return sprites.get(variants[(x * 19 + y * 23) % len(variants)])
    return None


def draw_bar(surf, x, y, w, h, val, max_val, color, bg=DGRAY):
    pygame.draw.rect(surf, bg, (x, y, w, h))
    if max_val > 0:
        fill = int(w * val / max_val)
        pygame.draw.rect(surf, color, (x, y, fill, h))
    pygame.draw.rect(surf, GRAY, (x, y, w, h), 1)


# ── HUD ───────────────────────────────────────────────────────────────────────
def draw_hud(surf, fonts, player, sprites=None):
    sprites = sprites or {}
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
    y += lh
    draw_bar(surf, x, y, PANEL_W - 20, 10, max(0, player.hunger), BASE_HUNGER, hunger_color)
    y += 14

    draw_text(surf, fonts, "── Equipment ──", x, y, GRAY)
    y += lh
    wname = player.weapon.display_name() if player.weapon else "none"
    aname = player.armor.display_name()  if player.armor  else "none"
    if player.weapon:
        _draw_item_sprite(surf, player.weapon, sprites, x, y, 20)
    draw_text(surf, fonts, f"W: {wname[:24]}", x + (24 if player.weapon else 0),
              y, YELLOW); y += lh
    if player.armor:
        _draw_item_sprite(surf, player.armor, sprites, x, y, 20)
    draw_text(surf, fonts, f"A: {aname[:24]}", x + (24 if player.armor else 0),
              y, BLUE); y += lh
    if player.ring1:
        _draw_item_sprite(surf, player.ring1, sprites, x, y, 20)
        draw_text(surf, fonts, f"R1:{player.ring1.display_name()[:22]}",
                  x + (24 if _item_sprite(player.ring1, sprites) else 0),
                  y, PURPLE); y += lh
    if player.ring2:
        _draw_item_sprite(surf, player.ring2, sprites, x, y, 20)
        draw_text(surf, fonts, f"R2:{player.ring2.display_name()[:22]}",
                  x + (24 if _item_sprite(player.ring2, sprites) else 0),
                  y, PURPLE); y += lh
    if player.missile_slot:
        _draw_item_sprite(surf, player.missile_slot, sprites, x, y, 20)
        draw_text(surf, fonts, f"M: {player.missile_slot.display_name()[:22]}",
                  x + (24 if _item_sprite(player.missile_slot, sprites) else 0),
                  y, ORANGE); y += lh

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

    # Dew drops on minimap
    for dx, dy in dungeon.dew_drops:
        if dungeon.visited[dx][dy]:
            dpx = int(mx + dx * cell_w)
            dpy = int(my + dy * cell_h)
            pygame.draw.rect(surf, CYAN, (dpx, dpy, max(2, int(cell_w)+1), max(2, int(cell_h)+1)))

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
QUICKSLOT_GAP = 6
QUICKSLOT_BOTTOM_MARGIN = 30


def quickslot_rect(index):
    if not 0 <= index < QUICKSLOT_COUNT:
        raise IndexError(f"Quickslot index out of range: {index}")
    bar_w = QUICKSLOT_COUNT * SLOT_SIZE + (QUICKSLOT_COUNT - 1) * QUICKSLOT_GAP
    bx = (SIDEBAR_X - bar_w) // 2
    by = SCREEN_H - SLOT_SIZE - QUICKSLOT_BOTTOM_MARGIN
    return pygame.Rect(bx + index * (SLOT_SIZE + QUICKSLOT_GAP), by, SLOT_SIZE, SLOT_SIZE)


def quickslot_at(position):
    return next((i for i in range(QUICKSLOT_COUNT)
                 if quickslot_rect(i).collidepoint(position)), None)

def draw_quickslots(surf, fonts, player, sprites=None):
    sprites = sprites or {}
    bar_w = QUICKSLOT_COUNT * SLOT_SIZE + (QUICKSLOT_COUNT - 1) * QUICKSLOT_GAP
    bx = (SIDEBAR_X - bar_w) // 2
    by = SCREEN_H - SLOT_SIZE - QUICKSLOT_BOTTOM_MARGIN
    ability = player.ability_info
    draw_text(surf, fonts, f"QUICKSLOTS  CLICK OR PRESS 1-4  SLOT 1: {ability['name']}",
              bx, by - 22,
              (188, 202, 224), 'tiny')
    for i in range(QUICKSLOT_COUNT):
        rect = quickslot_rect(i)
        sx, sy = rect.topleft
        item = player.quickslots[i] if i < len(player.quickslots) else None
        if i > 0 and item not in player.inventory:
            item = None
        is_ability = i == 0
        available = player.ability_cooldown <= 0
        bg = ((40, 50, 72) if item or (is_ability and available)
              else (25, 30, 43))
        pygame.draw.rect(surf, bg, rect, border_radius=7)
        pygame.draw.rect(surf, (112, 130, 160) if item or is_ability else (74, 83, 102),
                         rect, 1, border_radius=7)
        pygame.draw.rect(surf, (21, 27, 40), (sx + 3, sy + 3, 18, 17), border_radius=4)
        draw_text(surf, fonts, str(i + 1), sx + 8, sy + 2, (225, 232, 244), 'tiny')
        if is_ability:
            ability_color = ability['color'] if available else (112, 120, 138)
            label_font = fonts['tiny']
            draw_text(surf, fonts, ability['glyph'], sx + 18, sy + 7,
                      ability_color, 'med')
            label = (ability['short_name'] if available
                     else f"CD:{player.ability_cooldown}")
            label_surface = label_font.render(label, True,
                                               (153, 211, 167) if available else (172, 158, 130))
            surf.blit(label_surface, (sx + (SLOT_SIZE - label_surface.get_width()) // 2,
                                      sy + SLOT_SIZE - label_surface.get_height() - 3))
            continue
        elif item:
            if not _draw_item_sprite(surf, item, sprites, sx + 12, sy + 5, 32):
                draw_text(surf, fonts, item.char, sx + 18, sy + 10, item.color, 'med')
            label = item.display_name()
            status = None
            status_color = WHITE
        else:
            draw_text(surf, fonts, "EMPTY", sx + 7, sy + 20, (120, 132, 153), 'tiny')
            continue

        label_font = fonts['tiny']
        if label_font.size(label)[0] > SLOT_SIZE - 8:
            while label and label_font.size(label + "...")[0] > SLOT_SIZE - 8:
                label = label[:-1]
            label = label.rstrip() + "..."
        label_surface = label_font.render(label, True, (211, 219, 233))
        surf.blit(label_surface, (sx + (SLOT_SIZE - label_surface.get_width()) // 2,
                                  sy + SLOT_SIZE - label_surface.get_height() - 3))


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
def draw_tooltip(surf, fonts, item, mx, my, sprites=None):
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
    has_sprite = _item_sprite(item, sprites or {}) is not None
    w = max(fonts['tiny'].size(l)[0] for l in lines) + pad*2
    if has_sprite:
        w += 30
    h = len(lines) * (FONT_SIZE - 2) + pad*2
    tx = min(mx + 12, SCREEN_W - w - 4)
    ty = min(my + 12, SCREEN_H - h - 4)
    pygame.draw.rect(surf, (20, 20, 40), (tx, ty, w, h))
    pygame.draw.rect(surf, GRAY, (tx, ty, w, h), 1)
    _draw_item_sprite(surf, item, sprites or {}, tx+pad, ty+pad, 24)
    for i, line in enumerate(lines):
        col = item.color if i == 0 else WHITE
        offset = 30 if i == 0 and has_sprite else 0
        draw_text(surf, fonts, line, tx+pad+offset,
                  ty+pad+i*(FONT_SIZE-2), col, 'tiny')


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
    tick = pygame.time.get_ticks()
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
                tile_spr = _tile_sprite(sprites, tile, mx, my, tick)

                # Secret door looks like wall until searched
                if (mx, my) in dungeon.secret_doors:
                    wall_spr = _tile_sprite(sprites, WALL, mx, my, tick)
                    if wall_spr: surf.blit(wall_spr, (px, py))
                    else: pygame.draw.rect(surf, TILE_COLORS[WALL], (px, py, TILE_SIZE, TILE_SIZE))
                    continue

                if tile_spr:
                    surf.blit(tile_spr, (px, py))
                else:
                    pygame.draw.rect(surf, color, (px, py, TILE_SIZE, TILE_SIZE))
                    if tile not in (WALL, FLOOR):
                        char = TILE_CHARS.get(tile, '?')
                        draw_text(surf, fonts, char, px+TILE_SIZE//4,
                                  py+TILE_SIZE//4, _dim(color, 1.4))

                if tile == FLOOR:
                    room = dungeon.room_at(mx, my)
                    if room and room.kind in ROOM_TINTS:
                        tint = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        r,g,b = ROOM_TINTS[room.kind]
                        tint.fill((r, g, b, 60))
                        surf.blit(tint, (px, py))

                # Trap indicator
                trap_type = dungeon.traps.get((mx, my))
                if trap_type:
                    trap_sprites = {
                        'damage': 'trap_spike',
                        'poison': 'trap_poison',
                        'teleport': 'trap_teleport',
                        'alarm': 'trap_alarm',
                        'gripping': 'trap_paralysis',
                        'fire': 'trap_fire',
                        'chasm': 'trap_spike',
                        'disintegration': 'trap_spike',
                        'frost': 'trap_frost',
                    }
                    trap_spr = sprites.get(trap_sprites.get(trap_type, 'trap_inactive'))
                    if not _blit_sprite(surf, trap_spr, px+TILE_SIZE//4,
                                        py+TILE_SIZE//4, TILE_SIZE//2):
                        pygame.draw.rect(surf, (180, 50, 50),
                                         (px+TILE_SIZE//2-4, py+TILE_SIZE//2-4, 8, 8))

                # Dew drop
                if (mx, my) in dungeon.dew_drops:
                    dew_key = 'dew_cluster' if (mx * 17 + my * 31) % 3 == 0 else 'dewdrop'
                    if not _blit_sprite(surf, sprites.get(dew_key), px+TILE_SIZE//3,
                                        py+TILE_SIZE//3, TILE_SIZE//3):
                        pygame.draw.circle(surf, CYAN, (px+TILE_SIZE//2, py+TILE_SIZE//2), 4)

            elif dungeon.visited[mx][my]:
                tile  = dungeon.tiles[mx][my]
                color = _dim(TILE_COLORS.get(tile, BLACK), 0.4)
                if (mx, my) in dungeon.secret_doors:
                    wall_spr = _tile_sprite(sprites, WALL, mx, my, tick)
                    if wall_spr:
                        d = wall_spr.copy(); d.set_alpha(80); surf.blit(d, (px, py))
                    else:
                        pygame.draw.rect(surf, color, (px, py, TILE_SIZE, TILE_SIZE))
                    continue
                tile_spr = _tile_sprite(sprites, tile, mx, my, tick)
                if tile_spr:
                    d = tile_spr.copy()
                    d.set_alpha(80)
                    surf.blit(d, (px, py))
                else:
                    pygame.draw.rect(surf, color, (px, py, TILE_SIZE, TILE_SIZE))
                    char = TILE_CHARS.get(tile, '?')
                    draw_text(surf, fonts, char, px+TILE_SIZE//4, py+TILE_SIZE//4, _dim(color, 0.6))
            else:
                pygame.draw.rect(surf, BLACK, (px, py, TILE_SIZE, TILE_SIZE))

    # Items
    potion_sprs = [sprites.get('potion_r'), sprites.get('potion_b'),
                   sprites.get('potion_g'), sprites.get('potion_y')]
    gold_spr    = sprites.get('gold')
    for ix, iy, item in dungeon.items:
        if dungeon.lit[ix][iy]:
            sx = (ix - cam_x) * TILE_SIZE
            sy = (iy - cam_y) * TILE_SIZE
            if 0 <= sx < SIDEBAR_X and 0 <= sy < SCREEN_H:
                if not _draw_item_sprite(surf, item, sprites, sx, sy, TILE_SIZE):
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
                enemy_frames = sprites.get(enemy.name)
                if enemy_frames:
                    if isinstance(enemy_frames, (tuple, list)):
                        frame_index = (pygame.time.get_ticks() // 180
                                       + enemy.x + enemy.y) % len(enemy_frames)
                        spr = enemy_frames[frame_index]
                    else:
                        spr = enemy_frames
                    surf.blit(spr, (sx, sy))
                else:
                    pygame.draw.rect(surf, (80, 20, 20),
                                     (sx, sy, TILE_SIZE, TILE_SIZE))
                    draw_text(surf, fonts, enemy.char, sx+TILE_SIZE//4, sy+TILE_SIZE//4, enemy.color)
                draw_bar(surf, sx, sy+TILE_SIZE-5, TILE_SIZE, 5,
                         enemy.stats.hp, enemy.stats.max_hp, RED, (40,0,0))

    # Player
    ppx = (player.x - cam_x) * TILE_SIZE
    ppy = (player.y - cam_y) * TILE_SIZE
    player_spr = sprites.get(f"player_{player.cls_name.lower()}",
                             sprites.get('player'))
    if player_spr:
        surf.blit(player_spr, (ppx, ppy))
    else:
        pygame.draw.rect(surf, (30, 60, 120), (ppx, ppy, TILE_SIZE, TILE_SIZE))
        draw_text(surf, fonts, '@', ppx+TILE_SIZE//4, ppy+TILE_SIZE//4, WHITE)

    # Shopkeeper
    if dungeon.shop_pos:
        sx_s, sy_s = dungeon.shop_pos
        if dungeon.lit[sx_s][sy_s]:
            spx = (sx_s - cam_x) * TILE_SIZE
            spy = (sy_s - cam_y) * TILE_SIZE
            if 0 <= spx < SIDEBAR_X and 0 <= spy < SCREEN_H:
                pygame.draw.rect(surf, (80, 60, 10), (spx, spy, TILE_SIZE, TILE_SIZE))
                draw_text(surf, fonts, '@', spx+TILE_SIZE//4, spy+TILE_SIZE//4, YELLOW, 'med')

    # Floating damage numbers
    for ft in float_texts:
        ft.draw(surf, fonts, cam_x, cam_y)

    # Shop prompt
    for ix, iy, item in dungeon.items:
        if hasattr(item, '_shop_price') and ix == player.x and iy == player.y:
            msg = f"G — Buy {item.display_name()} for {item._shop_price} gold"
            s = fonts['small'].render(msg, True, YELLOW)
            surf.blit(s, (SIDEBAR_X // 2 - s.get_width() // 2, SCREEN_H - 60))


def _dim(color, factor):
    return tuple(min(255, max(0, int(c * factor))) for c in color)


# ── Item select (scroll targeting) ───────────────────────────────────────────
_SELECT_PROMPTS = {
    'identify':      "IDENTIFY — choose an item:",
    'upgrade':       "UPGRADE — choose a weapon or armor:",
    'enchant_weapon':"ENCHANT WEAPON — choose a weapon:",
    'enchant_armor': "ENCHANT ARMOR — choose armor:",
    'transmute':     "TRANSMUTATION — choose an item to transform:",
}

def draw_item_select(surf, fonts, items, purpose, selected=0, sprites=None):
    sprites = sprites or {}
    surf.fill((20, 20, 30))
    prompt = _SELECT_PROMPTS.get(purpose, "Choose an item:")
    draw_text(surf, fonts, prompt, 20, 10, YELLOW, 'med')
    draw_text(surf, fonts, "Arrows/a-z=select  Enter=confirm  ESC=cancel", 20, 38, GRAY, 'tiny')
    for i, item in enumerate(items):
        y = 70 + i * 26
        bg = (50, 50, 80) if i == selected else (20, 20, 30)
        pygame.draw.rect(surf, bg, (10, y, SCREEN_W - PANEL_W - 20, 24))
        _draw_item_sprite(surf, item, sprites, 16, y+2, 20)
        draw_text(surf, fonts, f"{chr(97+i)}) {item.display_name()}", 42, y+3, item.color)
    if not items:
        draw_text(surf, fonts, "No valid items.", 20, 70, RED)


# ── Inventory ─────────────────────────────────────────────────────────────────
def draw_inventory(surf, fonts, player, selected=0, sprites=None):
    sprites = sprites or {}
    items = player.inventory
    surf.fill((10, 13, 22))
    pygame.draw.rect(surf, (24, 30, 45), (28, 24, SCREEN_W - 56, SCREEN_H - 48), border_radius=14)
    pygame.draw.rect(surf, (62, 75, 100), (28, 24, SCREEN_W - 56, SCREEN_H - 48), 2, border_radius=14)

    draw_text(surf, fonts, "INVENTORY", 54, 43, (238, 226, 184), 'big')
    draw_text(surf, fonts, f"{len(items)} items", 58, 82, (160, 176, 198), 'tiny')
    draw_text(surf, fonts, f"GOLD  {player.gold}", SCREEN_W - 250, 54, YELLOW, 'med')
    pygame.draw.line(surf, (62, 75, 100), (52, 116), (SCREEN_W - 52, 116), 2)

    list_x, list_y, list_w = 54, 158, 850
    detail_x, detail_y, detail_w = 928, 158, SCREEN_W - 982
    row_h, row_gap = 58, 6
    visible_rows = max(1, (SCREEN_H - 300) // (row_h + row_gap))
    if items:
        selected = max(0, min(selected, len(items) - 1))
    first_item = max(0, min(selected - visible_rows // 2, len(items) - visible_rows))

    draw_text(surf, fonts, "YOUR ITEMS", list_x + 4, 130, (188, 202, 224), 'tiny')
    pygame.draw.rect(surf, (17, 22, 34), (list_x, list_y, list_w, SCREEN_H - 250), border_radius=10)
    for row in range(visible_rows):
        i = first_item + row
        if i >= len(items):
            break
        item = items[i]
        y = list_y + 12 + row * (row_h + row_gap)
        is_selected = i == selected
        row_color = (57, 70, 96) if is_selected else (29, 37, 54)
        pygame.draw.rect(surf, row_color, (list_x + 10, y, list_w - 20, row_h), border_radius=8)
        if is_selected:
            pygame.draw.rect(surf, (125, 164, 220), (list_x + 10, y, 4, row_h), border_radius=2)

        _draw_item_sprite(surf, item, sprites, list_x + 22, y + 8, 42)
        draw_text(surf, fonts, f"{i + 1:02}", list_x + 78, y + 7, (145, 160, 185), 'tiny')
        draw_text(surf, fonts, item.display_name(), list_x + 122, y + 7, item.color, 'med')
        draw_text(surf, fonts, str(item.itype).upper(), list_x + 123, y + 34, (157, 174, 198), 'tiny')

        equipped = item in [player.weapon, player.armor, player.ring1, player.ring2, player.missile_slot]
        qs_idx = next((j for j, slot in enumerate(player.quickslots) if slot is item), None)
        if equipped:
            tag, tag_color = "EQUIPPED", (153, 211, 167)
        elif qs_idx is not None:
            tag, tag_color = f"QUICK {qs_idx + 1}", (225, 198, 130)
        else:
            tag = None
        if tag:
            tag_surface = fonts['tiny'].render(tag, True, tag_color)
            surf.blit(tag_surface, (list_x + list_w - 28 - tag_surface.get_width(), y + 20))

    if not items:
        draw_text(surf, fonts, "Your pack is empty.", list_x + 24, list_y + 28, (165, 177, 198), 'med')

    # Item details
    pygame.draw.rect(surf, (17, 22, 34), (detail_x, detail_y, detail_w, SCREEN_H - 250), border_radius=10)
    draw_text(surf, fonts, "SELECTED ITEM", detail_x + 22, 174, (188, 202, 224), 'tiny')
    if 0 <= selected < len(items):
        item = items[selected]
        icon_size = 96
        icon_x = detail_x + 22
        icon_y = detail_y + 52
        pygame.draw.rect(surf, (34, 43, 62), (icon_x, icon_y, icon_size, icon_size), border_radius=12)
        _draw_item_sprite(surf, item, sprites, icon_x + 8, icon_y + 8, icon_size - 16)
        name_x = icon_x + icon_size + 20
        draw_text(surf, fonts, item.display_name(), name_x, icon_y + 8, item.color, 'med')
        draw_text(surf, fonts, str(item.itype).upper(), name_x, icon_y + 38, (157, 174, 198), 'tiny')

        equipped = item in [player.weapon, player.armor, player.ring1, player.ring2, player.missile_slot]
        if equipped:
            draw_text(surf, fonts, "Currently equipped", name_x, icon_y + 62, (153, 211, 167), 'tiny')

        dy = icon_y + icon_size + 28
        pygame.draw.line(surf, (62, 75, 100), (detail_x + 22, dy), (detail_x + detail_w - 22, dy), 1)
        dy += 18
        if hasattr(item, 'min_dmg'):
            draw_text(surf, fonts, f"Damage   {item.min_dmg + item.level}-{item.max_dmg + item.level}", detail_x + 24, dy, WHITE)
            dy += 28
        if hasattr(item, 'defense'):
            draw_text(surf, fonts, f"Defense  {item.dr()}", detail_x + 24, dy, WHITE)
            dy += 28
        if hasattr(item, 'nutrition'):
            draw_text(surf, fonts, f"Nutrition  {item.nutrition}", detail_x + 24, dy, WHITE)
            dy += 28
        if hasattr(item, 'charges'):
            draw_text(surf, fonts, f"Charges   {item.charges}/{item.max_charges}", detail_x + 24, dy, WHITE)
            dy += 28
        if item.cursed and item.identified:
            draw_text(surf, fonts, "CURSED", detail_x + 24, dy, RED)

    footer_y = SCREEN_H - 78
    pygame.draw.line(surf, (62, 75, 100), (52, footer_y - 14), (SCREEN_W - 52, footer_y - 14), 1)
    draw_text(surf, fonts, "Up/Down or K/J  Navigate    E  Use    R  Throw potion    D  Drop    Q  Assign item (slots 2-4)    ESC  Close",
              58, footer_y, (198, 209, 226), 'tiny')
    if items:
        draw_text(surf, fonts, f"{selected + 1} / {len(items)}", SCREEN_W - 116, footer_y, (160, 176, 198), 'tiny')


# ── Class select ──────────────────────────────────────────────────────────────
def draw_class_select(surf, fonts, has_save=False, sprites=None):
    sprites = sprites or {}
    surf.fill(BLACK)
    draw_text(surf, fonts, "PIXEL DUNGEON", SCREEN_W//2 - 200, 80, YELLOW, 'title')
    if has_save:
        draw_text(surf, fonts, "C  —  Continue", SCREEN_W//2 - 100, 175, GREEN, 'med')
        pygame.draw.line(surf, DGRAY, (SCREEN_W//2-220, 210), (SCREEN_W//2+220, 210), 1)
    draw_text(surf, fonts, "New Game — choose class:", SCREEN_W//2 - 160, 220 if has_save else 180, WHITE, 'med')
    for i, (name, desc) in enumerate(CLASSES_INFO.items()):
        y = 260 + i * 90 if has_save else 250 + i * 90
        col = YELLOW if i == 0 else WHITE
        portrait = sprites.get(f"player_{name.lower()}")
        if portrait:
            _blit_sprite(surf, portrait, SCREEN_W//2 - 290, y, 52)
        draw_text(surf, fonts, f"{i+1}. {name}", SCREEN_W//2 - 220, y, col, 'med')
        draw_text(surf, fonts, desc, SCREEN_W//2 - 220, y+26, GRAY)
    draw_text(surf, fonts, "Press 1-4 to select", SCREEN_W//2 - 130, 680, GRAY)


CLASSES_INFO = {
    'Warrior':  "High HP & STR. Starts with Short Sword & Mail Armor.",
    'Mage':     "Starts with a Wand of Magic Missile. Identifies wands on use.",
    'Rogue':    "High DEX. Detects traps. Starts with Dagger.",
    'Huntress': "Ranged specialist. Starts with Boomerang.",
}


# ── Game over ─────────────────────────────────────────────────────────────────
def draw_game_over(surf, fonts, player, won=False, sprites=None):
    surf.fill(BLACK)
    msg = "YOU WIN!" if won else "YOU DIED"
    col = YELLOW if won else RED
    if sprites:
        portrait = sprites.get(f"player_{player.cls_name.lower()}", sprites.get('player'))
        if portrait:
            _blit_sprite(surf, portrait, SCREEN_W//2 - 32, 80, 64)
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
    ("Throw potion","R  (in inventory) — enter targeting mode"),
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
