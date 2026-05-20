# 战斗系统设计文档

## 概述

Phase 2 战斗系统为 LLM NPC 像素风 RPG 添加了回合制战斗玩法。玩家在地图上遇到怪物，触发战斗，通过攻击/防御/使用物品/逃跑等操作进行战斗，胜利后获得经验值、金币和物品掉落。

## 系统架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  地图怪物    │────▶│  战斗触发    │────▶│  战斗面板 UI    │
│  (canvas)   │     │  (碰撞/E键)  │     │  (DOM overlay)  │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                                   ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  玩家状态    │◀────│  API 端点    │◀────│  玩家动作       │
│  (HP/EXP)   │     │  (FastAPI)   │     │  (attack/defend) │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │  战斗引擎    │
                   │  (Python)    │
                   └──────────────┘
```

## 伤害公式

```
基础伤害 = 攻击力 × (100 / (100 + 防御力))
浮动范围 = 基础伤害 × random(0.9, 1.1)
暴击率   = clamp(5%, 25%, 5% + 速度差 × 0.5%)
暴击伤害 = 浮动范围 × 1.5
防御减伤 = 暴击伤害 × 0.5（防御姿态时生效）
最终伤害 = max(1, floor(防御减伤))
```

### 示例

- 战士 Lv.3 (ATK=24, DEF=18, SPD=10) vs 史莱姆 (ATK=8, DEF=3, SPD=5)
- 战士攻击：24 × (100/103) × 1.0 ≈ 23 伤害
- 史莱姆攻击：8 × (100/118) × 1.0 ≈ 7 伤害
- 暴击率：5% + (10-5) × 0.5% = 7.5%

## 逃跑公式

```
速度比 = 玩家速度 / 怪物速度
逃跑率 = clamp(20%, 95%, 50% + (速度比 - 1) × 40%)
```

- 速度相同时：50%
- 速度是怪物2倍：90%
- 速度是怪物一半：30%

## 怪物配置

配置文件：`config/monsters.json`

```json
{
  "monster_id": {
    "id": "monster_id",
    "name": "怪物名称",
    "description": "描述",
    "type": "normal|elite|boss",
    "sprite_color": "#hex",
    "sprite_accent": "#hex",
    "stats": {
      "hp": 30,
      "attack": 8,
      "defense": 3,
      "speed": 5
    },
    "exp_reward": 15,
    "gold_reward": [5, 15],
    "drops": [
      {"item_id": "item_id", "chance": 0.3}
    ],
    "ai": {
      "behavior": "aggressive|cautious|defensive",
      "attack_weight": 80,
      "defend_weight": 15,
      "special_weight": 5,
      "special": null | {
        "type": "apply_effect",
        "effect": "poison",
        "chance": 0.3,
        "duration": 3,
        "value": 0,
        "message": "特殊技能消息"
      }
    },
    "level": 1,
    "tags": ["forest", "common"]
  }
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| type | normal=普通, elite=精英(★标记), boss=BOSS(预留) |
| sprite_color/sprite_accent | 像素精灵颜色 |
| gold_reward | [最小, 最大] 随机范围 |
| drops | 独立概率判定，每项单独 roll |
| ai.behavior | aggressive=偏好攻击, cautious=低血量增加防御, defensive=偏好防御 |
| ai.special | 特殊技能，null表示无特殊技能 |
| tags | 用于任务系统匹配(预留) |

### 初始怪物

| 怪物 | 等级 | HP | ATK | DEF | SPD | 经验 | 掉落 |
|------|------|----|-----|-----|-----|------|------|
| 史莱姆 | 1 | 30 | 8 | 3 | 5 | 15 | 草药, 蘑菇 |
| 野狼 | 2 | 45 | 12 | 4 | 12 | 25 | 狼皮, 兽骨, 肉干 |
| 毒蛛 | 3 | 35 | 10 | 2 | 14 | 30 | 解毒剂, 布料(有毒液攻击) |
| 哥布林 | 3 | 50 | 14 | 6 | 10 | 35 | 生命药水, 绷带, 铁矿(谨慎AI) |
| 暗熊 | 5 | 100 | 20 | 12 | 6 | 80 | 兽骨, 力量药剂, 皮甲(精英) |

## 地图怪物配置

地图 JSON 中添加 `"monsters"` 数组：

```json
{
  "monsters": [
    {
      "monster_id": "slime",
      "x": 15,
      "y": 12,
      "patrol": [
        {"x": 15, "y": 12},
        {"x": 18, "y": 12}
      ]
    }
  ]
}
```

- `patrol` 可选，有则怪物在路径点间巡逻，无则原地不动
- 村庄地图 `"monsters": []`（安全区）

## API 端点

### GET /api/monsters

返回所有怪物配置（供前端渲染）。

### POST /api/combat/start

发起战斗。

**请求：**
```json
{
  "monster_instance_id": "slime_0",
  "map_id": "forest"
}
```

**响应：**
```json
{
  "session_id": "abc123",
  "monster": {
    "id": "slime",
    "name": "史莱姆",
    "hp": 30,
    "max_hp": 30,
    "sprite_color": "#44cc44",
    "sprite_accent": "#228822"
  },
  "player": {
    "hp": 120,
    "max_hp": 120,
    "mp": 50,
    "max_mp": 50,
    "attack": 24,
    "defense": 18,
    "speed": 10,
    "skills": [
      {"skill_id": "heavy_strike", "name": "重击", "mp_cost": 10, "cooldown": 0, "cooldown_remaining": 0}
    ]
  },
  "phase": "player_turn",
  "log": []
}
```

### POST /api/combat/action

提交战斗动作。

**请求：**
```json
{
  "session_id": "abc123",
  "action": "attack|defend|use_item|skill|flee",
  "item_id": "health_potion",  // 仅 use_item 时需要
  "skill_id": "heavy_strike"   // 仅 skill 时需要
}
```

**响应：**
```json
{
  "session_id": "abc123",
  "phase": "player_turn|victory|defeat",
  "turn_count": 1,
  "player_hp": 113,
  "player_max_hp": 120,
  "monster_hp": 7,
  "monster_max_hp": 30,
  "monster_name": "史莱姆",
  "log": [
    {"type": "player_attack", "text": "你对史莱姆造成 23 点伤害。", "damage": 23, "crit": false, "defended": false},
    {"type": "monster_attack", "text": "史莱姆攻击了你，造成 7 点伤害。", "damage": 7, "crit": false, "defended": false}
  ],
  "player_effects": [],
  "monster_effects": [],
  "exp_reward": 15,
  "gold_reward": 10,
  "drops": [{"item_id": "herb", "quantity": 1}],
  "level_up": false
}
```

### POST /api/combat/end

结束战斗会话，清理资源。

**请求：**
```json
{
  "session_id": "abc123"
}
```

## 战斗流程

1. 玩家在地图上碰到怪物或按 E 键靠近怪物
2. 前端调用 `POST /api/combat/start`
3. 后端创建 CombatSession（内存中），快照玩家属性
4. 前端显示战斗面板，渲染怪物精灵和 HP 条
5. 玩家选择动作，前端调用 `POST /api/combat/action`
6. 后端执行 `resolve_turn()`：
   - 处理玩家状态效果
   - 执行玩家动作
   - 检查怪物是否死亡
   - 处理怪物状态效果
   - 怪物 AI 决策并执行
   - 检查玩家是否死亡
7. 返回结果，前端更新 UI 和战斗日志
8. 重复 5-7 直到战斗结束
9. 胜利：应用 EXP/金币/掉落，检查升级
10. 失败：HP 设为 1，扣除金币
11. 前端调用 `POST /api/combat/end` 清理

## 战斗动作

| 动作 | 效果 |
|------|------|
| 攻击 | 对怪物造成伤害，可能暴击 | 1 |
| 防御 | 本回合减少 50% 受到的伤害 | 2 |
| 技能 | 消耗 MP 释放技能，打开技能选择面板 | 3 |
| 使用物品 | 消耗背包中的消耗品（药水/解毒剂/增益药剂），打开物品选择面板 | 4 |
| 逃跑 | 基于速度的逃跑概率，成功则结束战斗（无奖励） | 5 |

## 状态效果

### 已有效果

| 效果 | 类型 | 效果描述 |
|------|------|----------|
| 中毒 | 持续伤害 | 每回合失去 5% 最大生命值 |
| 灼烧 | 持续伤害 | 每回合失去 3% 最大生命值 |
| 冻结 | 控制 | 无法行动 1 回合 |
| 攻击增强 | 增益 | 攻击力 +N 持续 N 回合 |
| 速度增强 | 增益 | 速度 +N 持续 N 回合 |
| 防御增强 | 增益 | 防御力 +N% 持续 N 回合 |

### 已实现效果（v1.1）

| 效果 | 类型 | 效果描述 |
|------|------|----------|
| 眩晕 | 控制 | 无法行动 1-2 回合，跳过整个回合 |
| 沉默 | 控制 | 无法使用技能 2 回合 |
| 减速 | 属性削弱 | 速度 -30% 持续 3 回合 |
| 流血 | 持续伤害 | 每回合 4% HP × 层数，可叠加 3 层 |
| 护盾 | 吸收 | 吸收 N 点伤害后消失 |
| 再生 | 持续治疗 | 每回合恢复 3% 最大生命值 |
| 反伤 | 反击 | 受击时反弹 20% 伤害，持续 3 回合 |
| 吸血 | 生命偷取 | 造成伤害的 15% 转化为 HP，持续 3 回合 |

### 效果规则

- **叠加**：同类效果默认不叠加，刷新持续时间；流血可叠加至 3 层
- **互斥**：灼烧与冻结互斥（`MUTEX_PAIRS` 定义）
- **护盾**：`player_shield` 独立追踪，伤害先扣护盾再扣 HP
- **反伤**：受击时反弹伤害，`_apply_reflect()` 在伤害结算后触发
- **吸血**：造成伤害时回复 HP，`_apply_lifesteal()` 在伤害结算后触发
- **控制**：眩晕/冻结 → 跳过整个回合；沉默 → 禁止使用技能
- **免疫**：BOSS 眩晕/冻结免疫，精英 BOSS 中毒免疫

### 数据结构

```python
class StatusEffect:
    effect_type: str    # 效果类型 ID
    duration: int       # 剩余回合数
    value: int          # 效果数值
    stack: int          # 当前层数
    source: str         # 来源（skill/item/monster/talent）
```

## 天赋战斗集成

天赋被动通过 `get_talent_passives()` 传入战斗快照，在 `CombatSession` 中自动触发：

| 触发时机 | 函数 | 说明 |
|----------|------|------|
| 战斗开始 | `_apply_talent_on_combat_start()` | 烟雾弹等 |
| 每回合 | `_apply_talent_conditional()` | HP/MP 条件检查 |
| 每回合 | `_apply_talent_mp_regen()` | 魔力涌流回复 MP |
| 每回合 | `_apply_talent_element_storm()` | 元素风暴自动释放 |
| 玩家攻击 | `_apply_talent_on_attack()` | 吸血/流血/眩晕 |
| 玩家攻击 | `_apply_talent_skill_enhance()` | 技能强化 |
| 击杀怪物 | `_apply_talent_on_kill()` | 恢复 HP/攻击力提升 |
| 玩家闪避 | `_apply_talent_on_dodge()` | 影分身反击 |
| 玩家防御 | `_apply_talent_defend_boost()` | 不屈意志提升减伤 |
| 致命伤害 | `_apply_talent_last_stand()` | 坚韧保留 1 HP |

## 可用物品

| 物品 | 效果 |
|------|------|
| 生命药水 | 恢复 30 HP |
| 强效生命药水 | 恢复 80 HP |
| 绷带 | 恢复 15 HP |
| 小型魔力药水 | 恢复 20 MP |
| 魔力药水 | 恢复 50 MP |
| 大型魔力药水 | 恢复 100 MP |
| 解毒剂 | 解除中毒 |
| 净化药水 | 解除诅咒 |
| 力量药剂 | 攻击 +5 持续 3 回合 |
| 速度药剂 | 速度 +5 持续 3 回合 |

## 文件清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `config/monsters.json` | 怪物定义 |
| `backend/combat_engine.py` | 战斗引擎核心逻辑 |
| `frontend/js/combat.js` | 前端战斗 UI 和地图怪物 |
| `docs/combat_system.md` | 本文档 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `config/maps/forest.json` | 添加 monsters 数组 |
| `config/maps/village.json` | 添加空 monsters 数组 |
| `backend/main.py` | 添加战斗 API 端点 |
| `frontend/index.html` | 添加战斗面板 HTML 和 script 标签 |
| `frontend/css/style.css` | 添加战斗相关样式 |
| `frontend/js/game.js` | 集成怪物渲染和更新 |
| `frontend/js/player.js` | 添加 combatOpen 守卫和怪物碰撞检测 |
| `frontend/js/npc.js` | 添加 combatOpen 守卫 |
| `frontend/js/inventory.js` | 添加 combatOpen 守卫 |
| `frontend/js/player_info.js` | 添加 combatOpen 守卫 |
| `frontend/js/dialogue.js` | 添加 combatOpen 守卫 |
| `frontend/js/help.js` | 添加 combatOpen 守卫 |

## 技能系统

技能配置在 `config/skills.json`，每个职业拥有专属技能。玩家通过使用技能书学习技能，技能消耗 MP，有冷却回合限制。

### 技能列表

| 技能 | 职业 | 等级 | MP | 冷却 | 类型 | 效果 |
|------|------|------|----|------|------|------|
| 重击 | 战士 | 1 | 10 | 0 | 伤害 | 1.5× 物理伤害 |
| 盾墙 | 战士 | 3 | 15 | 3 | 增益 | 3回合防御+50% |
| 狂暴 | 战士 | 5 | 20 | 5 | 增益 | 3回合攻击+30%，防御-20% |
| 背刺 | 盗贼 | 1 | 12 | 0 | 伤害 | 1.8× 物理伤害，暴击率提升 |
| 毒刃 | 盗贼 | 3 | 15 | 2 | 伤害 | 1.2× 伤害，50%概率中毒3回合 |
| 闪避 | 盗贼 | 5 | 10 | 4 | 增益 | 2回合闪避率+30% |
| 火球术 | 法师 | 1 | 15 | 0 | 伤害 | 1.5× 魔法伤害，30%概率灼烧 |
| 治愈术 | 法师 | 1 | 20 | 3 | 治疗 | 恢复40 HP |
| 冰冻术 | 法师 | 3 | 18 | 2 | 伤害 | 1.3× 魔法伤害，50%概率冻结1回合 |
| 魔力护盾 | 法师 | 5 | 15 | 4 | 增益 | 3回合受到伤害减少30% |
| 雷霆一击 | 通用 | 8 | 25 | 3 | 伤害 | 2.0× 魔法伤害，无视50%防御 |

### 技能书获取

各NPC商店出售对应职业的技能书。导师艾尔文（skill_master）提供所有技能书，并可直接传授技能（无需购买技能书，学费 = 技能书价格 × 1.5）：

| 技能书 | 学习技能 | 售价 | 适用职业 | 出售NPC |
|--------|----------|------|---------|--------|
| 技能书：重击 | 重击 | 200 | 战士 | 铁匠老王 |
| 技能书：盾墙 | 盾墙 | 250 | 战士 | 铁匠老王 |
| 技能书：狂暴 | 狂暴 | 300 | 战士 | 铁匠老王 |
| 技能书：背刺 | 背刺 | 200 | 盗贼 | 采药人老林 |
| 技能书：毒刃 | 毒刃 | 250 | 盗贼 | 采药人老林 |
| 技能书：闪避 | 闪避 | 300 | 盗贼 | 采药人老林 |
| 技能书：火球术 | 火球术 | 200 | 法师 | 杂货婆刘婶 |
| 技能书：治愈术 | 治愈术 | 200 | 法师 | 杂货婆刘婶/采药人老林/导师艾尔文 |
| 技能书：冰冻术 | 冰冻术 | 250 | 法师 | 杂货婆刘婶/导师艾尔文 |
| 技能书：魔力护盾 | 魔力护盾 | 300 | 法师 | 杂货婆刘婶 |
| 技能书：雷霆一击 | 雷霆一击 | 500 | 通用(Lv.8) | 导师艾尔文 |
| 技能书：旋风斩 | 旋风斩 | 250 | 战士(Lv.4) | 导师艾尔文 |
| 技能书：战吼 | 战吼 | 350 | 战士(Lv.7) | 导师艾尔文 |
| 技能书：毒雾 | 毒雾 | 250 | 盗贼(Lv.4) | 导师艾尔文 |
| 技能书：影袭 | 影袭 | 350 | 盗贼(Lv.7) | 导师艾尔文 |
| 技能书：烈焰风暴 | 烈焰风暴 | 250 | 法师(Lv.4) | 导师艾尔文 |
| 技能书：暴风雪 | 暴风雪 | 350 | 法师(Lv.6) | 导师艾尔文 |
| 技能书：神圣祈祷 | 神圣祈祷 | 500 | 法师(Lv.8) | 导师艾尔文 |

### 技能使用规则

- 战斗中点击「技能」按钮或按快捷键 3 打开技能选择面板
- 技能消耗 MP，MP 不足时按钮禁用
- 技能有冷却回合，冷却中显示剩余回合数
- 伤害类技能受防御力和威力倍率影响
- 魔法伤害公式：`攻击力 × power × 100 / (100 + 防御力 × 0.5)`
- 增益类技能效果有持续时间，到期自动消失

## 扩展路线

### 多敌人战斗 ✅ 已实现

`CombatSession` 支持多个怪物，前端渲染多个怪物卡片，玩家点击选择目标。

**规则：**
- 每组怪物 1-3 只，由地图配置决定
- 玩家攻击和单体技能需选择目标怪物
- AOE 技能命中所有怪物（2 目标 80%，3 目标 65%，4+ 目标 50%）
- 怪物各自独立行动，按速度排序
- 战斗奖励按怪物分别计算

**数据结构扩展：**
```json
{
  "monster_groups": [
    {
      "group_id": "wolf_pack",
      "x": 41, "y": 20,
      "monsters": [
        {"monster_id": "wild_wolf", "count": 2}
      ]
    }
  ]
}
```

**API 响应扩展（monsters 数组）：**
```json
{
  "monsters": [
    {
      "index": 0,
      "monster_id": "wild_wolf",
      "name": "野狼 A",
      "hp": 45, "max_hp": 45,
      "alive": true,
      "level": 2,
      "monster_type": "normal",
      "next_action": "attack",
      "sprite_color": "#888888",
      "sprite_accent": "#555555"
    }
  ]
}
```

### BOSS 战 ✅ 已实现

`type: "boss"` 怪物支持：
- 阶段转换（HP 阈值触发：75% / 50% / 25%）
- 每个阶段有独立的 AI 权重和可用技能
- 状态免疫（冻结、眩晕等）
- 狂暴机制（低血量攻击力提升）
- 丰厚奖励（稀有装备、大量经验、唯一掉落）

**BOSS 数据结构：**
```json
{
  "monster_id": "shadow_tree_spirit",
  "type": "boss",
  "phases": [
    {"name": "正常", "hp_threshold": 1.0, "ai": {"attack": 0.5, "defend": 0.3, "special": 0.2}},
    {"name": "愤怒", "hp_threshold": 0.5, "ai": {"attack": 0.7, "defend": 0.1, "special": 0.2}, "stat_boost": {"attack": 1.3}},
    {"name": "狂暴", "hp_threshold": 0.25, "ai": {"attack": 0.8, "defend": 0.0, "special": 0.2}, "stat_boost": {"attack": 1.5}}
  ]
}
```

**BOSS 列表：**

| BOSS | 等级 | 位置 | 阶段数 | 特殊机制 |
|------|------|------|--------|----------|
| 暗影树精 | 8 | 幽暗森林深处 | 3 | 召唤树苗小怪 |
| 骷髅王 | 12 | 幽暗洞穴核心区 | 3 | 阶段转换时回血 |

---

## 怪物意图系统

### 概述

怪物意图系统在每回合开始时预计算每个存活怪物的下一步行动，并通过 API 返回给前端，在怪物卡片上显示意图图标，让玩家能够预判怪物行为。

### 意图类型

| 意图 | 图标 | 说明 |
|------|------|------|
| attack | ⚔️ | 怪物将攻击玩家 |
| defend | 🛡️ | 怪物将进入防御姿态 |
| special | ✨ | 怪物将使用特殊技能 |

### 实现方式

- 后端在 `_build_state()` 中调用 `decide_action()` 预计算每个存活怪物的 `next_action`
- `MonsterInstance.to_dict(next_action)` 将意图数据包含在返回的怪物信息中
- 前端优先使用后端返回的 `next_action`，回退到前端 `guessMonsterIntent()` 猜测

### 决策逻辑

怪物 AI 根据以下因素决定行动：
1. **AI 权重**：`attack_weight`、`defend_weight`、`special_weight`
2. **行为模式**：`aggressive`（偏好攻击）、`cautious`（低血量防御）、`defensive`（偏好防御）
3. **BOSS 阶段**：不同阶段有不同的 AI 权重
4. **特殊技能**：无特殊技能时，special 权重合并到 attack

---

## 战斗 UI 优化

### 怪物卡片增强

| 新增元素 | 说明 |
|----------|------|
| 等级显示 | `Lv.X` 显示怪物等级 |
| 类型标记 | 精英 ★（金色）、BOSS ♛（红色） |
| 意图图标 | ⚔️/🛡️/✨ 预判怪物下回合行动 |
| 状态效果中文化 | ☠️中毒(3)、🔥灼烧(2) 等图标+中文名 |
| 选中指示器 | 底部箭头 ▲ 替代右上角标签 |

### 玩家状态栏增强

| 新增元素 | 说明 |
|----------|------|
| 玩家头像 | 48×48 像素风格头像（根据职业显示不同颜色） |
| 名称+等级 | 显示玩家名称和等级 |
| 护盾条 | 金色护盾条，有护盾时显示 |
| HP 颜色渐变 | >50% 绿色，25-50% 黄色，<25% 红色 |
| 状态效果图标 | 彩色图标+中文名称 |

### 战斗日志优化

- 与玩家状态栏并排显示（右侧），占据约 60% 宽度
- 日志条目增加类型图标前缀：⚔玩家攻击、🗡怪物攻击、✨技能、🧪物品、☠状态效果、🏆胜利、💀失败

### 战斗结果面板增强

- 增加战斗统计：总回合数、总伤害、最大单次伤害、暴击次数
- 奖励区域增加图标：✨经验值、💰金币、📦掉落
- 等级提升时显示 🎉 等级提升！

### 状态效果中文化映射

| 英文 key | 中文名 | 图标 | 颜色 |
|----------|--------|------|------|
| poison | 中毒 | ☠️ | #88ff88 |
| burn | 灼烧 | 🔥 | #ff8844 |
| freeze | 冻结 | ❄️ | #44ddff |
| stun | 眩晕 | 💫 | #ffff44 |
| silence | 沉默 | 🤐 | #aaaaff |
| bleed | 流血 | 🩸 | #ff4444 |
| speed_down | 减速 | 🐌 | #cc88ff |
| shield | 护盾 | 🛡️ | #ffcc00 |
| regen | 再生 | 💚 | #44ff88 |
| reflect | 反伤 | 🔄 | #ff88ff |
| lifesteal | 吸血 | 🧛 | #cc44ff |
| attack_up | 攻击↑ | ⚔️ | #ff6644 |
| defense_up | 防御↑ | 🛡️ | #4488ff |
| speed_up | 速度↑ | 💨 | #44ffcc |
| defense_down | 防御↓ | 💔 | #ff4488 |
| fear | 恐惧 | 👁️ | #9944cc |
| attack_down | 攻击↓ | 📉 | #cc4444 |
| evasion_up | 闪避↑ | 💨 | #88ffaa |
| damage_reduction | 伤害减免 | 🛡️ | #aaaaff |

---

## 群体技能系统 ✅ 已实现

### 概述

群体技能（AOE）可同时影响多个目标，是多敌人战斗中的核心策略。技能配置中 `aoe: true` 标记为群体技能。

### AOE 伤害递减

| 目标数 | 伤害倍率 |
|--------|----------|
| 1 | 100% |
| 2 | 80% |
| 3 | 65% |
| 4+ | 50% |

递减仅影响伤害数值，附加效果（灼烧/中毒等）对每个目标独立判定概率。

### 玩家群体技能

| 技能 | 职业 | MP | CD | 类型 | 效果 | 等级 |
|------|------|-----|-----|------|------|------|
| 旋风斩 | 战士 | 18 | 2 | 群体伤害 | 1.0× 物理伤害 | 4 |
| 战吼 | 战士 | 25 | 5 | 群体增益 | 攻击+20%，防御+15%，2回合 | 7 |
| 毒雾 | 盗贼 | 20 | 3 | 群体伤害 | 0.6× 伤害，60%中毒2回合 | 4 |
| 影袭 | 盗贼 | 22 | 4 | 群体伤害 | 1.2× 物理伤害，20%眩晕 | 7 |
| 烈焰风暴 | 法师 | 25 | 2 | 群体伤害 | 1.3× 魔法伤害，40%灼烧2回合 | 4 |
| 暴风雪 | 法师 | 30 | 3 | 群体伤害 | 1.1× 魔法伤害，35%冻结1回合 | 6 |
| 神圣祈祷 | 法师 | 35 | 5 | 群体治疗 | 恢复60点生命值 | 8 |

### AOE 战斗日志格式

群体技能按目标分别返回伤害数据：

```json
{
  "type": "skill",
  "aoe": true,
  "targets": [
    {"monster_index": 0, "damage": 18, "crit": false, "effects": ["灼烧"]},
    {"monster_index": 1, "damage": 22, "crit": true, "effects": []}
  ],
  "text": "使用 烈焰风暴！群体魔法攻击！ 野狼 A: 18[灼烧] | 野狼 B: 22(暴击)"
}
```

### 前端 AOE 适配

- **技能面板**：AOE 技能显示橙色 `群体` 标签
- **伤害数字**：按 `targets` 数组分别显示每个怪物的伤害和暴击
- **AOE 动画**：群体技能释放时所有怪物同时闪烁（`aoe-hit-flash`），单体技能仅目标怪物闪烁
- **目标选择**：AOE 技能无需选择目标，直接对所有存活敌人生效

---

## 怪物特殊技能扩展 ✅ 已实现

### 特殊技能类型

| 类型 | 说明 | 配置字段 |
|------|------|----------|
| `apply_effect` | 单体施加效果（原有） | effect, chance, duration, value, message |
| `aoe_attack` | 群体攻击+可选效果 | damage_multiplier, effect, chance, duration, message |
| `self_heal` | 自我治疗 | heal_percent, message |

### aoe_attack 配置示例

```json
{
  "type": "aoe_attack",
  "damage_multiplier": 0.9,
  "effect": "fear",
  "chance": 0.25,
  "duration": 1,
  "message": "骷髅王释放亡灵风暴！"
}
```

### self_heal 配置示例

```json
{
  "type": "self_heal",
  "heal_percent": 0.15,
  "message": "野狼舔舐伤口恢复体力！"
}
```

### BOSS AOE 技能配置

| BOSS | 阶段 | 特殊技能 | 伤害倍率 | 附加效果 |
|------|------|----------|----------|----------|
| 骷髅王 | 正常 | apply_effect (恐惧) | - | 30%恐惧2回合 |
| 骷髅王 | 愤怒 | aoe_attack (亡灵风暴) | 0.9× | 25%恐惧1回合 |
| 骷髅王 | 狂暴 | aoe_attack (毁灭之怒) | 1.2× | 35%恐惧2回合 |
| 暗影树精 | 沉睡 | apply_effect (毒雾) | - | 40%中毒3回合 |
| 暗影树精 | 觉醒 | aoe_attack (暗焰风暴) | 0.8× | 35%灼烧2回合 |
| 暗影树精 | 狂暴 | aoe_attack (暗影震击) | 1.0× | 25%眩晕1回合 |

---

## 已完成优化记录

> 更新日期：2026-05-18

| 优化项 | 说明 | 涉及模块 |
|--------|------|----------|
| 多敌人战斗 | 1-3 个怪物 + BOSS 战，前端支持多槽位点击/Tab 切换目标 | `CombatSession`, `combat.js` |
| BOSS 阶段转换 | HP 阈值触发阶段切换，改变 AI 行为和属性，前端红色闪烁动画 | `MonsterInstance`, `combat.js` |
| BOSS 免疫机制 | BOSS 免疫眩晕/冻结，精英 BOSS 额外免疫中毒 | `effects.py` |
| AOE 技能（玩家） | 7 个群体技能，伤害按目标数递减（1→100%, 2→80%, 3→65%） | `skills.py`, `skills.json` |
| AOE 技能（怪物） | BOSS 支持 `aoe_attack` 类型，前端所有怪物同时闪烁动画 | `monster_ai.py`, `combat.js` |
| 怪物意图系统 | 后端预计算 `next_action`，前端显示意图图标（⚔️/🛡️/✨） | `monster_ai.py`, `combat.js` |
| 状态效果系统 | 16 种效果 + 中文化 + 图标 + 颜色，灼烧/冻结互斥，流血可叠加 3 层 | `effects.py`, `combat.js` |
| 战斗 UI 重构 | 怪物卡片增强（等级/类型/意图）、玩家状态栏（头像/护盾/HP 渐变）、战斗日志优化 | `combat.js`, `style.css` |
| 伤害数字浮动 | 攻击/技能/状态效果分别显示浮动数字，暴击放大显示，AOE 按目标分别显示 | `combat.js` |
| 动画系统 | HP 条平滑过渡、状态效果脉冲、日志淡入、BOSS 阶段闪烁、AOE 全屏闪烁 | `combat.js`, `style.css` |
| 战斗物品面板 | 战斗中可使用消耗品/食物 | `combat.js` |
| 战斗结果统计 | 总回合数、总伤害、暴击次数、最大单次伤害 | `combat.js` |
| 怪物 self_heal | 怪物 AI 支持 `self_heal` 类型特殊技能 | `monster_ai.py` |

**当前模块结构**：
- 后端：`backend/combat/` 8 文件（session/damage/effects/events/monster_ai/skills/turn/engine）
- 前端：`frontend/js/combat.js` — 战斗 UI 完整实现

---

## 相关优化记录

> 以下内容整合自已完成的优化设计文档。

### 战斗引擎模块化重构 ✅ 已完成

将 `combat_engine.py`（约 1050 行）拆分为模块化结构：

```
backend/combat/
├── session.py     # CombatSession + MonsterInstance + 会话管理
├── damage.py      # 伤害计算（含属性克制）
├── effects.py     # 状态效果系统（策略模式）
├── events.py      # 事件驱动系统（词条/天赋触发）
├── monster_ai.py  # 怪物 AI 决策
├── skills.py      # 技能执行
├── turn.py        # 回合解析核心
└── engine.py      # 对外暴露统一接口
```

关键设计：策略模式效果系统（`EffectHandler` 注册机制）、事件驱动系统（`EventDispatcher` + `CombatEvent`）、向后兼容层（`engine.py` 重新导出）。

### 战斗 UI 重构 ✅ 已完成

面板从 520px 扩展到 640px，怪物卡片从 120px 到 160px。新增：等级/类型标记/意图图标/状态效果中文化/玩家头像/护盾条/HP颜色渐变/战斗统计/战斗结果面板增强。

### 多敌人与 BOSS 战 ✅ 已完成

`CombatSession` 支持 1-3 个怪物，BOSS 阶段转换（HP 阈值触发），BOSS 免疫机制，AOE 群体技能（伤害递减），目标选择系统。

### 属性克制系统 ✅ 已完成

火 > 草 > 水 > 火 三角克制（克制 ×1.5，被克制 ×0.67）。所有伤害计算调用点已传入元素参数，怪物/技能配置已添加 element 字段，前端显示元素图标和克制提示。
