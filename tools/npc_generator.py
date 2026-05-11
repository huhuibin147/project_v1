#!/usr/bin/env python3
"""
NPC 生成器 - 用于创建和管理游戏 NPC 配置

功能：
1. 从模板生成新 NPC（商人、治疗师、技能导师、任务发布者等）
2. 为 NPC 分配商店库存（基于物品类型过滤）
3. 验证 NPC 配置完整性
4. 列出所有 NPC
5. 预览 NPC 属性分布
6. 批量生成同类型 NPC（如多个村庄商人）

使用方法：
  python npc_generator.py create <模板名> <npc_id> [选项]     # 从模板创建 NPC
  python npc_generator.py create-merchant <npc_id> <名称>      # 创建商人 NPC
  python npc_generator.py create-healer <npc_id> <名称>        # 创建治疗师 NPC
  python npc_generator.py create-master <npc_id> <名称>        # 创建技能导师 NPC
  python npc_generator.py create-quest <npc_id> <名称>         # 创建任务发布者 NPC
  python npc_generator.py shop <npc_id> [item_type...]         # 为 NPC 分配商店库存
  python npc_generator.py validate                             # 验证 NPC 配置
  python npc_generator.py list                                 # 列出所有 NPC
  python npc_generator.py preview                              # 预览 NPC 属性
  python npc_generator.py apply                                # 应用生成的 NPC 到 npcs.json
  python npc_generator.py batch <模板名> <数量> [前缀]          # 批量生成 NPC

示例：
  python npc_generator.py create-merchant baker "面包师老李"    # 创建面包师
  python npc_generator.py create-healer priest2 "修女玛丽"      # 创建治疗师
  python npc_generator.py shop baker food consumable            # 给面包师分配食物库存
  python npc_generator.py batch merchant 3 "旅商"               # 批量生成3个旅行商人
"""

import json
import os
import sys
import random
import copy
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
NPCS_FILE = CONFIG_DIR / "npcs.json"
ITEMS_FILE = CONFIG_DIR / "items.json"


# ===== NPC 角色模板 =====
# 定义不同类型 NPC 的默认配置，便于快速创建

NPC_TEMPLATES = {
    "merchant": {
        "role": "商人",
        "personality": {
            "traits": "精明能干，善于交际，对价格敏感",
            "pronoun": "我",
            "style": "热情客气，偶尔推销商品",
            "likes": "大方的顾客、稀有的货物",
            "dislikes": "讨价还价过头的人、小偷"
        },
        "default_mood": "平静",
        "default_affinity": 50,
        "personality_params": {
            "friendliness": 0.7,
            "courage": 0.4,
            "greed": 0.6,
            "humor": 0.5
        },
        "intents": {
            "chat": "闲聊、打听市场行情、询问商品来源",
            "quest": "委托玩家寻找稀有货物、护送商队",
            "trade": "买卖商品、讨价还价",
            "unknown": "无法判断意图"
        },
        "has_shop": True,
        "default_gold": 300,
        "services": {}
    },
    "blacksmith": {
        "role": "铁匠",
        "personality": {
            "traits": "豪爽直率，说话带点江湖气，对自己的手艺很自豪",
            "pronoun": "俺",
            "style": "口语化，带江湖气，偶尔粗犷",
            "likes": "冒险者、有胆识的人、好材料",
            "dislikes": "偷东西的人、胆小鬼、不懂装懂的人"
        },
        "default_mood": "平静",
        "default_affinity": 50,
        "personality_params": {
            "friendliness": 0.8,
            "courage": 0.6,
            "greed": 0.3,
            "humor": 0.7
        },
        "intents": {
            "chat": "闲聊、聊锻造技术、打听矿石消息",
            "quest": "委托玩家收集稀有矿石、打造特殊装备",
            "trade": "买卖武器装备、修理装备",
            "unknown": "无法判断意图"
        },
        "has_shop": True,
        "default_gold": 500,
        "services": {}
    },
    "healer": {
        "role": "治疗师",
        "personality": {
            "traits": "温柔善良，虔诚慈悲，说话轻声细语",
            "pronoun": "我",
            "style": "温和有礼，带有祈祷和祝福的口吻",
            "likes": "虔诚的信徒、需要帮助的人",
            "dislikes": "邪恶之物、亵渎神殿的人"
        },
        "default_mood": "平静",
        "default_affinity": 60,
        "personality_params": {
            "friendliness": 0.9,
            "courage": 0.6,
            "greed": 0.1,
            "humor": 0.4
        },
        "intents": {
            "chat": "闲聊、询问神殿的事、打听村里的传闻",
            "quest": "委托玩家寻找神圣遗物、净化被污染的区域",
            "trade": "购买治疗用品、出售草药",
            "unknown": "无法判断意图"
        },
        "has_shop": True,
        "default_gold": 150,
        "services": {
            "heal": {
                "name": "恢复生命",
                "description": "恢复全部生命值",
                "cost": 20
            },
            "restore_mp": {
                "name": "恢复魔法",
                "description": "恢复全部魔法值",
                "cost": 15
            },
            "cure": {
                "name": "解除异常",
                "description": "解除所有负面状态效果",
                "cost": 30
            }
        }
    },
    "skill_master": {
        "role": "技能导师",
        "personality": {
            "traits": "严谨认真，博学多才，对学徒要求严格",
            "pronoun": "老夫",
            "style": "正式庄重，偶尔引用古语和典故",
            "likes": "勤奋好学的学生、有天赋的年轻人",
            "dislikes": "懒惰懈怠、半途而废的人"
        },
        "default_mood": "严肃",
        "default_affinity": 45,
        "personality_params": {
            "friendliness": 0.6,
            "courage": 0.7,
            "greed": 0.3,
            "humor": 0.2
        },
        "intents": {
            "chat": "闲聊、询问战斗技巧、打听学院往事",
            "quest": "委托玩家收集稀有材料、测试新招式",
            "trade": "购买技能书、学习技能",
            "unknown": "无法判断意图"
        },
        "has_shop": True,
        "default_gold": 300,
        "services": {
            "learn_skill": {
                "name": "直接传授",
                "description": "无需技能书，直接学习职业技能（等级要求不变）",
                "cost_multiplier": 1.5
            }
        }
    },
    "quest_giver": {
        "role": "任务发布者",
        "personality": {
            "traits": "见多识广，善于观察，说话有条理",
            "pronoun": "我",
            "style": "正式但亲切，喜欢讲故事",
            "likes": "有能力的冒险者、守信的人",
            "dislikes": "言而无信的人、懒惰的人"
        },
        "default_mood": "平静",
        "default_affinity": 55,
        "personality_params": {
            "friendliness": 0.7,
            "courage": 0.5,
            "greed": 0.2,
            "humor": 0.5
        },
        "intents": {
            "chat": "闲聊、讲述往事、分享情报",
            "quest": "发布任务、追踪任务进度、发放奖励",
            "trade": "买卖情报、特殊物品",
            "unknown": "无法判断意图"
        },
        "has_shop": False,
        "default_gold": 200,
        "services": {}
    },
    "innkeeper": {
        "role": "旅店老板",
        "personality": {
            "traits": "热情好客，消息灵通，喜欢八卦",
            "pronoun": "我",
            "style": "热情随意，像对老熟人一样",
            "likes": "喝酒的客人、会讲故事的人",
            "dislikes": "闹事的醉汉、不付账的人"
        },
        "default_mood": "高兴",
        "default_affinity": 60,
        "personality_params": {
            "friendliness": 0.9,
            "courage": 0.4,
            "greed": 0.4,
            "humor": 0.8
        },
        "intents": {
            "chat": "闲聊、打听传闻、听冒险故事",
            "quest": "委托玩家送酒、找失踪的客人",
            "trade": "卖酒食、提供住宿",
            "unknown": "无法判断意图"
        },
        "has_shop": True,
        "default_gold": 250,
        "services": {
            "rest": {
                "name": "休息一晚",
                "description": "恢复全部 HP 和 MP",
                "cost": 10
            }
        }
    },
    "guard": {
        "role": "守卫",
        "personality": {
            "traits": "正直严肃，忠于职守，不善言辞",
            "pronoun": "本守卫",
            "style": "简短直接，带有命令口吻",
            "likes": "守法的公民、勇敢的冒险者",
            "dislikes": "可疑的人、违法者"
        },
        "default_mood": "严肃",
        "default_affinity": 40,
        "personality_params": {
            "friendliness": 0.4,
            "courage": 0.9,
            "greed": 0.1,
            "humor": 0.2
        },
        "intents": {
            "chat": "询问来意、通报情况、闲聊",
            "quest": "委托玩家巡逻、追捕逃犯、调查案件",
            "trade": "买卖武器防具",
            "unknown": "无法判断意图"
        },
        "has_shop": False,
        "default_gold": 100,
        "services": {}
    }
}


# ===== 预设 NPC 数据 =====
# 用于快速创建特定类型的 NPC

NPC_PRESETS = {
    "baker": {
        "template": "merchant",
        "name": "面包师老李",
        "role": "面包师",
        "location": "青石村面包房",
        "map_id": "village",
        "backstory": "老李是青石村唯一的面包师，每天凌晨就开始烤面包。他的面包香气能飘遍整个村子，村民们都说吃了他的面包一整天都有力气。",
        "greeting": "欢迎欢迎！刚出炉的面包，要不要来一块？",
        "shop_name": "老李面包房",
        "shop_types": ["food"],
        "default_gold": 150
    },
    "bartender": {
        "template": "innkeeper",
        "name": "酒馆老板老赵",
        "role": "酒馆老板",
        "location": "青石村酒馆",
        "map_id": "village",
        "backstory": "老赵经营着青石村唯一的酒馆，这里汇集了各路冒险者和村民。他消息灵通，知道村里村外的大小事情。",
        "greeting": "来来来，喝一杯！今天有什么新鲜事想聊聊？",
        "shop_name": "老赵酒馆",
        "shop_types": ["food", "consumable"],
        "default_gold": 300
    },
    "village_guard": {
        "template": "guard",
        "name": "守卫大壮",
        "role": "守卫",
        "location": "青石村入口",
        "map_id": "village",
        "backstory": "大壮是青石村的守卫队长，身材魁梧，力大无穷。他负责保护村庄的安全，对每一个进出村庄的人都保持警惕。",
        "greeting": "站住！报上姓名和来意。……哦，是冒险者啊，进去吧，但别闹事。",
        "shop_name": None,
        "shop_types": [],
        "default_gold": 100
    },
    "wandering_merchant": {
        "template": "merchant",
        "name": "旅行商人阿明",
        "role": "旅行商人",
        "location": "随机出现",
        "map_id": "forest",
        "backstory": "阿明是个四处漂泊的旅行商人，他的货物来自四面八方。虽然价格稍贵，但总能找到一些稀奇古怪的东西。",
        "greeting": "嘿！看看我这次带来了什么好东西？都是从远方运来的稀罕货！",
        "shop_name": "阿明的百宝箱",
        "shop_types": ["consumable", "material", "tool", "accessory"],
        "default_gold": 400
    }
}


# ===== 商店库存分配规则 =====
# 定义不同类型 NPC 默认销售的物品类型和数量范围

SHOP_RULES = {
    "weapon": {"quantity_range": (2, 5), "tiers": ["tier1", "tier2", "tier3"]},
    "armor": {"quantity_range": (2, 4), "tiers": ["tier1", "tier2", "tier3"]},
    "accessory": {"quantity_range": (1, 3), "tiers": ["tier1", "tier2", "tier3"]},
    "consumable": {"quantity_range": (5, 20), "tiers": None},
    "food": {"quantity_range": (5, 15), "tiers": None},
    "material": {"quantity_range": (5, 20), "tiers": None},
    "tool": {"quantity_range": (3, 8), "tiers": None},
}


class NPCGenerator:
    def __init__(self):
        self.npcs = self._load_npcs()
        self.items = self._load_items()
        self.generated = {}

    def _load_npcs(self):
        if NPCS_FILE.exists():
            with open(NPCS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _load_items(self):
        if ITEMS_FILE.exists():
            with open(ITEMS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_npcs(self):
        with open(NPCS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.npcs, f, ensure_ascii=False, indent=2)
        print(f"已保存到 {NPCS_FILE}")

    def create_npc(self, template_name, npc_id, name=None, location=None, map_id="village", **kwargs):
        """从模板创建 NPC"""
        if template_name not in NPC_TEMPLATES:
            print(f"错误：未知模板 '{template_name}'")
            print(f"可用模板：{', '.join(NPC_TEMPLATES.keys())}")
            return None

        template = NPC_TEMPLATES[template_name]

        # 检查 ID 是否已存在
        if npc_id in self.npcs or npc_id in self.generated:
            print(f"错误：NPC ID '{npc_id}' 已存在")
            return None

        npc = {
            "id": npc_id,
            "name": name or f"未命名{template['role']}",
            "role": template["role"],
            "location": location or "未知地点",
            "map_id": map_id,
            "personality": copy.deepcopy(template["personality"]),
            "backstory": kwargs.get("backstory", f"一位{template['role']}，在{location or '某个地方'}工作。"),
            "greeting": kwargs.get("greeting", f"你好，我是{template['role']}。"),
            "default_mood": template["default_mood"],
            "default_affinity": template["default_affinity"],
            "personality_params": copy.deepcopy(template["personality_params"]),
            "intents": copy.deepcopy(template["intents"]),
            "default_gold": kwargs.get("default_gold", template["default_gold"]),
        }

        # 添加服务
        if template.get("services"):
            npc["services"] = copy.deepcopy(template["services"])

        # 添加商店
        if template.get("has_shop") and kwargs.get("shop_name"):
            npc["shop"] = {
                "name": kwargs["shop_name"],
                "gold": kwargs.get("shop_gold", template["default_gold"]),
                "inventory": kwargs.get("inventory", [])
            }

        self.generated[npc_id] = npc
        print(f"已创建 NPC：{npc['name']} ({npc_id}) - {npc['role']}")
        return npc

    def create_from_preset(self, preset_name):
        """从预设创建 NPC"""
        if preset_name not in NPC_PRESETS:
            print(f"错误：未知预设 '{preset_name}'")
            print(f"可用预设：{', '.join(NPC_PRESETS.keys())}")
            return None

        preset = NPC_PRESETS[preset_name]
        template_name = preset["template"]

        npc = self.create_npc(
            template_name=template_name,
            npc_id=preset_name,
            name=preset["name"],
            location=preset["location"],
            map_id=preset["map_id"],
            backstory=preset["backstory"],
            greeting=preset["greeting"],
            shop_name=preset.get("shop_name"),
            default_gold=preset.get("default_gold", 200)
        )

        if npc and preset.get("shop_types"):
            self.assign_shop_inventory(preset_name, preset["shop_types"])

        return npc

    def assign_shop_inventory(self, npc_id, item_types=None, specific_items=None):
        """为 NPC 分配商店库存"""
        npc = self.generated.get(npc_id) or self.npcs.get(npc_id)
        if not npc:
            print(f"错误：NPC '{npc_id}' 不存在")
            return False

        if "shop" not in npc:
            npc["shop"] = {
                "name": f"{npc['name']}的商店",
                "gold": npc.get("default_gold", 200),
                "inventory": []
            }

        inventory = []

        # 按类型分配物品
        if item_types:
            for item_type in item_types:
                rule = SHOP_RULES.get(item_type, {})
                qty_range = rule.get("quantity_range", (1, 5))
                tiers = rule.get("tiers")

                # 筛选符合条件的物品
                candidates = []
                for item_id, item in self.items.items():
                    if item.get("type") == item_type:
                        if tiers is None or item.get("tier") in tiers:
                            candidates.append(item_id)

                # 随机选择并分配数量
                if candidates:
                    selected = random.sample(candidates, min(len(candidates), random.randint(2, 5)))
                    for item_id in selected:
                        qty = random.randint(*qty_range)
                        inventory.append({"item_id": item_id, "quantity": qty})

        # 添加指定物品
        if specific_items:
            for item_entry in specific_items:
                if isinstance(item_entry, str):
                    inventory.append({"item_id": item_entry, "quantity": random.randint(3, 10)})
                elif isinstance(item_entry, dict):
                    inventory.append(item_entry)

        npc["shop"]["inventory"] = inventory
        print(f"已为 {npc['name']} 分配 {len(inventory)} 种商品")
        return True

    def batch_create(self, template_name, count, name_prefix="", map_id="village"):
        """批量生成同类型 NPC"""
        if template_name not in NPC_TEMPLATES:
            print(f"错误：未知模板 '{template_name}'")
            return []

        template = NPC_TEMPLATES[template_name]
        created = []

        for i in range(count):
            npc_id = f"{template_name}_{i+1}"
            if name_prefix:
                npc_id = f"{name_prefix}_{i+1}"

            name = f"{name_prefix or template['role']}{i+1}号"
            location = f"{map_id}某处"

            npc = self.create_npc(
                template_name=template_name,
                npc_id=npc_id,
                name=name,
                location=location,
                map_id=map_id
            )
            if npc:
                created.append(npc)

        print(f"\n批量生成完成：{len(created)} 个 {template['role']} NPC")
        return created

    def validate_npc(self, npc_id, npc_data):
        """验证单个 NPC 配置"""
        issues = []
        required_fields = ["id", "name", "role", "location", "map_id", "personality", "backstory", "greeting", "default_mood", "default_affinity", "personality_params", "intents"]

        for field in required_fields:
            if field not in npc_data:
                issues.append(f"{npc_id}: 缺少必填字段 '{field}'")

        # 验证 personality_params
        params = npc_data.get("personality_params", {})
        for key in ["friendliness", "courage", "greed", "humor"]:
            if key not in params:
                issues.append(f"{npc_id}: personality_params 缺少 '{key}'")
            elif not (0 <= params[key] <= 1):
                issues.append(f"{npc_id}: personality_params.{key} 应在 0-1 范围内")

        # 验证商店
        if "shop" in npc_data:
            shop = npc_data["shop"]
            if "name" not in shop:
                issues.append(f"{npc_id}: shop 缺少 'name'")
            if "inventory" not in shop:
                issues.append(f"{npc_id}: shop 缺少 'inventory'")
            else:
                for item in shop["inventory"]:
                    if "item_id" not in item or "quantity" not in item:
                        issues.append(f"{npc_id}: shop inventory 格式错误")
                        break

        # 验证服务
        if "services" in npc_data:
            for svc_id, svc in npc_data["services"].items():
                if "name" not in svc or "description" not in svc:
                    issues.append(f"{npc_id}: service '{svc_id}' 缺少 name 或 description")

        return issues

    def validate(self):
        """验证所有 NPC 配置"""
        all_issues = []
        for npc_id, npc_data in self.npcs.items():
            issues = self.validate_npc(npc_id, npc_data)
            all_issues.extend(issues)

        if all_issues:
            print(f"发现 {len(all_issues)} 个问题：")
            for issue in all_issues:
                print(f"  - {issue}")
        else:
            print("所有 NPC 配置验证通过！")
        return len(all_issues)

    def list_npcs(self):
        """列出所有 NPC"""
        print(f"\n当前共有 {len(self.npcs)} 个 NPC：\n")
        print(f"{'ID':<20} {'名称':<12} {'角色':<10} {'位置':<15} {'地图':<10} {'商店':<6} {'服务':<6}")
        print("-" * 85)

        for npc_id, npc in sorted(self.npcs.items()):
            has_shop = "是" if "shop" in npc else "否"
            has_services = "是" if "services" in npc else "否"
            print(f"{npc_id:<20} {npc['name']:<12} {npc['role']:<10} {npc['location']:<15} {npc['map_id']:<10} {has_shop:<6} {has_services:<6}")

    def preview(self):
        """预览 NPC 属性分布"""
        print("\n=== NPC 属性分布 ===")

        # 按角色统计
        roles = {}
        for npc in self.npcs.values():
            role = npc["role"]
            roles[role] = roles.get(role, 0) + 1
        print("\n按角色分类：")
        for role, count in sorted(roles.items()):
            print(f"  {role}: {count} 人")

        # 按地图统计
        maps = {}
        for npc in self.npcs.values():
            m = npc["map_id"]
            maps[m] = maps.get(m, 0) + 1
        print("\n按地图分类：")
        for m, count in sorted(maps.items()):
            print(f"  {m}: {count} 人")

        # 性格参数平均值
        print("\n性格参数平均值：")
        params_sum = {"friendliness": 0, "courage": 0, "greed": 0, "humor": 0}
        for npc in self.npcs.values():
            for key in params_sum:
                params_sum[key] += npc["personality_params"].get(key, 0)
        count = len(self.npcs)
        for key, total in params_sum.items():
            print(f"  {key}: {total/count:.2f}")

        # 商店统计
        shop_count = sum(1 for npc in self.npcs.values() if "shop" in npc)
        service_count = sum(1 for npc in self.npcs.values() if "services" in npc)
        print(f"\n有商店的 NPC: {shop_count}/{len(self.npcs)}")
        print(f"有服务的 NPC: {service_count}/{len(self.npcs)}")

    def apply(self):
        """将生成的 NPC 应用到 npcs.json"""
        if not self.generated:
            print("没有新生成的 NPC 需要应用")
            return

        # 合并到现有 NPC
        self.npcs.update(self.generated)
        self._save_npcs()
        print(f"已应用 {len(self.generated)} 个新 NPC")
        self.generated.clear()

    def generate_schedule(self, npc_id):
        schedule_templates = {
            "merchant": [
                {"time": "06:00", "action": "开店", "location": "商店"},
                {"time": "12:00", "action": "午休", "location": "商店后屋"},
                {"time": "13:00", "action": "营业", "location": "商店"},
                {"time": "20:00", "action": "关门", "location": "商店"},
                {"time": "21:00", "action": "休息", "location": "家中"},
            ],
            "blacksmith": [
                {"time": "05:00", "action": "生火开炉", "location": "铁匠铺"},
                {"time": "08:00", "action": "锻造", "location": "铁匠铺"},
                {"time": "12:00", "action": "午休", "location": "铁匠铺后屋"},
                {"time": "13:00", "action": "营业", "location": "铁匠铺"},
                {"time": "19:00", "action": "收工", "location": "铁匠铺"},
                {"time": "20:00", "action": "去酒馆", "location": "酒馆"},
            ],
            "healer": [
                {"time": "06:00", "action": "晨祷", "location": "神殿"},
                {"time": "08:00", "action": "治疗服务", "location": "神殿"},
                {"time": "12:00", "action": "午休", "location": "神殿后院"},
                {"time": "13:00", "action": "治疗服务", "location": "神殿"},
                {"time": "18:00", "action": "晚祷", "location": "神殿"},
                {"time": "20:00", "action": "休息", "location": "神殿后院"},
            ],
            "skill_master": [
                {"time": "06:00", "action": "晨练", "location": "学院"},
                {"time": "08:00", "action": "授课", "location": "学院"},
                {"time": "12:00", "action": "午休", "location": "学院"},
                {"time": "13:00", "action": "训练", "location": "学院"},
                {"time": "18:00", "action": "研究", "location": "学院"},
                {"time": "21:00", "action": "休息", "location": "学院"},
            ],
            "innkeeper": [
                {"time": "08:00", "action": "开店", "location": "酒馆"},
                {"time": "12:00", "action": "忙碌", "location": "酒馆"},
                {"time": "18:00", "action": "高峰期", "location": "酒馆"},
                {"time": "23:00", "action": "打烊", "location": "酒馆"},
            ],
            "guard": [
                {"time": "06:00", "action": "换班巡逻", "location": "村口"},
                {"time": "10:00", "action": "站岗", "location": "村口"},
                {"time": "14:00", "action": "巡逻", "location": "村庄"},
                {"time": "18:00", "action": "换班", "location": "村口"},
                {"time": "22:00", "action": "夜间巡逻", "location": "村庄"},
            ],
            "quest_giver": [
                {"time": "08:00", "action": "发布任务", "location": "广场"},
                {"time": "12:00", "action": "午休", "location": "家中"},
                {"time": "14:00", "action": "收集情报", "location": "广场"},
                {"time": "18:00", "action": "整理任务", "location": "广场"},
                {"time": "20:00", "action": "休息", "location": "家中"},
            ],
        }
        npc = self.generated.get(npc_id) or self.npcs.get(npc_id)
        if not npc:
            print(f"错误：NPC '{npc_id}' 不存在")
            return None
        role = npc.get("role", "")
        template_name = None
        for tname, tmpl in NPC_TEMPLATES.items():
            if tmpl["role"] == role:
                template_name = tname
                break
        schedule = schedule_templates.get(template_name, schedule_templates.get("quest_giver"))
        npc["schedule"] = schedule
        print(f"已为 {npc['name']} 生成日程：{len(schedule)} 个时间段")
        return schedule

    def generate_all_schedules(self):
        count = 0
        for npc_id in list(self.npcs.keys()):
            if self.generate_schedule(npc_id):
                count += 1
        self._save_npcs()
        print(f"已为 {count} 个 NPC 生成日程")
        return count

    def export_npc(self, npc_id, output_dir=None):
        npc = self.npcs.get(npc_id)
        if not npc:
            print(f"错误：NPC '{npc_id}' 不存在")
            return False
        out_dir = Path(output_dir) if output_dir else ROOT_DIR / "tools" / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        filepath = out_dir / f"{npc_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(npc, f, ensure_ascii=False, indent=2)
        print(f"已导出 NPC '{npc_id}' 到 {filepath}")
        return True

    def import_npc(self, filepath):
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"错误：文件 '{filepath}' 不存在")
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            npc = json.load(f)
        npc_id = npc.get("id")
        if not npc_id:
            print("错误：导入的 NPC 缺少 id 字段")
            return False
        self.npcs[npc_id] = npc
        self._save_npcs()
        print(f"已导入 NPC '{npc_id}' ({npc.get('name', '未知')})")
        return True

    def export_all(self, output_dir=None):
        out_dir = Path(output_dir) if output_dir else ROOT_DIR / "tools" / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for npc_id, npc in self.npcs.items():
            filepath = out_dir / f"{npc_id}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(npc, f, ensure_ascii=False, indent=2)
            count += 1
        print(f"已导出 {count} 个 NPC 到 {out_dir}")
        return count

    def show_templates(self):
        """显示所有可用模板"""
        print("\n=== 可用 NPC 模板 ===")
        for name, template in NPC_TEMPLATES.items():
            print(f"\n{name}: {template['role']}")
            print(f"  性格: {template['personality']['traits']}")
            print(f"  默认好感度: {template['default_affinity']}")
            print(f"  有商店: {'是' if template['has_shop'] else '否'}")
            if template.get("services"):
                print(f"  服务: {', '.join(template['services'].keys())}")

    def show_presets(self):
        """显示所有可用预设"""
        print("\n=== 可用 NPC 预设 ===")
        for name, preset in NPC_PRESETS.items():
            print(f"\n{name}: {preset['name']} ({preset['role']})")
            print(f"  位置: {preset['location']} ({preset['map_id']})")
            print(f"  模板: {preset['template']}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    gen = NPCGenerator()

    if cmd == "create":
        if len(sys.argv) < 4:
            print("用法：python npc_generator.py create <模板名> <npc_id> [名称] [位置] [地图]")
            return
        template_name = sys.argv[2]
        npc_id = sys.argv[3]
        name = sys.argv[4] if len(sys.argv) > 4 else None
        location = sys.argv[5] if len(sys.argv) > 5 else None
        map_id = sys.argv[6] if len(sys.argv) > 6 else "village"
        gen.create_npc(template_name, npc_id, name, location, map_id)

    elif cmd == "create-merchant":
        if len(sys.argv) < 4:
            print("用法：python npc_generator.py create-merchant <npc_id> <名称> [位置] [地图]")
            return
        npc_id = sys.argv[2]
        name = sys.argv[3]
        location = sys.argv[4] if len(sys.argv) > 4 else "村庄商店"
        map_id = sys.argv[5] if len(sys.argv) > 5 else "village"
        gen.create_npc("merchant", npc_id, name, location, map_id,
                       shop_name=f"{name}的商店", shop_gold=300)

    elif cmd == "create-healer":
        if len(sys.argv) < 4:
            print("用法：python npc_generator.py create-healer <npc_id> <名称> [位置] [地图]")
            return
        npc_id = sys.argv[2]
        name = sys.argv[3]
        location = sys.argv[4] if len(sys.argv) > 4 else "神殿"
        map_id = sys.argv[5] if len(sys.argv) > 5 else "village"
        gen.create_npc("healer", npc_id, name, location, map_id,
                       shop_name=f"{name}的治疗所", shop_gold=200)

    elif cmd == "create-master":
        if len(sys.argv) < 4:
            print("用法：python npc_generator.py create-master <npc_id> <名称> [位置] [地图]")
            return
        npc_id = sys.argv[2]
        name = sys.argv[3]
        location = sys.argv[4] if len(sys.argv) > 4 else "训练场"
        map_id = sys.argv[5] if len(sys.argv) > 5 else "village"
        gen.create_npc("skill_master", npc_id, name, location, map_id,
                       shop_name=f"{name}的书斋", shop_gold=500)

    elif cmd == "create-quest":
        if len(sys.argv) < 4:
            print("用法：python npc_generator.py create-quest <npc_id> <名称> [位置] [地图]")
            return
        npc_id = sys.argv[2]
        name = sys.argv[3]
        location = sys.argv[4] if len(sys.argv) > 4 else "村庄广场"
        map_id = sys.argv[5] if len(sys.argv) > 5 else "village"
        gen.create_npc("quest_giver", npc_id, name, location, map_id)

    elif cmd == "preset":
        if len(sys.argv) < 3:
            print("用法：python npc_generator.py preset <预设名>")
            print(f"可用预设：{', '.join(NPC_PRESETS.keys())}")
            return
        preset_name = sys.argv[2]
        gen.create_from_preset(preset_name)

    elif cmd == "shop":
        if len(sys.argv) < 3:
            print("用法：python npc_generator.py shop <npc_id> [item_type...]")
            return
        npc_id = sys.argv[2]
        item_types = sys.argv[3:] if len(sys.argv) > 3 else ["consumable"]
        gen.assign_shop_inventory(npc_id, item_types)

    elif cmd == "batch":
        if len(sys.argv) < 4:
            print("用法：python npc_generator.py batch <模板名> <数量> [名称前缀] [地图]")
            return
        template_name = sys.argv[2]
        count = int(sys.argv[3])
        prefix = sys.argv[4] if len(sys.argv) > 4 else ""
        map_id = sys.argv[5] if len(sys.argv) > 5 else "village"
        gen.batch_create(template_name, count, prefix, map_id)

    elif cmd == "validate":
        gen.validate()

    elif cmd == "list":
        gen.list_npcs()

    elif cmd == "preview":
        gen.preview()

    elif cmd == "templates":
        gen.show_templates()

    elif cmd == "presets":
        gen.show_presets()

    elif cmd == "apply":
        gen.apply()

    elif cmd == "schedule":
        if len(sys.argv) < 3:
            print("用法：python npc_generator.py schedule <npc_id|all>")
            return
        target = sys.argv[2]
        if target == "all":
            gen.generate_all_schedules()
        else:
            gen.generate_schedule(target)
            gen._save_npcs()

    elif cmd == "export":
        if len(sys.argv) < 3:
            print("用法：python npc_generator.py export <npc_id|all> [output_dir]")
            return
        target = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else None
        if target == "all":
            gen.export_all(output_dir)
        else:
            gen.export_npc(target, output_dir)

    elif cmd == "import":
        if len(sys.argv) < 3:
            print("用法：python npc_generator.py import <filepath>")
            return
        gen.import_npc(sys.argv[2])

    else:
        print(f"未知命令：{cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
