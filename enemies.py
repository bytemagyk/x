import random
import math
from constants import *
from combat import Stats, attack_roll

class Enemy:
    def __init__(self, name, char, color, hp, str_, dex, exp, defense=0, depth=1):
        self.name    = name
        self.char    = char
        self.color   = color
        self.stats   = Stats(hp, str_, dex)
        self.exp     = exp
        self.defense = defense
        self.depth   = depth
        self.x = self.y = 0
        self.state   = 'idle'   # idle, chase, flee
        self.path    = []
        self.loot_chance = 0.3
        self.abilities = []
        self.armor   = None
        self.weapon  = None
        self.sleeping = False
        self.sleep_turns = 0

    def is_alive(self):
        return self.stats.is_alive()

    def take_damage(self, dmg):
        self.stats.hp -= dmg
        if self.sleeping:
            self.sleeping = False

    def dr(self):
        return self.defense + (self.armor.dr() if self.armor else 0)

    def act(self, dungeon, player, messages):
        if self.sleeping:
            self.sleep_turns -= 1
            if self.sleep_turns <= 0:
                self.sleeping = False
            return

        self.stats.tick_buffs()

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx*dx + dy*dy)

        if self.stats.has_buff('terror') or self.stats.has_buff('flee'):
            self._flee(dungeon, player)
            return

        if dist <= 1.5:
            self._melee(player, messages)
        elif dist <= 8 and dungeon.lit[self.x][self.y]:
            self.state = 'chase'
            self._move_toward(dungeon, player)
        elif self.state == 'chase':
            self._move_toward(dungeon, player)

    def _melee(self, player, messages):
        from items import Weapon
        dummy_weapon = type('W', (), {'damage': lambda s: random.randint(1, self.stats.str_), 'level': 0, 'enchantment': None})()
        hit, dmg, crit = attack_roll(self.stats, dummy_weapon, player.stats, player.armor)
        if hit:
            player.stats.hp -= dmg
            crit_str = " Critical!" if crit else ""
            messages.append(f"{self.name} hits you for {dmg}.{crit_str}")
            self._on_hit(player, messages)
        else:
            messages.append(f"{self.name} misses you.")

    def _on_hit(self, player, messages):
        if 'poison' in self.abilities:
            if random.random() < 0.3:
                player.stats.add_buff('poison', 6)
                messages.append("You are poisoned!")
        if 'bleed' in self.abilities:
            if random.random() < 0.25:
                player.stats.add_buff('bleed', 4)
                messages.append("You are bleeding!")
        if 'stun' in self.abilities:
            if random.random() < 0.2:
                player.stats.add_buff('paralysis', 2)
                messages.append("You are stunned!")
        if 'steal' in self.abilities:
            self._steal(player, messages)

    def _steal(self, player, messages):
        if player.gold > 0 and random.random() < 0.4:
            stolen = random.randint(1, max(1, player.gold // 4))
            player.gold -= stolen
            messages.append(f"{self.name} stole {stolen} gold!")

    def _flee(self, dungeon, player):
        dx = self.x - player.x
        dy = self.y - player.y
        nx = self.x + (1 if dx > 0 else -1 if dx < 0 else 0)
        ny = self.y + (1 if dy > 0 else -1 if dy < 0 else 0)
        if dungeon.walkable(nx, ny) and not self._occupied(nx, ny, dungeon):
            self.x, self.y = nx, ny

    def _move_toward(self, dungeon, player):
        path = self._bfs(dungeon, player)
        if path and len(path) > 1:
            nx, ny = path[1]
            if not self._occupied(nx, ny, dungeon):
                self.x, self.y = nx, ny

    def _occupied(self, x, y, dungeon):
        return any(e.x == x and e.y == y for e in dungeon.enemies if e is not self and e.is_alive())

    def _bfs(self, dungeon, player):
        from collections import deque
        start = (self.x, self.y)
        goal  = (player.x, player.y)
        queue = deque([[start]])
        visited = {start}
        while queue:
            path = queue.popleft()
            cx, cy = path[-1]
            if (cx, cy) == goal:
                return path
            if len(path) > 15:
                break
            for ddx, ddy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = cx+ddx, cy+ddy
                if (nx, ny) not in visited and dungeon.walkable(nx, ny):
                    visited.add((nx, ny))
                    queue.append(path + [(nx, ny)])
        return None

    def drop_loot(self, depth):
        from items import random_item, Gold
        loot = []
        if random.random() < self.loot_chance:
            loot.append(random_item(depth))
        if random.random() < 0.4:
            loot.append(Gold(random.randint(2, 10) * depth))
        return loot


# ── Enemy factories ───────────────────────────────────────────────────────────
def make_rat():
    e = Enemy("Rat", 'r', GRAY, 8, 4, 8, 2, 0)
    return e

def make_gnoll():
    e = Enemy("Gnoll", 'g', BROWN, 14, 8, 6, 5, 1)
    return e

def make_sewage_crab():
    e = Enemy("Sewage Crab", 'c', GREEN, 20, 10, 4, 7, 3)
    e.abilities = ['bleed']
    return e

def make_swamp_shaman():
    e = Enemy("Swamp Shaman", 's', DGREEN, 18, 7, 9, 8, 1)
    e.abilities = ['poison']
    return e

def make_skeleton():
    e = Enemy("Skeleton", 'S', WHITE, 22, 10, 7, 9, 2)
    return e

def make_thief():
    e = Enemy("Thief", 't', ORANGE, 16, 8, 12, 8, 1)
    e.abilities = ['steal']
    e.loot_chance = 0.6
    return e

def make_guard():
    e = Enemy("Guard", 'G', BLUE, 30, 12, 8, 12, 4)
    e.abilities = ['stun']
    return e

def make_necromancer():
    e = Enemy("Necromancer", 'N', PURPLE, 28, 10, 10, 15, 2)
    e.abilities = ['summon']
    return e

def make_cave_spinner():
    e = Enemy("Cave Spinner", 'x', BROWN, 35, 14, 8, 18, 3)
    e.abilities = ['poison', 'web']
    return e

def make_bat():
    e = Enemy("Vampire Bat", 'b', PURPLE, 25, 12, 14, 14, 1)
    e.abilities = ['bleed']
    return e

def make_golem():
    e = Enemy("Golem", 'G', GRAY, 60, 18, 5, 25, 8)
    e.abilities = ['stun']
    return e

def make_warlock():
    e = Enemy("Warlock", 'W', PURPLE, 40, 14, 12, 28, 3)
    e.abilities = ['poison', 'steal']
    return e

def make_elemental():
    e = Enemy("Fire Elemental", 'E', RED, 45, 16, 10, 30, 4)
    e.abilities = ['burn']
    return e

def make_demon():
    e = Enemy("Demon", 'D', RED, 55, 20, 10, 40, 5)
    e.abilities = ['bleed', 'stun']
    return e

def make_succubus():
    e = Enemy("Succubus", 'S', PURPLE, 50, 18, 14, 38, 3)
    e.abilities = ['steal', 'poison']
    return e

def make_scorpio():
    e = Enemy("Scorpio", 'X', ORANGE, 65, 22, 12, 50, 6)
    e.abilities = ['poison', 'bleed']
    return e

def make_dwarf_monk():
    e = Enemy("Dwarf Monk", 'm', BROWN, 70, 24, 14, 55, 5)
    e.abilities = ['stun']
    return e

def make_dwarf_king():
    e = Enemy("Dwarf King", 'K', YELLOW, 200, 30, 15, 200, 10)
    e.abilities = ['stun', 'summon']
    e.loot_chance = 1.0
    return e

def make_goo():
    e = Enemy("Goo", 'G', GREEN, 100, 15, 6, 100, 5)
    e.abilities = ['bleed']
    e.loot_chance = 1.0
    return e

def make_tengu():
    e = Enemy("Tengu", 'T', ORANGE, 120, 20, 18, 150, 6)
    e.abilities = ['steal', 'bleed']
    e.loot_chance = 1.0
    return e

def make_dm300():
    e = Enemy("DM-300", 'M', GRAY, 160, 25, 10, 175, 12)
    e.abilities = ['stun', 'burn']
    e.loot_chance = 1.0
    return e

def make_yog():
    e = Enemy("Yog-Dzewa", 'Y', RED, 250, 35, 12, 500, 15)
    e.abilities = ['poison', 'burn', 'bleed', 'stun']
    e.loot_chance = 1.0
    return e


ENEMY_TABLE = {
    1:  [make_rat, make_rat, make_gnoll],
    2:  [make_rat, make_gnoll, make_sewage_crab],
    3:  [make_gnoll, make_sewage_crab, make_swamp_shaman],
    4:  [make_sewage_crab, make_swamp_shaman, make_gnoll],
    5:  [make_goo],  # boss
    6:  [make_skeleton, make_thief, make_gnoll],
    7:  [make_skeleton, make_thief, make_guard],
    8:  [make_guard, make_thief, make_skeleton],
    9:  [make_guard, make_necromancer, make_skeleton],
    10: [make_tengu],  # boss
    11: [make_cave_spinner, make_bat, make_skeleton],
    12: [make_cave_spinner, make_bat, make_golem],
    13: [make_golem, make_bat, make_cave_spinner],
    14: [make_golem, make_warlock, make_cave_spinner],
    15: [make_dm300],  # boss
    16: [make_elemental, make_warlock, make_golem],
    17: [make_elemental, make_demon, make_warlock],
    18: [make_demon, make_succubus, make_elemental],
    19: [make_demon, make_succubus, make_scorpio],
    20: [make_dwarf_king],  # boss
    21: [make_scorpio, make_dwarf_monk, make_demon],
    22: [make_scorpio, make_dwarf_monk, make_succubus],
    23: [make_dwarf_monk, make_scorpio, make_demon],
    24: [make_dwarf_monk, make_scorpio, make_succubus],
    25: [make_yog],  # final boss
}


def spawn_enemies(dungeon, depth):
    table = ENEMY_TABLE.get(depth, [make_rat])
    is_boss = depth in BOSS_DEPTHS
    count = 1 if is_boss else random.randint(4, 8)
    occupied = {(dungeon.stairs_up or (0,0)), (dungeon.stairs_down or (0,0))}
    for _ in range(count):
        factory = random.choice(table)
        e = factory()
        pos = dungeon.random_floor(occupied)
        if pos:
            e.x, e.y = pos
            occupied.add(pos)
            dungeon.enemies.append(e)
