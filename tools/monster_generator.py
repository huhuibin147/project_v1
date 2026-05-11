#!/usr/bin/env python3
"""
怪物生成器 - 用于创建和管理游戏怪物配置

功能：
1. 从模板生成新怪物（普通、精英、BOSS）
2. 按等级自动平衡怪物属性
3. 为怪物分配掉落物品
4. 配置怪物 AI 行为（攻击型、谨慎型、防御型、特殊型）
5. 验证怪物数据完整性
6. 列出所有怪物
7. 预览怪物属性分布

使用方法：
  python monster_generator.py create <模板名> <怪物id> [等级] [名称]    # 从模板创建怪物
  python monster_generator.py create-normal <id> <名称> <等级>            # 创建普通怪物
  python monster_generator.py create-elite <id> <名称> <等级>             # 创建精英怪物
  python monster_generator.py create-boss <id> <名称> <等级>              # 创建 BOSS
  python monster_generator.py drops <怪物id> [物品类型...]                # 分配掉落物品
  python monster_generator.py validate                                    # 验证怪物配置
  python monster_generator.py list                                        # 列出所有怪物
  python monster_generator.py preview                                     # 预览怪物属性
  python monster_generator.py apply                                       # 应用生成的怪物到 monsters.json
  python monster_generator.py batch <模板名> <数量> [等级范围] [前缀]      # 批量生成怪物

示例：
  python monster_generator.py create-normal skeleton "骷髅兵" 2
  python monster_generator.py create-elite dark_knight "黑暗骑士" 8
  python monster_generator.py create-boss dragon "远古巨龙" 15
  python monster_generator.py drops skeleton material weapon
  python monster_generator.py batch normal 5 "1-3" "森林"
"""

import json
import os
import sys
import random
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
MONSTERS_FILE = CONFIG_DIR / "monsters.json"
ITEMS_FILE = CONFIG_DIR / "items.json"


# ===== 怪物类型模板 =====
# 定义不同类型怪物的默认配置

MONSTER_TEMPLATES = {
    "normal": {
        "type": "normal",
        "hp_multiplier": 1.0,
        "attack_multiplier": 1.0,
        "defense_multiplier": 1.0,
        "speed_multiplier": 1.0,
        "exp_multiplier": 1.0,
        "gold_range": (5, 20),
        "drop_count": (1, 3),
        "ai_behavior": "aggressive",
        "attack_weight": 80,
        "defend_weight": 15,
        "special_weight": 5,
        "description_suffix": ""
    },
    "elite": {
        "type": "elite",
        "hp_multiplier": 2.0,
        "attack_multiplier": 1.5,
        "defense_multiplier": 1.3,
        "speed_multiplier": 1.2,
        "exp_multiplier": 2.5,
        "gold_range": (30, 80),
        "drop_count": (2, 5),
        "ai_behavior": "aggressive",
        "attack_weight": 75,
        "defend_weight": 20,
        "special_weight": 5,
        "description_suffix": "（精英）"
    },
    "boss": {
        "type": "boss",
        "hp_multiplier": 4.0,
        "attack_multiplier": 2.0,
        "defense_multiplier": 1.8,
        "speed_multiplier": 1.0,
        "exp_multiplier": 5.0,
        "gold_range": (100, 300),
        "drop_count": (4, 8),
        "ai_behavior": "defensive",
        "attack_weight": 60,
        "defend_weight": 30,
        "special_weight": 10,
        "description_suffix": "（BOSS）"
    },
    "cautious": {
        "type": "normal",
        "hp_multiplier": 0.9,
        "attack_multiplier": 0.9,
        "defense_multiplier": 1.2,
        "speed_multiplier": 1.1,
        "exp_multiplier": 1.0,
        "gold_range": (5, 20),
        "drop_count": (1, 3),
        "ai_behavior": "cautious",
        "attack_weight": 65,
        "defend_weight": 25,
        "special_weight": 10,
        "description_suffix": ""
    },
    "defensive": {
        "type": "normal",
        "hp_multiplier": 1.3,
        "attack_multiplier": 0.8,
        "defense_multiplier": 1.5,
        "speed_multiplier": 0.7,
        "exp_multiplier": 1.1,
        "gold_range": (8, 25),
        "drop_count": (1, 3),
        "ai_behavior": "defensive",
        "attack_weight": 50,
        "defend_weight": 40,
        "special_weight": 10,
        "description_suffix": ""
    }
}


# ===== 怪物种族预设 =====
# 用于快速创建特定类型的怪物

MONSTER_PRESETS = {
    "skeleton": {
        "template": "normal",
        "name": "骷髅兵",
        "description": "被黑暗魔法复活的骷髅，手持锈剑",
        "sprite_color": "#dddddd",
        "sprite_accent": "#999999",
        "base_stats": {"hp": 35, "attack": 10, "defense": 4, "speed": 6},
        "level": 2,
        "tags": ["undead", "common"],
        "special": None
    },
    "zombie": {
        "template": "normal",
        "name": "僵尸",
        "description": "行动缓慢但力大无穷的亡灵",
        "sprite_color": "#557755",
        "sprite_accent": "#334433",
        "base_stats": {"hp": 50, "attack": 12, "defense": 3, "speed": 3},
        "level": 2,
        "tags": ["undead", "common"],
        "special": None
    },
    "ghost": {
        "template": "cautious",
        "name": "幽灵",
        "description": "飘忽不定的幽灵，物理攻击难以命中",
        "sprite_color": "#aaddff",
        "sprite_accent": "#88bbdd",
        "base_stats": {"hp": 30, "attack": 14, "defense": 2, "speed": 15},
        "level": 4,
        "tags": ["undead", "rare"],
        "special": {
            "type": "apply_effect",
            "effect": "fear",
            "chance": 0.2,
            "duration": 2,
            "value": 0,
            "message": "幽灵发出恐怖的尖啸！"
        }
    },
    "dark_knight": {
        "template": "elite",
        "name": "黑暗骑士",
        "description": "堕落的骑士，身披黑色铠甲",
        "sprite_color": "#333344",
        "sprite_accent": "#111122",
        "base_stats": {"hp": 80, "attack": 22, "defense": 18, "speed": 8},
        "level": 8,
        "tags": ["humanoid", "elite", "rare"],
        "special": {
            "type": "apply_effect",
            "effect": "bleed",
            "chance": 0.3,
            "duration": 3,
            "value": 5,
            "message": "黑暗骑士的剑刺穿了你的护甲！"
        }
    },
    "dragon": {
        "template": "boss",
        "name": "远古巨龙",
        "description": "沉睡千年的巨龙，喷吐着毁灭性的火焰",
        "sprite_color": "#cc3333",
        "sprite_accent": "#aa1111",
        "base_stats": {"hp": 200, "attack": 35, "defense": 25, "speed": 10},
        "level": 15,
        "tags": ["dragon", "boss", "legendary"],
        "special": {
            "type": "apply_effect",
            "effect": "burn",
            "chance": 0.5,
            "duration": 3,
            "value": 10,
            "message": "巨龙喷出炽热的火焰！"
        }
    },
    "giant_spider": {
        "template": "normal",
        "name": "巨型蜘蛛",
        "description": "洞穴深处的巨型蜘蛛，毒性强烈",
        "sprite_color": "#664422",
        "sprite_accent": "#442211",
        "base_stats": {"hp": 40, "attack": 12, "defense": 5, "speed": 12},
        "level": 3,
        "tags": ["beast", "cave", "common"],
        "special": {
            "type": "apply_effect",
            "effect": "poison",
            "chance": 0.4,
            "duration": 3,
            "value": 0,
            "message": "巨型蜘蛛咬了你一口！"
        }
    },
    "orc": {
        "template": "normal",
        "name": "兽人战士",
        "description": "强壮的兽人战士，挥舞着巨大的战斧",
        "sprite_color": "#448844",
        "sprite_accent": "#226622",
        "base_stats": {"hp": 55, "attack": 16, "defense": 8, "speed": 7},
        "level": 4,
        "tags": ["humanoid", "common"],
        "special": None
    },
    "vampire": {
        "template": "elite",
        "name": "吸血鬼伯爵",
        "description": "高贵的吸血鬼，以鲜血为食",
        "sprite_color": "#880000",
        "sprite_accent": "#550000",
        "base_stats": {"hp": 90, "attack": 20, "defense": 12, "speed": 18},
        "level": 10,
        "tags": ["undead", "elite", "rare"],
        "special": {
            "type": "life_drain",
            "effect": "heal",
            "chance": 0.3,
            "duration": 1,
            "value": 15,
            "message": "吸血鬼吸取了你的生命力！"
        }
    }
}


# ===== 掉落物品规则 =====
# 定义不同类型怪物掉落的物品类型和概率

DROP_RULES = {
    "undead": {
        "materials": ["beast_bone", "magic_crystal", "cloth"],
        "consumables": ["health_potion", "purify_potion"],
        "equipment": ["weapon", "accessory"],
        "chance": 0.4
    },
    "beast": {
        "materials": ["wolf_pelt", "beast_bone", "venom_sac"],
        "consumables": ["health_potion", "antidote"],
        "equipment": ["armor", "accessory"],
        "chance": 0.5
    },
    "humanoid": {
        "materials": ["iron_ore", "cloth", "steel_ingot"],
        "consumables": ["health_potion", "bandage", "mana_potion"],
        "equipment": ["weapon", "armor", "shield"],
        "chance": 0.35
    },
    "dragon": {
        "materials": ["dragon_scale", "magic_crystal", "crystal_shard"],
        "consumables": ["greater_health_potion", "strength_elixir"],
        "equipment": ["weapon", "armor", "accessory"],
        "chance": 0.7
    },
    "default": {
        "materials": ["herb", "mushroom", "cloth"],
        "consumables": ["health_potion", "bandage"],
        "equipment": [],
        "chance": 0.3
    }
}


class MonsterGenerator:
    def __init__(self):
        self.monsters = self._load_monsters()
        self.items = self._load_items()
        self.generated = {}

    def _load_monsters(self):
        if MONSTERS_FILE.exists():
            with open(MONSTERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _load_items(self):
        if ITEMS_FILE.exists():
            with open(ITEMS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_monsters(self):
        with open(MONSTERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.monsters, f, ensure_ascii=False, indent=2)
        print(f"已保存到 {MONSTERS_FILE}")

    def _calc_stats(self, base_stats, level, template):
        """根据等级和模板计算怪物属性"""
        level_factor = 1 + (level - 1) * 0.15

        stats = {
            "hp": round(base_stats["hp"] * level_factor * template["hp_multiplier"]),
            "attack": round(base_stats["attack"] * level_factor * template["attack_multiplier"]),
            "defense": round(base_stats["defense"] * level_factor * template["defense_multiplier"]),
            "speed": round(base_stats["speed"] * level_factor * template["speed_multiplier"])
        }
        return stats

    def _generate_drops(self, tags, template, level):
        """根据怪物标签生成掉落物品"""
        drops = []

        # 根据标签确定掉落规则
        rule = DROP_RULES["default"]
        for tag in tags:
            if tag in DROP_RULES:
                rule = DROP_RULES[tag]
                break

        # 材料掉落
        for material_id in rule.get("materials", []):
            if material_id in self.items and random.random() < rule["chance"]:
                drops.append({
                    "item_id": material_id,
                    "chance": round(random.uniform(0.2, 0.6), 2)
                })

        # 消耗品掉落
        for consumable_id in rule.get("consumables", []):
            if consumable_id in self.items and random.random() < rule["chance"] * 0.8:
                drops.append({
                    "item_id": consumable_id,
                    "chance": round(random.uniform(0.15, 0.4), 2)
                })

        # 装备掉落（精英和BOSS更高概率）
        if template["type"] in ["elite", "boss"]:
            equip_types = rule.get("equipment", [])
            for equip_type in equip_types:
                candidates = [item_id for item_id, item in self.items.items()
                             if item.get("type") == equip_type or item.get("equip_slot") == equip_type]
                if candidates:
                    item_id = random.choice(candidates)
                    drops.append({
                        "item_id": item_id,
                        "chance": round(random.uniform(0.05, 0.15), 2)
                    })

        # BOSS 额外掉落
        if template["type"] == "boss":
            rare_items = [item_id for item_id, item in self.items.items()
                         if item.get("rarity") in ["epic", "legendary"]]
            if rare_items:
                drops.append({
                    "item_id": random.choice(rare_items),
                    "chance": 0.1
                })

        return drops

    def create_monster(self, template_name, monster_id, name=None, level=1,
                       description=None, sprite_color=None, sprite_accent=None,
                       base_stats=None, tags=None, special=None):
        """从模板创建怪物"""
        if template_name not in MONSTER_TEMPLATES:
            print(f"错误：未知模板 '{template_name}'")
            print(f"可用模板：{', '.join(MONSTER_TEMPLATES.keys())}")
            return None

        template = MONSTER_TEMPLATES[template_name]

        # 检查 ID 是否已存在
        if monster_id in self.monsters or monster_id in self.generated:
            print(f"错误：怪物 ID '{monster_id}' 已存在")
            return None

        # 使用默认属性
        final_name = name or f"未命名{template_name}"
        final_description = description or f"一只{level}级的{final_name}。"
        final_sprite_color = sprite_color or "#888888"
        final_sprite_accent = sprite_accent or "#555555"
        final_base_stats = base_stats or {"hp": 30, "attack": 8, "defense": 3, "speed": 5}
        final_tags = tags or ["common"]

        # 计算属性
        stats = self._calc_stats(final_base_stats, level, template)

        # 计算奖励
        exp_reward = round(level * 15 * template["exp_multiplier"])
        gold_min, gold_max = template["gold_range"]
        gold_reward = [round(gold_min * (1 + (level - 1) * 0.1)),
                      round(gold_max * (1 + (level - 1) * 0.1))]

        # 生成掉落
        drops = self._generate_drops(final_tags, template, level)

        monster = {
            "id": monster_id,
            "name": final_name,
            "description": final_description + template["description_suffix"],
            "type": template["type"],
            "sprite_color": final_sprite_color,
            "sprite_accent": final_sprite_accent,
            "stats": stats,
            "exp_reward": exp_reward,
            "gold_reward": gold_reward,
            "drops": drops,
            "ai": {
                "behavior": template["ai_behavior"],
                "attack_weight": template["attack_weight"],
                "defend_weight": template["defend_weight"],
                "special_weight": template["special_weight"],
                "special": special
            },
            "level": level,
            "tags": final_tags
        }

        self.generated[monster_id] = monster
        print(f"已创建怪物：{monster['name']} ({monster_id}) - Lv.{level} {template['type']}")
        print(f"  HP:{stats['hp']} ATK:{stats['attack']} DEF:{stats['defense']} SPD:{stats['speed']}")
        print(f"  EXP:{exp_reward} GOLD:{gold_reward} DROPS:{len(drops)}")
        return monster

    def create_from_preset(self, preset_name):
        """从预设创建怪物"""
        if preset_name not in MONSTER_PRESETS:
            print(f"错误：未知预设 '{preset_name}'")
            print(f"可用预设：{', '.join(MONSTER_PRESETS.keys())}")
            return None

        preset = MONSTER_PRESETS[preset_name]
        template_name = preset["template"]

        monster = self.create_monster(
            template_name=template_name,
            monster_id=preset_name,
            name=preset["name"],
            level=preset["level"],
            description=preset["description"],
            sprite_color=preset["sprite_color"],
            sprite_accent=preset["sprite_accent"],
            base_stats=preset["base_stats"],
            tags=preset["tags"],
            special=preset.get("special")
        )

        return monster

    def assign_drops(self, monster_id, item_types=None, specific_items=None):
        """为怪物分配掉落物品"""
        monster = self.generated.get(monster_id) or self.monsters.get(monster_id)
        if not monster:
            print(f"错误：怪物 '{monster_id}' 不存在")
            return False

        drops = []

        # 按类型分配掉落
        if item_types:
            for item_type in item_types:
                candidates = [item_id for item_id, item in self.items.items()
                             if item.get("type") == item_type or item.get("equip_slot") == item_type]
                if candidates:
                    selected = random.sample(candidates, min(len(candidates), random.randint(1, 3)))
                    for item_id in selected:
                        drops.append({
                            "item_id": item_id,
                            "chance": round(random.uniform(0.1, 0.5), 2)
                        })

        # 添加指定物品
        if specific_items:
            for item_entry in specific_items:
                if isinstance(item_entry, str):
                    drops.append({"item_id": item_entry, "chance": round(random.uniform(0.1, 0.5), 2)})
                elif isinstance(item_entry, dict):
                    drops.append(item_entry)

        monster["drops"] = drops
        print(f"已为 {monster['name']} 分配 {len(drops)} 种掉落物品")
        return True

    def batch_create(self, template_name, count, level_range="1-5", name_prefix=""):
        """批量生成同类型怪物"""
        if template_name not in MONSTER_TEMPLATES:
            print(f"错误：未知模板 '{template_name}'")
            return []

        # 解析等级范围
        if "-" in level_range:
            min_level, max_level = map(int, level_range.split("-"))
        else:
            min_level = max_level = int(level_range)

        created = []
        for i in range(count):
            monster_id = f"{name_prefix or template_name}_{i+1}"
            level = random.randint(min_level, max_level)
            name = f"{name_prefix or template_name}{i+1}号"

            monster = self.create_monster(
                template_name=template_name,
                monster_id=monster_id,
                name=name,
                level=level
            )
            if monster:
                created.append(monster)

        print(f"\n批量生成完成：{len(created)} 个 {template_name} 怪物")
        return created

    def validate_monster(self, monster_id, monster_data):
        """验证单个怪物配置"""
        issues = []
        required_fields = ["id", "name", "description", "type", "stats", "exp_reward", "gold_reward", "drops", "ai", "level", "tags"]

        for field in required_fields:
            if field not in monster_data:
                issues.append(f"{monster_id}: 缺少必填字段 '{field}'")

        # 验证 stats
        stats = monster_data.get("stats", {})
        for key in ["hp", "attack", "defense", "speed"]:
            if key not in stats:
                issues.append(f"{monster_id}: stats 缺少 '{key}'")
            elif stats[key] <= 0:
                issues.append(f"{monster_id}: stats.{key} 应大于 0")

        # 验证 AI
        ai = monster_data.get("ai", {})
        for key in ["behavior", "attack_weight", "defend_weight", "special_weight"]:
            if key not in ai:
                issues.append(f"{monster_id}: ai 缺少 '{key}'")

        # 验证掉落
        for drop in monster_data.get("drops", []):
            if "item_id" not in drop or "chance" not in drop:
                issues.append(f"{monster_id}: drops 格式错误")
                break
            if not (0 <= drop["chance"] <= 1):
                issues.append(f"{monster_id}: drop chance 应在 0-1 范围内")

        return issues

    def validate(self):
        """验证所有怪物配置"""
        all_issues = []
        for monster_id, monster_data in self.monsters.items():
            issues = self.validate_monster(monster_id, monster_data)
            all_issues.extend(issues)

        if all_issues:
            print(f"发现 {len(all_issues)} 个问题：")
            for issue in all_issues:
                print(f"  - {issue}")
        else:
            print("所有怪物配置验证通过！")
        return len(all_issues)

    def list_monsters(self):
        """列出所有怪物"""
        print(f"\n当前共有 {len(self.monsters)} 个怪物：\n")
        print(f"{'ID':<20} {'名称':<12} {'类型':<8} {'等级':<6} {'HP':<6} {'ATK':<6} {'DEF':<6} {'SPD':<6}")
        print("-" * 80)

        for monster_id, monster in sorted(self.monsters.items(), key=lambda x: x[1].get("level", 0)):
            mtype = monster["type"]
            level = monster["level"]
            stats = monster["stats"]
            print(f"{monster_id:<20} {monster['name']:<12} {mtype:<8} {level:<6} {stats['hp']:<6} {stats['attack']:<6} {stats['defense']:<6} {stats['speed']:<6}")

    def preview(self):
        """预览怪物属性分布"""
        print("\n=== 怪物属性分布 ===")

        # 按类型统计
        types = {}
        for monster in self.monsters.values():
            t = monster["type"]
            types[t] = types.get(t, 0) + 1
        print("\n按类型分类：")
        for t, count in sorted(types.items()):
            print(f"  {t}: {count} 只")

        # 按等级统计
        levels = {}
        for monster in self.monsters.values():
            lv = monster["level"]
            levels[lv] = levels.get(lv, 0) + 1
        print("\n按等级分类：")
        for lv, count in sorted(levels.items()):
            print(f"  Lv.{lv}: {count} 只")

        # 属性平均值
        print("\n属性平均值：")
        stats_sum = {"hp": 0, "attack": 0, "defense": 0, "speed": 0}
        for monster in self.monsters.values():
            for key in stats_sum:
                stats_sum[key] += monster["stats"].get(key, 0)
        count = len(self.monsters)
        for key, total in stats_sum.items():
            print(f"  {key}: {total/count:.1f}")

        # 奖励平均值
        print("\n奖励平均值：")
        exp_sum = sum(m["exp_reward"] for m in self.monsters.values())
        gold_sum = sum(sum(m["gold_reward"]) / 2 for m in self.monsters.values())
        print(f"  经验: {exp_sum/count:.1f}")
        print(f"  金币: {gold_sum/count:.1f}")

    def apply(self):
        """将生成的怪物应用到 monsters.json"""
        if not self.generated:
            print("没有新生成的怪物需要应用")
            return

        # 合并到现有怪物
        self.monsters.update(self.generated)
        self._save_monsters()
        print(f"已应用 {len(self.generated)} 个新怪物")
        self.generated.clear()

    def create_boss_with_phases(self, monster_id, name, level, phases_config):
        if monster_id in self.monsters or monster_id in self.generated:
            print(f"错误：怪物 ID '{monster_id}' 已存在")
            return None
        template = MONSTER_TEMPLATES["boss"]
        base_stats = phases_config.get("base_stats", {"hp": 150, "attack": 25, "defense": 15, "speed": 8})
        stats = self._calc_stats(base_stats, level, template)
        phases = []
        for i, phase_cfg in enumerate(phases_config.get("phases", [
            {"name": "正常", "hp_threshold": 1.0, "ai": {"attack": 0.5, "defend": 0.3, "special": 0.2}},
            {"name": "愤怒", "hp_threshold": 0.5, "ai": {"attack": 0.7, "defend": 0.1, "special": 0.2}, "stat_boost": {"attack": 1.3}},
            {"name": "狂暴", "hp_threshold": 0.25, "ai": {"attack": 0.8, "defend": 0.0, "special": 0.2}, "stat_boost": {"attack": 1.5}},
        ])):
            phase = {
                "name": phase_cfg.get("name", f"阶段{i+1}"),
                "hp_threshold": phase_cfg.get("hp_threshold", 1.0 - i * 0.3),
                "ai": phase_cfg.get("ai", {"attack": 0.5, "defend": 0.3, "special": 0.2}),
            }
            if "stat_boost" in phase_cfg:
                phase["stat_boost"] = phase_cfg["stat_boost"]
            if "new_special" in phase_cfg:
                phase["new_special"] = phase_cfg["new_special"]
            phases.append(phase)
        exp_reward = round(level * 15 * template["exp_multiplier"])
        gold_min, gold_max = template["gold_range"]
        gold_reward = [round(gold_min * (1 + (level - 1) * 0.1)),
                      round(gold_max * (1 + (level - 1) * 0.1))]
        drops = self._generate_drops(phases_config.get("tags", ["boss", "legendary"]), template, level)
        monster = {
            "id": monster_id,
            "name": name,
            "description": phases_config.get("description", f"强大的BOSS：{name}"),
            "type": "boss",
            "sprite_color": phases_config.get("sprite_color", "#cc3333"),
            "sprite_accent": phases_config.get("sprite_accent", "#aa1111"),
            "stats": stats,
            "exp_reward": exp_reward,
            "gold_reward": gold_reward,
            "drops": drops,
            "ai": {
                "behavior": template["ai_behavior"],
                "attack_weight": template["attack_weight"],
                "defend_weight": template["defend_weight"],
                "special_weight": template["special_weight"],
                "special": phases_config.get("special", None),
            },
            "phases": phases,
            "level": level,
            "tags": phases_config.get("tags", ["boss", "legendary"]),
        }
        self.generated[monster_id] = monster
        print(f"已创建 BOSS：{name} ({monster_id}) - Lv.{level}，{len(phases)} 阶段")
        for p in phases:
            print(f"  阶段：{p['name']} (HP<{p['hp_threshold']*100:.0f}%) AI:{p['ai']}")
        return monster

    def generate_monster_skills(self, monster_id, skill_count=2):
        monster = self.generated.get(monster_id) or self.monsters.get(monster_id)
        if not monster:
            print(f"错误：怪物 '{monster_id}' 不存在")
            return []
        SKILL_TEMPLATES = [
            {"name": "猛击", "type": "damage", "power": 1.3, "effect": None, "desc": "全力一击"},
            {"name": "毒咬", "type": "damage", "power": 1.0, "effect": {"type": "poison", "duration": 3, "value": 0}, "desc": "注入毒素"},
            {"name": "火焰吐息", "type": "damage", "power": 1.5, "effect": {"type": "burn", "duration": 3, "value": 5}, "desc": "喷出火焰"},
            {"name": "冰霜之息", "type": "damage", "power": 1.2, "effect": {"type": "freeze", "duration": 1, "value": 0}, "desc": "冻结敌人"},
            {"name": "暗影打击", "type": "damage", "power": 1.4, "effect": {"type": "fear", "duration": 2, "value": 0}, "desc": "暗影侵袭"},
            {"name": "生命汲取", "type": "life_drain", "power": 0.8, "effect": {"type": "heal", "duration": 1, "value": 15}, "desc": "吸取生命"},
            {"name": "防御强化", "type": "buff", "power": 0, "effect": {"type": "defense_up", "duration": 3, "value": 30}, "desc": "提升防御"},
            {"name": "狂暴", "type": "buff", "power": 0, "effect": {"type": "attack_up", "duration": 3, "value": 30}, "desc": "提升攻击"},
            {"name": "治愈", "type": "heal", "power": 0, "effect": {"type": "heal", "duration": 1, "value": 20}, "desc": "恢复生命"},
            {"name": "召唤", "type": "summon", "power": 0, "effect": None, "desc": "召唤小怪"},
        ]
        eligible = SKILL_TEMPLATES[:]
        if monster["type"] == "normal":
            eligible = [s for s in eligible if s["type"] in ("damage", "buff")]
            skill_count = min(skill_count, 1)
        elif monster["type"] == "elite":
            eligible = [s for s in eligible if s["type"] in ("damage", "buff", "life_drain")]
            skill_count = min(skill_count, 2)
        selected = random.sample(eligible, min(skill_count, len(eligible)))
        skills = []
        for i, tmpl in enumerate(selected):
            skill = {
                "skill_id": f"{monster_id}_skill_{i+1}",
                "name": tmpl["name"],
                "type": tmpl["type"],
                "power": tmpl["power"],
                "effect": tmpl["effect"],
                "description": tmpl["desc"],
                "cooldown": random.randint(2, 4),
            }
            skills.append(skill)
        monster["skills"] = skills
        print(f"已为 {monster['name']} 生成 {len(skills)} 个技能")
        return skills

    def balance_check(self):
        issues = []
        for monster_id, monster in self.monsters.items():
            level = monster.get("level", 1)
            stats = monster.get("stats", {})
            mtype = monster.get("type", "normal")
            expected_hp = level * 15 * (2.0 if mtype == "elite" else 4.0 if mtype == "boss" else 1.0)
            expected_atk = level * 5 * (1.5 if mtype == "elite" else 2.0 if mtype == "boss" else 1.0)
            expected_def = level * 3 * (1.3 if mtype == "elite" else 1.8 if mtype == "boss" else 1.0)
            hp = stats.get("hp", 0)
            atk = stats.get("attack", 0)
            dfn = stats.get("defense", 0)
            if hp < expected_hp * 0.5:
                issues.append(f"{monster_id} (Lv.{level} {mtype}): HP={hp} 偏低（预期≈{expected_hp:.0f}）")
            elif hp > expected_hp * 2.0:
                issues.append(f"{monster_id} (Lv.{level} {mtype}): HP={hp} 偏高（预期≈{expected_hp:.0f}）")
            if atk < expected_atk * 0.5:
                issues.append(f"{monster_id} (Lv.{level} {mtype}): ATK={atk} 偏低（预期≈{expected_atk:.0f}）")
            elif atk > expected_atk * 2.0:
                issues.append(f"{monster_id} (Lv.{level} {mtype}): ATK={atk} 偏高（预期≈{expected_atk:.0f}）")
            if dfn < expected_def * 0.3:
                issues.append(f"{monster_id} (Lv.{level} {mtype}): DEF={dfn} 偏低（预期≈{expected_def:.0f}）")
            exp = monster.get("exp_reward", 0)
            expected_exp = level * 15 * (2.5 if mtype == "elite" else 5.0 if mtype == "boss" else 1.0)
            if exp < expected_exp * 0.5:
                issues.append(f"{monster_id}: EXP={exp} 偏低（预期≈{expected_exp:.0f}）")
            ai = monster.get("ai", {})
            weights = [ai.get("attack_weight", 0), ai.get("defend_weight", 0), ai.get("special_weight", 0)]
            if sum(weights) != 100:
                issues.append(f"{monster_id}: AI权重总和={sum(weights)}（应为100）")
        if issues:
            print(f"平衡性检查发现 {len(issues)} 个问题：")
            for issue in issues:
                print(f"  ⚠ {issue}")
        else:
            print("平衡性检查通过！所有怪物属性在合理范围内")
        return len(issues)

    def show_templates(self):
        """显示所有可用模板"""
        print("\n=== 可用怪物模板 ===")
        for name, template in MONSTER_TEMPLATES.items():
            print(f"\n{name}: {template['type']}")
            print(f"  属性倍率: HP×{template['hp_multiplier']}, ATK×{template['attack_multiplier']}, DEF×{template['defense_multiplier']}, SPD×{template['speed_multiplier']}")
            print(f"  经验倍率: ×{template['exp_multiplier']}")
            print(f"  金币范围: {template['gold_range']}")
            print(f"  AI: {template['ai_behavior']} (攻击{template['attack_weight']}/防御{template['defend_weight']}/特殊{template['special_weight']})")

    def show_presets(self):
        """显示所有可用预设"""
        print("\n=== 可用怪物预设 ===")
        for name, preset in MONSTER_PRESETS.items():
            print(f"\n{name}: {preset['name']} (Lv.{preset['level']})")
            print(f"  模板: {preset['template']}")
            print(f"  描述: {preset['description']}")
            print(f"  标签: {', '.join(preset['tags'])}")
            stats = preset['base_stats']
            print(f"  基础属性: HP{stats['hp']} ATK{stats['attack']} DEF{stats['defense']} SPD{stats['speed']}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    gen = MonsterGenerator()

    if cmd == "create":
        if len(sys.argv) < 4:
            print("用法：python monster_generator.py create <模板名> <怪物id> [等级] [名称] [描述]")
            return
        template_name = sys.argv[2]
        monster_id = sys.argv[3]
        level = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        name = sys.argv[5] if len(sys.argv) > 5 else None
        description = sys.argv[6] if len(sys.argv) > 6 else None
        gen.create_monster(template_name, monster_id, name, level, description)

    elif cmd == "create-normal":
        if len(sys.argv) < 5:
            print("用法：python monster_generator.py create-normal <怪物id> <名称> <等级>")
            return
        monster_id = sys.argv[2]
        name = sys.argv[3]
        level = int(sys.argv[4])
        gen.create_monster("normal", monster_id, name, level)

    elif cmd == "create-elite":
        if len(sys.argv) < 5:
            print("用法：python monster_generator.py create-elite <怪物id> <名称> <等级>")
            return
        monster_id = sys.argv[2]
        name = sys.argv[3]
        level = int(sys.argv[4])
        gen.create_monster("elite", monster_id, name, level)

    elif cmd == "create-boss":
        if len(sys.argv) < 5:
            print("用法：python monster_generator.py create-boss <怪物id> <名称> <等级>")
            return
        monster_id = sys.argv[2]
        name = sys.argv[3]
        level = int(sys.argv[4])
        gen.create_monster("boss", monster_id, name, level)

    elif cmd == "preset":
        if len(sys.argv) < 3:
            print("用法：python monster_generator.py preset <预设名>")
            print(f"可用预设：{', '.join(MONSTER_PRESETS.keys())}")
            return
        preset_name = sys.argv[2]
        gen.create_from_preset(preset_name)

    elif cmd == "drops":
        if len(sys.argv) < 3:
            print("用法：python monster_generator.py drops <怪物id> [item_type...]")
            return
        monster_id = sys.argv[2]
        item_types = sys.argv[3:] if len(sys.argv) > 3 else ["material"]
        gen.assign_drops(monster_id, item_types)

    elif cmd == "batch":
        if len(sys.argv) < 4:
            print("用法：python monster_generator.py batch <模板名> <数量> [等级范围] [名称前缀]")
            return
        template_name = sys.argv[2]
        count = int(sys.argv[3])
        level_range = sys.argv[4] if len(sys.argv) > 4 else "1-5"
        prefix = sys.argv[5] if len(sys.argv) > 5 else ""
        gen.batch_create(template_name, count, level_range, prefix)

    elif cmd == "validate":
        gen.validate()

    elif cmd == "list":
        gen.list_monsters()

    elif cmd == "preview":
        gen.preview()

    elif cmd == "templates":
        gen.show_templates()

    elif cmd == "presets":
        gen.show_presets()

    elif cmd == "apply":
        gen.apply()

    elif cmd == "boss":
        if len(sys.argv) < 5:
            print("用法：python monster_generator.py boss <id> <名称> <等级> [描述]")
            return
        monster_id = sys.argv[2]
        name = sys.argv[3]
        level = int(sys.argv[4])
        gen.create_boss_with_phases(monster_id, name, level, {})

    elif cmd == "skills":
        if len(sys.argv) < 3:
            print("用法：python monster_generator.py skills <怪物id> [技能数量]")
            return
        monster_id = sys.argv[2]
        skill_count = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        gen.generate_monster_skills(monster_id, skill_count)

    elif cmd == "balance":
        gen.balance_check()

    else:
        print(f"未知命令：{cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
