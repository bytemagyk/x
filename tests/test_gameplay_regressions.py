import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pygame
import entities
from constants import MAP_H, MAP_W
from enemies import Enemy
from engine import Game
from entities import Player
from items import Potion, Scroll, Wand


class GameplayRegressionTests(unittest.TestCase):
    def make_combat_case(self, player_class="Warrior", enemy_pos=(2, 1)):
        player = Player(player_class)
        player.x, player.y = 1, 1
        enemy = Enemy("Test enemy", "e", (255, 255, 255), 2, 1, 1, 3)
        enemy.x, enemy.y = enemy_pos
        loot = SimpleNamespace(x=None, y=None)
        enemy.drop_loot = Mock(return_value=[loot])
        lit = [[False] * MAP_H for _ in range(MAP_W)]
        lit[enemy.x][enemy.y] = True
        dungeon = SimpleNamespace(enemies=[enemy], items=[], lit=lit)
        return player, enemy, dungeon, loot

    def assert_rewards_once(self, player, enemy, dungeon, loot, messages):
        self.assertEqual(player.stats.exp, enemy.exp)
        self.assertNotIn(enemy, dungeon.enemies)
        self.assertEqual(len(dungeon.items), 1)
        self.assertEqual(dungeon.items[0][:2], (enemy.x, enemy.y))
        self.assertIs(dungeon.items[0][2], loot)
        enemy.drop_loot.assert_called_once_with(player.depth)
        self.assertEqual(messages.count("Test enemy is defeated!"), 1)

    def test_canceling_scroll_target_selection_keeps_scroll(self):
        player = Player()
        scroll = Scroll("upgrade", "upgrade")
        player.inventory.append(scroll)
        game = Game.__new__(Game)
        game.state = "item_select"
        game.player = player
        game.messages = []
        game._select_scroll = scroll
        game._select_purpose = "upgrade"
        game._select_items = [player.weapon]
        game._end_turn = Mock()

        Game._handle_item_select(
            game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        )

        self.assertIn(scroll, player.inventory)
        self.assertEqual(game.state, "playing")
        self.assertIsNone(game._select_scroll)
        self.assertIsNone(game._select_purpose)
        self.assertEqual(game._select_items, [])
        game._end_turn.assert_not_called()

    def test_paralysis_consumes_turn_without_movement_or_quickslot_action(self):
        player = Player()
        player.stats.add_buff("paralysis", 4)
        game = Game.__new__(Game)
        game.state = "playing"
        game.player = player
        game.dungeon = SimpleNamespace()
        game.messages = []
        game.mouse_path = []
        game._end_turn = Mock()
        game._try_move = Mock(return_value=True)
        game._activate_quickslot = Mock(return_value=True)

        Game._handle_playing(
            game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        )
        with patch("engine.quickslot_at", return_value=0):
            Game._handle_playing(
                game,
                pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=1, pos=(1, 1)
                ),
            )

        self.assertEqual(game._end_turn.call_count, 2)
        game._try_move.assert_not_called()
        game._activate_quickslot.assert_not_called()
        self.assertEqual(len(game.messages), 2)

    def test_lethal_damage_sources_award_xp_and_loot_exactly_once(self):
        sources = (
            "melee", "missile", "class ability", "drink liquid flame",
            "throw liquid flame", "psionic blast scroll",
            "wand: magic missile", "wand: firebolt", "wand: lightning",
            "wand: blast wave", "wand: corrosion", "wand: transfusion",
        )
        for source in sources:
            with self.subTest(source=source):
                enemy_pos = (4, 4) if source == "throw liquid flame" else (2, 1)
                player_class = "Mage" if source == "class ability" else "Warrior"
                player, enemy, dungeon, loot = self.make_combat_case(
                    player_class=player_class, enemy_pos=enemy_pos
                )
                messages = []
                with patch("entities.random.randint", return_value=100):
                    if source == "melee":
                        with patch("entities.attack_roll", return_value=(True, 100, False)):
                            player.attack(enemy, dungeon, messages)
                    elif source == "missile":
                        player.missile_slot = SimpleNamespace(name="Dart", quantity=2)
                        with patch("entities.ranged_attack", return_value=(True, 100, False)):
                            player.throw_missile(enemy, dungeon, messages)
                    elif source == "class ability":
                        player.use_ability(dungeon, messages)
                    elif source == "drink liquid flame":
                        potion = Potion("liquid flame", "liquid flame")
                        player.inventory.append(potion)
                        player.use_item(potion, dungeon, messages)
                    elif source == "throw liquid flame":
                        potion = Potion("liquid flame", "liquid flame")
                        player.inventory.append(potion)
                        player.throw_potion(potion, enemy.x, enemy.y, dungeon, messages)
                    elif source == "psionic blast scroll":
                        scroll = Scroll("psionic blast", "psionic blast")
                        player.inventory.append(scroll)
                        player.use_item(scroll, dungeon, messages)
                    else:
                        effect = source.split(": ", 1)[1]
                        wand = Wand(effect, effect, charges=1)
                        player.inventory.append(wand)
                        player.use_item(wand, dungeon, messages)

                self.assert_rewards_once(player, enemy, dungeon, loot, messages)


if __name__ == "__main__":
    unittest.main()
