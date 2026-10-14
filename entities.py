import random
from constants import *
from combat import Stats, attack_roll, ranged_attack, gain_exp
from items import Weapon, Armor, Potion, Scroll, Wand, Ring, Food, MissileWeapon, Gold, Seed
QUICKSLOT_COUNT = 4
CLASS_ABILITIES = {
    'Warrior': {
        'id': 'shield_bash',
        'name': 'Shield Bash',
        'short_name': 'BASH',
        'glyph': 'B',
        'color': YELLOW,
        'cooldown': 6,
    },
    'Mage': {
        'id': 'arcane_bolt',
        'name': 'Arcane Bolt',
        'short_name': 'BOLT',
        'glyph': '*',
        'color': CYAN,
        'cooldown': 5,
    },
    'Rogue': {
        'id': 'smoke_veil',
        'name': 'Smoke Veil',
        'short_name': 'VEIL',
        'glyph': 'S',
        'color': PURPLE,
        'cooldown': 7,
    },
    'Huntress': {
        'id': 'pinning_shot',
        'name': 'Pinning Shot',
        'short_name': 'SHOT',
        'glyph': 'P',
        'color': GREEN,
        'cooldown': 5,
    },
}

CLASSES = {
    'Warrior':  {'hp': 30, 'str': 11, 'dex': 8,  'start_weapon': 'Short Sword', 'start_armor': 'Mail Armor'},
    'Mage':     {'hp': 20, 'str': 8,  'dex': 10, 'start_weapon': 'Knuckleduster', 'start_armor': 'Cloth Armor'},
    'Rogue':    {'hp': 20, 'str': 9,  'dex': 12, 'start_weapon': 'Dagger', 'start_armor': 'Leather Armor'},
    'Huntress': {'hp': 20, 'str': 9,  'dex': 11, 'start_weapon': 'Knuckleduster', 'start_armor': 'Leather Armor'},
}


class Player:
    def __init__(self, cls_name='Warrior'):
        cls = CLASSES[cls_name]
        self.cls_name = cls_name
        self.stats  = Stats(cls['hp'], cls['str'], cls['dex'])
        self.x = self.y = 1
        self.gold   = 0
        self.hunger = BASE_HUNGER
        self.hunger_state = 'full'  # full, hungry, starving, dead
        self.inventory = []
        self.weapon = None
        self.armor  = None
        self.ring1  = None
        self.ring2  = None
        self.missile_slot = None
        self.identified_potions = set()
        self.identified_scrolls = set()
        self.identified_wands   = set()
        self.identified_rings   = set()
        self.depth  = 1
        self.turns  = 0
        self.alive  = True
        self.messages = []
        self.regen_counter = 0
        self.ability_cooldown = 0
        self.quickslots = [None] * QUICKSLOT_COUNT
        self._equip_start(cls)

    @property
    def ability_info(self):
        return CLASS_ABILITIES[self.cls_name]

    def use_ability(self, dungeon, messages):
        ability = self.ability_info
        if self.ability_cooldown > 0:
            messages.append(
                f"{ability['name']} is on cooldown ({self.ability_cooldown} turns).")
            return False

        ability_id = ability['id']
        if ability_id == 'shield_bash':
            targets = [enemy for enemy in dungeon.enemies
                       if enemy.is_alive()
                       and max(abs(enemy.x - self.x), abs(enemy.y - self.y)) == 1]
            if not targets:
                messages.append("Shield Bash needs an adjacent enemy.")
                return False
            target = min(targets, key=lambda enemy:
                         abs(enemy.x - self.x) + abs(enemy.y - self.y))
            damage = random.randint(3, 5) + self.stats.str_ // 3
            self._ability_damage(target, damage, dungeon, messages, ability['name'])
            if target.is_alive():
                target.stats.add_buff('paralysis', 2)
                messages.append(f"{target.name} is stunned!")
        elif ability_id == 'arcane_bolt':
            targets = self._visible_ability_targets(dungeon)
            if not targets:
                messages.append("No visible target for Arcane Bolt.")
                return False
            target = min(targets, key=lambda enemy:
                         abs(enemy.x - self.x) + abs(enemy.y - self.y))
            damage = random.randint(5, 8) + (self.stats.lvl - 1) * 2
            self._ability_damage(target, damage, dungeon, messages, ability['name'])
        elif ability_id == 'smoke_veil':
            self.stats.add_buff('invisible', 6)
            messages.append("Smoke Veil hides you from enemies!")
        elif ability_id == 'pinning_shot':
            targets = [enemy for enemy in self._visible_ability_targets(dungeon)
                       if abs(enemy.x - self.x) + abs(enemy.y - self.y) <= 8]
            if not targets:
                messages.append("No nearby visible target for Pinning Shot.")
                return False
            target = min(targets, key=lambda enemy:
                         abs(enemy.x - self.x) + abs(enemy.y - self.y))
            damage = random.randint(3, 6) + self.stats.lvl - 1
            self._ability_damage(target, damage, dungeon, messages, ability['name'])
            if target.is_alive():
                target.stats.add_buff('paralysis', 2)
                messages.append(f"{target.name} is pinned!")

        self.ability_cooldown = ability['cooldown'] + 1
        return True

    def _visible_ability_targets(self, dungeon):
        return [enemy for enemy in dungeon.enemies
                if enemy.is_alive() and dungeon.lit[enemy.x][enemy.y]]

    def _ability_damage(self, enemy, damage, dungeon, messages, ability_name):
        enemy.take_damage(damage)
        messages.append(f"{ability_name} hits {enemy.name} for {damage}!")
        if enemy.is_alive():
            return
        messages.append(f"{enemy.name} is defeated!")
        gain_exp(self.stats, enemy.exp, messages)
        for item in enemy.drop_loot(self.depth):
            item.x, item.y = enemy.x, enemy.y
            dungeon.items.append((enemy.x, enemy.y, item))
        if enemy in dungeon.enemies:
            dungeon.enemies.remove(enemy)

    def _equip_start(self, cls):
        from items import WEAPONS, ARMORS, Weapon, Armor
        w = next((f() for f in WEAPONS if f().name == cls['start_weapon']), Weapon("Dagger",1,4,1))
        a = next((f() for f in ARMORS if f().name == cls['start_armor']), Armor("Leather Armor",2,1))
        w.identified = True
        a.identified = True
        self.weapon = w
        self.armor  = a
        self.inventory.append(w)
        self.inventory.append(a)
        if self.cls_name == 'Mage':
            from items import Wand
            wand = Wand("magic missile", "magic missile", 5)
            wand.identified = True
            self.inventory.append(wand)
        if self.cls_name == 'Huntress':
            from items import MissileWeapon
            m = MissileWeapon("Boomerang", 2, 6, 1)
            self.missile_slot = m
            self.inventory.append(m)
        from items import Food
        self.inventory.append(Food("Ration", 500))

    def add_item(self, item):
        if len(self.inventory) >= 20:
            return False
        # Stack missiles
        if item.itype == MISSILE:
            for i in self.inventory:
                if i.itype == MISSILE and i.name == item.name:
                    i.quantity += item.quantity
                    return True
        # Stack gold
        if item.itype == GOLD:
            self.gold += item.amount
            return True
        self.inventory.append(item)
        return True

    def remove_item(self, item):
        if item in self.inventory:
            self.inventory.remove(item)

    def equip(self, item, messages):
        if item.itype == WEAPON:
            if self.weapon:
                messages.append(f"Unequipped {self.weapon.name}.")
            self.weapon = item
            messages.append(f"Equipped {item.display_name()}.")
        elif item.itype == ARMOR:
            if self.armor:
                messages.append(f"Unequipped {self.armor.name}.")
            self.armor = item
            messages.append(f"Equipped {item.display_name()}.")
        elif item.itype == RING:
            if not self.ring1:
                self.ring1 = item
            elif not self.ring2:
                self.ring2 = item
            else:
                messages.append("Both ring slots full.")
                return
            messages.append(f"Equipped {item.display_name()}.")
        elif item.itype == MISSILE:
            self.missile_slot = item
            messages.append(f"Readied {item.display_name()}.")

    def unequip(self, item, messages):
        if self.weapon is item:
            self.weapon = None
        elif self.armor is item:
            self.armor = None
        elif self.ring1 is item:
            self.ring1 = None
        elif self.ring2 is item:
            self.ring2 = None
        elif self.missile_slot is item:
            self.missile_slot = None
        messages.append(f"Unequipped {item.display_name()}.")

    def use_item(self, item, dungeon, messages):
        if item.itype == POTION:
            self._use_potion(item, dungeon, messages)
            self.remove_item(item)
        elif item.itype == SCROLL:
            result = self._use_scroll(item, dungeon, messages)
            if result:  # needs item selection — don't remove yet
                return result
            self.remove_item(item)
        elif item.itype == FOOD:
            self.hunger = min(BASE_HUNGER, self.hunger + item.nutrition)
            messages.append(f"You eat the {item.name}. Delicious!")
            self.remove_item(item)
        elif item.itype == WAND:
            self._use_wand(item, dungeon, messages)
        elif item.itype in (WEAPON, ARMOR, RING, MISSILE):
            self.equip(item, messages)

    def throw_potion(self, item, tx, ty, dungeon, messages):
        """Throw a potion at tile (tx,ty). Identifies it and applies splash."""
        item.identified = True
        self.identified_potions.add(item.true_name)
        self._identify_all(item.true_name, POTION, dungeon)
        self.remove_item(item)

        # Find enemy at target
        target = next((e for e in dungeon.enemies if e.x == tx and e.y == ty and e.is_alive()), None)
        e = item.effect
        hit_self = (tx == self.x and ty == self.y)

        messages.append(f"You throw a Potion of {item.true_name}!")

        if e == 'healing':
            if target:
                heal = target.stats.max_hp // 3
                target.stats.hp = min(target.stats.max_hp, target.stats.hp + heal)
                messages.append(f"{target.name} is healed!")
            elif hit_self:
                heal = self.stats.max_hp // 2 + random.randint(1, 6)
                self.stats.hp = min(self.stats.max_hp, self.stats.hp + heal)
                messages.append(f"The potion splashes on you. (+{heal} HP)")

        elif e == 'toxic gas':
            messages.append("Toxic gas erupts!")
            for en in dungeon.enemies:
                if abs(en.x - tx) + abs(en.y - ty) <= 2:
                    en.stats.add_buff('poison', 8)
                    messages.append(f"{en.name} is poisoned!")
            if abs(self.x - tx) + abs(self.y - ty) <= 2:
                self.stats.add_buff('poison', 4)
                messages.append("You are caught in the gas!")

        elif e == 'liquid flame':
            messages.append("Flames burst out!")
            for en in dungeon.enemies:
                if abs(en.x - tx) + abs(en.y - ty) <= 2:
                    dmg = random.randint(6, 14)
                    en.take_damage(dmg)
                    messages.append(f"{en.name} takes {dmg} fire damage!")
            if abs(self.x - tx) + abs(self.y - ty) <= 1:
                dmg = random.randint(3, 7)
                self.stats.hp -= dmg
                messages.append(f"You are singed for {dmg}!")

        elif e == 'frost':
            messages.append("Ice shatters on impact!")
            for en in dungeon.enemies:
                if abs(en.x - tx) + abs(en.y - ty) <= 2:
                    en.stats.add_buff('paralysis', 4)
                    messages.append(f"{en.name} is frozen!")

        elif e == 'paralysis':
            if target:
                target.stats.add_buff('paralysis', random.randint(3, 6))
                messages.append(f"{target.name} is paralyzed!")

        elif e == 'invisibility':
            if hit_self or not target:
                self.stats.add_buff('invisible', 20)
                messages.append("The mist surrounds you — you vanish!")

        elif e == 'levitation':
            if hit_self or not target:
                self.stats.add_buff('levitation', 20)
                messages.append("You float up!")

        elif e == 'mind vision':
            self.stats.add_buff('mind_vision', 15)
            messages.append("Your mind expands!")

        elif e == 'strength':
            if hit_self or not target:
                self.stats.str_ += 1
                messages.append("The potion splashes on you — you feel stronger!")

        elif e == 'experience':
            if hit_self or not target:
                from combat import gain_exp
                gain_exp(self.stats, self.stats.exp_next // 2, messages)

        elif e == 'haste':
            if hit_self or not target:
                self.stats.add_buff('haste', 20)
                messages.append("You feel fast!")
            elif target:
                target.stats.add_buff('haste', 10)
                messages.append(f"{target.name} moves faster!")

        elif e == 'mana':
            if hit_self or not target:
                for i in self.inventory:
                    if i.itype == WAND:
                        i.charges = min(i.max_charges, i.charges + 2)
                messages.append("Your wands recharge!")

    def _identify_all(self, true_name, itype, dungeon):
        """Mark every copy of this potion/scroll as identified."""
        for i in self.inventory:
            if i.itype == itype and hasattr(i, 'true_name') and i.true_name == true_name:
                i.identified = True
        for _, _, i in dungeon.items:
            if i.itype == itype and hasattr(i, 'true_name') and i.true_name == true_name:
                i.identified = True

    def _use_potion(self, item, dungeon, messages):
        item.identified = True
        self.identified_potions.add(item.true_name)
        self._identify_all(item.true_name, POTION, dungeon)
        e = item.effect
        if e == 'healing':
            heal = self.stats.max_hp // 2 + random.randint(1, 6)
            self.stats.hp = min(self.stats.max_hp, self.stats.hp + heal)
            messages.append(f"You feel much better! (+{heal} HP)")
        elif e == 'strength':
            self.stats.str_ += 1
            messages.append("You feel stronger!")
        elif e == 'paralysis':
            self.stats.add_buff('paralysis', random.randint(2, 5))
            messages.append("You can't move!")
        elif e == 'levitation':
            self.stats.add_buff('levitation', 20)
            messages.append("You float into the air!")
        elif e == 'invisibility':
            self.stats.add_buff('invisible', 20)
            messages.append("You become invisible!")
        elif e == 'toxic gas':
            messages.append("Toxic gas fills the area!")
            for enemy in dungeon.enemies:
                if abs(enemy.x - self.x) + abs(enemy.y - self.y) < 4:
                    enemy.stats.add_buff('poison', 6)
        elif e == 'liquid flame':
            messages.append("Flames burst out!")
            for enemy in dungeon.enemies:
                if abs(enemy.x - self.x) + abs(enemy.y - self.y) < 3:
                    enemy.take_damage(random.randint(5, 12))
        elif e == 'frost':
            messages.append("A wave of cold freezes nearby enemies!")
            for enemy in dungeon.enemies:
                if abs(enemy.x - self.x) + abs(enemy.y - self.y) < 4:
                    enemy.stats.add_buff('paralysis', 3)
        elif e == 'mind vision':
            self.stats.add_buff('mind_vision', 15)
            messages.append("You sense all living creatures!")
        elif e == 'experience':
            gain_exp(self.stats, self.stats.exp_next // 2, messages)
            messages.append("You feel more experienced!")
        elif e == 'haste':
            self.stats.add_buff('haste', 20)
            messages.append("You feel very fast!")
        elif e == 'mana':
            for i in self.inventory:
                if i.itype == WAND:
                    i.charges = min(i.max_charges, i.charges + 2)
            messages.append("Your wands feel recharged!")

    def apply_scroll_to_item(self, scroll, target, dungeon, messages):
        """Apply an interactive scroll effect to a chosen target item."""
        e = scroll.effect
        if e == 'identify':
            target.identified = True
            messages.append(f"Identified: {target.display_name()}")
        elif e == 'upgrade':
            target.level += 1
            messages.append(f"{target.display_name()} glows and upgrades to +{target.level}!")
        elif e == 'enchant weapon':
            enchants = ['fire', 'poison', 'vampiric', 'lucky', 'swift']
            target.enchantment = random.choice(enchants)
            messages.append(f"{target.display_name()} is enchanted with {target.enchantment}!")
        elif e == 'enchant armor':
            glyphs = ['affection', 'anti-entropy', 'brimstone', 'camouflage', 'flow']
            target.glyph = random.choice(glyphs)
            messages.append(f"{target.display_name()} is enchanted!")
        elif e == 'transmutation':
            from items import random_item
            self.remove_item(target)
            new_item = random_item(self.depth)
            self.add_item(new_item)
            messages.append(f"{target.name} transmuted into {new_item.display_name()}!")
        self.remove_item(scroll)

    def _use_scroll(self, item, dungeon, messages):
        item.identified = True
        self.identified_scrolls.add(item.true_name)
        self._identify_all(item.true_name, SCROLL, dungeon)
        e = item.effect
        # Interactive scrolls — defer to item_select state
        if e == 'identify':
            unid = [i for i in self.inventory if not i.identified and i is not item]
            if not unid:
                messages.append("Nothing to identify."); return None
            messages.append("Choose an item to identify.")
            return {'action': 'identify', 'scroll': item}
        elif e == 'upgrade':
            targets = [i for i in self.inventory if i.itype in (WEAPON, ARMOR) and i is not item]
            if not targets:
                messages.append("Nothing to upgrade."); return None
            messages.append("Choose an item to upgrade.")
            return {'action': 'upgrade', 'scroll': item}
        elif e == 'enchant weapon':
            if not self.weapon:
                messages.append("No weapon equipped."); return None
            messages.append("Choose a weapon to enchant.")
            return {'action': 'enchant_weapon', 'scroll': item}
        elif e == 'enchant armor':
            if not self.armor:
                messages.append("No armor equipped."); return None
            messages.append("Choose armor to enchant.")
            return {'action': 'enchant_armor', 'scroll': item}
        elif e == 'transmutation':
            targets = [i for i in self.inventory if i not in (self.weapon, self.armor, self.ring1, self.ring2) and i is not item]
            if not targets:
                messages.append("Nothing to transmute."); return None
            messages.append("Choose an item to transmute.")
            return {'action': 'transmute', 'scroll': item}
        # Immediate scrolls
        elif e == 'remove curse':
            for i in [self.weapon, self.armor, self.ring1, self.ring2]:
                if i and i.cursed:
                    i.cursed = False
            messages.append("Your equipment glows with a golden light.")
        elif e == 'magic mapping':
            for x in range(dungeon.width):
                for y in range(dungeon.height):
                    dungeon.visited[x][y] = True
            messages.append("The dungeon map is revealed!")
        elif e == 'mirror image':
            self.stats.add_buff('mirror_image', 10)
            messages.append("Mirror images surround you!")
        elif e == 'recharging':
            for i in self.inventory:
                if i.itype == WAND:
                    i.charges = i.max_charges
            messages.append("Your wands are fully recharged!")
        elif e == 'terror':
            for enemy in dungeon.enemies:
                if dungeon.lit[enemy.x][enemy.y]:
                    enemy.stats.add_buff('terror', 10)
            messages.append("Enemies flee in terror!")
        elif e == 'lullaby':
            for enemy in dungeon.enemies:
                if dungeon.lit[enemy.x][enemy.y]:
                    enemy.sleeping = True
                    enemy.sleep_turns = random.randint(5, 10)
            messages.append("Enemies fall asleep!")
        elif e == 'psionic blast':
            for enemy in dungeon.enemies:
                if dungeon.lit[enemy.x][enemy.y]:
                    dmg = random.randint(5, 15)
                    enemy.take_damage(dmg)
            messages.append("A psionic blast damages all visible enemies!")

    def _use_wand(self, item, dungeon, messages):
        if item.charges <= 0:
            messages.append("The wand has no charges!")
            return
        item.charges -= 1
        item.identified = True
        e = item.effect
        # Find nearest visible enemy
        targets = [en for en in dungeon.enemies
                   if en.is_alive() and dungeon.lit[en.x][en.y]]
        targets.sort(key=lambda en: abs(en.x-self.x)+abs(en.y-self.y))
        target = targets[0] if targets else None

        if e == 'magic missile':
            if target:
                dmg = random.randint(4, 8) + item.level * 2
                target.take_damage(dmg)
                messages.append(f"Magic missile hits {target.name} for {dmg}!")
        elif e == 'firebolt':
            if target:
                dmg = random.randint(6, 12) + item.level * 2
                target.take_damage(dmg)
                messages.append(f"Firebolt hits {target.name} for {dmg}!")
        elif e == 'frost':
            if target:
                target.stats.add_buff('paralysis', 4)
                messages.append(f"{target.name} is frozen!")
        elif e == 'lightning':
            for en in targets[:3]:
                dmg = random.randint(5, 10)
                en.take_damage(dmg)
            messages.append("Lightning arcs through enemies!")
        elif e == 'disintegration':
            if target:
                target.stats.hp = 1
                messages.append(f"{target.name} is nearly disintegrated!")
        elif e == 'venom':
            if target:
                target.stats.add_buff('poison', 8)
                messages.append(f"{target.name} is poisoned!")
        elif e == 'blast wave':
            for en in targets[:2]:
                dmg = random.randint(3, 7)
                en.take_damage(dmg)
                en.stats.add_buff('terror', 3)
            messages.append("Blast wave pushes enemies back!")
        elif e == 'corrosion':
            if target:
                if target.armor:
                    target.armor.defense = max(0, target.armor.defense - 1)
                dmg = random.randint(2, 5)
                target.take_damage(dmg)
                messages.append(f"{target.name}'s armor corrodes!")
        elif e == 'living earth':
            self.stats.add_buff('stone_skin', 10)
            messages.append("Stone armor forms around you!")
        elif e == 'warding':
            messages.append("Magical wards protect you!")
            self.stats.add_buff('warding', 5)
        elif e == 'regrowth':
            messages.append("Plants grow around you!")
        elif e == 'transfusion':
            if target:
                heal = random.randint(5, 10)
                self.stats.hp = min(self.stats.max_hp, self.stats.hp + heal)
                target.take_damage(heal // 2)
                messages.append(f"Transfusion heals you for {heal}!")

    def attack(self, enemy, dungeon, messages):
        hit, dmg, crit = attack_roll(self.stats, self.weapon, enemy.stats,
                                     type('A', (), {'dr': lambda s: enemy.dr()})())
        if hit:
            enemy.take_damage(dmg)
            crit_str = " Critical!" if crit else ""
            messages.append(f"You hit {enemy.name} for {dmg}.{crit_str}")
            if not enemy.is_alive():
                messages.append(f"{enemy.name} is defeated!")
                gain_exp(self.stats, enemy.exp, messages)
                loot = enemy.drop_loot(self.depth)
                for l in loot:
                    l.x, l.y = enemy.x, enemy.y
                    dungeon.items.append((enemy.x, enemy.y, l))
        else:
            messages.append(f"You miss {enemy.name}.")

    def throw_missile(self, enemy, dungeon, messages):
        if not self.missile_slot or self.missile_slot.quantity <= 0:
            messages.append("Nothing to throw!")
            return
        m = self.missile_slot
        hit, dmg, _ = ranged_attack(self.stats, m, enemy.stats,
                                    type('A', (), {'dr': lambda s: enemy.dr()})())
        if hit:
            enemy.take_damage(dmg)
            messages.append(f"You throw {m.name} at {enemy.name} for {dmg}!")
            if not enemy.is_alive():
                messages.append(f"{enemy.name} is defeated!")
                gain_exp(self.stats, enemy.exp, messages)
                loot = enemy.drop_loot(self.depth)
                for l in loot:
                    dungeon.items.append((enemy.x, enemy.y, l))
        else:
            messages.append(f"Your {m.name} misses {enemy.name}.")
        if m.name != "Boomerang":
            m.quantity -= 1
            if m.quantity <= 0:
                self.remove_item(m)
                self.missile_slot = None

    def tick(self, dungeon, messages):
        self.turns += 1
        expired = self.stats.tick_buffs()
        if self.ability_cooldown > 0:
            self.ability_cooldown -= 1

        # Hunger
        self.hunger -= HUNGER_RATE
        if self.hunger <= 0:
            self.stats.hp -= 1
            self.hunger_state = 'starving'
            if self.stats.hp <= 0:
                self.alive = False
                messages.append("You starved to death!")
        elif self.hunger < 50:
            self.hunger_state = 'starving'
        elif self.hunger < 150:
            self.hunger_state = 'hungry'
        else:
            self.hunger_state = 'full'

        # Poison damage
        if self.stats.has_buff('poison'):
            self.stats.hp -= 1
            if self.stats.hp <= 0:
                self.alive = False
                messages.append("You died from poison!")

        # Bleed damage
        if self.stats.has_buff('bleed'):
            self.stats.hp -= 1

        # Regen
        self.regen_counter += 1
        regen_rate = 10 - self.stats.lvl // 3
        if self.regen_counter >= max(3, regen_rate):
            self.regen_counter = 0
            if self.stats.hp < self.stats.max_hp and self.hunger_state != 'starving':
                self.stats.hp += 1

        # Ring effects
        if self.ring1 and self.ring1.effect == 'wealth' and self.turns % 50 == 0:
            self.gold += random.randint(1, 5)
        if self.ring2 and self.ring2.effect == 'wealth' and self.turns % 50 == 0:
            self.gold += random.randint(1, 5)

        # Trap
        tile = dungeon.get_tile(self.x, self.y)
        if (self.x, self.y) in dungeon.traps and not self.stats.has_buff('levitation'):
            if random.random() < 0.3:
                effect = dungeon.traps[(self.x, self.y)]
                if effect == 'damage':
                    dmg = random.randint(3, 8)
                    self.stats.hp -= dmg
                    messages.append(f"A trap fires! You take {dmg} damage!")
                elif effect == 'poison':
                    self.stats.add_buff('poison', 5)
                    messages.append("A poison trap! You are poisoned!")
                elif effect == 'teleport':
                    pos = dungeon.random_floor()
                    if pos:
                        self.x, self.y = pos
                    messages.append("A teleport trap! You are teleported!")
                elif effect == 'alarm':
                    for en in dungeon.enemies:
                        en.state = 'chase'
                    messages.append("An alarm trap! Enemies are alerted!")
                elif effect == 'gripping':
                    self.stats.add_buff('paralysis', 2)
                    messages.append("A gripping trap! You are held!")
                elif effect == 'fire':
                    dmg = random.randint(4, 10)
                    self.stats.hp -= dmg
                    messages.append(f"A fire trap! You take {dmg} damage!")
                elif effect == 'chasm':
                    self.stats.hp -= self.stats.max_hp // 4
                    messages.append("You fall into a chasm!")
                elif effect == 'disintegration':
                    dmg = random.randint(8, 16)
                    self.stats.hp -= dmg
                    messages.append(f"A disintegration trap! You take {dmg} damage!")
                dungeon.traps.pop((self.x, self.y), None)

        if self.stats.hp <= 0:
            self.alive = False
