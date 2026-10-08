import pygame
import sys
import random
from constants import *
from dungeon import DungeonMap
from entities import Player
from enemies import spawn_enemies
from items import random_item, init_aliases, Gold
from ui import (init_fonts, draw_hud, draw_messages, draw_map,
                draw_inventory, draw_class_select, draw_game_over,
                draw_depth_transition, draw_settings, CLASSES_INFO)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Pixel Dungeon")
        self.clock  = pygame.time.Clock()
        self.fonts  = init_fonts()
        self.sprites = self._load_sprites()
        self.state  = 'class_select'  # class_select, settings, playing, inventory, game_over, win
        self._prev_state = 'class_select'
        self.player = None
        self.dungeon = None
        self.messages = []
        self.inv_sel  = 0
        self.cam_x = self.cam_y = 0
        init_aliases()

    def _load_sprites(self):
        sprites = {}
        sprite_files = {
            'Rat':   'assets/rat.png',
            'wall':  'assets/Wall1.png',
            'floor': 'assets/floor one.png',
            'player': 'assets/HeroK.jpg',
        }
        for name, path in sprite_files.items():
            try:
                img = pygame.image.load(path).convert_alpha()
                sprites[name] = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            except Exception:
                pass
        return sprites

    def new_game(self, cls_name):
        self.player  = Player(cls_name)
        self.messages = []
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
        draw_depth_transition(self.screen, self.fonts, depth)

    def _populate_items(self, depth):
        rooms = self.dungeon.rooms[1:]  # skip start room
        item_count = len(rooms) + random.randint(2, 5)
        occupied = set()
        for _ in range(item_count):
            pos = self.dungeon.random_floor(occupied)
            if pos:
                item = random_item(depth)
                item.x, item.y = pos
                self.dungeon.items.append((pos[0], pos[1], item))
                occupied.add(pos)
        # Guaranteed healing potion near start
        from items import Potion
        p = Potion("healing", "healing")
        pos = self.dungeon.random_floor()
        if pos:
            self.dungeon.items.append((pos[0], pos[1], p))

    def _update_camera(self):
        view_w = (SCREEN_W - PANEL_W) // TILE_SIZE
        view_h = SCREEN_H // TILE_SIZE
        self.cam_x = max(0, min(self.player.x - view_w // 2, self.dungeon.width - view_w))
        self.cam_y = max(0, min(self.player.y - view_h // 2, self.dungeon.height - view_h))

    def run(self):
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                self._handle_event(event)
            self._draw()

    def _handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            if self.state != 'settings':
                self._prev_state = self.state
                self.state = 'settings'
            else:
                self.state = self._prev_state
            return
        if self.state == 'class_select':
            self._handle_class_select(event)
        elif self.state == 'settings':
            self._handle_settings(event)
        elif self.state == 'playing':
            self._handle_playing(event)
        elif self.state == 'inventory':
            self._handle_inventory(event)
        elif self.state in ('game_over', 'win'):
            self._handle_end(event)

    def _handle_settings(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = self._prev_state

    def _handle_class_select(self, event):
        if event.type == pygame.KEYDOWN:
            classes = list(CLASSES_INFO.keys())
            for i, cls in enumerate(classes):
                if event.key == getattr(pygame, f'K_{i+1}'):
                    self.new_game(cls)

    def _handle_end(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.state = 'class_select'
                init_aliases()
            elif event.key == pygame.K_q:
                pygame.quit(); sys.exit()

    def _handle_playing(self, event):
        if event.type != pygame.KEYDOWN:
            return
        p = self.player
        d = self.dungeon
        moved = False

        key_dirs = {
            pygame.K_UP:    (0, -1), pygame.K_k: (0, -1),
            pygame.K_DOWN:  (0,  1), pygame.K_j: (0,  1),
            pygame.K_LEFT:  (-1, 0), pygame.K_h: (-1, 0),
            pygame.K_RIGHT: ( 1, 0), pygame.K_l: ( 1, 0),
            pygame.K_y: (-1, -1), pygame.K_u: (1, -1),
            pygame.K_b: (-1,  1), pygame.K_n: (1,  1),
        }

        if event.key in key_dirs:
            dx, dy = key_dirs[event.key]
            moved = self._try_move(dx, dy)

        elif event.key == pygame.K_i or event.key == pygame.K_TAB:
            self.state = 'inventory'
            self.inv_sel = 0

        elif event.key == pygame.K_g:
            self._pick_up()
            moved = True

        elif event.key == pygame.K_PERIOD:  # > stairs down
            if d.get_tile(p.x, p.y) == STAIRS_DOWN:
                if p.depth >= MAX_DEPTH:
                    self.state = 'win'
                else:
                    self._load_depth(p.depth + 1)
                    self.messages.append(f"You descend to depth {p.depth}.")
            else:
                self.messages.append("No stairs here.")

        elif event.key == pygame.K_COMMA:  # < stairs up
            if d.get_tile(p.x, p.y) == STAIRS_UP and p.depth > 1:
                self._load_depth(p.depth - 1)
                self.messages.append(f"You ascend to depth {p.depth}.")
            else:
                self.messages.append("No stairs up here.")

        elif event.key == pygame.K_s:  # wait/rest
            moved = True

        elif event.key == pygame.K_t:  # throw missile at nearest enemy
            targets = [e for e in d.enemies if e.is_alive() and d.lit[e.x][e.y]]
            if targets:
                targets.sort(key=lambda e: abs(e.x-p.x)+abs(e.y-p.y))
                p.throw_missile(targets[0], d, self.messages)
                moved = True
            else:
                self.messages.append("No visible targets.")

        elif event.key == pygame.K_m:  # magic mapping cheat / show map toggle
            pass  # reserved

        if moved:
            self._end_turn()

    def _try_move(self, dx, dy):
        p = self.player
        d = self.dungeon
        nx, ny = p.x + dx, p.y + dy

        if not (0 <= nx < d.width and 0 <= ny < d.height):
            return False

        # Attack enemy
        for enemy in d.enemies:
            if enemy.x == nx and enemy.y == ny and enemy.is_alive():
                p.attack(enemy, d, self.messages)
                if not enemy.is_alive():
                    d.enemies.remove(enemy)
                return True

        # Open door
        if d.tiles[nx][ny] == DOOR:
            d.tiles[nx][ny] = FLOOR
            self.messages.append("You open the door.")
            p.x, p.y = nx, ny
            return True

        if d.walkable(nx, ny):
            p.x, p.y = nx, ny
            return True

        return False

    def _pick_up(self):
        p = self.player
        d = self.dungeon
        to_remove = []
        picked = False
        for entry in d.items:
            ix, iy, item = entry
            if ix == p.x and iy == p.y:
                if p.add_item(item):
                    self.messages.append(f"You pick up {item.display_name()}.")
                    to_remove.append(entry)
                    picked = True
                else:
                    self.messages.append("Inventory full!")
        for e in to_remove:
            d.items.remove(e)
        if not picked:
            self.messages.append("Nothing here.")

    def _end_turn(self):
        p = self.player
        d = self.dungeon

        p.tick(d, self.messages)
        if not p.alive:
            self.state = 'game_over'
            return

        # Enemy turns
        for enemy in list(d.enemies):
            if enemy.is_alive():
                enemy.act(d, p, self.messages)
                # Necromancer summon
                if 'summon' in enemy.abilities and random.random() < 0.05:
                    self._summon_near(enemy, d)

        if not p.alive:
            self.state = 'game_over'
            return

        d.compute_fov(p.x, p.y)
        self._update_camera()
        # Trim messages
        if len(self.messages) > 200:
            self.messages = self.messages[-100:]

    def _summon_near(self, summoner, dungeon):
        from enemies import make_rat, make_skeleton
        factory = make_skeleton if summoner.depth >= 6 else make_rat
        pos = dungeon.random_floor({(summoner.x, summoner.y)})
        if pos and abs(pos[0]-summoner.x)+abs(pos[1]-summoner.y) < 5:
            e = factory()
            e.x, e.y = pos
            dungeon.enemies.append(e)

    def _handle_inventory(self, event):
        if event.type != pygame.KEYDOWN:
            return
        p = self.player
        items = p.inventory

        if event.key == pygame.K_ESCAPE:
            self.state = 'playing'
        elif event.key == pygame.K_UP or event.key == pygame.K_k:
            self.inv_sel = max(0, self.inv_sel - 1)
        elif event.key == pygame.K_DOWN or event.key == pygame.K_j:
            self.inv_sel = min(len(items) - 1, self.inv_sel + 1)
        elif event.key == pygame.K_e and items:
            item = items[self.inv_sel]
            p.use_item(item, self.dungeon, self.messages)
            self.inv_sel = min(self.inv_sel, max(0, len(p.inventory) - 1))
            self._end_turn()
        elif event.key == pygame.K_d and items:
            item = items[self.inv_sel]
            if item in [p.weapon, p.armor, p.ring1, p.ring2]:
                self.messages.append("Unequip first.")
            else:
                p.remove_item(item)
                item.x, item.y = p.x, p.y
                self.dungeon.items.append((p.x, p.y, item))
                self.messages.append(f"Dropped {item.display_name()}.")
            self.inv_sel = min(self.inv_sel, max(0, len(p.inventory) - 1))
        # Quick letter select
        elif pygame.K_a <= event.key <= pygame.K_z:
            idx = event.key - pygame.K_a
            if 0 <= idx < len(items):
                self.inv_sel = idx

    def _draw(self):
        self.screen.fill(BLACK)

        if self.state == 'class_select':
            draw_class_select(self.screen, self.fonts)

        elif self.state in ('playing', 'inventory'):
            # Map area
            map_surf = pygame.Surface((SCREEN_W - PANEL_W, SCREEN_H))
            map_surf.fill(BLACK)
            draw_map(map_surf, self.fonts, self.dungeon, self.player, self.cam_x, self.cam_y, self.sprites)
            self.screen.blit(map_surf, (0, 0))

            # Sidebar
            pygame.draw.rect(self.screen, (15, 15, 25), (SCREEN_W - PANEL_W, 0, PANEL_W, SCREEN_H))
            pygame.draw.line(self.screen, DGRAY, (SCREEN_W - PANEL_W, 0), (SCREEN_W - PANEL_W, SCREEN_H))
            hud_bottom = draw_hud(self.screen, self.fonts, self.player)
            pygame.draw.line(self.screen, DGRAY, (SCREEN_W - PANEL_W, hud_bottom + 4), (SCREEN_W, hud_bottom + 4))
            draw_messages(self.screen, self.fonts, self.messages, hud_bottom + 8)

            if self.state == 'inventory':
                inv_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                inv_surf.fill((0, 0, 0, 210))
                self.screen.blit(inv_surf, (0, 0))
                draw_inventory(self.screen, self.fonts, self.player, self.inv_sel)

        elif self.state == 'settings':
            draw_settings(self.screen, self.fonts)

        elif self.state == 'game_over':
            draw_game_over(self.screen, self.fonts, self.player, won=False)

        elif self.state == 'win':
            draw_game_over(self.screen, self.fonts, self.player, won=True)

        # Controls hint
        if self.state == 'playing':
            hint = "Arrows/hjkl=move  G=pickup  I=inv  T=throw  ./,=stairs  S=wait"
            self.fonts['small'].render(hint, True, DGRAY)
            h = self.fonts['small'].render(hint, True, DGRAY)
            self.screen.blit(h, (4, SCREEN_H - 16))

        pygame.display.flip()
