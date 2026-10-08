import random
from constants import *

class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

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
        self.depth = depth
        self.width = MAP_W
        self.height = MAP_H
        self.tiles = [[WALL] * self.height for _ in range(self.width)]
        self.visited = [[False] * self.height for _ in range(self.width)]
        self.lit = [[False] * self.height for _ in range(self.width)]
        self.rooms = []
        self.items = []      # list of (x, y, Item)
        self.enemies = []    # list of Enemy
        self.traps = set()   # set of (x,y)
        self.stairs_down = None
        self.stairs_up = None
        self._generate()

    def _generate(self):
        attempts = 200
        for _ in range(attempts):
            w = random.randint(5, 10)
            h = random.randint(5, 10)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            room = Room(x, y, w, h)
            if any(room.intersects(r) for r in self.rooms):
                continue
            self._carve_room(room)
            if self.rooms:
                self._connect(self.rooms[-1].center(), room.center())
            self.rooms.append(room)
            if len(self.rooms) >= 12:
                break

        self._place_stairs()
        self._place_doors()
        self._place_water()
        self._place_grass()
        self._place_traps()

    def _carve_room(self, room):
        for x, y in room.inner_tiles():
            self.tiles[x][y] = FLOOR

    def _connect(self, a, b):
        x1, y1 = a
        x2, y2 = b
        if random.random() < 0.5:
            self._h_tunnel(x1, x2, y1)
            self._v_tunnel(y1, y2, x2)
        else:
            self._v_tunnel(y1, y2, x1)
            self._h_tunnel(x1, x2, y2)

    def _h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 < x < self.width and 0 < y < self.height:
                self.tiles[x][y] = FLOOR

    def _v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 < x < self.width and 0 < y < self.height:
                self.tiles[x][y] = FLOOR

    def _place_stairs(self):
        if len(self.rooms) < 2:
            return
        r0 = self.rooms[0]
        rn = self.rooms[-1]
        sx, sy = r0.center()
        self.tiles[sx][sy] = STAIRS_UP
        self.stairs_up = (sx, sy)
        dx, dy = rn.center()
        self.tiles[dx][dy] = STAIRS_DOWN
        self.stairs_down = (dx, dy)

    def _place_doors(self):
        for room in self.rooms:
            for x, y in room.border_tiles():
                if self.tiles[x][y] == FLOOR:
                    adj_floors = sum(
                        1 for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]
                        if 0 <= x+dx < self.width and 0 <= y+dy < self.height
                        and self.tiles[x+dx][y+dy] == FLOOR
                    )
                    if adj_floors == 2 and random.random() < 0.4:
                        self.tiles[x][y] = DOOR

    def _place_water(self):
        if self.depth % 5 in (0, 1):
            for room in random.sample(self.rooms, min(2, len(self.rooms))):
                cx, cy = room.center()
                for x, y in room.inner_tiles():
                    if abs(x - cx) + abs(y - cy) < 2 and random.random() < 0.6:
                        self.tiles[x][y] = WATER

    def _place_grass(self):
        if self.depth <= 5:
            for room in self.rooms:
                for x, y in room.inner_tiles():
                    if self.tiles[x][y] == FLOOR and random.random() < 0.15:
                        self.tiles[x][y] = GRASS

    def _place_traps(self):
        count = self.depth // 3 + 2
        floors = [(x, y) for x in range(self.width) for y in range(self.height)
                  if self.tiles[x][y] == FLOOR]
        for pos in random.sample(floors, min(count, len(floors))):
            self.traps.add(pos)

    def walkable(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tiles[x][y] in (FLOOR, DOOR, STAIRS_DOWN, STAIRS_UP, GRASS, TRAP, WATER)

    def is_transparent(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tiles[x][y] != WALL

    def compute_fov(self, ox, oy, radius=8):
        self.lit = [[False] * self.height for _ in range(self.width)]
        for angle in range(360):
            import math
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
        floors = [(x, y) for x in range(self.width) for y in range(self.height)
                  if self.tiles[x][y] in (FLOOR, GRASS) and (x, y) not in exclude]
        return random.choice(floors) if floors else None

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[x][y]
        return WALL
