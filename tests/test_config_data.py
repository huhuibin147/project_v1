"""层级1：配置数据测试 - 校验所有 JSON 配置文件的完整性和一致性"""
import json
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
MAPS_DIR = CONFIG_DIR / "maps"

CONFIG_FILES = {
    "items": CONFIG_DIR / "items.json",
    "monsters": CONFIG_DIR / "monsters.json",
    "npcs": CONFIG_DIR / "npcs.json",
    "skills": CONFIG_DIR / "skills.json",
    "talents": CONFIG_DIR / "talents.json",
    "quests": CONFIG_DIR / "quests.json",
    "tiles": CONFIG_DIR / "tiles.json",
    "player_default": CONFIG_DIR / "player_default.json",
}

VALID_CLASSES = ["warrior", "mage", "rogue", "priest"]
VALID_MONSTER_TYPES = ["normal", "elite", "boss"]
VALID_EQUIP_SLOTS = ["weapon", "head", "body", "legs", "feet", "accessory", "ring", "necklace", "shield"]
VALID_ITEM_TYPES = ["consumable", "equipment", "material", "quest_item", "misc", "skill_book"]


def _load_json(filepath):
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


class TestConfigData(unittest.TestCase):
    """配置数据测试"""

    @classmethod
    def setUpClass(cls):
        cls.configs = {}
        for name, filepath in CONFIG_FILES.items():
            cls.configs[name] = _load_json(filepath)
        cls.maps = {}
        if MAPS_DIR.exists():
            for fp in MAPS_DIR.glob("*.json"):
                cls.maps[fp.stem] = _load_json(fp)

    # ---- CFG-01 ~ CFG-03: 物品配置 ----

    def test_cfg_01_items_parseable(self):
        items = self.configs.get("items")
        self.assertIsNotNone(items, "items.json 不存在或无法解析")
        self.assertIsInstance(items, dict, "items.json 应为字典")

    def test_cfg_02_items_required_fields(self):
        items = self.configs.get("items", {})
        for iid, item in items.items():
            with self.subTest(item=iid):
                self.assertEqual(item.get("id"), iid, f"物品 {iid}: id 不匹配")
                self.assertIn("name", item, f"物品 {iid}: 缺少 name")
                self.assertIn("type", item, f"物品 {iid}: 缺少 type")

    def test_cfg_03_items_price_non_negative(self):
        items = self.configs.get("items", {})
        for iid, item in items.items():
            with self.subTest(item=iid):
                self.assertGreaterEqual(item.get("buy_price", 0), 0,
                                        f"物品 {iid}: buy_price 不能为负")
                self.assertGreaterEqual(item.get("sell_price", 0), 0,
                                        f"物品 {iid}: sell_price 不能为负")

    # ---- CFG-04 ~ CFG-06: 怪物配置 ----

    def test_cfg_04_monsters_parseable(self):
        monsters = self.configs.get("monsters")
        self.assertIsNotNone(monsters, "monsters.json 不存在或无法解析")
        self.assertIsInstance(monsters, dict, "monsters.json 应为字典")

    def test_cfg_05_monsters_required_stats(self):
        monsters = self.configs.get("monsters", {})
        for mid, monster in monsters.items():
            with self.subTest(monster=mid):
                self.assertEqual(monster.get("id"), mid, f"怪物 {mid}: id 不匹配")
                self.assertIn("name", monster, f"怪物 {mid}: 缺少 name")
                self.assertIn("type", monster, f"怪物 {mid}: 缺少 type")
                self.assertIn("stats", monster, f"怪物 {mid}: 缺少 stats")
                self.assertIn("level", monster, f"怪物 {mid}: 缺少 level")
                stats = monster.get("stats", {})
                for stat in ["hp", "attack", "defense", "speed"]:
                    self.assertIn(stat, stats, f"怪物 {mid}: stats 缺少 {stat}")
                    self.assertGreater(stats[stat], 0, f"怪物 {mid}: stats.{stat} 应大于 0")

    def test_cfg_06_monsters_drop_references(self):
        items = self.configs.get("items", {})
        monsters = self.configs.get("monsters", {})
        for mid, monster in monsters.items():
            for drop in monster.get("drops", []):
                item_id = drop.get("item_id")
                if item_id:
                    with self.subTest(monster=mid, drop=item_id):
                        self.assertIn(item_id, items,
                                      f"怪物 {mid} 掉落物品 '{item_id}' 不存在")

    # ---- CFG-07 ~ CFG-08: NPC 配置 ----

    def test_cfg_07_npcs_parseable(self):
        npcs = self.configs.get("npcs")
        self.assertIsNotNone(npcs, "npcs.json 不存在或无法解析")
        self.assertIsInstance(npcs, dict, "npcs.json 应为字典")

    def test_cfg_08_npc_shop_item_references(self):
        items = self.configs.get("items", {})
        npcs = self.configs.get("npcs", {})
        for nid, npc in npcs.items():
            for inv_item in npc.get("shop", {}).get("inventory", []):
                item_id = inv_item.get("item_id")
                if item_id:
                    with self.subTest(npc=nid, item=item_id):
                        self.assertIn(item_id, items,
                                      f"NPC {nid} 商品 '{item_id}' 不存在")

    # ---- CFG-09 ~ CFG-10: 技能配置 ----

    def test_cfg_09_skills_parseable(self):
        skills = self.configs.get("skills")
        self.assertIsNotNone(skills, "skills.json 不存在或无法解析")
        self.assertIsInstance(skills, dict, "skills.json 应为字典")

    def test_cfg_10_skill_class_requirements(self):
        skills = self.configs.get("skills", {})
        for sid, skill in skills.items():
            with self.subTest(skill=sid):
                self.assertEqual(skill.get("skill_id"), sid, f"技能 {sid}: skill_id 不匹配")
                self.assertIn("name", skill, f"技能 {sid}: 缺少 name")
                self.assertIn("type", skill, f"技能 {sid}: 缺少 type")
                for cls in skill.get("class_requirement", []):
                    self.assertIn(cls, VALID_CLASSES,
                                  f"技能 {sid}: 未知职业 '{cls}'")

    # ---- CFG-11 ~ CFG-12: 天赋配置 ----

    def test_cfg_11_talents_parseable(self):
        talents = self.configs.get("talents")
        self.assertIsNotNone(talents, "talents.json 不存在或无法解析")
        self.assertIsInstance(talents, dict, "talents.json 应为字典")

    def test_cfg_12_talent_prerequisites(self):
        talents = self.configs.get("talents", {})
        for tid, talent in talents.items():
            with self.subTest(talent=tid):
                self.assertEqual(talent.get("talent_id"), tid, f"天赋 {tid}: talent_id 不匹配")
                self.assertIn("name", talent, f"天赋 {tid}: 缺少 name")
                self.assertIn("class", talent, f"天赋 {tid}: 缺少 class")
                self.assertIn("tier", talent, f"天赋 {tid}: 缺少 tier")
                self.assertIn(talent["class"], VALID_CLASSES,
                              f"天赋 {tid}: 未知职业 '{talent['class']}'")
                self.assertGreaterEqual(talent["tier"], 1, f"天赋 {tid}: tier >= 1")
                self.assertLessEqual(talent["tier"], 5, f"天赋 {tid}: tier <= 5")
                for prereq in talent.get("prerequisites", []):
                    self.assertIn(prereq, talents,
                                  f"天赋 {tid}: 前置天赋 '{prereq}' 不存在")

    # ---- CFG-13 ~ CFG-14: 任务配置 ----

    def test_cfg_13_quests_parseable(self):
        quests = self.configs.get("quests")
        self.assertIsNotNone(quests, "quests.json 不存在或无法解析")
        self.assertIsInstance(quests, dict, "quests.json 应为字典")

    def test_cfg_14_quest_objective_references(self):
        quests = self.configs.get("quests", {})
        monsters = self.configs.get("monsters", {})
        items = self.configs.get("items", {})
        npcs = self.configs.get("npcs", {})
        for qid, quest in quests.items():
            with self.subTest(quest=qid):
                self.assertEqual(quest.get("id"), qid, f"任务 {qid}: id 不匹配")
                self.assertIn("name", quest, f"任务 {qid}: 缺少 name")
                self.assertIn("type", quest, f"任务 {qid}: 缺少 type")
                self.assertIn("objectives", quest, f"任务 {qid}: 缺少 objectives")
                self.assertIn("rewards", quest, f"任务 {qid}: 缺少 rewards")
                npc_id = quest.get("npc_id")
                if npc_id:
                    self.assertIn(npc_id, npcs,
                                  f"任务 {qid}: NPC '{npc_id}' 不存在")
                for obj in quest.get("objectives", []):
                    self.assertIn("type", obj, f"任务 {qid}: objective 缺少 type")
                    obj_type = obj["type"]
                    if obj_type == "kill":
                        target = obj.get("target")
                        if target:
                            self.assertIn(target, monsters,
                                          f"任务 {qid}: 击杀目标 '{target}' 不存在")
                    elif obj_type == "collect":
                        item_id = obj.get("item_id")
                        if item_id:
                            self.assertIn(item_id, items,
                                          f"任务 {qid}: 收集物品 '{item_id}' 不存在")
                    elif obj_type == "talk":
                        talk_npc = obj.get("npc_id")
                        if talk_npc:
                            self.assertIn(talk_npc, npcs,
                                          f"任务 {qid}: 对话NPC '{talk_npc}' 不存在")
                    elif obj_type == "explore":
                        target_map = obj.get("map_id")
                        if target_map:
                            self.assertIn(target_map, self.maps,
                                          f"任务 {qid}: 探索地图 '{target_map}' 不存在")

    # ---- CFG-15: 编码校验 ----

    def test_cfg_15_json_utf8_encoding(self):
        for name, filepath in CONFIG_FILES.items():
            with self.subTest(config=name):
                self.assertTrue(filepath.exists(), f"{filepath.name} 不存在")
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    self.fail(f"{filepath.name} JSON 解析失败: {e}")
                except UnicodeDecodeError as e:
                    self.fail(f"{filepath.name} UTF-8 编码错误: {e}")

    # ---- 交叉引用测试 ----

    def test_cfg_cross_npc_map_references(self):
        npcs = self.configs.get("npcs", {})
        for nid, npc in npcs.items():
            map_id = npc.get("map_id")
            if map_id:
                with self.subTest(npc=nid, map=map_id):
                    self.assertIn(map_id, self.maps,
                                  f"NPC {nid} 所在地图 '{map_id}' 不存在")

    def test_cfg_cross_quest_explore_targets(self):
        quests = self.configs.get("quests", {})
        for qid, quest in quests.items():
            for obj in quest.get("objectives", []):
                if obj.get("type") == "explore":
                    target_map = obj.get("map_id")
                    if target_map:
                        with self.subTest(quest=qid, map=target_map):
                            self.assertIn(target_map, self.maps,
                                          f"任务 {qid} 探索地图 '{target_map}' 不存在")

    def test_cfg_cross_map_npc_references(self):
        npcs = self.configs.get("npcs", {})
        for map_id, map_data in self.maps.items():
            for npc_ref in map_data.get("npcs", []):
                ref_id = npc_ref.get("npc_id") or npc_ref.get("id")
                if ref_id:
                    with self.subTest(map=map_id, npc=ref_id):
                        self.assertIn(ref_id, npcs,
                                      f"地图 {map_id} 引用NPC '{ref_id}' 不存在")

    def test_cfg_cross_map_monster_references(self):
        monsters = self.configs.get("monsters", {})
        for map_id, map_data in self.maps.items():
            for monster_ref in map_data.get("monsters", []):
                ref_id = monster_ref.get("monster_id") or monster_ref.get("id")
                if ref_id:
                    with self.subTest(map=map_id, monster=ref_id):
                        self.assertIn(ref_id, monsters,
                                      f"地图 {map_id} 引用怪物 '{ref_id}' 不存在")

    def test_cfg_aoe_skill_scrolls_exist(self):
        items = self.configs.get("items", {})
        skills = self.configs.get("skills", {})
        aoe_skill_ids = ["whirlwind", "war_cry", "poison_mist", "shadow_raid",
                         "flame_storm", "blizzard", "holy_prayer"]
        for sid in aoe_skill_ids:
            scroll_id = f"scroll_{sid}"
            with self.subTest(scroll=scroll_id):
                self.assertIn(scroll_id, items, f"缺少群体技能书: {scroll_id}")
                scroll = items[scroll_id]
                self.assertEqual(scroll.get("type"), "skill_book")
                effect = scroll.get("effect", {})
                self.assertEqual(effect.get("type"), "learn_skill")
                self.assertEqual(effect.get("skill_id"), sid)
                self.assertIn(sid, skills, f"技能 '{sid}' 在 skills.json 中不存在")

    def test_cfg_skill_master_has_aoe_scrolls(self):
        npcs = self.configs.get("npcs", {})
        skill_master = npcs.get("skill_master")
        self.assertIsNotNone(skill_master, "缺少 skill_master NPC")
        inventory = skill_master.get("shop", {}).get("inventory", [])
        scroll_ids = [item["item_id"] for item in inventory]
        aoe_scrolls = ["scroll_whirlwind", "scroll_war_cry", "scroll_poison_mist",
                       "scroll_shadow_raid", "scroll_flame_storm", "scroll_blizzard",
                       "scroll_holy_prayer"]
        for sid in aoe_scrolls:
            self.assertIn(sid, scroll_ids,
                          f"skill_master 缺少群体技能书: {sid}")

    def test_cfg_forest_no_overlapping_monsters_and_groups(self):
        forest = self.maps.get("forest")
        if not forest:
            self.skipTest("forest 地图不存在")
        group_positions = set()
        for g in forest.get("monster_groups", []):
            group_positions.add((g.get("x"), g.get("y")))
        for m in forest.get("monsters", []):
            pos = (m.get("x"), m.get("y"))
            self.assertNotIn(pos, group_positions,
                             f"怪物 {m.get('monster_id')} 在 ({pos[0]},{pos[1]}) 与怪物组位置重叠")


if __name__ == "__main__":
    unittest.main()
