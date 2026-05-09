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
逃跑率 = clamp(10%, 90%, 30% + (速度比 - 1) × 30%)
```

- 速度相同时：30%
- 速度是怪物2倍：60%
- 速度是怪物一半：15%

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

| 效果 | 类型 | 效果描述 |
|------|------|----------|
| 中毒 | 持续伤害 | 每回合失去 5% 最大生命值 |
| 灼烧 | 持续伤害 | 每回合失去 3% 最大生命值 |
| 眩晕 | 控制 | 无法行动（预留） |
| 攻击增强 | 增益 | 攻击力 +N 持续 N 回合 |
| 速度增强 | 增益 | 速度 +N 持续 N 回合 |

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

### 技能使用规则

- 战斗中点击「技能」按钮或按快捷键 3 打开技能选择面板
- 技能消耗 MP，MP 不足时按钮禁用
- 技能有冷却回合，冷却中显示剩余回合数
- 伤害类技能受防御力和威力倍率影响
- 魔法伤害公式：`攻击力 × power × 100 / (100 + 防御力 × 0.5)`
- 增益类技能效果有持续时间，到期自动消失

## 扩展路线

### 多敌人战斗（预留）

将 `CombatSession` 中的单个怪物改为列表，前端渲染多个怪物精灵，玩家点击选择目标。

### BOSS 战（预留）

`type: "boss"` 怪物支持：
- 阶段转换（HP 阈值触发）
- 特殊技能冷却
- 状态免疫
- 多阶段 AI

### 装备词条触发（预留）

装备的 `affixes` 字段支持：
- `on_attack`：攻击时触发（附加火焰伤害、冰冻）
- `on_hit`：被击中时触发（荆棘、护盾）
- `on_kill`：击杀时触发（吸血、经验加成）
- `conditional`：条件触发（低血量增加攻击）

### 任务击杀（预留）

怪物的 `tags` 字段支持任务匹配：
- "击杀 5 只森林怪物" → 检查 `tags.includes("forest")`
- 击杀时检查并更新任务进度
