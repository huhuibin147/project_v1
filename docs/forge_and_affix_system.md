# 锻造系统与词条系统设计文档

## 概述

本文档详细描述锻造系统和词条系统的设计与实现方案。这两个系统共同构成游戏核心循环的关键环节：

```
战斗 → 材料掉落 → 锻造装备 → 词条随机化 → 更强装备 → 更高难度战斗
```

---

# 第一部分：锻造系统

## 1.1 系统目标

- 玩家通过收集材料 + 金币在铁匠处锻造装备
- 锻造有成功率，失败返还部分材料
- 锻造产出的装备自动附带随机词条
- 高级配方需要玩家达到一定等级

## 1.2 数据结构

### 锻造配方 `config/forge_recipes.json`

```json
{
  "forge_iron_sword": {
    "recipe_id": "forge_iron_sword",
    "name": "锻造铁剑",
    "description": "用铁矿石锻造一把坚固的铁剑",
    "output": {
      "item_id": "iron_sword",
      "quantity": 1
    },
    "materials": [
      { "item_id": "iron_ore", "quantity": 3 },
      { "item_id": "wood", "quantity": 1 }
    ],
    "gold_cost": 50,
    "level_requirement": 3,
    "success_rate": 1.0,
    "fail_return_rate": 0.5,
    "category": "weapon",
    "tier": "basic",
    "rarity_guarantee": "uncommon"
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| recipe_id | string | 配方唯一ID |
| name | string | 配方显示名称 |
| description | string | 配方描述 |
| output.item_id | string | 产出物品ID（对应 items.json） |
| output.quantity | int | 产出数量 |
| materials | array | 材料列表 [{item_id, quantity}] |
| gold_cost | int | 金币消耗 |
| level_requirement | int | 玩家等级要求 |
| success_rate | float | 成功率 (0.0~1.0) |
| fail_return_rate | float | 失败时材料返还比例 (0.0~1.0) |
| category | string | 分类：weapon/armor/accessory |
| tier | string | 配方等级：basic/intermediate/advanced/master |
| rarity_guarantee | string | 保底稀有度（产出装备至少为此稀有度） |

### 配方等级段

| 等级段 | tier | 等级要求 | 成功率基础 | 说明 |
|--------|------|----------|------------|------|
| 初级 | basic | Lv.1 | 100% | 铁制装备 |
| 中级 | intermediate | Lv.5 | 90% | 秘银装备 |
| 高级 | advanced | Lv.10 | 75% | 精金装备 |
| 大师 | master | Lv.15 | 60% | 传说装备 |

## 1.3 锻造逻辑

### 锻造流程

```
1. 玩家选择配方
2. 系统检查：等级、材料、金币
3. 扣除金币和材料
4. 判定成功/失败
   - 成功：生成装备（含随机词条）→ 放入背包
   - 失败：按 fail_return_rate 返还部分材料
5. 返回结果
```

### 成功率计算

```python
final_rate = recipe["success_rate"]
# 无额外修正，直接使用配方成功率
# 未来可扩展：天赋加成、NPC好感度加成等
```

### 产出装备稀有度

锻造产出的装备稀有度由配方保底 + 随机提升决定：

```python
rarity_order = ["common", "uncommon", "rare", "epic", "legendary"]
guarantee_idx = rarity_order.index(recipe["rarity_guarantee"])
# 20% 概率提升一级稀有度
if random.random() < 0.2 and guarantee_idx < len(rarity_order) - 1:
    final_rarity = rarity_order[guarantee_idx + 1]
else:
    final_rarity = recipe["rarity_guarantee"]
```

### 产出装备词条

根据最终稀有度决定词条数量，调用词条系统生成：

| 稀有度 | 词条数 |
|--------|--------|
| common | 0 |
| uncommon | 1 |
| rare | 2 |
| epic | 3 |
| legendary | 4 |

## 1.4 完整配方列表

### 武器配方

| recipe_id | 名称 | 产出 | 材料 | 金币 | 等级 | 成功率 | 保底稀有度 |
|-----------|------|------|------|------|------|--------|-----------|
| forge_iron_sword | 锻造铁剑 | iron_sword | 铁矿×3 + 木材×1 | 50 | 3 | 100% | uncommon |
| forge_iron_dagger | 锻造铁匕首 | iron_dagger | 铁矿×2 + 木材×1 | 40 | 2 | 100% | uncommon |
| forge_iron_axe | 锻造铁斧 | iron_axe | 铁矿×4 + 木材×2 | 60 | 3 | 100% | uncommon |
| forge_steel_sword | 锻造精钢剑 | steel_sword | 铁矿×5 + 钢锭×2 | 150 | 5 | 90% | uncommon |
| forge_silver_dagger | 锻造银匕首 | silver_dagger | 铁矿×3 + 钢锭×2 | 130 | 5 | 90% | uncommon |
| forge_bronze_hammer | 锻造青铜锤 | bronze_hammer | 铁矿×4 + 钢锭×2 + 兽骨×1 | 200 | 6 | 90% | uncommon |
| forge_mithril_sword | 锻造秘银剑 | mithril_sword | 秘银矿×4 + 钢锭×3 + 兽骨×2 | 400 | 10 | 75% | rare |
| forge_darkgold_dagger | 锻造暗金匕首 | darkgold_dagger | 秘银矿×3 + 暗影精华×2 + 兽骨×2 | 600 | 12 | 70% | epic |
| forge_crystal_staff | 锻造魔晶法杖 | crystal_staff | 魔晶×3 + 秘银矿×2 + 古代碎片×2 | 700 | 14 | 65% | epic |

### 防具配方

| recipe_id | 名称 | 产出 | 材料 | 金币 | 等级 | 成功率 | 保底稀有度 |
|-----------|------|------|------|------|------|--------|-----------|
| forge_leather_armor | 锻造皮甲 | leather_armor | 狼皮×3 + 布料×2 | 40 | 2 | 100% | common |
| forge_iron_shield | 锻造铁盾 | iron_shield | 铁矿×4 + 木材×2 | 80 | 4 | 100% | uncommon |
| forge_iron_helmet | 锻造铁盔 | iron_helmet | 铁矿×3 + 木材×1 | 60 | 3 | 100% | uncommon |
| forge_iron_armor | 锻造铁甲 | iron_armor | 铁矿×6 + 木材×2 + 布料×1 | 200 | 5 | 90% | uncommon |
| forge_steel_shield | 锻造精钢盾 | steel_shield | 铁矿×5 + 钢锭×3 | 180 | 6 | 90% | uncommon |
| forge_hard_leather_armor | 锻造硬皮衣 | hard_leather_armor | 狼皮×5 + 布料×3 + 兽骨×1 | 150 | 5 | 90% | uncommon |
| forge_silver_helmet | 锻造银盔 | silver_helmet | 铁矿×4 + 钢锭×2 + 兽骨×1 | 200 | 6 | 90% | uncommon |
| forge_steel_armor | 锻造精钢甲 | steel_armor | 铁矿×6 + 钢锭×4 + 兽骨×2 | 400 | 10 | 75% | rare |
| forge_mithril_shield | 锻造秘银盾 | mithril_shield | 秘银矿×5 + 钢锭×3 + 暗影精华×1 | 550 | 12 | 70% | epic |
| forge_dragon_leather_armor | 锻造龙皮衣 | dragon_leather_armor | 龙鳞×3 + 秘银矿×2 + 暗影精华×2 | 600 | 13 | 65% | epic |

### 饰品配方

| recipe_id | 名称 | 产出 | 材料 | 金币 | 等级 | 成功率 | 保底稀有度 |
|-----------|------|------|------|------|------|--------|-----------|
| forge_ring_of_power | 锻造力量戒指 | ring_of_power | 铁矿×2 + 兽骨×1 | 200 | 3 | 100% | common |
| forge_life_necklace | 锻造生命项链 | life_necklace | 兽骨×2 + 布料×2 | 180 | 2 | 100% | common |
| forge_silver_ring | 锻造银戒指 | silver_ring | 铁矿×3 + 钢锭×2 + 魔晶×1 | 350 | 7 | 85% | uncommon |
| forge_guardian_necklace | 锻造守护项链 | guardian_necklace | 铁矿×2 + 钢锭×2 + 兽骨×2 | 320 | 6 | 90% | uncommon |
| forge_darkgold_ring | 锻造暗金戒指 | darkgold_ring | 秘银矿×3 + 暗影精华×2 + 魔晶×2 | 900 | 14 | 60% | epic |
| forge_eternal_necklace | 锻造永恒项链 | eternal_necklace | 秘银矿×3 + 龙鳞×2 + 古代碎片×2 | 800 | 13 | 65% | epic |

## 1.5 API 接口

### 获取锻造配方列表

```
GET /api/forge/recipes?npc_id=blacksmith
```

**响应：**
```json
{
  "recipes": [
    {
      "recipe_id": "forge_iron_sword",
      "name": "锻造铁剑",
      "description": "用铁矿石锻造一把坚固的铁剑",
      "output": { "item_id": "iron_sword", "name": "铁剑", "quantity": 1 },
      "materials": [
        { "item_id": "iron_ore", "name": "铁矿石", "quantity": 3, "owned": 5 },
        { "item_id": "wood", "name": "木材", "quantity": 1, "owned": 3 }
      ],
      "gold_cost": 50,
      "level_requirement": 3,
      "success_rate": 1.0,
      "can_craft": true,
      "missing_materials": [],
      "missing_gold": 0,
      "category": "weapon",
      "tier": "basic",
      "rarity_guarantee": "uncommon"
    }
  ],
  "player_level": 5,
  "player_gold": 300
}
```

### 执行锻造

```
POST /api/forge/craft
```

**请求体：**
```json
{
  "recipe_id": "forge_iron_sword",
  "npc_id": "blacksmith"
}
```

**响应（成功）：**
```json
{
  "success": true,
  "message": "锻造成功！获得【铁剑】！",
  "result": {
    "item_id": "iron_sword",
    "name": "铁剑",
    "rarity": "uncommon",
    "affixes": [
      { "affix_id": "sharp", "name": "锋利", "description": "攻击力 +5%" }
    ]
  },
  "player_inventory": [...],
  "player_gold": 250
}
```

**响应（失败）：**
```json
{
  "success": false,
  "message": "锻造失败...返还了部分材料。",
  "result": {
    "returned_materials": [
      { "item_id": "iron_ore", "name": "铁矿石", "quantity": 2 }
    ]
  },
  "player_inventory": [...],
  "player_gold": 250
}
```

## 1.6 前端 UI 设计

### 锻造面板

锻造面板作为独立 DOM 面板覆盖在 Canvas 上，与商店/治疗面板风格一致。

**面板结构：**
```
┌─────────────────────────────────────────┐
│  ⚒️ 锻造工坊          你的金币: 300    × │
├─────────────────────────────────────────┤
│  [武器] [防具] [饰品]                   │ ← 分类标签
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐    │
│  │ ⚔️ 锻造铁剑              [初级] │    │
│  │ 产出: 铁剑 ×1                  │    │
│  │ 材料: 铁矿石×3(✓) 木材×1(✓)   │    │
│  │ 金币: 50  等级: Lv.3           │    │
│  │ 成功率: 100%                    │    │
│  │ 保底: [优秀]                    │    │
│  │                    [开始锻造]   │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ ⚔️ 锻造精钢剑            [中级] │    │
│  │ 产出: 精钢剑 ×1                │    │
│  │ 材料: 铁矿×5(✓) 钢锭×2(✗)     │    │
│  │ 金币: 150  等级: Lv.5          │    │
│  │ 成功率: 90%                     │    │
│  │ 保底: [优秀]                    │    │
│  │                    [材料不足]   │    │
│  └─────────────────────────────────┘    │
├─────────────────────────────────────────┤
│  ◀ 1/3 ▶                              │ ← 分页
└─────────────────────────────────────────┘
```

### 铁匠 NPC 交互选项

在铁匠老王的交互选项中新增「锻造」按钮：

```
┌─────────────────────────┐
│     铁匠老王            │
│                         │
│  [对话 (1)]             │
│  [任务 (2)]             │
│  [商店 (3)]             │
│  [锻造 (4)]   ← 新增    │
└─────────────────────────┘
```

### 锻造结果弹窗

锻造完成后显示结果弹窗，展示产出装备和词条信息：

```
┌─────────────────────────┐
│     ⚒️ 锻造成功！       │
│                         │
│  获得: 铁剑             │
│  稀有度: [优秀]         │
│  词条:                  │
│  · 锋利 - 攻击力 +5%    │
│                         │
│       [确定]            │
└─────────────────────────┘
```

---

# 第二部分：词条系统

## 2.1 系统目标

- 装备可附带随机词条，增加装备多样性和收集驱动力
- 词条效果在战斗中实际生效
- 词条通过锻造自动生成，也可通过附魔添加
- 不同稀有度的装备拥有不同数量的词条槽位

## 2.2 数据结构

### 词条配置 `config/affixes.json`

```json
{
  "sharp": {
    "affix_id": "sharp",
    "name": "锋利",
    "category": "passive",
    "description": "攻击力 +5%",
    "effects": [
      {
        "type": "stat_percent",
        "stat": "attack",
        "value": 0.05
      }
    ],
    "tier": 1,
    "weight": 40,
    "level_range": { "min": 1, "max": 20 },
    "compatible_slots": ["weapon"]
  },
  "burning": {
    "affix_id": "burning",
    "name": "灼烧",
    "category": "on_attack",
    "description": "攻击时 15% 概率附加灼烧效果",
    "effects": [
      {
        "type": "on_hit",
        "trigger_chance": 0.15,
        "apply_effect": "burn",
        "effect_duration": 3
      }
    ],
    "tier": 2,
    "weight": 30,
    "level_range": { "min": 1, "max": 15 },
    "compatible_slots": ["weapon"]
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| affix_id | string | 词条唯一ID |
| name | string | 词条显示名称 |
| category | string | 类别：passive/on_attack/on_hit/on_kill/conditional |
| description | string | 词条描述 |
| effects | array | 效果列表 |
| tier | int | 词条等级（1=初级, 2=中级, 3=高级） |
| weight | int | 随机抽取权重 |
| level_range | object | 适用等级范围 {min, max} |
| compatible_slots | array | 兼容装备槽位 |

### 词条效果类型

| 效果类型 | type | 参数 | 说明 |
|----------|------|------|------|
| 百分比属性加成 | stat_percent | stat, value | 如攻击力+5% |
| 固定属性加成 | stat_flat | stat, value | 如速度+5 |
| 攻击触发 | on_hit | trigger_chance, apply_effect, effect_duration | 攻击命中时概率触发效果 |
| 吸血 | lifesteal | trigger_chance, value | 攻击命中时概率吸血 |
| 反伤 | reflect | trigger_chance, value | 受击时概率反弹伤害 |
| 减伤 | damage_reduce | trigger_chance, value | 受击时概率减伤 |
| 金币加成 | gold_bonus | value | 金币获取+百分比 |
| 经验加成 | exp_bonus | value | 经验获取+百分比 |
| 条件属性 | conditional_stat | condition, stat, value | 满足条件时属性加成 |

### 装备上的词条存储

在 `items.json` 中，装备的 `affixes` 字段存储词条列表：

```json
{
  "iron_sword": {
    "affixes": [
      {
        "affix_id": "sharp",
        "name": "锋利",
        "description": "攻击力 +5%",
        "effects": [
          { "type": "stat_percent", "stat": "attack", "value": 0.05 }
        ]
      }
    ]
  }
}
```

**注意**：锻造产出的装备是独立实例，词条存储在玩家背包的物品数据中，而非 items.json 模板。

### 背包物品词条存储

玩家背包中的装备物品需要存储实例化的词条数据。修改背包数据结构：

```json
{
  "items": [
    {
      "item_id": "iron_sword",
      "quantity": 1,
      "instance_affixes": [
        {
          "affix_id": "sharp",
          "name": "锋利",
          "description": "攻击力 +5%",
          "effects": [
            { "type": "stat_percent", "stat": "attack", "value": 0.05 }
          ]
        }
      ]
    }
  ]
}
```

`instance_affixes` 为空或不存在时，使用 items.json 中的 `affixes` 字段（模板词条）。

## 2.3 词条生成逻辑

### 生成流程

```python
def generate_affixes(equip_slot: str, rarity: str, player_level: int) -> list[dict]:
    # 1. 确定词条数量
    affix_count = RARITY_AFFIX_COUNT[rarity]  # common=0, uncommon=1, ...

    # 2. 筛选可用词条池
    pool = [a for a in ALL_AFFIXES
            if equip_slot in a["compatible_slots"]
            and a["level_range"]["min"] <= player_level <= a["level_range"]["max"]]

    # 3. 按权重随机抽取（不重复）
    selected = weighted_sample_without_replacement(pool, affix_count, key="weight")

    # 4. 返回词条列表
    return selected
```

### 稀有度与词条数量映射

```python
RARITY_AFFIX_COUNT = {
    "common": 0,
    "uncommon": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
}
```

## 2.4 完整词条列表

### 武器词条

| affix_id | 名称 | 类别 | 效果 | tier | 权重 | 等级范围 |
|----------|------|------|------|------|------|----------|
| sharp | 锋利 | passive | 攻击力 +5% | 1 | 40 | 1-20 |
| burning | 灼烧 | on_attack | 15%概率附加灼烧3回合 | 2 | 30 | 1-15 |
| frost | 冰霜 | on_attack | 10%概率冻结1回合 | 2 | 25 | 1-15 |
| thunder | 雷击 | on_attack | 8%概率额外50%伤害 | 3 | 15 | 5-20 |
| lifesteal_affix | 吸血 | on_attack | 10%造成伤害恢复HP | 2 | 25 | 3-20 |
| crit_bonus | 暴击 | passive | 暴击率 +5% | 2 | 30 | 1-20 |
| desperate | 绝境 | conditional | HP<30%攻击+20% | 3 | 15 | 5-20 |

### 防具词条

| affix_id | 名称 | 类别 | 效果 | tier | 权重 | 等级范围 |
|----------|------|------|------|------|------|----------|
| sturdy | 坚固 | passive | 防御力 +8% | 1 | 40 | 1-20 |
| thorns | 荆棘 | on_hit | 受击反弹15%伤害 | 2 | 25 | 3-20 |
| shield_affix | 护盾 | on_hit | 10%概率减伤50% | 2 | 25 | 3-20 |
| vitality | 生命 | passive | 最大HP +10% | 1 | 35 | 1-20 |
| regen_affix | 再生 | passive | 每回合恢复3%HP | 3 | 15 | 5-20 |

### 饰品词条

| affix_id | 名称 | 类别 | 效果 | tier | 权重 | 等级范围 |
|----------|------|------|------|------|------|----------|
| agile | 灵活 | passive | 速度 +5 | 1 | 35 | 1-20 |
| crit_bonus_acc | 暴击 | passive | 暴击率 +5% | 2 | 30 | 1-20 |
| vitality_acc | 生命 | passive | 最大HP +10% | 1 | 35 | 1-20 |
| mana_affix | 魔力 | passive | 最大MP +10% | 1 | 30 | 1-20 |
| greed | 贪婪 | on_kill | 金币获取 +15% | 2 | 25 | 1-20 |
| hunter | 猎手 | on_kill | 经验获取 +10% | 2 | 25 | 1-20 |
| speed_affix | 迅捷 | passive | 速度 +8 | 3 | 15 | 5-20 |

## 2.5 词条效果与战斗集成

### 被动词条（passive）

被动词条在装备时直接修改玩家属性，在 `_calc_equip_bonus()` 中计算：

```python
def _calc_equip_bonus(self) -> dict:
    from item_system import ITEMS_DB
    from affix_system import calc_affix_stat_bonus
    bonus = {"attack": 0, "defense": 0, "speed": 0, "max_hp": 0, "max_mp": 0}
    for slot_name, item_id in self.equipment.items():
        if item_id:
            info = ITEMS_DB.get(item_id, {})
            stats = info.get("stats", {})
            for key in bonus:
                bonus[key] += stats.get(key, 0)
            # 计算词条属性加成
            affixes = get_item_affixes(item_id, self.inventory)
            affix_bonus = calc_affix_stat_bonus(affixes, bonus)
            for key in bonus:
                bonus[key] += affix_bonus.get(key, 0)
    return bonus
```

### 触发类词条（on_attack / on_hit / on_kill）

在战斗引擎中集成触发逻辑：

**攻击时触发（on_attack）：**
- 在玩家攻击命中后检查装备中的 on_attack 词条
- 按 trigger_chance 判定是否触发
- 触发后应用效果（灼烧、冰冻、雷击额外伤害、吸血）

**受击时触发（on_hit）：**
- 在玩家受到伤害后检查装备中的 on_hit 词条
- 按 trigger_chance 判定是否触发
- 触发后应用效果（荆棘反伤、护盾减伤）

**击杀时触发（on_kill）：**
- 在怪物被击败后检查装备中的 on_kill 词条
- 直接应用效果（金币加成、经验加成）

### 条件词条（conditional）

在战斗每回合开始时检查条件：
- `desperate`（绝境）：HP < 30% 时攻击力 +20%

## 2.6 API 接口

### 获取词条类型

```
GET /api/affixes/types
```

**响应：**
```json
{
  "categories": [
    { "id": "passive", "name": "被动加成" },
    { "id": "on_attack", "name": "攻击触发" },
    { "id": "on_hit", "name": "受击触发" },
    { "id": "on_kill", "name": "击杀触发" },
    { "id": "conditional", "name": "条件触发" }
  ]
}
```

### 附魔词条（预留）

```
POST /api/affixes/enchant
```

**请求体：**
```json
{
  "item_id": "iron_sword",
  "npc_id": "blacksmith",
  "slot_index": 0
}
```

> 附魔功能为后续扩展，本次实现中预留接口但不实现完整逻辑。

---

# 第三部分：系统集成

## 3.1 背包系统修改

### 物品实例化

当前背包中物品仅存储 `{item_id, quantity}`。为支持词条，需要扩展为：

```json
{
  "item_id": "iron_sword",
  "quantity": 1,
  "instance_affixes": [...],
  "instance_rarity": "uncommon"
}
```

- `instance_affixes`：实例化词条，覆盖模板词条
- `instance_rarity`：实例化稀有度，覆盖模板稀有度
- 非装备物品和堆叠物品不需要这些字段

### 兼容性

- 旧存档无 `instance_affixes` 字段时，使用 items.json 中的 `affixes` 字段
- 旧存档无 `instance_rarity` 字段时，使用 items.json 中的 `rarity` 字段

## 3.2 装备系统修改

### 属性计算

在 `_calc_equip_bonus()` 中加入词条属性加成计算：

```
装备加成 = 基础属性 + 词条被动加成
```

词条被动加成类型：
- `stat_percent`：按百分比增加属性（基于基础属性）
- `stat_flat`：固定增加属性值

### 装备详情

`_get_equipment_detail()` 返回数据中包含词条信息：

```json
{
  "weapon": {
    "item_id": "iron_sword",
    "name": "铁剑",
    "stats": { "attack": 8 },
    "rarity": "uncommon",
    "affixes": [
      { "affix_id": "sharp", "name": "锋利", "description": "攻击力 +5%" }
    ]
  }
}
```

## 3.3 战斗引擎修改

### 战斗快照

在创建 `CombatSession` 时，需要将装备词条信息传入玩家快照：

```python
player_snapshot = {
    ...
    "equipment_affixes": get_all_equipment_affixes(player)
}
```

### 攻击流程集成

```
玩家攻击 → 计算伤害 → 命中判定 →
  → 检查 on_attack 词条（灼烧/冰冻/雷击/吸血）→
  → 应用伤害和效果 →
  → 生成战斗日志
```

### 受击流程集成

```
怪物攻击 → 计算伤害 →
  → 检查 on_hit 词条（护盾减伤）→ 修正伤害 →
  → 应用伤害 →
  → 检查 on_hit 词条（荆棘反伤）→ 对怪物造成反伤 →
  → 生成战斗日志
```

### 击杀流程集成

```
怪物被击败 →
  → 计算掉落和奖励 →
  → 检查 on_kill 词条（金币加成/经验加成）→ 修正奖励 →
  → 生成战斗日志
```

## 3.4 NPC 交互修改

### 铁匠老王交互选项

```
原：[对话(1)] [任务(2)] [商店(3)]
新：[对话(1)] [任务(2)] [商店(3)] [锻造(4)]
```

快捷键 `4` 绑定锻造功能。

### 其他铁匠 NPC

宫廷铁匠赵师傅（王城）同样提供锻造服务。

## 3.5 前端修改清单

| 文件 | 修改内容 |
|------|----------|
| index.html | 新增锻造面板 DOM 结构 |
| css/style.css | 新增锻造面板样式、词条标签样式 |
| js/npc.js | 铁匠交互选项新增「锻造」，快捷键4 |
| js/inventory.js | 装备卡片显示词条信息，词条标签样式 |
| js/player_info.js | 角色面板装备详情显示词条 |
| js/combat.js | 战斗日志显示词条触发效果 |
| 新增 js/forge.js | 锻造面板逻辑 |

---

# 第四部分：实现状态

## 4.1 已完成功能

| 模块 | 状态 | 说明 |
|------|------|------|
| 配置文件 | ✅ 完成 | `config/affixes.json`（30+词条）、`config/forge_recipes.json`（25种配方） |
| 后端核心 | ✅ 完成 | `backend/affix_system.py`、`backend/forge_system.py` |
| 后端集成 | ✅ 完成 | `item_system.py`（实例词条支持）、`player_profile.py`（词条属性加成）、`combat_engine.py`（词条触发）、`main.py`（API路由） |
| 前端 UI | ✅ 完成 | 锻造面板、词条显示、NPC交互修改 |
| 测试验证 | ✅ 完成 | 后端单元测试、API接口测试、前端交互测试 |

## 4.2 API 接口

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/forge/recipes` | GET | 获取所有锻造配方，含玩家材料/金币/等级检查 |
| `/api/forge/craft` | POST | 执行锻造，返回锻造结果、新装备信息、更新后的背包和金币 |
| `/api/affixes/types` | GET | 获取词条类别列表 |

## 4.3 战斗词条触发机制

| 类别 | 触发时机 | 效果示例 |
|------|----------|----------|
| passive | 始终生效 | 属性加成（攻击/防御/速度/最大HP） |
| on_attack | 玩家攻击时 | 灼烧、冰冻、雷击、中毒、沉默 |
| on_hit | 玩家受击时 | 反伤、减伤、吸血 |
| on_kill | 击杀怪物时 | 额外金币、额外经验 |
| conditional | 满足条件时 | 绝境之力（HP<30%时属性翻倍） |
