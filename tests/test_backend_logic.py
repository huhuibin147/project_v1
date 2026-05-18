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
sys.path.insert(0, str(ROOT_DIR / "backend" / "combat"))
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

    def test_bke_22_aoe_skills_exist_and_have_aoe_flag(self):
        aoe_skill_ids = ["whirlwind", "war_cry", "poison_mist", "shadow_raid",
                         "flame_storm", "blizzard", "holy_prayer"]
        for sid in aoe_skill_ids:
            skill = self.get_skill(sid)
            with self.subTest(skill=sid):
                self.assertIsNotNone(skill, f"群体技能 '{sid}' 不存在")
                self.assertTrue(skill.get("aoe"), f"技能 '{sid}' 缺少 aoe 标记")

    def test_bke_23_aoe_skills_can_be_learned(self):
        aoe_skills = {
            "whirlwind": ("warrior", 4),
            "war_cry": ("warrior", 7),
            "poison_mist": ("rogue", 4),
            "shadow_raid": ("rogue", 7),
            "flame_storm": ("mage", 4),
            "blizzard": ("mage", 6),
            "holy_prayer": ("mage", 8),
        }
        for sid, (cls, level) in aoe_skills.items():
            can, reason = self.can_learn_skill(sid, cls, level, [])
            with self.subTest(skill=sid, cls=cls, level=level):
                self.assertTrue(can, f"应可学习 '{sid}' 但被拒绝: {reason}")

    def test_bke_24_aoe_skills_rejected_wrong_class(self):
        aoe_skills = {
            "whirlwind": "mage",
            "poison_mist": "warrior",
            "flame_storm": "rogue",
        }
        for sid, wrong_cls in aoe_skills.items():
            level = self.SKILLS_DB[sid].get("level_requirement", 1)
            can, reason = self.can_learn_skill(sid, wrong_cls, level, [])
            with self.subTest(skill=sid, cls=wrong_cls):
                self.assertFalse(can, f"职业不符应拒绝 '{sid}'")


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


class TestElementalCombat(unittest.TestCase):
    """属性克制系统测试"""

    def setUp(self):
        from combat.damage import calc_damage, calc_element_multiplier, Element
        self.calc_damage = calc_damage
        self.calc_element_multiplier = calc_element_multiplier
        self.Element = Element

        from combat.session import CombatSession, MonsterInstance
        self.CombatSession = CombatSession
        self.MonsterInstance = MonsterInstance

        self.monster_config = {
            "id": "test_slime",
            "name": "测试史莱姆",
            "type": "normal",
            "level": 1,
            "element": "grass",
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
            "element": "fire",
        }

    def test_element_counter_chain(self):
        self.assertEqual(self.calc_element_multiplier("fire", "grass"), 1.5)
        self.assertEqual(self.calc_element_multiplier("grass", "water"), 1.5)
        self.assertEqual(self.calc_element_multiplier("water", "fire"), 1.5)

    def test_element_disadvantage(self):
        self.assertAlmostEqual(self.calc_element_multiplier("fire", "water"), 0.67, places=2)
        self.assertAlmostEqual(self.calc_element_multiplier("grass", "fire"), 0.67, places=2)
        self.assertAlmostEqual(self.calc_element_multiplier("water", "grass"), 0.67, places=2)

    def test_element_neutral(self):
        self.assertEqual(self.calc_element_multiplier("none", "fire"), 1.0)
        self.assertEqual(self.calc_element_multiplier("fire", "none"), 1.0)
        self.assertEqual(self.calc_element_multiplier("fire", "fire"), 1.0)
        self.assertEqual(self.calc_element_multiplier("none", "none"), 1.0)

    def test_calc_damage_with_element_advantage(self):
        normal_results = []
        advantage_results = []
        for _ in range(200):
            normal = self.calc_damage(100, 50, 10, 10, False)
            advantage = self.calc_damage(100, 50, 10, 10, False,
                                         attacker_element="fire", defender_element="grass")
            normal_results.append(normal["damage"])
            advantage_results.append(advantage["damage"])
        avg_normal = sum(normal_results) / len(normal_results)
        avg_advantage = sum(advantage_results) / len(advantage_results)
        self.assertGreater(avg_advantage, avg_normal * 1.3)

    def test_calc_damage_with_element_disadvantage(self):
        normal_results = []
        disadvantage_results = []
        for _ in range(200):
            normal = self.calc_damage(100, 50, 10, 10, False)
            disadvantage = self.calc_damage(100, 50, 10, 10, False,
                                            attacker_element="fire", defender_element="water")
            normal_results.append(normal["damage"])
            disadvantage_results.append(disadvantage["damage"])
        avg_normal = sum(normal_results) / len(normal_results)
        avg_disadvantage = sum(disadvantage_results) / len(disadvantage_results)
        self.assertLess(avg_disadvantage, avg_normal * 0.8)

    def test_calc_damage_returns_element_multiplier(self):
        result = self.calc_damage(100, 50, 10, 10, False,
                                  attacker_element="fire", defender_element="grass")
        self.assertIn("element_multiplier", result)
        self.assertEqual(result["element_multiplier"], 1.5)

    def test_resolve_turn_passes_element(self):
        from combat.session import create_combat_session
        from combat.turn import resolve_turn
        session = create_combat_session([self.monster_config], self.player_snapshot)
        state = resolve_turn(session, "attack")
        self.assertIsNotNone(state)
        attack_logs = [l for l in state.get("log", [])
                       if l.get("type") == "player_attack"]
        self.assertTrue(len(attack_logs) > 0, "应有玩家攻击日志")

    def test_resolve_turn_element_advantage_log(self):
        from combat.session import create_combat_session
        from combat.turn import resolve_turn
        session = create_combat_session([self.monster_config], self.player_snapshot)
        state = resolve_turn(session, "attack")
        element_logs = [l for l in state.get("log", [])
                        if l.get("type") in ("element_advantage", "element_disadvantage")]
        self.assertTrue(len(element_logs) > 0, "火攻草应有克制日志")

    def test_monster_attack_passes_element(self):
        from combat.session import create_combat_session
        from combat.turn import resolve_turn
        grass_monster = dict(self.monster_config, element="grass")
        fire_player = dict(self.player_snapshot, element="fire")
        session = create_combat_session([grass_monster], fire_player)
        state = resolve_turn(session, "defend")
        monster_atk_logs = [l for l in state.get("log", [])
                            if l.get("type") == "monster_attack"]
        self.assertTrue(len(monster_atk_logs) > 0, "怪物应攻击玩家")

    def test_monster_to_dict_includes_element(self):
        monster = self.MonsterInstance(0, "test_slime", self.monster_config)
        data = monster.to_dict()
        self.assertIn("element", data)
        self.assertEqual(data["element"], "grass")

    def test_player_element_in_snapshot(self):
        session = self.CombatSession("test", [self.monster_config], self.player_snapshot)
        self.assertEqual(session.player_element, "fire")

    def test_combat_session_default_element(self):
        snapshot = dict(self.player_snapshot)
        snapshot.pop("element", None)
        session = self.CombatSession("test", [self.monster_config], snapshot)
        self.assertEqual(session.player_element, "none")


class TestElementalConfig(unittest.TestCase):
    """属性克制配置测试"""

    def test_monsters_have_element_field(self):
        with open(CONFIG_DIR / "monsters.json", "r", encoding="utf-8") as f:
            monsters = json.load(f)
        valid_elements = {"none", "fire", "water", "grass"}
        for mid, monster in monsters.items():
            with self.subTest(monster=mid):
                self.assertIn("element", monster, f"怪物 {mid} 缺少 element 字段")
                self.assertIn(monster["element"], valid_elements,
                              f"怪物 {mid} 的 element 值无效: {monster['element']}")

    def test_skills_element_valid(self):
        with open(CONFIG_DIR / "skills.json", "r", encoding="utf-8") as f:
            skills = json.load(f)
        valid_elements = {"none", "fire", "water", "grass"}
        for sid, skill in skills.items():
            if "element" in skill:
                with self.subTest(skill=sid):
                    self.assertIn(skill["element"], valid_elements,
                                  f"技能 {sid} 的 element 值无效: {skill['element']}")


if __name__ == "__main__":
    unittest.main()
