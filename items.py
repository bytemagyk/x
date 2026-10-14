import random
from constants import *

class Item:
    def __init__(self, name, itype, char, color, value=0):
        self.name   = name
        self.itype  = itype
        self.char   = char
        self.color  = color
        self.value  = value
        self.x = self.y = None
        self.identified = False
        self.cursed = False
        self.level  = 0  # upgrade level

    def display_name(self):
        if self.identified:
            lvl = f" +{self.level}" if self.level > 0 else (f" {self.level}" if self.level < 0 else "")
            curse = " {cursed}" if self.cursed else ""
            return f"{self.name}{lvl}{curse}"
        return self.name

    def __repr__(self):
        return self.display_name()


# ── Weapons ──────────────────────────────────────────────────────────────────
class Weapon(Item):
    def __init__(self, name, min_dmg, max_dmg, tier=1, two_handed=False):
        super().__init__(name, WEAPON, ')', YELLOW)
        self.min_dmg = min_dmg
        self.max_dmg = max_dmg
        self.tier = tier
        self.two_handed = two_handed
        self.enchantment = None

    def damage(self):
        base = random.randint(self.min_dmg, self.max_dmg) + self.level
        if self.enchantment == 'fire':
            base += random.randint(1, 4)
        elif self.enchantment == 'poison':
            base += 1
        return max(1, base)

    def display_name(self):
        n = super().display_name()
        if self.identified and self.enchantment:
            n += f" of {self.enchantment}"
        return n


class Armor(Item):
    def __init__(self, name, defense, tier=1):
        super().__init__(name, ARMOR, '[', BLUE)
        self.defense = defense
        self.tier = tier
        self.glyph = None

    def dr(self):
        return max(0, self.defense + self.level)

    def display_name(self):
        n = super().display_name()
        if self.identified and self.glyph:
            n += f" of {self.glyph}"
        return n


class Potion(Item):
    _aliases = {}

    def __init__(self, name, effect):
        alias = Potion._aliases.get(name, name)
        super().__init__(alias, POTION, '!', RED)
        self.true_name = name
        self.effect = effect

    def display_name(self):
        if self.identified:
            return f"Potion of {self.true_name}"
        return f"Potion of {self.name}"

    @classmethod
    def randomize_aliases(cls):
        colors = ["crimson","azure","golden","murky","bubbly","smoky",
                  "silver","amber","jade","violet","ivory","obsidian"]
        effects = ["healing","mana","strength","paralysis","levitation",
                   "invisibility","toxic gas","liquid flame","frost","mind vision",
                   "experience","haste"]
        random.shuffle(colors)
        cls._aliases = {e: c for e, c in zip(effects, colors)}


class Scroll(Item):
    _aliases = {}

    def __init__(self, name, effect):
        alias = Scroll._aliases.get(name, name)
        super().__init__(alias, SCROLL, '?', WHITE)
        self.true_name = name
        self.effect = effect

    def display_name(self):
        if self.identified:
            return f"Scroll of {self.true_name}"
        return f"Scroll of {self.name}"

    @classmethod
    def randomize_aliases(cls):
        words = ["KAUNAN","SOWILO","TIWAZ","BERKANO","EHWAZ","MANNAZ",
                 "LAGUZ","INGWAZ","OTHALAN","DAGAZ","FEHU","URUZ"]
        effects = ["identify","remove curse","upgrade","enchant weapon",
                   "enchant armor","magic mapping","mirror image","recharging",
                   "terror","lullaby","psionic blast","transmutation"]
        random.shuffle(words)
        cls._aliases = {e: w for e, w in zip(effects, words)}


class Wand(Item):
    def __init__(self, name, effect, charges=3):
        super().__init__(name, WAND, '/', CYAN)
        self.effect = effect
        self.charges = charges
        self.max_charges = charges

    def display_name(self):
        if self.identified:
            return f"Wand of {self.name} [{self.charges}]"
        return f"Wand of {self.name}"


class Ring(Item):
    _aliases = {}

    def __init__(self, name, effect, power=1):
        alias = Ring._aliases.get(name, name)
        super().__init__(alias, RING, '=', PURPLE)
        self.true_name = name
        self.effect = effect
        self.power = power

    def display_name(self):
        if self.identified:
            return f"Ring of {self.true_name} +{self.power}"
        return f"Ring of {self.name}"

    @classmethod
    def randomize_aliases(cls):
        gems = ["garnet","ruby","topaz","opal","tourmaline","amethyst",
                "onyx","agate","diamond","pearl","zircon","sapphire"]
        effects = ["accuracy","evasion","haste","might","tenacity","furor",
                   "sharpshooting","arcana","wealth","energy","force","thorns"]
        random.shuffle(gems)
        cls._aliases = {e: g for e, g in zip(effects, gems)}


class Food(Item):
    def __init__(self, name, nutrition):
        super().__init__(name, FOOD, '%', ORANGE)
        self.nutrition = nutrition
        self.identified = True


class Seed(Item):
    def __init__(self, name, effect):
        super().__init__(name, SEED, ';', DGREEN)
        self.effect = effect


class MissileWeapon(Item):
    def __init__(self, name, min_dmg, max_dmg, quantity=1):
        super().__init__(name, MISSILE, '\\', BROWN)
        self.min_dmg = min_dmg
        self.max_dmg = max_dmg
        self.quantity = quantity
        self.identified = True

    def damage(self):
        return random.randint(self.min_dmg, self.max_dmg) + self.level

    def display_name(self):
        return f"{self.name} x{self.quantity}"


class Gold(Item):
    def __init__(self, amount):
        super().__init__("Gold", GOLD, '$', YELLOW, amount)
        self.amount = amount
        self.identified = True

    def display_name(self):
        return f"Gold ({self.amount})"


# ── Item factories ────────────────────────────────────────────────────────────
WEAPONS = [
    lambda: Weapon("Knuckleduster", 1, 3, 1),
    lambda: Weapon("Dagger", 1, 4, 1),
    lambda: Weapon("Hand Axe", 1, 6, 1),
    lambda: Weapon("Short Sword", 2, 6, 2),
    lambda: Weapon("Mace", 2, 8, 2),
    lambda: Weapon("Spear", 3, 7, 2),
    lambda: Weapon("Long Sword", 3, 10, 3),
    lambda: Weapon("Battle Axe", 4, 12, 3, True),
    lambda: Weapon("War Hammer", 5, 15, 4, True),
    lambda: Weapon("Glaive", 5, 14, 4, True),
    lambda: Weapon("Greataxe", 6, 18, 5, True),
    lambda: Weapon("Greatshield", 0, 0, 5),
]

ARMORS = [
    lambda: Armor("Cloth Armor", 0, 1),
    lambda: Armor("Leather Armor", 2, 1),
    lambda: Armor("Mail Armor", 4, 2),
    lambda: Armor("Scale Armor", 6, 3),
    lambda: Armor("Plate Armor", 8, 4),
    lambda: Armor("Warrior Armor", 10, 5),
]

POTIONS_DEF = [
    ("healing", "Restores HP"),
    ("strength", "Permanently increases STR"),
    ("paralysis", "Paralyzes for several turns"),
    ("levitation", "Levitate over traps/water"),
    ("invisibility", "Become invisible"),
    ("toxic gas", "Release toxic cloud"),
    ("liquid flame", "Release fire cloud"),
    ("frost", "Freeze nearby enemies"),
    ("mind vision", "See all enemies"),
    ("experience", "Gain experience"),
    ("haste", "Move faster"),
    ("mana", "Restore wand charges"),
]

SCROLLS_DEF = [
    ("identify", "Identify one item"),
    ("remove curse", "Remove curses"),
    ("upgrade", "Upgrade one item"),
    ("enchant weapon", "Enchant weapon"),
    ("enchant armor", "Enchant armor"),
    ("magic mapping", "Reveal map"),
    ("mirror image", "Create mirror images"),
    ("recharging", "Recharge wands"),
    ("terror", "Frighten enemies"),
    ("lullaby", "Put enemies to sleep"),
    ("psionic blast", "Damage all visible enemies"),
    ("transmutation", "Transform item"),
]

WANDS_DEF = [
    ("magic missile", 3), ("firebolt", 3), ("frost", 3),
    ("lightning", 3), ("disintegration", 2), ("venom", 3),
    ("blast wave", 3), ("corrosion", 3), ("living earth", 2),
    ("warding", 3), ("regrowth", 3), ("transfusion", 3),
]

RINGS_DEF = [
    ("accuracy", 1), ("evasion", 1), ("haste", 1), ("might", 1),
    ("tenacity", 1), ("furor", 1), ("sharpshooting", 1), ("arcana", 1),
    ("wealth", 1), ("energy", 1), ("force", 1), ("thorns", 1),
]

MISSILES_DEF = [
    ("Throwing Stone", 2, 5, 3),
    ("Dart", 1, 3, 5),
    ("Javelin", 3, 8, 2),
    ("Boomerang", 2, 6, 1),
    ("Shuriken", 4, 8, 3),
    ("Tomahawk", 5, 10, 2),
]


def random_item(depth=1, cursed_chance=0.1):
    tier = min(5, (depth - 1) // 5 + 1)
    roll = random.random()
    if roll < 0.25:
        item = random.choice([f for f in WEAPONS if f().tier <= tier + 1])()
    elif roll < 0.40:
        item = random.choice([f for f in ARMORS if f().tier <= tier + 1])()
    elif roll < 0.55:
        name, _ = random.choice(POTIONS_DEF)
        item = Potion(name, name)
    elif roll < 0.68:
        name, _ = random.choice(SCROLLS_DEF)
        item = Scroll(name, name)
    elif roll < 0.75:
        name, charges = random.choice(WANDS_DEF)
        item = Wand(name, name, charges)
    elif roll < 0.80:
        name, power = random.choice(RINGS_DEF)
        item = Ring(name, name, power)
    elif roll < 0.88:
        n, mn, mx, q = random.choice(MISSILES_DEF)
        item = MissileWeapon(n, mn, mx, q)
    elif roll < 0.95:
        item = Food("Ration", 500) if random.random() < 0.7 else Food("Pasty", 250)
    else:
        item = Gold(random.randint(5, 30) * depth)
    # Assign cursed to equippable items
    if item.itype in (WEAPON, ARMOR, RING) and random.random() < cursed_chance:
        item.cursed = True
        item.level  = -random.randint(1, 2)
    return item


def init_aliases():
    Potion.randomize_aliases()
    Scroll.randomize_aliases()
    Ring.randomize_aliases()
