import pygame
import sys
import random
from constants import *
from dungeon import DungeonMap
from entities import Player
from enemies import spawn_enemies
from items import random_item, init_aliases, Gold, Potion, Scroll, Wand, Food, Weapon, Armor, Ring
from ui import (init_fonts, draw_hud, draw_messages, draw_map, draw_minimap,
                draw_inventory, draw_class_select, draw_game_over,
                draw_depth_transition, draw_settings, draw_quickslots,
                draw_tooltip, FloatText, CLASSES_INFO)

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
        init_aliases()

    def _load_sprites(self):
        sprites = {}
        files = {
            'Rat':    'assets/rat.png',
            'wall':   'assets/Wall1.png',
            'floor':  'assets/floor one.png',
            'player': 'assets/HeroK.jpg',
        }
        for name, path in files.items():
            try:
                img = pygame.image.load(path).convert_alpha()
                sprites[name] = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            except Exception:
                pass
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
                    item._shop_price = (item.value or 10) * depth + random.randint(5, 20)
                    self.dungeon.items.append((pos[0], pos[1], item))
                    occupied.add(pos)

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
        if self.state == 'class_select':  self._handle_class_select(event)
        elif self.state == 'settings':    self._handle_settings(event)
        elif self.state == 'playing':     self._handle_playing(event)
        elif self.state == 'inventory':   self._handle_inventory(event)
        elif self.state in ('game_over', 'win'): self._handle_end(event)

    def _handle_settings(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = self._prev_state

    def _handle_class_select(self, event):
        if event.type == pygame.KEYDOWN:
            for i, cls in enumerate(CLASSES_INFO.keys()):
                if event.key == getattr(pygame, f'K_{i+1}'):
                    self.new_game(cls)

    def _handle_end(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.state = 'class_select'; init_aliases()
            elif event.key == pygame.K_q:
                pygame.quit(); sys.exit()

    def _handle_playing(self, event):
        p = self.player
        d = self.dungeon

        # Mouse click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
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
            else:
                self.messages.append("No stairs here.")

        elif event.key == pygame.K_COMMA:
            if d.get_tile(p.x, p.y) == STAIRS_UP and p.depth > 1:
                self._load_depth(p.depth - 1)
                self.messages.append(f"You ascend to depth {p.depth}.")
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
            if idx < len(p.quickslots) and p.quickslots[idx]:
                item = p.quickslots[idx]
                if item in p.inventory:
                    p.use_item(item, d, self.messages)
                    moved = True
                else:
                    p.quickslots[idx] = None

        if moved:
            self._end_turn()

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
            p.use_item(item, self.dungeon, self.messages)
            self.inv_sel = min(self.inv_sel, max(0, len(p.inventory)-1))
            self._end_turn()
        elif event.key == pygame.K_d and items:
            item = items[self.inv_sel]
            if item in [p.weapon, p.armor, p.ring1, p.ring2]:
                self.messages.append("Unequip first.")
            else:
                p.remove_item(item)
                self.dungeon.items.append((p.x, p.y, item))
                self.messages.append(f"Dropped {item.display_name()}.")
            self.inv_sel = min(self.inv_sel, max(0, len(p.inventory)-1))
        elif event.key == pygame.K_q and items:
            # Assign to quickslot
            item = items[self.inv_sel]
            # Find empty slot or cycle
            empty = next((i for i,s in enumerate(p.quickslots) if s is None), None)
            if empty is not None:
                p.quickslots[empty] = item
                self.messages.append(f"Assigned {item.display_name()} to slot {empty+1}.")
            else:
                # Replace slot 0
                p.quickslots[0] = item
                self.messages.append(f"Assigned {item.display_name()} to slot 1.")
        elif pygame.K_a <= event.key <= pygame.K_z:
            idx = event.key - pygame.K_a
            if 0 <= idx < len(items):
                self.inv_sel = idx

    # ── Draw ──────────────────────────────────────────────────────────────────
    def _draw(self):
        self.screen.fill(BLACK)

        if self.state == 'class_select':
            draw_class_select(self.screen, self.fonts)

        elif self.state in ('playing', 'inventory'):
            map_surf = pygame.Surface((SCREEN_W - PANEL_W, SCREEN_H))
            map_surf.fill(BLACK)
            draw_map(map_surf, self.fonts, self.dungeon, self.player,
                     self.cam_x, self.cam_y, self.sprites, self.float_texts)
            self.screen.blit(map_surf, (0, 0))

            # Quickslot bar
            draw_quickslots(self.screen, self.fonts, self.player)

            # Sidebar
            pygame.draw.rect(self.screen, (15,15,25), (SIDEBAR_X, 0, PANEL_W, SCREEN_H))
            pygame.draw.line(self.screen, DGRAY, (SIDEBAR_X, 0), (SIDEBAR_X, SCREEN_H))
            hud_bottom = draw_hud(self.screen, self.fonts, self.player)
            pygame.draw.line(self.screen, DGRAY, (SIDEBAR_X, hud_bottom+4), (SCREEN_W, hud_bottom+4))
            mini_bottom = draw_minimap(self.screen, self.fonts, self.dungeon, self.player, hud_bottom+8)
            pygame.draw.line(self.screen, DGRAY, (SIDEBAR_X, mini_bottom), (SCREEN_W, mini_bottom))
            draw_messages(self.screen, self.fonts, self.messages, mini_bottom+6)

            # Tooltip
            if self.hover_item and self.state == 'playing':
                mx, my = pygame.mouse.get_pos()
                draw_tooltip(self.screen, self.fonts, self.hover_item, mx, my)

            if self.state == 'inventory':
                ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                ov.fill((0,0,0,210))
                self.screen.blit(ov, (0,0))
                draw_inventory(self.screen, self.fonts, self.player, self.inv_sel)

        elif self.state == 'settings':
            draw_settings(self.screen, self.fonts)
        elif self.state == 'game_over':
            draw_game_over(self.screen, self.fonts, self.player, won=False)
        elif self.state == 'win':
            draw_game_over(self.screen, self.fonts, self.player, won=True)

        if self.state == 'playing':
            hint = "Arrows/hjkl=move  G=pickup  I=inv  T=throw  F=search  ./,=stairs  1-4=quickslot  S=wait"
            h = self.fonts['tiny'].render(hint, True, DGRAY)
            self.screen.blit(h, (4, SCREEN_H - 18))

        pygame.display.flip()
