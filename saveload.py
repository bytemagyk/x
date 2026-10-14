import json
import os
from items import (Weapon, Armor, Potion, Scroll, Wand, Ring,
                   Food, MissileWeapon, Gold, Seed, Potion, Scroll)
from enemies import (make_rat, make_gnoll, make_sewage_crab, make_swamp_shaman,
                     make_skeleton, make_thief, make_guard, make_necromancer,
                     make_cave_spinner, make_bat, make_golem, make_warlock,
                     make_elemental, make_demon, make_succubus, make_scorpio,
                     make_dwarf_monk, make_dwarf_king, make_goo, make_tengu,
                     make_dm300, make_yog)
from dungeon import DungeonMap, Room
from entities import Player
from combat import Stats
from constants import *

SAVE_FILE = 'savegame.json'

ENEMY_FACTORIES = {
    'Rat': make_rat, 'Gnoll': make_gnoll, 'Sewage Crab': make_sewage_crab,
    'Swamp Shaman': make_swamp_shaman, 'Skeleton': make_skeleton,
    'Thief': make_thief, 'Guard': make_guard, 'Necromancer': make_necromancer,
    'Cave Spinner': make_cave_spinner, 'Vampire Bat': make_bat,
    'Golem': make_golem, 'Warlock': make_warlock, 'Fire Elemental': make_elemental,
    'Demon': make_demon, 'Succubus': make_succubus, 'Scorpio': make_scorpio,
    'Dwarf Monk': make_dwarf_monk, 'Dwarf King': make_dwarf_king,
    'Goo': make_goo, 'Tengu': make_tengu, 'DM-300': make_dm300, 'Yog-Dzewa': make_yog,
}

# ── Item serialization ────────────────────────────────────────────────────────

def _item_to_dict(item):
    if item is None:
        return None
    d = {
        'cls':        type(item).__name__,
        'name':       item.name,
        'itype':      item.itype,
        'identified': item.identified,
        'cursed':     item.cursed,
        'level':      item.level,
    }
    if hasattr(item, 'min_dmg') and hasattr(item, 'tier'):
        d.update({'min_dmg': item.min_dmg, 'max_dmg': item.max_dmg,
                  'tier': item.tier, 'two_handed': item.two_handed,
                  'enchantment': item.enchantment})
    if hasattr(item, 'defense'):
        d.update({'defense': item.defense, 'tier': item.tier, 'glyph': item.glyph})
    if hasattr(item, 'true_name'):
        d.update({'true_name': item.true_name, 'effect': item.effect})
    if hasattr(item, 'charges'):
        d.update({'charges': item.charges, 'max_charges': item.max_charges,
                  'effect': item.effect})
    if hasattr(item, 'power'):
        d.update({'true_name': item.true_name, 'effect': item.effect,
                  'power': item.power})
    if hasattr(item, 'nutrition'):
        d['nutrition'] = item.nutrition
    if hasattr(item, 'quantity'):
        d['quantity'] = item.quantity
    if hasattr(item, 'amount'):
        d['amount'] = item.amount
    if hasattr(item, '_shop_price'):
        d['_shop_price'] = item._shop_price
    return d


def _dict_to_item(d):
    if d is None:
        return None
    cls = d['cls']
    if cls == 'Weapon':
        item = Weapon(d['name'], d['min_dmg'], d['max_dmg'],
                      d.get('tier', 1), d.get('two_handed', False))
        item.enchantment = d.get('enchantment')
    elif cls == 'Armor':
        item = Armor(d['name'], d['defense'], d.get('tier', 1))
        item.glyph = d.get('glyph')
    elif cls == 'Potion':
        item = Potion.__new__(Potion)
        item.name       = d['name']
        item.itype      = POTION
        item.char       = '!'
        item.color      = RED
        item.value      = 0
        item.x = item.y = None
        item.true_name  = d['true_name']
        item.effect     = d['effect']
    elif cls == 'Scroll':
        item = Scroll.__new__(Scroll)
        item.name       = d['name']
        item.itype      = SCROLL
        item.char       = '?'
        item.color      = WHITE
        item.value      = 0
        item.x = item.y = None
        item.true_name  = d['true_name']
        item.effect     = d['effect']
    elif cls == 'Wand':
        item = Wand(d['name'], d['effect'], d['max_charges'])
        item.charges = d['charges']
    elif cls == 'Ring':
        item = Ring.__new__(Ring)
        item.name       = d['name']
        item.itype      = RING
        item.char       = '='
        item.color      = PURPLE
        item.value      = 0
        item.x = item.y = None
        item.true_name  = d['true_name']
        item.effect     = d['effect']
        item.power      = d.get('power', 1)
    elif cls == 'Food':
        item = Food(d['name'], d['nutrition'])
    elif cls == 'MissileWeapon':
        item = MissileWeapon(d['name'], 0, 0, d.get('quantity', 1))
    elif cls == 'Gold':
        item = Gold(d.get('amount', 0))
    elif cls == 'Seed':
        item = Seed(d['name'], d.get('effect', ''))
    else:
        return None

    item.identified = d.get('identified', False)
    item.cursed     = d.get('cursed', False)
    item.level      = d.get('level', 0)
    if '_shop_price' in d:
        item._shop_price = d['_shop_price']
    return item


# ── Enemy serialization ───────────────────────────────────────────────────────

def _enemy_to_dict(e):
    return {
        'name':        e.name,
        'x': e.x, 'y': e.y,
        'hp':          e.stats.hp,
        'state':       e.state,
        'sleeping':    e.sleeping,
        'sleep_turns': e.sleep_turns,
        'buffs':       e.stats.buffs,
    }


def _dict_to_enemy(d):
    factory = ENEMY_FACTORIES.get(d['name'])
    if not factory:
        return None
    e = factory()
    e.x, e.y       = d['x'], d['y']
    e.stats.hp      = d['hp']
    e.state         = d.get('state', 'idle')
    e.sleeping      = d.get('sleeping', False)
    e.sleep_turns   = d.get('sleep_turns', 0)
    e.stats.buffs   = d.get('buffs', {})
    return e


# ── Dungeon serialization ─────────────────────────────────────────────────────

def _dungeon_to_dict(dungeon):
    return {
        'depth':        dungeon.depth,
        'tiles':        dungeon.tiles,
        'visited':      dungeon.visited,
        'rooms':        [{'x':r.x,'y':r.y,'w':r.w,'h':r.h,'kind':r.kind}
                         for r in dungeon.rooms],
        'items':        [{'x':x,'y':y,'item':_item_to_dict(item)}
                         for x,y,item in dungeon.items],
        'enemies':      [_enemy_to_dict(e) for e in dungeon.enemies if e.is_alive()],
        'traps':        {f"{k[0]},{k[1]}": v for k,v in dungeon.traps.items()},
        'secret_doors': [[x,y] for x,y in dungeon.secret_doors],
        'dew_drops':    [[x,y] for x,y in dungeon.dew_drops],
        'shop_pos':     list(dungeon.shop_pos) if dungeon.shop_pos else None,
        'stairs_up':    list(dungeon.stairs_up)   if dungeon.stairs_up   else None,
        'stairs_down':  list(dungeon.stairs_down) if dungeon.stairs_down else None,
    }


def _dict_to_dungeon(d):
    dungeon = DungeonMap.__new__(DungeonMap)
    dungeon.depth        = d['depth']
    dungeon.width        = MAP_W
    dungeon.height       = MAP_H
    dungeon.tiles        = d['tiles']
    dungeon.visited      = d['visited']
    dungeon.lit          = [[False]*MAP_H for _ in range(MAP_W)]
    dungeon.rooms        = [Room(r['x'],r['y'],r['w'],r['h'],r.get('kind','normal'))
                            for r in d['rooms']]
    dungeon.items        = [(e['x'], e['y'], _dict_to_item(e['item']))
                            for e in d['items'] if e['item']]
    dungeon.enemies      = [e for e in (_dict_to_enemy(e) for e in d['enemies']) if e]
    dungeon.traps        = {(int(k.split(',')[0]), int(k.split(',')[1])): v
                            for k,v in d['traps'].items()}
    dungeon.secret_doors = {(x,y) for x,y in d['secret_doors']}
    dungeon.dew_drops    = {(x,y) for x,y in d['dew_drops']}
    dungeon.shop_pos     = tuple(d['shop_pos']) if d['shop_pos'] else None
    dungeon.stairs_up    = tuple(d['stairs_up'])   if d['stairs_up']   else None
    dungeon.stairs_down  = tuple(d['stairs_down']) if d['stairs_down'] else None
    return dungeon


# ── Player serialization ──────────────────────────────────────────────────────

def _player_to_dict(p):
    inv = [_item_to_dict(i) for i in p.inventory]
    return {
        'cls_name':            p.cls_name,
        'x': p.x, 'y': p.y,
        'gold':                p.gold,
        'hunger':              p.hunger,
        'hunger_state':        p.hunger_state,
        'depth':               p.depth,
        'turns':               p.turns,
        'regen_counter':       p.regen_counter,
        'ability_cooldown':    p.ability_cooldown,
        'stats': {
            'hp': p.stats.hp, 'max_hp': p.stats.max_hp,
            'str_': p.stats.str_, 'dex': p.stats.dex,
            'lvl': p.stats.lvl, 'exp': p.stats.exp,
            'exp_next': p.stats.exp_next, 'buffs': p.stats.buffs,
        },
        'inventory':           inv,
        'weapon_idx':          p.inventory.index(p.weapon)       if p.weapon       in p.inventory else None,
        'armor_idx':           p.inventory.index(p.armor)        if p.armor        in p.inventory else None,
        'ring1_idx':           p.inventory.index(p.ring1)        if p.ring1        in p.inventory else None,
        'ring2_idx':           p.inventory.index(p.ring2)        if p.ring2        in p.inventory else None,
        'missile_idx':         p.inventory.index(p.missile_slot) if p.missile_slot in p.inventory else None,
        'quickslot_idxs':      [p.inventory.index(s) if s in p.inventory else None
                                for s in p.quickslots],
        'identified_potions':  list(p.identified_potions),
        'identified_scrolls':  list(p.identified_scrolls),
        'identified_wands':    list(p.identified_wands),
        'identified_rings':    list(p.identified_rings),
        'potion_aliases':      Potion._aliases,
        'scroll_aliases':      Scroll._aliases,
    }


def _dict_to_player(d):
    p = Player.__new__(Player)
    p.cls_name      = d['cls_name']
    p.x, p.y        = d['x'], d['y']
    p.gold          = d['gold']
    p.hunger        = d['hunger']
    p.hunger_state  = d['hunger_state']
    p.depth         = d['depth']
    p.turns         = d['turns']
    p.regen_counter = d['regen_counter']
    p.alive         = True
    p.messages      = []

    s = d['stats']
    p.stats          = Stats(s['max_hp'], s['str_'], s['dex'], s['lvl'])
    p.stats.hp       = s['hp']
    p.stats.exp      = s['exp']
    p.stats.exp_next = s['exp_next']
    p.stats.buffs    = s['buffs']

    p.inventory = [_dict_to_item(i) for i in d['inventory'] if i]

    def _get(idx):
        return p.inventory[idx] if idx is not None and idx < len(p.inventory) else None

    p.weapon       = _get(d.get('weapon_idx'))
    p.armor        = _get(d.get('armor_idx'))
    p.ring1        = _get(d.get('ring1_idx'))
    p.ring2        = _get(d.get('ring2_idx'))
    p.missile_slot = _get(d.get('missile_idx'))
    quickslot_idxs = d.get('quickslot_idxs', [None] * 4)
    if 'ability_cooldown' in d:
        p.quickslots = [_get(i) for i in quickslot_idxs]
    else:
        # Older saves used all four slots for items; reserve slot 1 for the ability.
        p.quickslots = [None] + [_get(i) for i in quickslot_idxs[:3]]
    p.quickslots = (p.quickslots + [None] * 4)[:4]
    p.ability_cooldown = d.get('ability_cooldown', 0)

    p.identified_potions = set(d.get('identified_potions', []))
    p.identified_scrolls = set(d.get('identified_scrolls', []))
    p.identified_wands   = set(d.get('identified_wands',   []))
    p.identified_rings   = set(d.get('identified_rings',   []))

    Potion._aliases = d.get('potion_aliases', Potion._aliases)
    Scroll._aliases = d.get('scroll_aliases', Scroll._aliases)

    return p


# ── Public API ────────────────────────────────────────────────────────────────

def save(player, dungeon, messages):
    data = {
        'player':   _player_to_dict(player),
        'dungeon':  _dungeon_to_dict(dungeon),
        'messages': messages[-50:],
    }
    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f)


def load():
    if not os.path.exists(SAVE_FILE):
        return None, None, []
    with open(SAVE_FILE, 'r') as f:
        data = json.load(f)
    player  = _dict_to_player(data['player'])
    dungeon = _dict_to_dungeon(data['dungeon'])
    dungeon.compute_fov(player.x, player.y)
    messages = data.get('messages', [])
    return player, dungeon, messages


def has_save():
    return os.path.exists(SAVE_FILE)


def delete_save():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
