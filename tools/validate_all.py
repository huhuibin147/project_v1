#!/usr/bin/env python3
"""全局配置验证工具 - 统一验证所有配置文件的完整性和一致性"""
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
MAPS_DIR = ROOT_DIR / "config" / "maps"

CONFIG_FILES = {
    "items": CONFIG_DIR / "items.json",
    "monsters": CONFIG_DIR / "monsters.json",
    "npcs": CONFIG_DIR / "npcs.json",
    "skills": CONFIG_DIR / "skills.json",
    "talents": CONFIG_DIR / "talents.json",
    "quests": CONFIG_DIR / "quests.json",
    "forge_recipes": CONFIG_DIR / "forge_recipes.json",
    "affixes": CONFIG_DIR / "affixes.json",
}


def load_config(name):
    filepath = CONFIG_FILES.get(name)
    if not filepath or not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_maps():
    maps = {}
    if not MAPS_DIR.exists():
        return maps
    for fp in MAPS_DIR.glob("*.json"):
        with open(fp, "r", encoding="utf-8") as f:
            maps[fp.stem] = json.load(f)
    return maps


class ConfigValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.configs = {}
        for name in CONFIG_FILES:
            self.configs[name] = load_config(name)
        self.maps = load_maps()

    def issue(self, msg):
        self.issues.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def validate_items(self):
        items = self.configs.get("items", {})
        if not items:
            self.warn("items.json 为空或不存在")
            return
        for iid, item in items.items():
            if item.get("id") != iid:
                self.issue(f"物品 {iid}: id 不匹配")
            for field in ["name", "type"]:
                if field not in item:
                    self.issue(f"物品 {iid}: 缺少 '{field}'")
            if item.get("buy_price", 0) < 0:
                self.issue(f"物品 {iid}: buy_price 不能为负")
            if item.get("sell_price", 0) < 0:
                self.issue(f"物品 {iid}: sell_price 不能为负")
            if item.get("equip_slot") and item.get("equip_slot") not in ("weapon", "head", "body", "legs", "feet", "accessory", "ring", "necklace"):
                self.warn(f"物品 {iid}: 未知装备槽位 '{item.get('equip_slot')}'")
        print(f"  物品验证: {len(items)} 个物品")

    def validate_monsters(self):
        monsters = self.configs.get("monsters", {})
        if not monsters:
            self.warn("monsters.json 为空或不存在")
            return
        for mid, monster in monsters.items():
            if monster.get("id") != mid:
                self.issue(f"怪物 {mid}: id 不匹配")
            for field in ["name", "type", "stats", "level"]:
                if field not in monster:
                    self.issue(f"怪物 {mid}: 缺少 '{field}'")
            stats = monster.get("stats", {})
            for stat in ["hp", "attack", "defense", "speed"]:
                if stat not in stats:
                    self.issue(f"怪物 {mid}: stats 缺少 '{stat}'")
                elif stats[stat] <= 0:
                    self.issue(f"怪物 {mid}: stats.{stat} 应大于 0")
            if monster.get("type") not in ("normal", "elite", "boss"):
                self.warn(f"怪物 {mid}: 未知类型 '{monster.get('type')}'")
        print(f"  怪物验证: {len(monsters)} 个怪物")

    def validate_npcs(self):
        npcs = self.configs.get("npcs", {})
        if not npcs:
            self.warn("npcs.json 为空或不存在")
            return
        for nid, npc in npcs.items():
            if npc.get("id") != nid:
                self.issue(f"NPC {nid}: id 不匹配")
            for field in ["name", "role", "location", "map_id"]:
                if field not in npc:
                    self.issue(f"NPC {nid}: 缺少 '{field}'")
            if "shop" in npc:
                shop = npc["shop"]
                if "name" not in shop:
                    self.issue(f"NPC {nid}: shop 缺少 name")
                for inv_item in shop.get("inventory", []):
                    if "item_id" not in inv_item:
                        self.issue(f"NPC {nid}: shop inventory 缺少 item_id")
        print(f"  NPC验证: {len(npcs)} 个NPC")

    def validate_skills(self):
        skills = self.configs.get("skills", {})
        if not skills:
            self.warn("skills.json 为空或不存在")
            return
        valid_classes = ["warrior", "mage", "rogue", "priest"]
        for sid, skill in skills.items():
            if skill.get("skill_id") != sid:
                self.issue(f"技能 {sid}: skill_id 不匹配")
            for field in ["name", "type", "mp_cost", "power", "class_requirement"]:
                if field not in skill:
                    self.issue(f"技能 {sid}: 缺少 '{field}'")
            for cls in skill.get("class_requirement", []):
                if cls not in valid_classes:
                    self.issue(f"技能 {sid}: 未知职业 '{cls}'")
        print(f"  技能验证: {len(skills)} 个技能")

    def validate_talents(self):
        talents = self.configs.get("talents", {})
        if not talents:
            self.warn("talents.json 为空或不存在")
            return
        valid_classes = ["warrior", "mage", "rogue", "priest"]
        for tid, talent in talents.items():
            if talent.get("talent_id") != tid:
                self.issue(f"天赋 {tid}: talent_id 不匹配")
            for field in ["name", "class", "tree", "tier", "effects"]:
                if field not in talent:
                    self.issue(f"天赋 {tid}: 缺少 '{field}'")
            if talent.get("class") not in valid_classes:
                self.issue(f"天赋 {tid}: 未知职业 '{talent.get('class')}'")
            if talent.get("tier", 0) < 1 or talent.get("tier", 0) > 5:
                self.issue(f"天赋 {tid}: tier 应在 1-5 范围内")
            for prereq in talent.get("prerequisites", []):
                if prereq not in talents:
                    self.issue(f"天赋 {tid}: 前置天赋 '{prereq}' 不存在")
        print(f"  天赋验证: {len(talents)} 个天赋")

    def validate_quests(self):
        quests = self.configs.get("quests", {})
        if not quests:
            self.warn("quests.json 为空或不存在")
            return
        npcs = self.configs.get("npcs", {})
        monsters = self.configs.get("monsters", {})
        items = self.configs.get("items", {})
        for qid, quest in quests.items():
            if quest.get("id") != qid:
                self.issue(f"任务 {qid}: id 不匹配")
            for field in ["name", "type", "objectives", "rewards"]:
                if field not in quest:
                    self.issue(f"任务 {qid}: 缺少 '{field}'")
            npc_id = quest.get("npc_id")
            if npc_id and npc_id not in npcs:
                self.warn(f"任务 {qid}: NPC '{npc_id}' 不在NPC配置中")
            for obj in quest.get("objectives", []):
                if "type" not in obj or "target" not in obj:
                    self.issue(f"任务 {qid}: objective 缺少 type 或 target")
                if obj.get("type") == "kill" and obj.get("target") not in monsters:
                    self.warn(f"任务 {qid}: 击杀目标 '{obj.get('target')}' 不在怪物配置中")
                if obj.get("type") == "collect" and obj.get("target") not in items:
                    self.warn(f"任务 {qid}: 收集目标 '{obj.get('target')}' 不在物品配置中")
        print(f"  任务验证: {len(quests)} 个任务")

    def validate_forge_recipes(self):
        recipes = self.configs.get("forge_recipes", {})
        if not recipes:
            return
        items = self.configs.get("items", {})
        for rid, recipe in recipes.items():
            if recipe.get("recipe_id") != rid:
                self.issue(f"配方 {rid}: recipe_id 不匹配")
            output = recipe.get("output", {})
            if output.get("item_id") and output["item_id"] not in items:
                self.warn(f"配方 {rid}: 产出物品 '{output['item_id']}' 不在物品配置中")
            for mat in recipe.get("materials", []):
                if mat.get("item_id") and mat["item_id"] not in items:
                    self.warn(f"配方 {rid}: 材料物品 '{mat['item_id']}' 不在物品配置中")
        print(f"  锻造配方验证: {len(recipes)} 个配方")

    def validate_affixes(self):
        affixes = self.configs.get("affixes", {})
        if not affixes:
            return
        for aid, affix in affixes.items():
            if affix.get("id") != aid:
                self.issue(f"词条 {aid}: id 不匹配")
            for field in ["name", "equip_slot", "stat", "value_range", "rarity_min"]:
                if field not in affix:
                    self.issue(f"词条 {aid}: 缺少 '{field}'")
        print(f"  词条验证: {len(affixes)} 个词条")

    def validate_cross_references(self):
        items = self.configs.get("items", {})
        monsters = self.configs.get("monsters", {})
        npcs = self.configs.get("npcs", {})
        quests = self.configs.get("quests", {})
        maps = self.maps

        for mid, monster in monsters.items():
            for drop in monster.get("drops", []):
                if drop.get("item_id") and drop["item_id"] not in items:
                    self.warn(f"交叉引用: 怪物 {mid} 掉落物品 '{drop['item_id']}' 不存在")

        for nid, npc in npcs.items():
            if "shop" in npc:
                for inv_item in npc["shop"].get("inventory", []):
                    if inv_item.get("item_id") and inv_item["item_id"] not in items:
                        self.warn(f"交叉引用: NPC {nid} 商品 '{inv_item['item_id']}' 不存在")
            npc_map = npc.get("map_id")
            if npc_map and maps and npc_map not in maps:
                self.warn(f"交叉引用: NPC {nid} 所在地图 '{npc_map}' 不存在")

        for qid, quest in quests.items():
            for obj in quest.get("objectives", []):
                if obj.get("type") == "explore":
                    target_map = obj.get("target")
                    if target_map and maps and target_map not in maps:
                        self.warn(f"交叉引用: 任务 {qid} 探索地图 '{target_map}' 不存在")

        for map_id, map_data in maps.items():
            for npc_ref in map_data.get("npcs", []):
                ref_id = npc_ref.get("npc_id") or npc_ref.get("id")
                if ref_id and ref_id not in npcs:
                    self.warn(f"交叉引用: 地图 {map_id} 引用NPC '{ref_id}' 不存在")
            for monster_ref in map_data.get("monsters", []):
                ref_id = monster_ref.get("monster_id") or monster_ref.get("id")
                if ref_id and ref_id not in monsters:
                    self.warn(f"交叉引用: 地图 {map_id} 引用怪物 '{ref_id}' 不存在")

        portal_links = {}
        for map_id, map_data in maps.items():
            for obj in map_data.get("objects", []):
                if obj.get("type") == "portal":
                    target_map = obj.get("properties", {}).get("target_map", "")
                    if target_map:
                        if map_id not in portal_links:
                            portal_links[map_id] = set()
                        portal_links[map_id].add(target_map)
        
        for map_id, targets in portal_links.items():
            for target in targets:
                if target in portal_links and map_id not in portal_links[target]:
                    self.warn(f"交叉引用: 地图 '{map_id}' 有传送门到 '{target}'，但 '{target}' 没有传送门回到 '{map_id}'（缺少双向链接）")

        print("  交叉引用验证完成")

    def validate_maps(self):
        if not self.maps:
            self.warn("没有地图配置")
            return
        for map_id, map_data in self.maps.items():
            if map_data.get("id") != map_id:
                self.issue(f"地图 {map_id}: id 不匹配")
            for field in ["name", "width", "height", "layers", "player_spawn"]:
                if field not in map_data:
                    self.issue(f"地图 {map_id}: 缺少 '{field}'")
            spawn = map_data.get("player_spawn", {})
            if spawn:
                if not (0 <= spawn.get("x", -1) < map_data.get("width", 0)):
                    self.issue(f"地图 {map_id}: player_spawn.x 超出范围")
                if not (0 <= spawn.get("y", -1) < map_data.get("height", 0)):
                    self.issue(f"地图 {map_id}: player_spawn.y 超出范围")
            for obj in map_data.get("objects", []):
                if obj.get("type") == "portal":
                    target_map = obj.get("properties", {}).get("target_map", "")
                    if target_map and target_map not in self.maps:
                        self.issue(f"地图 {map_id}: 传送门 '{obj.get('id', '?')}' 目标地图 '{target_map}' 不存在")
                    target_x = obj.get("properties", {}).get("target_x", -1)
                    target_y = obj.get("properties", {}).get("target_y", -1)
                    if target_map and target_map in self.maps:
                        target_data = self.maps[target_map]
                        tw, th = target_data.get("width", 0), target_data.get("height", 0)
                        if not (0 <= target_x < tw and 0 <= target_y < th):
                            self.issue(f"地图 {map_id}: 传送门 '{obj.get('id', '?')}' 落点 ({target_x},{target_y}) 超出目标地图 '{target_map}' 范围 ({tw}x{th})")
            for mg in map_data.get("monster_groups", []):
                for m in mg.get("monsters", []):
                    monster_id = m.get("monster_id", "")
                    if monster_id and monster_id not in self.configs.get("monsters", {}):
                        self.warn(f"地图 {map_id}: 怪物组 '{mg.get('group_id', '?')}' 引用怪物 '{monster_id}' 不存在")
        print(f"  地图验证: {len(self.maps)} 个地图")

    def validate_all(self):
        print("=" * 50)
        print("全局配置验证")
        print("=" * 50)
        print()
        print("[1/9] 验证物品配置...")
        self.validate_items()
        print("[2/9] 验证怪物配置...")
        self.validate_monsters()
        print("[3/9] 验证NPC配置...")
        self.validate_npcs()
        print("[4/9] 验证技能配置...")
        self.validate_skills()
        print("[5/9] 验证天赋配置...")
        self.validate_talents()
        print("[6/9] 验证任务配置...")
        self.validate_quests()
        print("[7/9] 验证锻造配方...")
        self.validate_forge_recipes()
        print("[8/9] 验证词条配置...")
        self.validate_affixes()
        print("[9/9] 验证地图配置...")
        self.validate_maps()
        print()
        print("交叉引用验证...")
        self.validate_cross_references()
        print()
        print("=" * 50)
        print(f"验证完成: {len(self.issues)} 个错误, {len(self.warnings)} 个警告")
        print("=" * 50)
        if self.issues:
            print("\n❌ 错误:")
            for issue in self.issues:
                print(f"  {issue}")
        if self.warnings:
            print("\n⚠️  警告:")
            for warning in self.warnings:
                print(f"  {warning}")
        if not self.issues and not self.warnings:
            print("\n✅ 所有配置验证通过！")
        return len(self.issues)

    def summary(self):
        print("\n配置文件概览:")
        print("-" * 40)
        for name, filepath in CONFIG_FILES.items():
            exists = "✓" if filepath.exists() else "✗"
            count = 0
            if filepath.exists():
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    count = len(data) if isinstance(data, dict) else len(data) if isinstance(data, list) else 0
                except Exception:
                    count = -1
            print(f"  {exists} {name:15s}: {count:4d} 条记录  ({filepath.name})")
        if MAPS_DIR.exists():
            map_count = len(list(MAPS_DIR.glob("*.json")))
            print(f"  ✓ {'maps':15s}: {map_count:4d} 条记录  (maps/)")


if __name__ == "__main__":
    validator = ConfigValidator()
    if len(sys.argv) < 2:
        validator.summary()
        print()
        validator.validate_all()
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "validate":
        validator.validate_all()
    elif cmd == "summary":
        validator.summary()
    elif cmd == "items":
        validator.validate_items()
    elif cmd == "monsters":
        validator.validate_monsters()
    elif cmd == "npcs":
        validator.validate_npcs()
    elif cmd == "skills":
        validator.validate_skills()
    elif cmd == "talents":
        validator.validate_talents()
    elif cmd == "quests":
        validator.validate_quests()
    elif cmd == "maps":
        validator.validate_maps()
    elif cmd == "cross":
        validator.validate_cross_references()
    else:
        print(f"未知命令: {cmd}")
        print("可用命令: validate, summary, items, monsters, npcs, skills, talents, quests, maps, cross")
