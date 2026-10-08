import random
import math

class Stats:
    def __init__(self, hp, str_, dex, lvl=1):
        self.max_hp = hp
        self.hp     = hp
        self.str_   = str_
        self.dex    = dex
        self.lvl    = lvl
        self.exp    = 0
        self.exp_next = lvl_exp(lvl)
        self.buffs  = {}   # name -> turns_remaining

    def add_buff(self, name, turns):
        self.buffs[name] = max(self.buffs.get(name, 0), turns)

    def has_buff(self, name):
        return self.buffs.get(name, 0) > 0

    def tick_buffs(self):
        expired = [k for k, v in self.buffs.items() if v <= 1]
        for k in expired:
            del self.buffs[k]
        for k in self.buffs:
            self.buffs[k] -= 1
        return expired

    def is_alive(self):
        return self.hp > 0


def lvl_exp(lvl):
    return int(5 * (lvl ** 1.8))


def attack_roll(attacker_stats, weapon, target_stats, armor):
    """Returns (hit: bool, damage: int, crit: bool)"""
    # Accuracy vs evasion
    acc = attacker_stats.dex + (weapon.level if weapon else 0)
    eva = target_stats.dex
    if attacker_stats.has_buff('haste'):
        acc += 3
    if target_stats.has_buff('haste'):
        eva += 3
    if target_stats.has_buff('paralysis') or target_stats.has_buff('sleep'):
        eva = 0

    hit_chance = 0.4 + 0.6 * (acc / (acc + eva)) if (acc + eva) > 0 else 0.5
    if not (random.random() < hit_chance):
        return False, 0, False

    # Damage
    raw = weapon.damage() if weapon else random.randint(1, attacker_stats.str_ // 2 + 1)
    raw += attacker_stats.str_ // 4

    # Crit
    crit = random.random() < 0.1
    if crit:
        raw = int(raw * 1.5)

    # DR
    dr = armor.dr() if armor else 0
    dr_roll = random.randint(0, dr)
    dmg = max(1, raw - dr_roll)

    # Enchantments
    if weapon and weapon.enchantment == 'vampiric':
        attacker_stats.hp = min(attacker_stats.max_hp, attacker_stats.hp + dmg // 3)

    return True, dmg, crit


def ranged_attack(attacker_stats, missile, target_stats, armor):
    acc = attacker_stats.dex + missile.level
    eva = target_stats.dex
    hit_chance = 0.5 + 0.5 * (acc / (acc + eva + 1))
    if not (random.random() < hit_chance):
        return False, 0, False
    raw = missile.damage() + attacker_stats.dex // 4
    dr = armor.dr() if armor else 0
    dmg = max(1, raw - random.randint(0, dr // 2))
    return True, dmg, False


def gain_exp(stats, amount, messages):
    stats.exp += amount
    while stats.exp >= stats.exp_next:
        stats.exp -= stats.exp_next
        stats.lvl += 1
        stats.exp_next = lvl_exp(stats.lvl)
        hp_gain = random.randint(3, 6)
        stats.max_hp += hp_gain
        stats.hp = min(stats.max_hp, stats.hp + hp_gain)
        messages.append(f"Level up! You are now level {stats.lvl}!")
        return True
    return False
