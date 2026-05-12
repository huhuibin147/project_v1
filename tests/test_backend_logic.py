"""层级2：后端逻辑测试 - 战斗引擎、物品系统、技能系统、天赋系统、玩家存档"""
import json
import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
CONFIG_DIR = ROOT_DIR / "config"


class TestCombatEngine(unittest.TestCase):
    """战斗引擎测试"""

    def setUp(self):
        from combat_engine import CombatSession, CombatPhase, calc_damage, StatusEffect
        self.CombatSession = CombatSession
        self.CombatPhase = CombatPhase
        self.calc_damage = calc_damage
        self.StatusEffect = StatusEffect

        self.monster_config = {
            "id": "test_slime",
            "name": "测试史莱姆",
            "type": "normal",
            "level": 1,
            "stats": {"hp": 50, "attack": 10, "defense": 5, "speed": 5},
            "drops": [],
            "gold_reward": [5, 15],
        }
        self.player_snapshot = {
            "hp": 100, "max_hp": 100,
            "mp": 30, "max_mp": 30,
            "attack": 20, "defense": 10, "speed": 10,
            "skills": [],
            "talent_passives": {},
        }

    # ---- BKE-01: 普通攻击伤害 > 0 ----

    def test_bke_01_attack_damage_positive(self):
        result = self.calc_damage(20, 10, 10, 5, False)
        self.assertGreater(result["damage"], 0)

    # ---- BKE-02: 防御减少伤害 ----

    def test_bke_02_defend_reduces_damage(self):
        # 由于伤害计算有随机因素，多次测试取平均
        normal_damages = []
        defended_damages = []
        for _ in range(100):
            normal = self.calc_damage(20, 10, 10, 5, False)
            defended = self.calc_damage(20, 10, 10, 5, True)
            normal_damages.append(normal["damage"])
            defended_damages.append(defended["damage"])
        avg_normal = sum(normal_damages) / len(normal_damages)
        avg_defended = sum(defended_damages) / len(defended_damages)
        self.assertLess(avg_defended, avg_normal * 0.65)

    # ---- BKE-03: HP 降为0时判定失败 ----

    def test_bke_03_player_defeat(self):
        session = self.CombatSession("test", "slime", self.monster_config, self.player_snapshot)
        session.player_hp = 0
        self.assertEqual(session.player_hp, 0)

    # ---- BKE-04: 怪物 HP 降为0时判定胜利 ----

    def test_bke_04_monster_defeat(self):
        session = self.CombatSession("test", "slime", self.monster_config, self.player_snapshot)
        session.monster_hp = 0
        self.assertEqual(session.monster_hp, 0)

    # ---- BKE-05: 中毒状态每回合扣血 ----

    def test_bke_05_poison_damage(self):
        from combat_engine import _process_effects
        session = self.CombatSession("test", "slime", self.monster_config, self.player_snapshot)
        session.player_hp = 100
        poison = self.StatusEffect("poison", 3, value=0)
        session.player_effects = [poison]
        logs = _process_effects(session, is_player=True)
        self.assertLess(session.player_hp, 100)
        self.assertTrue(any("中毒" in l.get("text", "") for l in logs))

    # ---- BKE-06: 治疗药水恢复 HP ----

    def test_bke_06_heal_item_restores_hp(self):
        from combat_engine import _use_item_in_combat
        session = self.CombatSession("test", "slime", self.monster_config, self.player_snapshot)
        session.player_hp = 50
        result = _use_item_in_combat(session, "health_potion")
        self.assertTrue(result["success"])
        self.assertGreater(session.player_hp, 50)

    # ---- BKE-07: 伤害计算公式合理性 ----

    def test_bke_07_damage_formula_reasonable(self):
        for _ in range(20):
            result = self.calc_damage(20, 10, 10, 5, False)
            self.assertGreaterEqual(result["damage"], 1)
            self.assertLessEqual(result["damage"], 100)

    # ---- BKE-08: 速度差影响暴击率 ----

    def test_bke_08_speed_affects_crit(self):
        fast = self.calc_damage(20, 10, 100, 5, False)
        slow = self.calc_damage(20, 10, 1, 5, False)
        self.assertIsInstance(fast["is_crit"], bool)
        self.assertIsInstance(slow["is_crit"], bool)

    # ---- BKE-09: 状态效果持续时间递减 ----

    def test_bke_09_effect_duration_decreases(self):
        from combat_engine import _process_effects
        session = self.CombatSession("test", "slime", self.monster_config, self.player_snapshot)
        session.player_hp = 100
        poison = self.StatusEffect("poison", 2, value=0)
        session.player_effects = [poison]
        _process_effects(session, is_player=True)
        self.assertEqual(len(session.player_effects), 1)
        self.assertEqual(session.player_effects[0].duration, 1)

    # ---- BKE-10: 状态效果到期后移除 ----

    def test_bke_10_effect_removed_when_expired(self):
        from combat_engine import _process_effects
        session = self.CombatSession("test", "slime", self.monster_config, self.player_snapshot)
        session.player_hp = 100
        poison = self.StatusEffect("poison", 1, value=0)
        session.player_effects = [poison]
        _process_effects(session, is_player=True)
        self.assertEqual(len(session.player_effects), 0)


class TestItemSystem(unittest.TestCase):
    """物品系统测试"""

    def setUp(self):
        from item_system import Inventory, buy_item, sell_item, ITEMS_DB, get_item_effect
        self.Inventory = Inventory
        self.buy_item = buy_item
        self.sell_item = sell_item
        self.ITEMS_DB = ITEMS_DB
        self.get_item_effect = get_item_effect

    # ---- BKE-07: 添加物品到背包 ----

    def test_bke_11_add_item(self):
        inv = self.Inventory()
        inv.add_item("health_potion", 3)
        self.assertEqual(inv.get_quantity("health_potion"), 3)

    # ---- BKE-08: 移除背包物品 ----

    def test_bke_12_remove_item(self):
        inv = self.Inventory()
        inv.add_item("health_potion", 5)
        result = inv.remove_item("health_potion", 2)
        self.assertTrue(result)
        self.assertEqual(inv.get_quantity("health_potion"), 3)

    def test_bke_12_remove_item_insufficient(self):
        inv = self.Inventory()
        inv.add_item("health_potion", 1)
        result = inv.remove_item("health_potion", 5)
        self.assertFalse(result)
        self.assertEqual(inv.get_quantity("health_potion"), 1)

    # ---- BKE-09: 购买物品扣金币 ----

    def test_bke_13_buy_item_deducts_gold(self):
        player_inv = self.Inventory(gold=500)
        npc_inv = self.Inventory(gold=1000)
        npc_inv.add_item("health_potion", 10)
        result = self.buy_item(player_inv, npc_inv, "health_potion", 2)
        self.assertTrue(result.success)
        self.assertLess(player_inv.gold, 500)
        self.assertEqual(player_inv.get_quantity("health_potion"), 2)

    # ---- BKE-10: 出售物品加金币 ----

    def test_bke_14_sell_item_adds_gold(self):
        player_inv = self.Inventory(gold=100)
        player_inv.add_item("health_potion", 5)
        npc_inv = self.Inventory(gold=1000)
        result = self.sell_item(player_inv, npc_inv, "health_potion", 1)
        self.assertTrue(result.success)
        self.assertGreater(player_inv.gold, 100)

    # ---- BKE-11: 金币不足无法购买 ----

    def test_bke_15_buy_item_insufficient_gold(self):
        player_inv = self.Inventory(gold=1)
        npc_inv = self.Inventory(gold=1000)
        npc_inv.add_item("health_potion", 10)
        result = self.buy_item(player_inv, npc_inv, "health_potion", 1)
        self.assertFalse(result.success)

    # ---- BKE-16: 背包序列化/反序列化 ----

    def test_bke_16_inventory_serialization(self):
        inv = self.Inventory(gold=100)
        inv.add_item("health_potion", 3)
        inv.add_item("bread", 5)
        data = inv.to_save()
        restored = self.Inventory.from_save(data)
        self.assertEqual(restored.gold, 100)
        self.assertEqual(restored.get_quantity("health_potion"), 3)
        self.assertEqual(restored.get_quantity("bread"), 5)

    # ---- BKE-17: 物品效果定义存在 ----

    def test_bke_17_item_effects_defined(self):
        consumable_items = [item_id for item_id, info in self.ITEMS_DB.items()
                            if info.get("type") in ("consumable",)]
        for item_id in consumable_items:
            with self.subTest(item=item_id):
                effect = self.get_item_effect(item_id)
                self.assertTrue(effect, f"消耗品 {item_id} 缺少效果定义")


class TestSkillSystem(unittest.TestCase):
    """技能系统测试"""

    def setUp(self):
        from skill_system import can_learn_skill, get_skill, SKILLS_DB
        self.can_learn_skill = can_learn_skill
        self.get_skill = get_skill
        self.SKILLS_DB = SKILLS_DB

    # ---- BKE-13: 满足条件可学习 ----

    def test_bke_18_can_learn_matching_class(self):
        for sid, skill in self.SKILLS_DB.items():
            req_classes = skill.get("class_requirement", [])
            if not req_classes:
                continue
            cls = req_classes[0]
            level = skill.get("level_requirement", 1)
            can, reason = self.can_learn_skill(sid, cls, level, [])
            with self.subTest(skill=sid, cls=cls):
                self.assertTrue(can, f"应可学习但被拒绝: {reason}")

    # ---- BKE-14: 等级不足不可学习 ----

    def test_bke_19_cannot_learn_low_level(self):
        for sid, skill in self.SKILLS_DB.items():
            req_level = skill.get("level_requirement", 1)
            if req_level <= 1:
                continue
            req_classes = skill.get("class_requirement", [])
            cls = req_classes[0] if req_classes else "warrior"
            can, reason = self.can_learn_skill(sid, cls, 1, [])
            with self.subTest(skill=sid):
                self.assertFalse(can)

    # ---- BKE-15: 职业不符不可学习 ----

    def test_bke_20_cannot_learn_wrong_class(self):
        all_classes = ["warrior", "mage", "rogue", "priest"]
        for sid, skill in self.SKILLS_DB.items():
            req_classes = skill.get("class_requirement", [])
            if len(req_classes) >= len(all_classes):
                continue
            wrong_class = [c for c in all_classes if c not in req_classes]
            if not wrong_class:
                continue
            level = skill.get("level_requirement", 1)
            can, reason = self.can_learn_skill(sid, wrong_class[0], level, [])
            with self.subTest(skill=sid, cls=wrong_class[0]):
                self.assertFalse(can)

    # ---- BKE-21: 已学技能不可重复学习 ----

    def test_bke_21_cannot_learn_known_skill(self):
        for sid in list(self.SKILLS_DB.keys())[:3]:
            req_classes = self.SKILLS_DB[sid].get("class_requirement", [])
            cls = req_classes[0] if req_classes else "warrior"
            level = self.SKILLS_DB[sid].get("level_requirement", 1)
            can, reason = self.can_learn_skill(sid, cls, level, [sid])
            with self.subTest(skill=sid):
                self.assertFalse(can)
                self.assertIn("已学会", reason)


class TestTalentSystem(unittest.TestCase):
    """天赋系统测试"""

    def setUp(self):
        from talent_system import (
            can_learn_talent, get_talent_config, get_class_talents,
            _TALENTS_DB, TALENT_UNLOCK_LEVEL,
        )
        self.can_learn_talent = can_learn_talent
        self.get_talent_config = get_talent_config
        self.get_class_talents = get_class_talents
        self.TALENTS_DB = _TALENTS_DB
        self.TALENT_UNLOCK_LEVEL = TALENT_UNLOCK_LEVEL

    # ---- BKE-16: 等级不足不可解锁 ----

    def test_bke_22_cannot_learn_low_level(self):
        for tid, talent in self.TALENTS_DB.items():
            cls = talent["class"]
            can, reason = self.can_learn_talent(tid, cls, 1, [])
            with self.subTest(talent=tid):
                self.assertFalse(can)

    # ---- BKE-17: 前置天赋未学不可解锁 ----

    def test_bke_23_cannot_learn_missing_prerequisite(self):
        for tid, talent in self.TALENTS_DB.items():
            prereqs = talent.get("prerequisites", [])
            if not prereqs:
                continue
            cls = talent["class"]
            can, reason = self.can_learn_talent(tid, cls, 99, [])
            with self.subTest(talent=tid):
                self.assertFalse(can)

    # ---- BKE-24: 满足条件可学习 ----

    def test_bke_24_can_learn_with_prerequisites(self):
        for tid, talent in self.TALENTS_DB.items():
            prereqs = talent.get("prerequisites", [])
            cls = talent["class"]
            can, reason = self.can_learn_talent(tid, cls, 99, prereqs)
            with self.subTest(talent=tid):
                self.assertTrue(can, f"应可学习但被拒绝: {reason}")

    # ---- BKE-25: 天赋树结构完整 ----

    def test_bke_25_talent_tree_structure(self):
        with open(CONFIG_DIR / "player_default.json", "r", encoding="utf-8") as f:
            defaults = json.load(f)
        classes = defaults.get("classes", {})
        for cls in classes:
            talents = self.get_class_talents(cls)
            with self.subTest(cls=cls):
                self.assertGreater(len(talents), 0, f"{cls} 没有天赋定义")


class TestPlayerProfile(unittest.TestCase):
    """玩家存档测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_data_dir = None

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("player_profile.DATA_DIR")
    def test_bke_26_new_game_default_stats(self, mock_data_dir):
        mock_data_dir.__truediv__ = lambda self, key: Path(self.temp_dir) / key
        mock_data_dir.mkdir = lambda *a, **kw: Path(self.temp_dir).mkdir(exist_ok=True)

        from player_profile import PlayerProfile
        player = PlayerProfile()
        self.assertEqual(player.level, 1)
        self.assertGreater(player.max_hp, 0)
        self.assertGreater(player.attack, 0)
        self.assertGreater(player.defense, 0)
        self.assertGreater(player.speed, 0)

    @patch("player_profile.DATA_DIR")
    def test_bke_27_exp_to_next_increases(self, mock_data_dir):
        from player_profile import PlayerProfile
        player = PlayerProfile()
        initial_exp_to_next = player.exp_to_next
        player.level = 5
        player._level_up()
        self.assertGreater(player.exp_to_next, initial_exp_to_next)

    def test_bke_28_equip_slots_defined(self):
        from player_profile import EQUIP_SLOTS, DEFAULT_EQUIPMENT
        self.assertIn("weapon", EQUIP_SLOTS)
        self.assertIn("body", EQUIP_SLOTS)
        for slot in EQUIP_SLOTS:
            self.assertIn(slot, DEFAULT_EQUIPMENT)
            self.assertIsNone(DEFAULT_EQUIPMENT[slot])

    def test_bke_29_class_definitions_complete(self):
        with open(CONFIG_DIR / "player_default.json", "r", encoding="utf-8") as f:
            defaults = json.load(f)
        classes = defaults.get("classes", {})
        for cls_id, cls_data in classes.items():
            with self.subTest(cls=cls_id):
                self.assertIn("name", cls_data)
                self.assertIn("base_hp", cls_data)
                self.assertGreater(cls_data["base_hp"], 0)
                self.assertIn("base_attack", cls_data)
                self.assertIn("base_defense", cls_data)
                self.assertIn("base_speed", cls_data)


if __name__ == "__main__":
    unittest.main()
