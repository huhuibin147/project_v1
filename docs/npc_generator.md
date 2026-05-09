# NPC 生成器

`tools/npc_generator.py` — 用于快速创建和管理游戏 NPC 配置。

## 功能概览

1. **从模板创建 NPC**：商人、铁匠、治疗师、技能导师、任务发布者、旅店老板、守卫
2. **预设 NPC 快速创建**：面包师、酒馆老板、守卫、旅行商人等
3. **商店库存分配**：根据物品类型自动为 NPC 分配商品
4. **批量生成**：一次性生成多个同类型 NPC
5. **数据验证**：检查 NPC 配置完整性
6. **预览**：查看 NPC 属性分布和统计

## 使用方法

```bash
cd tools

# 查看可用模板
python npc_generator.py templates

# 查看可用预设
python npc_generator.py presets

# 从模板创建 NPC
python npc_generator.py create merchant baker "面包师老李" "青石村面包房" village
python npc_generator.py create healer priest2 "修女玛丽" "森林神殿" forest
python npc_generator.py create skill_master master2 "剑术大师" "训练场" village

# 快捷创建命令
python npc_generator.py create-merchant baker "面包师老李"
python npc_generator.py create-healer priest2 "修女玛丽"
python npc_generator.py create-master master2 "剑术大师"
python npc_generator.py create-quest mayor "村长"

# 从预设创建
python npc_generator.py preset baker
python npc_generator.py preset bartender
python npc_generator.py preset village_guard

# 为 NPC 分配商店库存
python npc_generator.py shop baker food consumable
python npc_generator.py shop blacksmith weapon armor
python npc_generator.py shop herbalist consumable material

# 批量生成 NPC
python npc_generator.py batch merchant 3 "旅商" village
python npc_generator.py batch guard 5 "守卫" village

# 验证和预览
python npc_generator.py validate       # 验证所有 NPC 配置
python npc_generator.py list           # 列出所有 NPC
python npc_generator.py preview        # 预览属性分布

# 应用到 npcs.json
python npc_generator.py apply
```

## NPC 模板

| 模板名 | 角色 | 默认商店 | 默认服务 | 性格特点 |
|--------|------|---------|---------|---------|
| merchant | 商人 | 是 | 无 | 精明、善于交际 |
| blacksmith | 铁匠 | 是 | 无 | 豪爽、自豪 |
| healer | 治疗师 | 是 | 恢复HP/MP/解除异常 | 温柔、虔诚 |
| skill_master | 技能导师 | 是 | 直接学习技能 | 严谨、博学 |
| quest_giver | 任务发布者 | 否 | 无 | 见多识广 |
| innkeeper | 旅店老板 | 是 | 休息恢复 | 热情、八卦 |
| guard | 守卫 | 否 | 无 | 正直、严肃 |

### 治疗师服务

| 服务 | 效果 | 费用 |
|------|------|------|
| 恢复生命 | 恢复全部 HP | 20 金币 |
| 恢复魔法 | 恢复全部 MP | 15 金币 |
| 解除异常 | 清除所有负面状态 | 30 金币 |

### 技能导师服务

| 服务 | 效果 | 费用 |
|------|------|------|
| 直接传授 | 无需技能书学习技能 | 技能书原价 × 1.5 |

### 旅店老板服务

| 服务 | 效果 | 费用 |
|------|------|------|
| 休息一晚 | 恢复全部 HP 和 MP | 10 金币 |

## 预设 NPC

| 预设名 | 名称 | 角色 | 位置 | 特色 |
|--------|------|------|------|------|
| baker | 面包师老李 | 面包师 | 青石村面包房 | 出售各种食物 |
| bartender | 酒馆老板老赵 | 酒馆老板 | 青石村酒馆 | 出售酒食，消息灵通 |
| village_guard | 守卫大壮 | 守卫 | 青石村入口 | 无商店，可接任务 |
| wandering_merchant | 旅行商人阿明 | 旅行商人 | 幽暗森林 | 出售稀有物品 |

## NPC 数据结构

生成的 NPC 配置遵循以下结构：

```json
{
  "id": "npc_id",
  "name": "NPC名称",
  "role": "角色",
  "location": "所在位置",
  "map_id": "所在地图",
  "personality": {
    "traits": "性格特征",
    "pronoun": "自称",
    "style": "说话风格",
    "likes": "喜欢的事物",
    "dislikes": "讨厌的事物"
  },
  "backstory": "背景故事",
  "greeting": "问候语",
  "default_mood": "默认心情",
  "default_affinity": 50,
  "personality_params": {
    "friendliness": 0.7,
    "courage": 0.5,
    "greed": 0.3,
    "humor": 0.5
  },
  "intents": {
    "chat": "闲聊意图描述",
    "quest": "任务意图描述",
    "trade": "交易意图描述",
    "unknown": "无法判断意图"
  },
  "shop": {
    "name": "商店名称",
    "gold": 300,
    "inventory": [
      {"item_id": "item_1", "quantity": 5},
      {"item_id": "item_2", "quantity": 3}
    ]
  },
  "services": {
    "heal": {
      "name": "恢复生命",
      "description": "恢复全部生命值",
      "cost": 20
    }
  }
}
```

## 商店库存分配规则

| 物品类型 | 数量范围 | 等级段限制 |
|---------|---------|-----------|
| weapon | 2-5 | tier1-3 |
| armor | 2-4 | tier1-3 |
| accessory | 1-3 | tier1-3 |
| consumable | 5-20 | 无 |
| food | 5-15 | 无 |
| material | 5-20 | 无 |
| tool | 3-8 | 无 |

## 扩展模板

如需添加新的 NPC 模板，编辑 `tools/npc_generator.py` 中的 `NPC_TEMPLATES` 字典：

```python
NPC_TEMPLATES["alchemist"] = {
    "role": "炼金术士",
    "personality": {
        "traits": "神秘古怪，痴迷实验",
        "pronoun": "本座",
        "style": "古怪神秘，偶尔自言自语",
        "likes": "稀有材料、实验成功",
        "dislikes": "打扰实验的人、失败"
    },
    "default_mood": "专注",
    "default_affinity": 45,
    "personality_params": {
        "friendliness": 0.4,
        "courage": 0.6,
        "greed": 0.5,
        "humor": 0.3
    },
    "intents": {
        "chat": "闲聊、讨论炼金术",
        "quest": "委托收集材料、测试药剂",
        "trade": "买卖药剂、材料",
        "unknown": "无法判断意图"
    },
    "has_shop": True,
    "default_gold": 350,
    "services": {}
}
```

## 批量生成示例

为多个村庄生成守卫：

```bash
# 生成5个守卫
python npc_generator.py batch guard 5 "守卫" village

# 生成3个旅行商人
python npc_generator.py batch merchant 3 "旅商" forest

# 应用所有生成的 NPC
python npc_generator.py apply
```

## 验证检查项

`validate` 命令会检查以下内容：

- 必填字段完整性（id, name, role, location, map_id 等）
- personality_params 四项参数（friendliness, courage, greed, humor）是否在 0-1 范围内
- 商店配置格式（name, inventory）
- 服务配置格式（name, description）
