"""多敌人与 BOSS 战测试"""
import json
import os
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
CONFIG_DIR = ROOT_DIR / "config"


def load_monsters():
    with open(CONFIG_DIR / "monsters.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_forest_map():
    with open(CONFIG_DIR / "maps" / "forest.json", "r", encoding="utf-8") as f:
        return json.load(f)


class TestMultiEnemyCombat(unittest.TestCase):
    """多敌人战斗测试"""

    def setUp(self):
        from combat.session import CombatSession, MonsterInstance, StatusEffect, create_combat_session
        self.CombatSession = CombatSession
        self.MonsterInstance = MonsterInstance
        self.StatusEffect = StatusEffect
        self.create_combat_session = create_combat_session

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

    def test_multi_enemy_session_creation(self):
        monsters = [
            self.monster_config,
            {**self.monster_config, "id": "test_slime_2", "name": "测试史莱姆2"},
        ]
        session = self.CombatSession("test_multi", monsters, self.player_snapshot)
        self.assertEqual(len(session.monsters), 2)
        self.assertTrue(session.monsters[0].alive)
        self.assertTrue(session.monsters[1].alive)

    def test_target_selection(self):
        monsters = [
            self.monster_config,
            {**self.monster_config, "id": "test_slime_2", "name": "测试史莱姆2"},
        ]
        session = self.CombatSession("test_target", monsters, self.player_snapshot)
        session.target_index = 0
        target = session.get_target()
        self.assertEqual(target.index, 0)

        session.target_index = 1
        target = session.get_target()
        self.assertEqual(target.index, 1)

    def test_target_auto_switch_on_death(self):
        monsters = [
            self.monster_config,
            {**self.monster_config, "id": "test_slime_2", "name": "测试史莱姆2"},
        ]
        session = self.CombatSession("test_auto", monsters, self.player_snapshot)
        session.target_index = 0
        session.monsters[0].hp = 0
        target = session.get_target()
        self.assertIsNotNone(target)
        self.assertEqual(target.index, 1)

    def test_all_monsters_dead(self):
        monsters = [
            self.monster_config,
            {**self.monster_config, "id": "test_slime_2", "name": "测试史莱姆2"},
        ]
        session = self.CombatSession("test_all_dead", monsters, self.player_snapshot)
        session.monsters[0].hp = 0
        session.monsters[1].hp = 0
        self.assertTrue(session.all_monsters_dead())

    def test_alive_monsters_count(self):
        monsters = [
            self.monster_config,
            {**self.monster_config, "id": "test_slime_2", "name": "测试史莱姆2"},
            {**self.monster_config, "id": "test_slime_3", "name": "测试史莱姆3"},
        ]
        session = self.CombatSession("test_alive", monsters, self.player_snapshot)
        self.assertEqual(len(session.alive_monsters()), 3)
        session.monsters[1].hp = 0
        self.assertEqual(len(session.alive_monsters()), 2)

    def test_create_combat_session_multi(self):
        monsters = [
            self.monster_config,
            {**self.monster_config, "id": "test_slime_2", "name": "测试史莱姆2"},
        ]
        session = self.create_combat_session(monsters, self.player_snapshot)
        self.assertIsNotNone(session.session_id)
        self.assertEqual(len(session.monsters), 2)


class TestBossPhase(unittest.TestCase):
    """BOSS 阶段转换测试"""

    def setUp(self):
        from combat.session import CombatSession, MonsterInstance
        from combat.monster_ai import check_boss_phase
        self.CombatSession = CombatSession
        self.MonsterInstance = MonsterInstance
        self.check_boss_phase = check_boss_phase

        self.boss_config = {
            "id": "test_boss",
            "name": "测试 BOSS",
            "type": "boss",
            "level": 8,
            "stats": {"hp": 400, "attack": 22, "defense": 10, "speed": 8},
            "drops": [],
            "gold_reward": [100, 200],
            "tags": ["boss"],
            "phases": [
                {
                    "name": "沉睡",
                    "hp_threshold": 1.0,
                    "ai": {"attack": 0.4, "defend": 0.3, "special": 0.3},
                    "special": {"type": "apply_effect", "effect": "poison", "chance": 0.4, "duration": 3},
                },
                {
                    "name": "觉醒",
                    "hp_threshold": 0.6,
                    "ai": {"attack": 0.5, "defend": 0.15, "special": 0.35},
                    "stat_boost": {"attack": 1.3},
                    "special": {"type": "apply_effect", "effect": "burn", "chance": 0.35, "duration": 2},
                },
                {
                    "name": "狂暴",
                    "hp_threshold": 0.25,
                    "ai": {"attack": 0.65, "defend": 0.0, "special": 0.35},
                    "stat_boost": {"attack": 1.6, "defense": 0.8},
                    "special": {"type": "apply_effect", "effect": "stun", "chance": 0.25, "duration": 1},
                },
            ],
        }

        self.player_snapshot = {
            "hp": 100, "max_hp": 100,
            "mp": 30, "max_mp": 30,
            "attack": 20, "defense": 10, "speed": 10,
            "skills": [],
            "talent_passives": {},
        }

    def test_boss_initial_phase(self):
        boss = self.MonsterInstance(0, "test_boss", self.boss_config)
        self.assertEqual(boss.current_phase, 0)
        self.assertEqual(boss.get_phase_name(), "沉睡")

    def test_boss_phase_transition_awaken(self):
        boss = self.MonsterInstance(0, "test_boss", self.boss_config)
        boss.hp = 200
        phase = self.check_boss_phase(boss)
        self.assertIsNotNone(phase)
        self.assertEqual(boss.current_phase, 1)
        self.assertEqual(boss.get_phase_name(), "觉醒")
        self.assertEqual(boss.attack, int(22 * 1.3))

    def test_boss_phase_transition_berserk(self):
        boss = self.MonsterInstance(0, "test_boss", self.boss_config)
        boss.hp = 80
        phase = self.check_boss_phase(boss)
        self.assertIsNotNone(phase)
        self.assertEqual(boss.current_phase, 2)
        self.assertEqual(boss.get_phase_name(), "狂暴")
        self.assertEqual(boss.attack, int(22 * 1.6))
        self.assertEqual(boss.defense, int(10 * 0.8))

    def test_boss_no_phase_change_when_hp_high(self):
        boss = self.MonsterInstance(0, "test_boss", self.boss_config)
        boss.hp = 350
        phase = self.check_boss_phase(boss)
        self.assertIsNone(phase)
        self.assertEqual(boss.current_phase, 0)

    def test_boss_phase_skipped_when_low_hp_directly(self):
        boss = self.MonsterInstance(0, "test_boss", self.boss_config)
        boss.hp = 50
        phase = self.check_boss_phase(boss)
        self.assertIsNotNone(phase)
        self.assertEqual(boss.current_phase, 2)

    def test_non_boss_no_phase(self):
        normal_config = {
            "id": "test_slime",
            "name": "测试史莱姆",
            "type": "normal",
            "stats": {"hp": 50, "attack": 10, "defense": 5, "speed": 5},
        }
        monster = self.MonsterInstance(0, "test_slime", normal_config)
        monster.hp = 10
        phase = self.check_boss_phase(monster)
        self.assertIsNone(phase)


class TestBossImmunity(unittest.TestCase):
    """BOSS 免疫机制测试"""

    def setUp(self):
        from combat.session import is_immune_to_effect

        self.is_immune_to_effect = is_immune_to_effect

        self.boss_config = {
            "id": "test_boss",
            "name": "测试 BOSS",
            "type": "boss",
            "tags": ["boss"],
        }

        self.elite_boss_config = {
            "id": "test_elite_boss",
            "name": "测试精英 BOSS",
            "type": "boss",
            "tags": ["boss", "elite"],
        }

        self.normal_config = {
            "id": "test_slime",
            "name": "测试史莱姆",
            "type": "normal",
        }

    def test_boss_immune_stun(self):
        self.assertTrue(self.is_immune_to_effect(self.boss_config, "stun"))

    def test_boss_immune_freeze(self):
        self.assertTrue(self.is_immune_to_effect(self.boss_config, "freeze"))

    def test_boss_not_immune_poison(self):
        self.assertFalse(self.is_immune_to_effect(self.boss_config, "poison"))

    def test_elite_boss_immune_poison(self):
        self.assertTrue(self.is_immune_to_effect(self.elite_boss_config, "poison"))

    def test_elite_boss_immune_stun(self):
        self.assertTrue(self.is_immune_to_effect(self.elite_boss_config, "stun"))

    def test_normal_not_immune(self):
        self.assertFalse(self.is_immune_to_effect(self.normal_config, "stun"))
        self.assertFalse(self.is_immune_to_effect(self.normal_config, "freeze"))
        self.assertFalse(self.is_immune_to_effect(self.normal_config, "poison"))


class TestAOEDamage(unittest.TestCase):
    """AOE 技能统一伤害乘数测试"""

    def test_aoe_multiplier_unified(self):
        from combat.skills import _get_aoe_multiplier
        self.assertEqual(_get_aoe_multiplier(1), 0.65)
        self.assertEqual(_get_aoe_multiplier(2), 0.65)
        self.assertEqual(_get_aoe_multiplier(3), 0.65)
        self.assertEqual(_get_aoe_multiplier(4), 0.65)
        self.assertEqual(_get_aoe_multiplier(5), 0.65)


class TestMonsterGroupConfig(unittest.TestCase):
    """怪物组配置测试"""

    def test_forest_map_has_monster_groups(self):
        forest = load_forest_map()
        self.assertIn("monster_groups", forest)
        self.assertGreater(len(forest["monster_groups"]), 0)

    def test_shadow_tree_boss_exists(self):
        monsters = load_monsters()
        self.assertIn("shadow_tree_spirit", monsters)
        boss = monsters["shadow_tree_spirit"]
        self.assertEqual(boss["type"], "boss")
        self.assertEqual(boss["level"], 8)
        self.assertIn("phases", boss)
        self.assertEqual(len(boss["phases"]), 3)

    def test_shadow_tree_boss_phases(self):
        monsters = load_monsters()
        boss = monsters["shadow_tree_spirit"]
        phases = boss["phases"]
        self.assertEqual(phases[0]["name"], "沉睡")
        self.assertEqual(phases[1]["name"], "觉醒")
        self.assertEqual(phases[2]["name"], "狂暴")
        self.assertEqual(phases[0]["hp_threshold"], 1.0)
        self.assertEqual(phases[1]["hp_threshold"], 0.6)
        self.assertEqual(phases[2]["hp_threshold"], 0.25)

    def test_wolf_pack_group(self):
        forest = load_forest_map()
        groups = forest["monster_groups"]
        wolf_pack = next((g for g in groups if g["group_id"] == "wolf_pack"), None)
        self.assertIsNotNone(wolf_pack)
        self.assertEqual(len(wolf_pack["monsters"]), 1)
        self.assertEqual(wolf_pack["monsters"][0]["monster_id"], "wild_wolf")
        self.assertEqual(wolf_pack["monsters"][0]["count"], 2)

    def test_shadow_tree_boss_group(self):
        forest = load_forest_map()
        groups = forest["monster_groups"]
        boss_group = next((g for g in groups if g["group_id"] == "shadow_tree_boss"), None)
        self.assertIsNotNone(boss_group)
        self.assertEqual(boss_group["monsters"][0]["monster_id"], "shadow_tree_spirit")

    def test_no_overlapping_monsters_and_groups(self):
        forest = load_forest_map()
        group_positions = set()
        for g in forest.get("monster_groups", []):
            group_positions.add((g.get("x"), g.get("y")))
        for m in forest.get("monsters", []):
            pos = (m.get("x"), m.get("y"))
            self.assertNotIn(pos, group_positions,
                             f"怪物 {m.get('monster_id')} 在 ({pos[0]},{pos[1]}) 与怪物组位置重叠")

    def test_monster_group_combat_creates_correct_count(self):
        from combat.session import create_combat_session
        forest = load_forest_map()
        wolf_pack = next((g for g in forest["monster_groups"]
                          if g["group_id"] == "wolf_pack"), None)
        self.assertIsNotNone(wolf_pack)
        monster_configs = []
        for entry in wolf_pack["monsters"]:
            mid = entry["monster_id"]
            count = entry.get("count", 1)
            for i in range(count):
                mc = {"id": mid, "name": f"野狼 {chr(65 + i)}",
                      "type": "normal", "level": 2,
                      "stats": {"hp": 45, "attack": 12, "defense": 4, "speed": 12},
                      "drops": [], "gold_reward": [20, 30]}
                monster_configs.append(mc)
        player = {"hp": 100, "max_hp": 100, "mp": 30, "max_mp": 30,
                  "attack": 20, "defense": 10, "speed": 10,
                  "skills": [], "talent_passives": {}}
        session = create_combat_session(monster_configs, player)
        self.assertEqual(len(session.monsters), 2)
        self.assertTrue(all(m.alive for m in session.monsters))


class TestCombatSessionAPI(unittest.TestCase):
    """战斗会话 API 测试"""

    def setUp(self):
        from combat.session import (
            create_combat_session, get_session, remove_session,
            cleanup_expired_sessions, CombatSession
        )
        self.create_combat_session = create_combat_session
        self.get_session = get_session
        self.remove_session = remove_session

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

    def test_create_and_get_session(self):
        monsters = [self.monster_config]
        session = self.create_combat_session(monsters, self.player_snapshot)
        retrieved = self.get_session(session.session_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.session_id, session.session_id)

    def test_remove_session(self):
        monsters = [self.monster_config]
        session = self.create_combat_session(monsters, self.player_snapshot)
        sid = session.session_id
        self.remove_session(sid)
        self.assertIsNone(self.get_session(sid))

    def test_multi_monster_to_dict(self):
        monsters = [
            self.monster_config,
            {**self.monster_config, "id": "test_slime_2", "name": "测试史莱姆2"},
        ]
        session = self.create_combat_session(monsters, self.player_snapshot)
        monster_dicts = [m.to_dict() for m in session.monsters]
        self.assertEqual(len(monster_dicts), 2)
        self.assertEqual(monster_dicts[0]["name"], "测试史莱姆")
        self.assertEqual(monster_dicts[1]["name"], "测试史莱姆2")


if __name__ == "__main__":
    unittest.main()
