#!/usr/bin/env python3
"""
物品生成器 - 用于创建和管理游戏物品及NPC商店库存

功能：
1. 生成装备物品（武器、防具、饰品），按等级段自动平衡属性和价格
2. 生成消耗品、材料、食物等非装备物品
3. 为NPC商店自动分配对应等级段的物品
4. 验证物品数据完整性
5. 列出所有物品
6. 预览物品属性分布

使用方法：
  python item_generator.py generate equip tier1           # 生成1级段装备
  python item_generator.py generate equip tier2           # 生成5级段装备
  python item_generator.py generate equip tier3           # 生成10级段装备
  python item_generator.py generate equip all             # 生成所有等级段装备
  python item_generator.py generate consumable            # 生成消耗品
  python item_generator.py generate material              # 生成材料
  python item_generator.py generate food                  # 生成食物
  python item_generator.py shop blacksmith                # 为铁匠分配商店库存
  python item_generator.py shop merchant                  # 为商人分配商店库存
  python item_generator.py shop herbalist                 # 为采药人分配商店库存
  python item_generator.py shop all                       # 为所有NPC分配库存
  python item_generator.py validate                       # 验证物品数据
  python item_generator.py list                           # 列出所有物品
  python item_generator.py preview                        # 预览物品属性分布
  python item_generator.py apply                          # 应用生成的物品到items.json
"""

import json
import os
import sys
import random
import copy
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
ITEMS_FILE = CONFIG_DIR / "items.json"
NPCS_FILE = CONFIG_DIR / "npcs.json"


# ===== 等级段定义 =====

TIERS = {
    "tier1": {
        "name": "初级",
        "level_range": (1, 4),
        "price_multiplier": 1.0,
    },
    "tier2": {
        "name": "中级",
        "level_range": (5, 9),
        "price_multiplier": 2.5,
    },
    "tier3": {
        "name": "高级",
        "level_range": (10, 15),
        "price_multiplier": 6.0,
    },
}


# ===== 装备模板 =====
# 每个模板指定 prefix（材质前缀），避免不合理的组合如"皮剑"

WEAPON_TEMPLATES = [
    {"name": "木剑", "id": "wood_sword", "tier": "tier1", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.8, "defense": 0.0, "speed": 0.2, "max_hp": 0.0},
     "desc": "用硬木削成的剑，虽然简陋但聊胜于无。"},
    {"name": "石剑", "id": "stone_sword", "tier": "tier1", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.9, "defense": 0.0, "speed": 0.0, "max_hp": 0.0},
     "desc": "用磨利的石头制成的剑，比木剑锋利。"},
    {"name": "铜剑", "id": "copper_sword", "tier": "tier1", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 1.0, "defense": 0.0, "speed": 0.0, "max_hp": 0.0},
     "desc": "铜铸的剑，适合初出茅庐的冒险者。"},
    {"name": "铁剑", "id": "iron_sword", "tier": "tier1", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 1.0, "defense": 0.0, "speed": 0.0, "max_hp": 0.0},
     "desc": "一把坚固的铁剑，适合初级冒险者。"},
    {"name": "铁匕首", "id": "iron_dagger", "tier": "tier1", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.6, "defense": 0.0, "speed": 0.5, "max_hp": 0.0},
     "desc": "轻便的匕首，适合快速攻击。"},
    {"name": "猎人弓", "id": "hunter_bow", "tier": "tier1", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.5, "defense": 0.0, "speed": 0.6, "max_hp": 0.0},
     "desc": "灵活的猎弓，攻速快射程远。"},
    {"name": "法师杖", "id": "mage_staff", "tier": "tier1", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.7, "defense": 0.0, "speed": 0.3, "max_hp": 0.0},
     "desc": "蕴含魔力的法杖，适合施法者。"},
    {"name": "铁斧", "id": "iron_axe", "tier": "tier1", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 1.1, "defense": 0.0, "speed": -0.2, "max_hp": 0.0},
     "desc": "沉重的铁斧，攻击力强但影响速度。"},

    {"name": "精钢剑", "id": "steel_sword", "tier": "tier2", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 1.0, "defense": 0.0, "speed": 0.0, "max_hp": 0.0},
     "desc": "用精钢打造的利剑，锋利无比。"},
    {"name": "银匕首", "id": "silver_dagger", "tier": "tier2", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.6, "defense": 0.0, "speed": 0.5, "max_hp": 0.0},
     "desc": "银制的匕首，对暗系生物有额外伤害。"},
    {"name": "银弓", "id": "silver_bow", "tier": "tier2", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.5, "defense": 0.0, "speed": 0.6, "max_hp": 0.0},
     "desc": "银制的猎弓，精准而有力。"},
    {"name": "合金法杖", "id": "alloy_staff", "tier": "tier2", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.7, "defense": 0.0, "speed": 0.3, "max_hp": 0.0},
     "desc": "合金打造的法杖，魔力传导更顺畅。"},
    {"name": "精钢斧", "id": "steel_axe", "tier": "tier2", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 1.1, "defense": 0.0, "speed": -0.2, "max_hp": 0.0},
     "desc": "精钢锻造的战斧，劈砍力惊人。"},
    {"name": "青铜锤", "id": "bronze_hammer", "tier": "tier2", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.9, "defense": 0.2, "speed": -0.3, "max_hp": 0.0},
     "desc": "青铜铸成的战锤，攻防兼备。"},

    {"name": "秘银剑", "id": "mithril_sword", "tier": "tier3", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 1.0, "defense": 0.0, "speed": 0.0, "max_hp": 0.0},
     "desc": "秘银铸造的神剑，锋芒毕露。"},
    {"name": "暗金匕首", "id": "dark_gold_dagger", "tier": "tier3", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.6, "defense": 0.0, "speed": 0.5, "max_hp": 0.0},
     "desc": "暗金打造的匕首，快如闪电。"},
    {"name": "玄铁弓", "id": "dark_iron_bow", "tier": "tier3", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.5, "defense": 0.0, "speed": 0.6, "max_hp": 0.0},
     "desc": "玄铁制成的强弓，箭无虚发。"},
    {"name": "魔晶法杖", "id": "crystal_staff", "tier": "tier3", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.7, "defense": 0.0, "speed": 0.3, "max_hp": 0.0},
     "desc": "镶嵌魔晶的法杖，魔力澎湃。"},
    {"name": "玄铁斧", "id": "dark_iron_axe", "tier": "tier3", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 1.1, "defense": 0.0, "speed": -0.2, "max_hp": 0.0},
     "desc": "玄铁锻造的巨斧，一击必杀。"},
    {"name": "暗金锤", "id": "dark_gold_hammer", "tier": "tier3", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 0.9, "defense": 0.2, "speed": -0.3, "max_hp": 0.0},
     "desc": "暗金铸成的神锤，震天动地。"},
]

SHIELD_TEMPLATES = [
    {"name": "木盾", "id": "wood_shield", "tier": "tier1", "type": "armor", "equip_slot": "shield",
     "stat_weights": {"attack": 0.0, "defense": 0.7, "speed": -0.2, "max_hp": 0.1},
     "desc": "简陋的木盾，总比没有强。"},
    {"name": "铁盾", "id": "iron_shield", "tier": "tier1", "type": "armor", "equip_slot": "shield",
     "stat_weights": {"attack": 0.0, "defense": 1.0, "speed": -0.3, "max_hp": 0.0},
     "desc": "厚实的铁盾，能挡住不少伤害。"},

    {"name": "精钢盾", "id": "steel_shield", "tier": "tier2", "type": "armor", "equip_slot": "shield",
     "stat_weights": {"attack": 0.0, "defense": 1.0, "speed": -0.3, "max_hp": 0.0},
     "desc": "精钢锻造的盾牌，防御力极强。"},
    {"name": "银圆盾", "id": "silver_round_shield", "tier": "tier2", "type": "armor", "equip_slot": "shield",
     "stat_weights": {"attack": 0.0, "defense": 0.8, "speed": -0.15, "max_hp": 0.1},
     "desc": "银制的圆盾，轻便而坚固。"},

    {"name": "秘银盾", "id": "mithril_shield", "tier": "tier3", "type": "armor", "equip_slot": "shield",
     "stat_weights": {"attack": 0.0, "defense": 1.0, "speed": -0.3, "max_hp": 0.0},
     "desc": "秘银铸造的盾牌，坚不可摧。"},
    {"name": "暗金圆盾", "id": "dark_gold_round_shield", "tier": "tier3", "type": "armor", "equip_slot": "shield",
     "stat_weights": {"attack": 0.0, "defense": 0.8, "speed": -0.15, "max_hp": 0.1},
     "desc": "暗金打造的圆盾，轻巧而强大。"},
]

HEAD_TEMPLATES = [
    {"name": "皮帽", "id": "leather_hat", "tier": "tier1", "type": "armor", "equip_slot": "head",
     "stat_weights": {"attack": 0.0, "defense": 0.2, "speed": 0.15, "max_hp": 0.15},
     "desc": "轻便的皮帽，适合游侠和盗贼。"},
    {"name": "铁盔", "id": "iron_helmet", "tier": "tier1", "type": "armor", "equip_slot": "head",
     "stat_weights": {"attack": 0.0, "defense": 0.5, "speed": -0.15, "max_hp": 0.35},
     "desc": "沉重的铁盔，保护头部安全。"},

    {"name": "硬皮帽", "id": "hard_leather_hat", "tier": "tier2", "type": "armor", "equip_slot": "head",
     "stat_weights": {"attack": 0.0, "defense": 0.2, "speed": 0.15, "max_hp": 0.15},
     "desc": "硬化处理的皮帽，防护更佳。"},
    {"name": "银盔", "id": "silver_helmet", "tier": "tier2", "type": "armor", "equip_slot": "head",
     "stat_weights": {"attack": 0.0, "defense": 0.5, "speed": -0.15, "max_hp": 0.35},
     "desc": "银制的头盔，既美观又实用。"},
    {"name": "青铜冠", "id": "bronze_crown", "tier": "tier2", "type": "armor", "equip_slot": "head",
     "stat_weights": {"attack": 0.15, "defense": 0.15, "speed": 0.1, "max_hp": 0.1},
     "desc": "华丽的青铜冠，彰显身份。"},

    {"name": "龙皮帽", "id": "dragon_hat", "tier": "tier3", "type": "armor", "equip_slot": "head",
     "stat_weights": {"attack": 0.0, "defense": 0.2, "speed": 0.15, "max_hp": 0.15},
     "desc": "龙皮缝制的帽子，轻如鸿毛坚如磐石。"},
    {"name": "秘银盔", "id": "mithril_helmet", "tier": "tier3", "type": "armor", "equip_slot": "head",
     "stat_weights": {"attack": 0.0, "defense": 0.5, "speed": -0.15, "max_hp": 0.35},
     "desc": "秘银铸成的头盔，轻便而坚固。"},
    {"name": "魔晶冠", "id": "crystal_crown", "tier": "tier3", "type": "armor", "equip_slot": "head",
     "stat_weights": {"attack": 0.15, "defense": 0.15, "speed": 0.1, "max_hp": 0.1},
     "desc": "镶嵌魔晶的王冠，散发着神秘光芒。"},
]

BODY_TEMPLATES = [
    {"name": "布袍", "id": "cloth_robe", "tier": "tier1", "type": "armor", "equip_slot": "body",
     "stat_weights": {"attack": 0.0, "defense": 0.15, "speed": 0.15, "max_hp": 0.2},
     "desc": "轻柔的布袍，适合法师穿着。"},
    {"name": "皮甲", "id": "leather_armor", "tier": "tier1", "type": "armor", "equip_slot": "body",
     "stat_weights": {"attack": 0.0, "defense": 0.4, "speed": 0.0, "max_hp": 0.3},
     "desc": "轻便的皮甲，提供基础防护。"},
    {"name": "铁甲", "id": "iron_armor", "tier": "tier1", "type": "armor", "equip_slot": "body",
     "stat_weights": {"attack": 0.0, "defense": 0.7, "speed": -0.25, "max_hp": 0.55},
     "desc": "沉重的铁甲，防御力极强但影响行动。"},

    {"name": "硬皮衣", "id": "hard_leather_garb", "tier": "tier2", "type": "armor", "equip_slot": "body",
     "stat_weights": {"attack": 0.0, "defense": 0.4, "speed": 0.0, "max_hp": 0.3},
     "desc": "硬化处理的皮衣，防护力大增。"},
    {"name": "银袍", "id": "silver_robe", "tier": "tier2", "type": "armor", "equip_slot": "body",
     "stat_weights": {"attack": 0.0, "defense": 0.15, "speed": 0.15, "max_hp": 0.2},
     "desc": "银线织成的法袍，魔力流转其中。"},
    {"name": "精钢甲", "id": "steel_armor", "tier": "tier2", "type": "armor", "equip_slot": "body",
     "stat_weights": {"attack": 0.0, "defense": 0.7, "speed": -0.25, "max_hp": 0.55},
     "desc": "精钢锻造的铠甲，坚如磐石。"},

    {"name": "龙皮衣", "id": "dragon_garb", "tier": "tier3", "type": "armor", "equip_slot": "body",
     "stat_weights": {"attack": 0.0, "defense": 0.4, "speed": 0.0, "max_hp": 0.3},
     "desc": "龙皮缝制的战衣，轻巧而坚韧。"},
    {"name": "魔晶袍", "id": "crystal_robe", "tier": "tier3", "type": "armor", "equip_slot": "body",
     "stat_weights": {"attack": 0.0, "defense": 0.15, "speed": 0.15, "max_hp": 0.2},
     "desc": "魔晶织成的法袍，魔力无穷。"},
    {"name": "玄铁甲", "id": "dark_iron_armor", "tier": "tier3", "type": "armor", "equip_slot": "body",
     "stat_weights": {"attack": 0.0, "defense": 0.7, "speed": -0.25, "max_hp": 0.55},
     "desc": "玄铁锻造的铠甲，刀枪不入。"},
]

ACCESSORY_TEMPLATES = [
    {"name": "力量戒指", "id": "ring_of_power", "tier": "tier1", "type": "accessory", "equip_slot": "accessory",
     "stat_weights": {"attack": 0.3, "defense": 0.2, "speed": 0.2, "max_hp": 0.1},
     "desc": "蕴含力量的神秘戒指，全面提升能力。"},
    {"name": "生命项链", "id": "necklace_of_life", "tier": "tier1", "type": "accessory", "equip_slot": "accessory",
     "stat_weights": {"attack": 0.1, "defense": 0.3, "speed": 0.1, "max_hp": 0.4},
     "desc": "温暖的项链，佩戴后生命力旺盛。"},
    {"name": "疾风护符", "id": "charm_of_wind", "tier": "tier1", "type": "accessory", "equip_slot": "accessory",
     "stat_weights": {"attack": 0.2, "defense": 0.1, "speed": 0.3, "max_hp": 0.2},
     "desc": "轻灵的护符，佩戴后身轻如燕。"},

    {"name": "银戒指", "id": "silver_ring", "tier": "tier2", "type": "accessory", "equip_slot": "accessory",
     "stat_weights": {"attack": 0.3, "defense": 0.2, "speed": 0.2, "max_hp": 0.1},
     "desc": "银制的戒指，散发着柔和的光芒。"},
    {"name": "守护项链", "id": "necklace_of_guard", "tier": "tier2", "type": "accessory", "equip_slot": "accessory",
     "stat_weights": {"attack": 0.1, "defense": 0.3, "speed": 0.1, "max_hp": 0.4},
     "desc": "守护之力的项链，危难时庇护佩戴者。"},
    {"name": "迅捷护符", "id": "charm_of_swift", "tier": "tier2", "type": "accessory", "equip_slot": "accessory",
     "stat_weights": {"attack": 0.2, "defense": 0.1, "speed": 0.3, "max_hp": 0.2},
     "desc": "迅捷之力的护符，佩戴后行动如风。"},

    {"name": "暗金戒指", "id": "dark_gold_ring", "tier": "tier3", "type": "accessory", "equip_slot": "accessory",
     "stat_weights": {"attack": 0.3, "defense": 0.2, "speed": 0.2, "max_hp": 0.1},
     "desc": "暗金打造的戒指，蕴含远古之力。"},
    {"name": "永恒项链", "id": "necklace_of_eternity", "tier": "tier3", "type": "accessory", "equip_slot": "accessory",
     "stat_weights": {"attack": 0.1, "defense": 0.3, "speed": 0.1, "max_hp": 0.4},
     "desc": "永恒之力的项链，据说能延年益寿。"},
    {"name": "幻影护符", "id": "charm_of_phantom", "tier": "tier3", "type": "accessory", "equip_slot": "accessory",
     "stat_weights": {"attack": 0.2, "defense": 0.1, "speed": 0.3, "max_hp": 0.2},
     "desc": "幻影之力的护符，佩戴后如鬼魅般飘忽。"},
]

ALL_EQUIP_TEMPLATES = WEAPON_TEMPLATES + SHIELD_TEMPLATES + HEAD_TEMPLATES + BODY_TEMPLATES + ACCESSORY_TEMPLATES


# ===== 风味文本 =====

FLAVORS = {
    "tier1": [
        "适合初出茅庐的冒险者", "结实耐用", "虽然朴素但很可靠",
        "村子里最常见的装备", "新手必备", "物美价廉",
    ],
    "tier2": [
        "适合有经验的冒险者", "做工精良", "远胜普通装备",
        "冒险者间颇受好评", "性能均衡", "值得信赖",
    ],
    "tier3": [
        "只有顶尖冒险者才配得上", "传说级的工艺", "散发着神秘光芒",
        "据说是远古遗物", "蕴含强大力量", "举世罕见",
    ],
}

CONSUMABLE_FLAVORS = [
    "冒险者的好伙伴", "关键时刻能救命", "出门在外必备",
    "效果显著", "品质上乘", "口碑极好",
]

MATERIAL_FLAVORS = [
    "品质不错", "可以用来制作各种东西", "在商人那里能卖个好价钱",
    "冒险中常见的材料", "工匠们很需要", "采集起来不容易",
]

FOOD_FLAVORS = [
    "味道不错", "能恢复体力", "旅途中的好伴侣",
    "新鲜美味", "补充能量", "填饱肚子没问题",
]


# ===== 消耗品/材料/食物模板 =====

CONSUMABLE_TEMPLATES = [
    {"name": "生命药水", "id": "health_potion", "desc": "恢复少量生命值。", "buy": 30, "sell": 15},
    {"name": "强效生命药水", "id": "greater_health_potion", "desc": "恢复大量生命值。", "buy": 80, "sell": 40},
    {"name": "解毒药", "id": "antidote", "desc": "解除中毒状态。", "buy": 25, "sell": 12},
    {"name": "绷带", "id": "bandage", "desc": "简易的止血绷带。", "buy": 8, "sell": 4},
    {"name": "魔力药水", "id": "mana_potion", "desc": "恢复少量魔力。", "buy": 35, "sell": 17},
    {"name": "净化药水", "id": "purify_potion", "desc": "解除诅咒状态。", "buy": 50, "sell": 25},
    {"name": "力量药剂", "id": "strength_elixir", "desc": "暂时提升攻击力。", "buy": 60, "sell": 30},
    {"name": "速度药剂", "id": "speed_elixir", "desc": "暂时提升速度。", "buy": 60, "sell": 30},
]

MATERIAL_TEMPLATES = [
    {"name": "狼皮", "id": "wolf_pelt", "desc": "从野狼身上剥下的皮毛。", "buy": 0, "sell": 20},
    {"name": "铁矿石", "id": "iron_ore", "desc": "可以用来锻造武器的矿石。", "buy": 0, "sell": 15},
    {"name": "棉布", "id": "cloth", "desc": "柔软的棉布，可以做衣服或绷带。", "buy": 15, "sell": 7},
    {"name": "草药", "id": "herb", "desc": "山里采的草药，可以入药。", "buy": 0, "sell": 10},
    {"name": "蘑菇", "id": "mushroom", "desc": "森林里采的蘑菇，味道鲜美。", "buy": 0, "sell": 8},
    {"name": "兽骨", "id": "beast_bone", "desc": "坚硬的兽骨，可以制作武器。", "buy": 0, "sell": 25},
    {"name": "魔法水晶", "id": "magic_crystal", "desc": "蕴含魔力的水晶碎片。", "buy": 0, "sell": 40},
    {"name": "龙鳞", "id": "dragon_scale", "desc": "坚硬的龙鳞，极其珍贵。", "buy": 0, "sell": 80},
    {"name": "丝绸", "id": "silk", "desc": "光滑细腻的丝绸，价值不菲。", "buy": 25, "sell": 12},
    {"name": "精钢锭", "id": "steel_ingot", "desc": "精炼的钢锭，锻造高级装备的原料。", "buy": 0, "sell": 35},
]

FOOD_TEMPLATES = [
    {"name": "面包", "id": "bread", "desc": "刚出炉的面包，能填饱肚子。", "buy": 5, "sell": 2},
    {"name": "肉干", "id": "dried_meat", "desc": "风干的肉条，适合长途旅行携带。", "buy": 12, "sell": 6},
    {"name": "米酒", "id": "wine", "desc": "村里自酿的米酒，味道醇厚。", "buy": 20, "sell": 10},
    {"name": "烤鱼", "id": "grilled_fish", "desc": "香喷喷的烤鱼，回味无穷。", "buy": 15, "sell": 7},
    {"name": "果酱", "id": "jam", "desc": "甜美的果酱，涂面包最好。", "buy": 8, "sell": 4},
    {"name": "蜂蜜", "id": "honey", "desc": "森林里采的蜂蜜，甘甜可口。", "buy": 18, "sell": 9},
    {"name": "干粮", "id": "rations", "desc": "行军干粮，耐储存。", "buy": 10, "sell": 5},
    {"name": "炖汤", "id": "stew", "desc": "热腾腾的炖汤，暖身又暖心。", "buy": 22, "sell": 11},
]

TOOL_TEMPLATES = [
    {"name": "火把", "id": "torch", "desc": "照亮黑暗的洞穴。", "buy": 10, "sell": 5},
    {"name": "绳索", "id": "rope", "desc": "结实的麻绳，用途广泛。", "buy": 15, "sell": 7},
    {"name": "蜡烛", "id": "candle", "desc": "照明用的蜡烛。", "buy": 5, "sell": 2},
    {"name": "开锁器", "id": "lockpick", "desc": "精巧的开锁工具。", "buy": 25, "sell": 12},
    {"name": "望远镜", "id": "spyglass", "desc": "可以看清远处的东西。", "buy": 40, "sell": 20},
]


# ===== NPC商店模板 =====

SHOP_TEMPLATES = {
    "blacksmith": {
        "name": "老王铁匠铺",
        "equip_tiers": ["tier1", "tier2"],
        "equip_types": ["weapon", "shield", "head", "body"],
        "consumable_ids": ["health_potion", "antidote", "bandage"],
        "tool_ids": ["torch", "rope"],
        "material_ids": ["iron_ore"],
        "food_ids": [],
        "equip_quantity": {"tier1": (2, 5), "tier2": (1, 2)},
        "consumable_quantity": (5, 15),
        "tool_quantity": (10, 20),
        "material_quantity": (5, 10),
        "food_quantity": (0, 0),
        "gold": 500,
    },
    "merchant": {
        "name": "刘婶杂货铺",
        "equip_tiers": ["tier1"],
        "equip_types": ["body"],
        "consumable_ids": ["health_potion", "bandage"],
        "tool_ids": ["candle", "rope", "torch"],
        "material_ids": ["cloth"],
        "food_ids": ["bread", "dried_meat", "wine", "jam", "honey"],
        "equip_quantity": {"tier1": (1, 3)},
        "consumable_quantity": (10, 25),
        "tool_quantity": (10, 30),
        "material_quantity": (10, 20),
        "food_quantity": (10, 30),
        "gold": 300,
    },
    "herbalist": {
        "name": "老林草药铺",
        "equip_tiers": ["tier1"],
        "equip_types": ["head", "body", "accessory"],
        "consumable_ids": ["health_potion", "antidote", "bandage", "greater_health_potion", "purify_potion", "mana_potion"],
        "tool_ids": ["candle", "torch"],
        "material_ids": ["herb", "mushroom", "magic_crystal"],
        "food_ids": ["mushroom", "honey"],
        "equip_quantity": {"tier1": (1, 2)},
        "consumable_quantity": (8, 20),
        "tool_quantity": (5, 15),
        "material_quantity": (10, 25),
        "food_quantity": (5, 15),
        "gold": 150,
    },
}


class ItemGenerator:
    def __init__(self):
        self.items = {}
        self._load_items()

    def _load_items(self):
        if ITEMS_FILE.exists():
            with open(ITEMS_FILE, "r", encoding="utf-8") as f:
                self.items = json.load(f)

    def _save_items(self):
        with open(ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)

    def _load_npcs(self):
        if NPCS_FILE.exists():
            with open(NPCS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_npcs(self, npcs):
        with open(NPCS_FILE, "w", encoding="utf-8") as f:
            json.dump(npcs, f, ensure_ascii=False, indent=2)

    def _calc_stats(self, template, tier_key):
        tier = TIERS[tier_key]
        level_mid = sum(tier["level_range"]) / 2
        total_budget = level_mid * 1.5

        weights = template["stat_weights"]
        stats = {}
        for key in ["attack", "defense", "speed", "max_hp"]:
            raw = total_budget * weights.get(key, 0)
            if key == "max_hp":
                raw *= 3
            val = round(raw)
            if val > 0 and key not in ("max_hp",):
                val = max(val, 1)
            stats[key] = val

        return stats

    def _calc_price(self, stats, tier_key, equip_slot):
        tier = TIERS[tier_key]
        total_stat_value = sum(
            max(0, stats.get(k, 0)) * w
            for k, w in [("attack", 10), ("defense", 8), ("speed", 6), ("max_hp", 2)]
        )
        neg_value = sum(
            abs(min(0, stats.get(k, 0))) * w
            for k, w in [("speed", 3)]
        )
        base_price = total_stat_value - neg_value
        buy_price = max(10, round(base_price * tier["price_multiplier"]))
        sell_price = buy_price // 2
        return buy_price, sell_price

    def generate_equip(self, tier_key):
        if tier_key == "all":
            generated = {}
            for tk in TIERS:
                generated.update(self.generate_equip(tk))
            return generated

        if tier_key not in TIERS:
            print(f"错误：未知等级段 '{tier_key}'，可选：{', '.join(TIERS.keys())}, all")
            return {}

        tier = TIERS[tier_key]
        generated = {}

        for template in ALL_EQUIP_TEMPLATES:
            if template["tier"] != tier_key:
                continue

            item_id = template["id"]

            if item_id in self.items:
                continue

            stats = self._calc_stats(template, tier_key)
            buy_price, sell_price = self._calc_price(stats, tier_key, template["equip_slot"])

            item = {
                "id": item_id,
                "name": template["name"],
                "type": template["type"],
                "description": template["desc"],
                "buy_price": buy_price,
                "sell_price": sell_price,
                "stackable": False,
                "equip_slot": template["equip_slot"],
                "stats": stats,
            }
            generated[item_id] = item

        print(f"生成 {tier['name']}装备 ({tier_key})：{len(generated)} 件")
        return generated

    def generate_consumables(self):
        generated = {}
        for t in CONSUMABLE_TEMPLATES:
            if t["id"] not in self.items and t["id"] not in generated:
                generated[t["id"]] = {
                    "id": t["id"],
                    "name": t["name"],
                    "type": "consumable",
                    "description": t["desc"],
                    "buy_price": t["buy"],
                    "sell_price": t["sell"],
                    "stackable": True,
                }
        print(f"生成消耗品：{len(generated)} 件")
        return generated

    def generate_materials(self):
        generated = {}
        for t in MATERIAL_TEMPLATES:
            if t["id"] not in self.items and t["id"] not in generated:
                generated[t["id"]] = {
                    "id": t["id"],
                    "name": t["name"],
                    "type": "material",
                    "description": t["desc"],
                    "buy_price": t["buy"],
                    "sell_price": t["sell"],
                    "stackable": True,
                }
        print(f"生成材料：{len(generated)} 件")
        return generated

    def generate_foods(self):
        generated = {}
        for t in FOOD_TEMPLATES:
            if t["id"] not in self.items and t["id"] not in generated:
                generated[t["id"]] = {
                    "id": t["id"],
                    "name": t["name"],
                    "type": "food",
                    "description": t["desc"],
                    "buy_price": t["buy"],
                    "sell_price": t["sell"],
                    "stackable": True,
                }
        print(f"生成食物：{len(generated)} 件")
        return generated

    def generate_tools(self):
        generated = {}
        for t in TOOL_TEMPLATES:
            if t["id"] not in self.items and t["id"] not in generated:
                generated[t["id"]] = {
                    "id": t["id"],
                    "name": t["name"],
                    "type": "tool",
                    "description": t["desc"],
                    "buy_price": t["buy"],
                    "sell_price": t["sell"],
                    "stackable": True,
                }
        print(f"生成工具：{len(generated)} 件")
        return generated

    def generate_all(self):
        generated = {}
        for tk in TIERS:
            generated.update(self.generate_equip(tk))
        generated.update(self.generate_consumables())
        generated.update(self.generate_materials())
        generated.update(self.generate_foods())
        generated.update(self.generate_tools())
        return generated

    def apply(self, generated):
        count = 0
        for item_id, item in generated.items():
            if item_id not in self.items:
                self.items[item_id] = item
                count += 1
        self._save_items()
        print(f"已应用 {count} 件新物品到 items.json（跳过 {len(generated) - count} 件已存在物品）")
        return count

    def generate_shop(self, npc_id):
        if npc_id == "all":
            total = 0
            for nid in SHOP_TEMPLATES:
                total += self.generate_shop(nid)
            return total

        if npc_id not in SHOP_TEMPLATES:
            print(f"错误：未知NPC '{npc_id}'，可选：{', '.join(SHOP_TEMPLATES.keys())}, all")
            return 0

        template = SHOP_TEMPLATES[npc_id]
        inventory = []

        tier_item_map = {}
        for tmpl in ALL_EQUIP_TEMPLATES:
            tk = tmpl["tier"]
            if tk not in tier_item_map:
                tier_item_map[tk] = []
            tier_item_map[tk].append(tmpl["id"])

        for tier_key in template["equip_tiers"]:
            equip_slots = template["equip_types"]
            qty_range = template["equip_quantity"].get(tier_key, (1, 2))

            tier_items = tier_item_map.get(tier_key, [])
            for item_id in tier_items:
                item = self.items.get(item_id)
                if not item:
                    continue
                slot = item.get("equip_slot", "")
                if slot not in equip_slots and item.get("type") not in equip_slots:
                    continue
                qty = random.randint(*qty_range)
                inventory.append({"item_id": item_id, "quantity": qty})

        for cid in template.get("consumable_ids", []):
            if cid in self.items:
                qty = random.randint(*template["consumable_quantity"])
                inventory.append({"item_id": cid, "quantity": qty})

        for tid in template.get("tool_ids", []):
            if tid in self.items:
                qty = random.randint(*template["tool_quantity"])
                inventory.append({"item_id": tid, "quantity": qty})

        for mid in template.get("material_ids", []):
            if mid in self.items:
                qty = random.randint(*template["material_quantity"])
                inventory.append({"item_id": mid, "quantity": qty})

        for fid in template.get("food_ids", []):
            if fid in self.items:
                qty = random.randint(*template["food_quantity"])
                inventory.append({"item_id": fid, "quantity": qty})

        npcs = self._load_npcs()
        if npc_id in npcs:
            npcs[npc_id]["shop"]["inventory"] = inventory
            npcs[npc_id]["shop"]["gold"] = template["gold"]
            self._save_npcs(npcs)
            print(f"已更新 {npcs[npc_id]['name']} 的商店库存：{len(inventory)} 种物品，{template['gold']} 金币")
        else:
            print(f"警告：NPC '{npc_id}' 不在 npcs.json 中")
            return 0

        return len(inventory)

    def validate(self):
        issues = []
        for item_id, item in self.items.items():
            if item.get("id") != item_id:
                issues.append(f"ID不匹配：key={item_id}, id={item.get('id')}")

            if "name" not in item:
                issues.append(f"{item_id}：缺少name字段")

            if "type" not in item:
                issues.append(f"{item_id}：缺少type字段")

            if item.get("equip_slot"):
                if "stats" not in item:
                    issues.append(f"{item_id}：有equip_slot但缺少stats")
                else:
                    for k in ["attack", "defense", "speed", "max_hp"]:
                        if k not in item["stats"]:
                            issues.append(f"{item_id}：stats缺少 {k} 字段")

                if item.get("stackable", False):
                    issues.append(f"{item_id}：装备物品不应stackable")

                if "buy_price" not in item or item["buy_price"] <= 0:
                    issues.append(f"{item_id}：装备物品应有buy_price > 0")

            if item.get("stackable") and item.get("equip_slot"):
                issues.append(f"{item_id}：stackable和equip_slot不应同时存在")

        if issues:
            print(f"发现 {len(issues)} 个问题：")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("所有物品数据验证通过！")
        return len(issues)

    def list_items(self):
        by_type = {}
        for item_id, item in self.items.items():
            t = item.get("type", "unknown")
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(item)

        type_order = ["weapon", "armor", "accessory", "consumable", "food", "tool", "material"]
        for t in type_order:
            if t in by_type:
                items = by_type[t]
                print(f"\n── {t} ({len(items)}件) ──")
                for item in sorted(items, key=lambda x: x.get("buy_price", 0)):
                    stats_str = ""
                    if item.get("stats"):
                        parts = []
                        for k, v in item["stats"].items():
                            if v != 0:
                                parts.append(f"{k}:{'+' if v > 0 else ''}{v}")
                        stats_str = f" [{', '.join(parts)}]"
                    equip_str = f" → {item['equip_slot']}" if item.get("equip_slot") else ""
                    print(f"  {item['id']}: {item['name']}{equip_str}{stats_str} 买:{item.get('buy_price', 0)} 卖:{item.get('sell_price', 0)}")

        other_types = set(by_type.keys()) - set(type_order)
        for t in sorted(other_types):
            items = by_type[t]
            print(f"\n── {t} ({len(items)}件) ──")
            for item in items:
                print(f"  {item['id']}: {item['name']}")

    def preview(self):
        equip_items = {k: v for k, v in self.items.items() if v.get("equip_slot")}

        by_slot = {}
        for item_id, item in equip_items.items():
            slot = item["equip_slot"]
            if slot not in by_slot:
                by_slot[slot] = []
            by_slot[slot].append(item)

        slot_names = {"weapon": "武器", "shield": "盾牌", "head": "头部", "body": "身体", "accessory": "饰品"}
        for slot in ["weapon", "shield", "head", "body", "accessory"]:
            items = by_slot.get(slot, [])
            print(f"\n── {slot_names.get(slot, slot)} ({len(items)}件) ──")
            for item in sorted(items, key=lambda x: x.get("buy_price", 0)):
                stats = item.get("stats", {})
                stat_str = "  ".join(
                    f"{k}:{'+' if v > 0 else ''}{v}"
                    for k, v in stats.items() if v != 0
                )
                print(f"  {item['name']:<10} | {stat_str:<25} | 价格:{item.get('buy_price', 0):>4}")

        print(f"\n总计：{len(equip_items)} 件装备，{len(self.items)} 件物品")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    gen = ItemGenerator()

    if cmd == "generate":
        if len(sys.argv) < 3:
            print("用法：python item_generator.py generate <equip|consumable|material|food|tool|all> [tier1|tier2|tier3|all]")
            return

        sub = sys.argv[2]
        if sub == "equip":
            tier = sys.argv[3] if len(sys.argv) > 3 else "all"
            generated = gen.generate_equip(tier)
        elif sub == "consumable":
            generated = gen.generate_consumables()
        elif sub == "material":
            generated = gen.generate_materials()
        elif sub == "food":
            generated = gen.generate_foods()
        elif sub == "tool":
            generated = gen.generate_tools()
        elif sub == "all":
            generated = gen.generate_all()
        else:
            print(f"未知子命令：{sub}")
            return

        if generated:
            print(f"\n预览生成的物品：")
            for item_id, item in list(generated.items())[:10]:
                stats = item.get("stats", {})
                stat_str = " ".join(f"{k}:{'+' if v > 0 else ''}{v}" for k, v in stats.items() if v != 0)
                print(f"  {item_id}: {item['name']} [{stat_str}] 买:{item.get('buy_price', 0)}")
            if len(generated) > 10:
                print(f"  ... 还有 {len(generated) - 10} 件")
            print(f"\n使用 'python item_generator.py apply' 应用到 items.json")

    elif cmd == "shop":
        npc_id = sys.argv[2] if len(sys.argv) > 2 else "all"
        gen.generate_shop(npc_id)

    elif cmd == "validate":
        gen.validate()

    elif cmd == "list":
        gen.list_items()

    elif cmd == "preview":
        gen.preview()

    elif cmd == "apply":
        generated = gen.generate_all()
        if generated:
            gen.apply(generated)
        else:
            print("没有新物品需要应用")

    else:
        print(f"未知命令：{cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
