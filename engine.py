import pygame
import sys
import random
from constants import *
from dungeon import DungeonMap
from entities import Player
from enemies import spawn_enemies
from items import random_item, init_aliases, Gold, Potion, Scroll, Wand, Food, Weapon, Armor, Ring
from saveload import save, load, has_save, delete_save
from ui import (init_fonts, draw_hud, draw_messages, draw_map, draw_minimap,
                draw_inventory, draw_item_select, draw_class_select, draw_game_over,
                draw_depth_transition, draw_settings, draw_quickslots,
                draw_tooltip, quickslot_at, FloatText, CLASSES_INFO)

class Game:
    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Pixel Dungeon")
        self.clock   = pygame.time.Clock()
        self.fonts   = init_fonts()
        self.sprites = self._load_sprites()
        self.state   = 'class_select'
        self._prev_state = 'class_select'
        self.player  = None
        self.dungeon = None
        self.messages   = []
        self.inv_sel    = 0
        self.cam_x = self.cam_y = 0
        self.float_texts = []   # active FloatText instances
        self.hover_item  = None # item under mouse cursor
        self.mouse_path  = []   # click-to-move path
        self.targeting   = None # item being thrown (Potion)
        self.cursor_x = self.cursor_y = 0
        self._select_purpose = None  # 'identify'/'upgrade'/'enchant_weapon'/'enchant_armor'/'transmute'
        self._select_scroll  = None  # scroll item waiting for target
        self._select_items   = []    # filtered list shown in item_select
        init_aliases()

    def _load_sprites(self):
        sprites = {}
        files = {
            'door':   'assets/door.png',
            'player': 'assets/HeroK.jpg',
            'player_warrior': 'assets/HeroK.jpg',
            'player_mage': 'assets/1791341646010.jpg',
            'player_rogue': 'assets/1791341127560.jpg',
            'player_huntress': 'assets/1791341791756.jpg',
            'potion_r': 'assets/rpotion.png',
            'potion_b': 'assets/bpotion.png',
            'potion_g': 'assets/gpotion.png',
            'potion_y': 'assets/yellowpotion.png',
            'gold':     'assets/gold.png',
            'axe': 'assets/axe.png',
            'bow': 'assets/bow.png',
            'dagger': 'assets/dagger.png',
            'mace': 'assets/mace.png',
            'spear': 'assets/spear.png',
            'sword_iron': 'assets/sword_iron.png',
            'sword_steel': 'assets/sword_steel.png',
            'warhammer': 'assets/warhammer.png',
            'chest_leather': 'assets/chest_leather.png',
            'chest_iron': 'assets/chest_iron.png',
            'chest_gold': 'assets/chest_gold.png',
            'scroll_arcane': 'assets/scroll_open_arcane.png',
            'scroll_fire': 'assets/scroll_open_fire.png',
            'scroll_heal': 'assets/scroll_open_heal.png',
            'scroll_ice': 'assets/scroll_open_ice.png',
            'wand_arcane': 'assets/wand_arcane.png',
            'wand_fire': 'assets/wand_fire.png',
            'wand_ice': 'assets/wand_ice.png',
            'wand_light': 'assets/wand_light.png',
            'wand_nature': 'assets/wand_nature.png',
            'staff_arcane': 'assets/staff_arcane.png',
            'floor_cracked': 'assets/floor_cracked.png',
            'floor_mossy': 'assets/floor_mossy.png',
            'floor_stone': 'assets/floor_stone.png',
            'floor_stone_b': 'assets/floor_stone_b.png',
            'floor_wet': 'assets/floor_wet.png',
            'wall_brick': 'assets/wall_brick.png',
            'wall_brick_b': 'assets/wall_brick_b.png',
            'wall_cracked': 'assets/wall_cracked.png',
            'wall_mossy': 'assets/wall_mossy.png',
            'wall_torch_0': 'assets/wall_torch_0.png',
            'wall_torch_1': 'assets/wall_torch_1.png',
            'water_0': 'assets/water_0.png',
            'water_1': 'assets/water_1.png',
            'water_2': 'assets/water_2.png',
            'water_3': 'assets/water_3.png',
            'grass': 'assets/grass.png',
            'grass_b': 'assets/grass_b.png',
            'grass_flowers': 'assets/grass_flowers.png',
            'grass_tall': 'assets/grass_tall.png',
            'grass_tall_b': 'assets/grass_tall_b.png',
            'stairs_up': 'assets/stairs_up.png',
            'stairs_down': 'assets/stairs_down.png',
            'trap_alarm': 'assets/trap_alarm.png',
            'trap_fire': 'assets/trap_fire.png',
            'trap_frost': 'assets/trap_frost.png',
            'trap_inactive': 'assets/trap_inactive.png',
            'trap_paralysis': 'assets/trap_paralysis.png',
            'trap_poison': 'assets/trap_poison.png',
            'trap_spike': 'assets/trap_spike.png',
            'trap_teleport': 'assets/trap_teleport.png',
            'dew_cluster': 'assets/dew_cluster.png',
            'dew_vial': 'assets/dew_vial.png',
            'dewdrop': 'assets/dewdrop.png',
        }
        for name, path in files.items():
            img = pygame.image.load(path).convert_alpha()
            sprites[name] = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))

        sheet = pygame.image.load('assets/rat,crab,gnollsheet.png').convert_alpha()
        frame_w, frame_h = sheet.get_width() // 4, sheet.get_height() // 3
        enemy_rows = {'Rat': 0, 'Gnoll': 1, 'Sewage Crab': 2}
        for enemy_name, row in enemy_rows.items():
            sprites[enemy_name] = tuple(
                pygame.transform.scale(
                    sheet.subsurface((col * frame_w, row * frame_h, frame_w, frame_h)),
                    (TILE_SIZE, TILE_SIZE))
                for col in range(4)
            )
        return sprites

    # ── Game setup ────────────────────────────────────────────────────────────
    def new_game(self, cls_name):
        self.player = Player(cls_name)
        self.messages = []
        self.float_texts = []
        self._load_depth(1)
        self.messages.append(f"Welcome, {cls_name}! Find the Amulet of Yendor!")
        self.state = 'playing'

    def _load_depth(self, depth):
        self.player.depth = depth
        self.dungeon = DungeonMap(depth)
        spawn_enemies(self.dungeon, depth)
        self._populate_items(depth)
        sx, sy = self.dungeon.stairs_up or self.dungeon.rooms[0].center()
        self.player.x, self.player.y = sx, sy
        self.dungeon.compute_fov(self.player.x, self.player.y)
        self._update_camera()
        self.float_texts.clear()
        self.mouse_path.clear()
        draw_depth_transition(self.screen, self.fonts, depth)

    def _populate_items(self, depth):
        occupied = set()

        # Normal random items
        count = len(self.dungeon.rooms) + random.randint(2, 5)
        for _ in range(count):
            pos = self.dungeon.random_floor(occupied)
            if pos:
                item = random_item(depth)
                self.dungeon.items.append((pos[0], pos[1], item))
                occupied.add(pos)

        # Guaranteed healing potion
        pos = self.dungeon.random_floor(occupied)
        if pos:
            p = Potion("healing", "healing")
            self.dungeon.items.append((pos[0], pos[1], p))
            occupied.add(pos)

        # Special room loot
        for room in self.dungeon.rooms:
            self._populate_special_room(room, depth, occupied)

    def _populate_special_room(self, room, depth, occupied):
        cx, cy = room.center()
        if room.kind == 'treasure':
            for _ in range(4):
                pos = self._room_floor(room, occupied)
                if pos:
                    item = random_item(depth)
                    item.level += 1
                    self.dungeon.items.append((pos[0], pos[1], item))
                    occupied.add(pos)
            self.dungeon.items.append((cx, cy, Gold(random.randint(50, 150) * depth)))
            self.messages  # silent

        elif room.kind == 'armory':
            for _ in range(3):
                pos = self._room_floor(room, occupied)
                if pos:
                    w = random.choice([f() for f in __import__('items').WEAPONS])
                    self.dungeon.items.append((pos[0], pos[1], w))
                    occupied.add(pos)
            for _ in range(2):
                pos = self._room_floor(room, occupied)
                if pos:
                    a = random.choice([f() for f in __import__('items').ARMORS])
                    self.dungeon.items.append((pos[0], pos[1], a))
                    occupied.add(pos)

        elif room.kind == 'library':
            for _ in range(4):
                pos = self._room_floor(room, occupied)
                if pos:
                    name, _ = random.choice(__import__('items').SCROLLS_DEF)
                    s = Scroll(name, name)
                    self.dungeon.items.append((pos[0], pos[1], s))
                    occupied.add(pos)
            for _ in range(2):
                pos = self._room_floor(room, occupied)
                if pos:
                    n, ch = random.choice(__import__('items').WANDS_DEF)
                    w = Wand(n, n, ch)
                    self.dungeon.items.append((pos[0], pos[1], w))
                    occupied.add(pos)

        elif room.kind == 'garden':
            for x, y in room.inner_tiles():
                if self.dungeon.tiles[x][y] == FLOOR and random.random() < 0.5:
                    self.dungeon.tiles[x][y] = GRASS
            for _ in range(3):
                pos = self._room_floor(room, occupied)
                if pos:
                    p = Potion("healing", "healing")
                    self.dungeon.items.append((pos[0], pos[1], p))
                    occupied.add(pos)

        elif room.kind == 'shop':
            for _ in range(5):
                pos = self._room_floor(room, occupied)
                if pos:
                    item = random_item(depth)
                    item._shop_price = max(10, (item.value or 10) * depth + random.randint(5, 20))
                    self.dungeon.items.append((pos[0], pos[1], item))
                    occupied.add(pos)
            # Place shopkeeper at center
            cx, cy = room.center()
            self.dungeon.shop_pos = (cx, cy)
            occupied.add((cx, cy))

    def _room_floor(self, room, occupied):
        tiles = [(x, y) for x, y in room.inner_tiles()
                 if self.dungeon.tiles[x][y] in (FLOOR, GRASS) and (x, y) not in occupied]
        return random.choice(tiles) if tiles else None

    def _update_camera(self):
        view_w = (SCREEN_W - PANEL_W) // TILE_SIZE
        view_h = SCREEN_H // TILE_SIZE
        self.cam_x = max(0, min(self.player.x - view_w//2, self.dungeon.width  - view_w))
        self.cam_y = max(0, min(self.player.y - view_h//2, self.dungeon.height - view_h))

    # ── Main loop ─────────────────────────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                self._handle_event(event)

            # Advance floating texts
            self.float_texts = [ft for ft in self.float_texts if ft.alive()]
            for ft in self.float_texts:
                ft.update()

            # Click-to-move: one step per frame when no key held
            if self.state == 'playing' and self.mouse_path:
                nx, ny = self.mouse_path.pop(0)
                dx, dy = nx - self.player.x, ny - self.player.y
                moved = self._try_move(dx, dy)
                if moved:
                    self._end_turn()
                else:
                    self.mouse_path.clear()

            self._draw()

    # ── Event routing ─────────────────────────────────────────────────────────
    def _handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            if self.state != 'settings':
                self._prev_state = self.state
                self.state = 'settings'
            else:
                self.state = self._prev_state
            return
        # Ctrl+S to save
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_s
                and pygame.key.get_mods() & pygame.KMOD_CTRL
                and self.state == 'playing'):
            save(self.player, self.dungeon, self.messages)
            self.messages.append("Game saved.")
            return
        if self.state == 'class_select':  self._handle_class_select(event)
        elif self.state == 'settings':    self._handle_settings(event)
        elif self.state == 'targeting':   self._handle_targeting(event)
        elif self.state == 'playing':     self._handle_playing(event)
        elif self.state == 'inventory':   self._handle_inventory(event)
        elif self.state == 'item_select': self._handle_item_select(event)
        elif self.state in ('game_over', 'win'): self._handle_end(event)

    def _handle_targeting(self, event):
        if event.type == pygame.KEYDOWN:
            key_dirs = {
                pygame.K_UP:(0,-1), pygame.K_k:(0,-1),
                pygame.K_DOWN:(0,1), pygame.K_j:(0,1),
                pygame.K_LEFT:(-1,0), pygame.K_h:(-1,0),
                pygame.K_RIGHT:(1,0), pygame.K_l:(1,0),
                pygame.K_y:(-1,-1), pygame.K_u:(1,-1),
                pygame.K_b:(-1,1),  pygame.K_n:(1,1),
            }
            if event.key in key_dirs:
                dx, dy = key_dirs[event.key]
                nx = max(0, min(self.dungeon.width-1,  self.cursor_x + dx))
                ny = max(0, min(self.dungeon.height-1, self.cursor_y + dy))
                self.cursor_x, self.cursor_y = nx, ny
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.player.throw_potion(self.targeting, self.cursor_x, self.cursor_y,
                                         self.dungeon, self.messages)
                self.targeting = None
                self.state = 'playing'
                self._end_turn()
            elif event.key == pygame.K_ESCAPE:
                self.messages.append("Cancelled.")
                self.targeting = None
                self.state = 'playing'
        # Mouse click to confirm target
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if mx < SIDEBAR_X:
                self.cursor_x = mx // TILE_SIZE + self.cam_x
                self.cursor_y = my // TILE_SIZE + self.cam_y
                self.player.throw_potion(self.targeting, self.cursor_x, self.cursor_y,
                                         self.dungeon, self.messages)
                self.targeting = None
                self.state = 'playing'
                self._end_turn()

    def _handle_settings(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = self._prev_state

    def _handle_class_select(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c and has_save():
                self._continue_game()
            else:
                for i, cls in enumerate(CLASSES_INFO.keys()):
                    if event.key == getattr(pygame, f'K_{i+1}'):
                        self.new_game(cls)

    def _continue_game(self):
        player, dungeon, messages = load()
        if player and dungeon:
            self.player  = player
            self.dungeon = dungeon
            self.messages = messages
            self.messages.append("Game loaded.")
            self.float_texts.clear()
            self.mouse_path.clear()
            self._update_camera()
            self.state = 'playing'
        else:
            self.messages.append("No save found.")

    def _handle_end(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                delete_save()
                self.state = 'class_select'; init_aliases()
            elif event.key == pygame.K_q:
                pygame.quit(); sys.exit()

    def _handle_playing(self, event):
        p = self.player
        d = self.dungeon

        # Mouse click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            slot_index = quickslot_at(event.pos)
            if slot_index is not None:
                if self._activate_quickslot(slot_index):
                    self._end_turn()
                return
            if mx < SIDEBAR_X:
                tx = mx // TILE_SIZE + self.cam_x
                ty = my // TILE_SIZE + self.cam_y
                # Click on enemy = attack path
                target_enemy = next((e for e in d.enemies if e.x==tx and e.y==ty and e.is_alive()), None)
                if target_enemy:
                    self.mouse_path = self._path_to(p.x, p.y, tx, ty, adjacent=True)
                elif d.walkable(tx, ty):
                    self.mouse_path = self._path_to(p.x, p.y, tx, ty)
            return

        # Mouse move for tooltip
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if mx < SIDEBAR_X:
                tx = mx // TILE_SIZE + self.cam_x
                ty = my // TILE_SIZE + self.cam_y
                self.hover_item = next((item for ix,iy,item in d.items if ix==tx and iy==ty and d.lit[ix][iy]), None)
            return

        if event.type != pygame.KEYDOWN:
            return

        moved = False
        key_dirs = {
            pygame.K_UP:(0,-1), pygame.K_k:(0,-1),
            pygame.K_DOWN:(0,1), pygame.K_j:(0,1),
            pygame.K_LEFT:(-1,0), pygame.K_h:(-1,0),
            pygame.K_RIGHT:(1,0), pygame.K_l:(1,0),
            pygame.K_y:(-1,-1), pygame.K_u:(1,-1),
            pygame.K_b:(-1,1),  pygame.K_n:(1,1),
        }

        if event.key in key_dirs:
            self.mouse_path.clear()
            moved = self._try_move(*key_dirs[event.key])

        elif event.key in (pygame.K_i, pygame.K_TAB):
            self.state = 'inventory'; self.inv_sel = 0

        elif event.key == pygame.K_g:
            self._pick_up(); moved = True

        elif event.key == pygame.K_f:
            self._search_secret(); moved = True

        elif event.key == pygame.K_PERIOD:
            if d.get_tile(p.x, p.y) == STAIRS_DOWN:
                if p.depth >= MAX_DEPTH: self.state = 'win'
                else:
                    self._load_depth(p.depth + 1)
                    self.messages.append(f"You descend to depth {p.depth}.")
                    save(self.player, self.dungeon, self.messages)
            else:
                self.messages.append("No stairs here.")

        elif event.key == pygame.K_COMMA:
            if d.get_tile(p.x, p.y) == STAIRS_UP and p.depth > 1:
                self._load_depth(p.depth - 1)
                self.messages.append(f"You ascend to depth {p.depth}.")
                save(self.player, self.dungeon, self.messages)
            else:
                self.messages.append("No stairs up here.")

        elif event.key == pygame.K_s:
            moved = True

        elif event.key == pygame.K_t:
            targets = sorted([e for e in d.enemies if e.is_alive() and d.lit[e.x][e.y]],
                             key=lambda e: abs(e.x-p.x)+abs(e.y-p.y))
            if targets:
                p.throw_missile(targets[0], d, self.messages); moved = True
            else:
                self.messages.append("No visible targets.")

        # Quickslot use: keys 1-4
        elif pygame.K_1 <= event.key <= pygame.K_4:
            idx = event.key - pygame.K_1
            moved = self._activate_quickslot(idx)

        if moved:
            self._end_turn()

    def _activate_quickslot(self, index):
        p = self.player
        if not 0 <= index < len(p.quickslots):
            return False
        if index == 0:
            return p.use_ability(self.dungeon, self.messages)

        item = p.quickslots[index]
        if item is None:
            return False
        if item not in p.inventory:
            p.quickslots[index] = None
            return False

        result = p.use_item(item, self.dungeon, self.messages)
        if item not in p.inventory:
            p.quickslots[index] = None
        if result:
            self._select_purpose = result['action']
            self._select_scroll = result['scroll']
            self._select_items = self._scroll_targets(result['action'])
            self.inv_sel = 0
            self.state = 'item_select'
            return False
        return True

    def _try_move(self, dx, dy):
        p = self.player; d = self.dungeon
        nx, ny = p.x + dx, p.y + dy
        if not (0 <= nx < d.width and 0 <= ny < d.height):
            return False

        # Reveal secret door on bump
        if (nx, ny) in d.secret_doors:
            d.secret_doors.discard((nx, ny))
            self.messages.append("You found a secret door!")
            return True

        for enemy in d.enemies:
            if enemy.x == nx and enemy.y == ny and enemy.is_alive():
                prev_hp = enemy.stats.hp
                p.attack(enemy, d, self.messages)
                dmg = prev_hp - enemy.stats.hp
                if dmg > 0:
                    self.float_texts.append(FloatText(str(dmg), enemy.x, enemy.y, RED))
                if not enemy.is_alive():
                    d.enemies.remove(enemy)
                return True

        if d.tiles[nx][ny] == DOOR:
            d.tiles[nx][ny] = FLOOR
            self.messages.append("You open the door.")
            p.x, p.y = nx, ny
            return True

        if d.walkable(nx, ny):
            p.x, p.y = nx, ny
            # Dew drop
            if (nx, ny) in d.dew_drops:
                heal = random.randint(2, 5)
                p.stats.hp = min(p.stats.max_hp, p.stats.hp + heal)
                d.dew_drops.discard((nx, ny))
                self.messages.append(f"A dew drop restores {heal} HP.")
                self.float_texts.append(FloatText(f"+{heal}", nx, ny, GREEN))
            return True

        return False

    def _search_secret(self):
        p = self.player; d = self.dungeon
        found = False
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                pos = (p.x+dx, p.y+dy)
                if pos in d.secret_doors:
                    d.secret_doors.discard(pos)
                    self.messages.append("You found a secret door!")
                    found = True
        if not found:
            self.messages.append("You search but find nothing.")

    def _pick_up(self):
        p = self.player; d = self.dungeon
        to_remove = []; picked = False
        for entry in d.items:
            ix, iy, item = entry
            if ix == p.x and iy == p.y:
                # Shop item
                if hasattr(item, '_shop_price'):
                    if p.gold >= item._shop_price:
                        p.gold -= item._shop_price
                        del item._shop_price
                        if p.add_item(item):
                            self.messages.append(f"Bought {item.display_name()}.")
                            to_remove.append(entry); picked = True
                    else:
                        self.messages.append(f"Costs {item._shop_price} gold. You have {p.gold}.")
                    continue
                if p.add_item(item):
                    self.messages.append(f"You pick up {item.display_name()}.")
                    to_remove.append(entry); picked = True
                else:
                    self.messages.append("Inventory full!")
        for e in to_remove:
            d.items.remove(e)
        if not picked:
            self.messages.append("Nothing here.")

    def _end_turn(self):
        p = self.player; d = self.dungeon
        p.tick(d, self.messages)
        if not p.alive:
            self.state = 'game_over'; return

        for enemy in list(d.enemies):
            if enemy.is_alive():
                prev_hp = p.stats.hp
                enemy.act(d, p, self.messages)
                dmg = prev_hp - p.stats.hp
                if dmg > 0:
                    self.float_texts.append(FloatText(str(dmg), p.x, p.y, ORANGE))
                if 'summon' in enemy.abilities and random.random() < 0.05:
                    self._summon_near(enemy, d)

        if not p.alive:
            self.state = 'game_over'; return

        d.compute_fov(p.x, p.y)
        self._update_camera()
        if len(self.messages) > 200:
            self.messages = self.messages[-100:]

    def _summon_near(self, summoner, dungeon):
        from enemies import make_rat, make_skeleton
        factory = make_skeleton if summoner.depth >= 6 else make_rat
        pos = dungeon.random_floor({(summoner.x, summoner.y)})
        if pos and abs(pos[0]-summoner.x)+abs(pos[1]-summoner.y) < 5:
            e = factory(); e.x, e.y = pos
            dungeon.enemies.append(e)

    def _path_to(self, x1, y1, x2, y2, adjacent=False):
        from collections import deque
        goal = (x2, y2)
        queue = deque([[(x1, y1)]])
        visited = {(x1, y1)}
        while queue:
            path = queue.popleft()
            cx, cy = path[-1]
            if adjacent and abs(cx-x2) <= 1 and abs(cy-y2) <= 1:
                return path[1:]
            if (cx, cy) == goal:
                return path[1:]
            if len(path) > 30:
                break
            for ddx, ddy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = cx+ddx, cy+ddy
                if (nx,ny) not in visited and self.dungeon.walkable(nx, ny):
                    visited.add((nx,ny))
                    queue.append(path+[(nx,ny)])
        return []

    # ── Inventory ─────────────────────────────────────────────────────────────
    def _handle_inventory(self, event):
        if event.type != pygame.KEYDOWN:
            return
        p = self.player; items = p.inventory

        if event.key == pygame.K_ESCAPE:
            self.state = 'playing'
        elif event.key in (pygame.K_UP, pygame.K_k):
            self.inv_sel = max(0, self.inv_sel - 1)
        elif event.key in (pygame.K_DOWN, pygame.K_j):
            self.inv_sel = min(len(items)-1, self.inv_sel+1)
        elif event.key == pygame.K_e and items:
            item = items[self.inv_sel]
            result = p.use_item(item, self.dungeon, self.messages)
            if result:  # interactive scroll needs item selection
                self._select_purpose = result['action']
                self._select_scroll  = result['scroll']
                self._select_items   = self._scroll_targets(result['action'])
                self.inv_sel = 0
                self.state = 'item_select'
            else:
                self.inv_sel = min(self.inv_sel, max(0, len(p.inventory)-1))
                self._end_turn()
                self.state = 'playing'
        elif event.key == pygame.K_r and items:
            item = items[self.inv_sel]
            if item.itype == POTION:
                self.targeting  = item
                self.cursor_x   = self.player.x
                self.cursor_y   = self.player.y
                self.state      = 'targeting'
                self.messages.append("Throw where? (arrows to aim, Enter/click to throw, ESC to cancel)")
            else:
                self.messages.append("You can only throw potions.")
        elif event.key == pygame.K_d and items:
            item = items[self.inv_sel]
            if item in [p.weapon, p.armor, p.ring1, p.ring2]:
                self.messages.append("Unequip first.")
            else:
                p.remove_item(item)
                p.quickslots = [slot if slot is not item else None for slot in p.quickslots]
                self.dungeon.items.append((p.x, p.y, item))
                self.messages.append(f"Dropped {item.display_name()}.")
            self.inv_sel = min(self.inv_sel, max(0, len(p.inventory)-1))
        elif event.key == pygame.K_q and items:
            # Assign to quickslot
            item = items[self.inv_sel]
            # Slot 1 is reserved for the class ability.
            empty = next((i for i in range(1, len(p.quickslots))
                          if p.quickslots[i] is None), None)
            if empty is not None:
                p.quickslots[empty] = item
                self.messages.append(f"Assigned {item.display_name()} to slot {empty+1}.")
            else:
                p.quickslots[1] = item
                self.messages.append(f"Assigned {item.display_name()} to slot 2.")
        elif pygame.K_a <= event.key <= pygame.K_z:
            idx = event.key - pygame.K_a
            if 0 <= idx < len(items):
                self.inv_sel = idx

    def _scroll_targets(self, action):
        p = self.player
        if action == 'identify':
            return [i for i in p.inventory if not i.identified and i is not self._select_scroll]
        elif action == 'upgrade':
            return [i for i in p.inventory if i.itype in (WEAPON, ARMOR) and i is not self._select_scroll]
        elif action == 'enchant_weapon':
            return [i for i in p.inventory if i.itype == WEAPON]
        elif action == 'enchant_armor':
            return [i for i in p.inventory if i.itype == ARMOR]
        elif action == 'transmute':
            return [i for i in p.inventory
                    if i not in (p.weapon, p.armor, p.ring1, p.ring2) and i is not self._select_scroll]
        return []

    def _handle_item_select(self, event):
        if event.type != pygame.KEYDOWN:
            return
        items = self._select_items
        if event.key == pygame.K_ESCAPE:
            self.messages.append("Cancelled.")
            self.player.remove_item(self._select_scroll)
            self._select_scroll = self._select_purpose = None
            self.state = 'playing'
        elif event.key in (pygame.K_UP, pygame.K_k):
            self.inv_sel = max(0, self.inv_sel - 1)
        elif event.key in (pygame.K_DOWN, pygame.K_j):
            self.inv_sel = min(len(items) - 1, self.inv_sel + 1)
        elif event.key == pygame.K_RETURN and items:
            target = items[self.inv_sel]
            self.player.apply_scroll_to_item(self._select_scroll, target, self.dungeon, self.messages)
            self._select_scroll = self._select_purpose = None
            self._select_items = []
            self.inv_sel = 0
            self._end_turn()
            self.state = 'playing'
        elif pygame.K_a <= event.key <= pygame.K_z:
            idx = event.key - pygame.K_a
            if 0 <= idx < len(items):
                self.inv_sel = idx

    # ── Draw ──────────────────────────────────────────────────────────────────
    def _draw(self):
        self.screen.fill(BLACK)

        if self.state == 'class_select':
            draw_class_select(self.screen, self.fonts, has_save(), self.sprites)

        elif self.state in ('playing', 'inventory', 'item_select'):
            map_surf = pygame.Surface((SCREEN_W - PANEL_W, SCREEN_H))
            map_surf.fill(BLACK)
            draw_map(map_surf, self.fonts, self.dungeon, self.player,
                     self.cam_x, self.cam_y, self.sprites, self.float_texts)
            self.screen.blit(map_surf, (0, 0))

            # Quickslot bar
            draw_quickslots(self.screen, self.fonts, self.player, self.sprites)

            # Sidebar
            pygame.draw.rect(self.screen, (15,15,25), (SIDEBAR_X, 0, PANEL_W, SCREEN_H))
            pygame.draw.line(self.screen, DGRAY, (SIDEBAR_X, 0), (SIDEBAR_X, SCREEN_H))
            hud_bottom = draw_hud(self.screen, self.fonts, self.player, self.sprites)
            pygame.draw.line(self.screen, DGRAY, (SIDEBAR_X, hud_bottom+4), (SCREEN_W, hud_bottom+4))
            mini_bottom = draw_minimap(self.screen, self.fonts, self.dungeon, self.player, hud_bottom+8)
            pygame.draw.line(self.screen, DGRAY, (SIDEBAR_X, mini_bottom), (SCREEN_W, mini_bottom))
            draw_messages(self.screen, self.fonts, self.messages, mini_bottom+6)

            # Tooltip
            if self.hover_item and self.state == 'playing':
                mx, my = pygame.mouse.get_pos()
                draw_tooltip(self.screen, self.fonts, self.hover_item, mx, my,
                             self.sprites)

            if self.state == 'inventory':
                ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                ov.fill((0,0,0,210))
                self.screen.blit(ov, (0,0))
                draw_inventory(self.screen, self.fonts, self.player, self.inv_sel,
                               self.sprites)

            if self.state == 'item_select':
                ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                ov.fill((0,0,0,210))
                self.screen.blit(ov, (0,0))
                draw_item_select(self.screen, self.fonts, self._select_items,
                                 self._select_purpose, self.inv_sel, self.sprites)

            if self.state == 'targeting':
                # Cursor highlight
                cx = (self.cursor_x - self.cam_x) * TILE_SIZE
                cy = (self.cursor_y - self.cam_y) * TILE_SIZE
                pygame.draw.rect(self.screen, YELLOW, (cx, cy, TILE_SIZE, TILE_SIZE), 3)
                # Splash radius indicator (2 tiles)
                for rx in range(-2, 3):
                    for ry in range(-2, 3):
                        if abs(rx)+abs(ry) <= 2 and (rx, ry) != (0, 0):
                            sx = (self.cursor_x + rx - self.cam_x) * TILE_SIZE
                            sy = (self.cursor_y + ry - self.cam_y) * TILE_SIZE
                            if 0 <= sx < SIDEBAR_X and 0 <= sy < SCREEN_H:
                                s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                                s.fill((220, 200, 50, 50))
                                self.screen.blit(s, (sx, sy))
                hint_t = f"Throwing: {self.targeting.display_name()}  |  Arrows=aim  Enter/Click=throw  ESC=cancel"
                ht = self.fonts['small'].render(hint_t, True, YELLOW)
                self.screen.blit(ht, (SIDEBAR_X//2 - ht.get_width()//2, SCREEN_H - 40))

        elif self.state == 'settings':
            draw_settings(self.screen, self.fonts)
        elif self.state == 'game_over':
            draw_game_over(self.screen, self.fonts, self.player, won=False,
                           sprites=self.sprites)
        elif self.state == 'win':
            draw_game_over(self.screen, self.fonts, self.player, won=True,
                           sprites=self.sprites)

        if self.state == 'playing':
            hint = "Arrows/hjkl=move  G=pickup  I=inv  T=throw  F=search  ./,=stairs  Click/1-4=ability or item  S=wait  Ctrl+S=save"
            h = self.fonts['tiny'].render(hint, True, DGRAY)
            self.screen.blit(h, (4, SCREEN_H - 18))

        pygame.display.flip()
