import random
import math
from constants import *

class Room:
    def __init__(self, x, y, w, h, kind='normal'):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.kind = kind  # normal, treasure, shop, garden, armory, library, boss

    def center(self):
        return self.x + self.w // 2, self.y + self.h // 2

    def intersects(self, other, pad=1):
        return (self.x - pad < other.x + other.w and
                self.x + self.w + pad > other.x and
                self.y - pad < other.y + other.h and
                self.y + self.h + pad > other.y)

    def inner_tiles(self):
        for y in range(self.y + 1, self.y + self.h - 1):
            for x in range(self.x + 1, self.x + self.w - 1):
                yield x, y

    def border_tiles(self):
        for x in range(self.x, self.x + self.w):
            yield x, self.y
            yield x, self.y + self.h - 1
        for y in range(self.y + 1, self.y + self.h - 1):
            yield self.x, y
            yield self.x + self.w - 1, y


class DungeonMap:
    def __init__(self, depth):
        self.depth  = depth
        self.width  = MAP_W
        self.height = MAP_H
        self.tiles   = [[WALL]  * self.height for _ in range(self.width)]
        self.visited = [[False] * self.height for _ in range(self.width)]
        self.lit     = [[False] * self.height for _ in range(self.width)]
        self.rooms   = []
        self.items   = []       # (x, y, Item)
        self.enemies = []
        self.traps   = {}       # (x,y) -> trap_type str
        self.secret_doors = set()
        self.dew_drops = set()  # (x,y)
        self.shop_pos  = None   # (x,y) of shopkeeper
        self.stairs_down = None
        self.stairs_up   = None
        self._generate()

    # ── Generation ────────────────────────────────────────────────────────────
    def _generate(self):
        is_boss = self.depth in BOSS_DEPTHS

        if is_boss:
            self._generate_boss_arena()
        else:
            self._generate_rooms()

        self._place_stairs()
        self._place_doors()
        self._place_secret_doors()
        self._place_water()
        self._place_grass()
        self._place_traps()
        self._place_dew_drops()

    def _generate_rooms(self):
        special_pool = ['treasure', 'shop', 'garden', 'armory', 'library']
        random.shuffle(special_pool)
        special_assigned = 0

        for _ in range(300):
            w = random.randint(5, 11)
            h = random.randint(5, 11)
            x = random.randint(1, self.width  - w - 1)
            y = random.randint(1, self.height - h - 1)
            room = Room(x, y, w, h)
            if any(room.intersects(r) for r in self.rooms):
                continue
            # Assign special kind to some rooms (not first or last)
            if (special_assigned < len(special_pool) and
                    len(self.rooms) > 0 and random.random() < 0.25):
                room.kind = special_pool[special_assigned]
                special_assigned += 1
            self._carve_room(room)
            if self.rooms:
                self._connect(self.rooms[-1].center(), room.center())
            self.rooms.append(room)
            if len(self.rooms) >= 14:
                break

    def _generate_boss_arena(self):
        # Large central arena
        cx, cy = self.width // 2 - 6, self.height // 2 - 6
        arena = Room(cx, cy, 13, 13, 'boss')
        self._carve_room(arena)
        self.rooms.append(arena)
        # Entry corridor room
        entry = Room(2, self.height // 2 - 2, 6, 5)
        self._carve_room(entry)
        self._connect(entry.center(), arena.center())
        self.rooms.append(entry)

    def _carve_room(self, room):
        for x, y in room.inner_tiles():
            self.tiles[x][y] = FLOOR

    def _connect(self, a, b):
        x1, y1 = a; x2, y2 = b
        if random.random() < 0.5:
            self._h_tunnel(x1, x2, y1); self._v_tunnel(y1, y2, x2)
        else:
            self._v_tunnel(y1, y2, x1); self._h_tunnel(x1, x2, y2)

    def _h_tunnel(self, x1, x2, y):
        for x in range(min(x1,x2), max(x1,x2)+1):
            if 0 < x < self.width and 0 < y < self.height:
                self.tiles[x][y] = FLOOR

    def _v_tunnel(self, y1, y2, x):
        for y in range(min(y1,y2), max(y1,y2)+1):
            if 0 < x < self.width and 0 < y < self.height:
                self.tiles[x][y] = FLOOR

    def _place_stairs(self):
        if len(self.rooms) < 2:
            return
        sx, sy = self.rooms[0].center()
        self.tiles[sx][sy] = STAIRS_UP
        self.stairs_up = (sx, sy)
        dx, dy = self.rooms[-1].center()
        self.tiles[dx][dy] = STAIRS_DOWN
        self.stairs_down = (dx, dy)

    def _place_doors(self):
        for room in self.rooms:
            for x, y in room.border_tiles():
                if self.tiles[x][y] == FLOOR:
                    adj = sum(1 for ddx,ddy in [(0,1),(0,-1),(1,0),(-1,0)]
                              if 0<=x+ddx<self.width and 0<=y+ddy<self.height
                              and self.tiles[x+ddx][y+ddy] == FLOOR)
                    if adj == 2 and random.random() < 0.4:
                        self.tiles[x][y] = DOOR

    def _place_secret_doors(self):
        count = self.depth // 4 + 1
        walls = [(x, y) for x in range(1, self.width-1) for y in range(1, self.height-1)
                 if self.tiles[x][y] == WALL]
        candidates = []
        for x, y in walls:
            h_floors = (self.tiles[x-1][y] == FLOOR and self.tiles[x+1][y] == FLOOR)
            v_floors = (self.tiles[x][y-1] == FLOOR and self.tiles[x][y+1] == FLOOR)
            if h_floors or v_floors:
                candidates.append((x, y))
        for pos in random.sample(candidates, min(count, len(candidates))):
            self.secret_doors.add(pos)

    def _place_water(self):
        if self.depth % 5 in (0, 1):
            for room in random.sample(self.rooms, min(2, len(self.rooms))):
                cx, cy = room.center()
                for x, y in room.inner_tiles():
                    if abs(x-cx)+abs(y-cy) < 2 and random.random() < 0.6:
                        self.tiles[x][y] = WATER

    def _place_grass(self):
        if self.depth <= 5:
            for room in self.rooms:
                for x, y in room.inner_tiles():
                    if self.tiles[x][y] == FLOOR and random.random() < 0.15:
                        self.tiles[x][y] = GRASS

    def _place_traps(self):
        trap_types = ['damage', 'poison', 'teleport', 'alarm', 'gripping',
                      'fire', 'chasm', 'disintegration']
        count = self.depth // 3 + 2
        floors = [(x,y) for x in range(self.width) for y in range(self.height)
                  if self.tiles[x][y] == FLOOR]
        for pos in random.sample(floors, min(count, len(floors))):
            self.traps[pos] = random.choice(trap_types)

    def _place_dew_drops(self):
        count = random.randint(3, 7)
        floors = [(x,y) for x in range(self.width) for y in range(self.height)
                  if self.tiles[x][y] == FLOOR]
        for pos in random.sample(floors, min(count, len(floors))):
            self.dew_drops.add(pos)

    # ── Queries ───────────────────────────────────────────────────────────────
    def walkable(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tiles[x][y] in (FLOOR, DOOR, STAIRS_DOWN, STAIRS_UP, GRASS, WATER)

    def is_transparent(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        if (x, y) in self.secret_doors:
            return False
        return self.tiles[x][y] != WALL

    def compute_fov(self, ox, oy, radius=8):
        self.lit = [[False] * self.height for _ in range(self.width)]
        for angle in range(360):
            rad = math.radians(angle)
            rx, ry = float(ox), float(oy)
            for _ in range(radius):
                ix, iy = int(rx), int(ry)
                if not (0 <= ix < self.width and 0 <= iy < self.height):
                    break
                self.lit[ix][iy] = True
                self.visited[ix][iy] = True
                if not self.is_transparent(ix, iy):
                    break
                rx += math.cos(rad)
                ry += math.sin(rad)

    def random_floor(self, exclude=None):
        exclude = exclude or set()
        floors = [(x,y) for x in range(self.width) for y in range(self.height)
                  if self.tiles[x][y] in (FLOOR, GRASS) and (x,y) not in exclude]
        return random.choice(floors) if floors else None

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[x][y]
        return WALL

    def room_at(self, x, y):
        for r in self.rooms:
            if r.x < x < r.x+r.w-1 and r.y < y < r.y+r.h-1:
                return r
        return None
