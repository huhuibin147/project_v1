# 任务系统设计文档

## 概述

任务系统为游戏添加可接取、追踪、完成的主线与支线任务。NPC 通过对话或交互面板下发任务，玩家在探索和战斗中推进任务进度，完成后获得经验、金币和好感度奖励。

## 系统架构

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│  NPC 交互面板 │────▶│  任务接取    │────▶│  任务追踪 UI    │
│  (E键)       │     │  (API)       │     │  (DOM overlay)  │
└──────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                                   ▼
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│  玩家行为    │────▶│  进度更新    │────▶│  任务管理器     │
│  (击杀/采集) │     │  (事件触发)  │     │  (QuestManager) │
└──────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                                   ▼
                                           ┌──────────────┐
                                           │  奖励发放    │
                                           │  (EXP/Gold)  │
                                           └──────────────┘
```

## 任务数据结构

### 任务配置 (`config/quests.json`)

```json
{
  "quest_id": {
    "id": "quest_id",
    "name": "任务名称",
    "description": "任务描述",
    "type": "main|side|daily",
    "npc_id": "blacksmith",
    "prerequisites": {
      "level": 1,
      "quests_completed": [],
      "npc_affinity": 0
    },
    "objectives": [
      {
        "type": "kill",
        "target": "slime",
        "target_tags": [],
        "count": 3,
        "description": "击杀3只史莱姆"
      },
      {
        "type": "collect",
        "item_id": "herb",
        "count": 5,
        "description": "收集5个草药"
      },
      {
        "type": "talk",
        "npc_id": "merchant",
        "description": "与杂货婆刘婶对话"
      },
      {
        "type": "deliver",
        "item_id": "iron_ore",
        "count": 3,
        "target_npc_id": "blacksmith",
        "description": "将3个铁矿交给铁匠老王"
      },
      {
        "type": "explore",
        "map_id": "forest",
        "x": 40,
        "y": 20,
        "radius": 5,
        "description": "探索幽暗森林深处"
      }
    ],
    "rewards": {
      "exp": 50,
      "gold": 100,
      "items": [
        {"item_id": "health_potion", "quantity": 3}
      ],
      "affinity": {
        "npc_id": "blacksmith",
        "value": 10
      }
    },
    "dialogue": {
      "offer": "俺最近需要一些材料，你能帮忙吗？",
      "accept": "好嘞！俺等着你的好消息！",
      "decline": "行吧，俺再找别人。",
      "progress": "还没完成呢？别急，慢慢来。",
      "complete": "太好了！这些正是俺需要的！",
      "reminder": "别忘了帮俺收集那些材料啊。"
    }
  }
}
```

### 任务目标类型

| 类型 | 说明 | 进度触发 |
|------|------|----------|
| kill | 击杀怪物 | 战斗胜利时检查 monster_id 或 tags |
| collect | 收集物品 | 获得物品时检查 item_id（不扣除物品） |
| deliver | 递交物品 | 向目标NPC递交指定物品（扣除物品） |
| talk | 与NPC对话 | 与指定NPC对话时触发 |
| explore | 探索区域 | 到达指定地图坐标附近时触发 |

### 任务类型

| 类型 | 说明 |
|------|------|
| main | 主线任务，有前置任务链 |
| side | 支线任务，可自由接取 |
| daily | 每日任务，每日重置 |

### 任务状态

| 状态 | 说明 |
|------|------|
| locked | 未解锁（前置条件未满足） |
| available | 可接取（满足条件，未接取） |
| active | 已接取，进行中 |
| completed | 已完成 |
| abandoned | 已放弃 |

## 玩家存档中的任务数据

```json
{
  "quests": {
    "active": {
      "quest_id": {
        "status": "active",
        "objectives_progress": [0, 3, false],
        "accepted_at": "2026-05-10 12:00:00"
      }
    },
    "completed": ["quest_id_1", "quest_id_2"],
    "daily_reset": "2026-05-10"
  }
}
```

## API 端点

### GET /api/quests

获取所有任务列表及玩家当前状态。

**响应：**
```json
{
  "quests": [
    {
      "id": "quest_id",
      "name": "任务名称",
      "description": "任务描述",
      "type": "side",
      "npc_id": "blacksmith",
      "npc_name": "铁匠老王",
      "status": "available",
      "objectives": [
        {"type": "kill", "description": "击杀3只史莱姆", "count": 3, "progress": 0}
      ],
      "rewards": {"exp": 50, "gold": 100, "items": [...], "affinity": {...}},
      "can_accept": true
    }
  ]
}
```

### POST /api/quests/accept

接取任务。

**请求：**
```json
{"quest_id": "quest_id"}
```

**响应：**
```json
{
  "success": true,
  "quest": {...},
  "message": "任务已接取！"
}
```

### POST /api/quests/abandon

放弃任务。

**请求：**
```json
{"quest_id": "quest_id"}
```

### POST /api/quests/complete

完成任务并领取奖励（在NPC处交付）。

**请求：**
```json
{"quest_id": "quest_id"}
```

**响应：**
```json
{
  "success": true,
  "rewards": {"exp": 50, "gold": 100, "items": [...], "affinity": 10},
  "message": "任务完成！获得50经验、100金币"
}
```

### GET /api/quests/npc/{npc_id}

获取指定NPC可提供的任务。

### POST /api/quests/progress

内部接口，更新任务进度（由战斗、采集等事件触发）。

**请求：**
```json
{
  "event_type": "kill|collect|talk|explore|deliver",
  "data": {
    "monster_id": "slime",
    "monster_tags": ["forest", "common"],
    "item_id": "herb",
    "npc_id": "merchant",
    "map_id": "forest",
    "x": 40,
    "y": 20
  }
}
```

## 进度触发机制

### 击杀触发

战斗胜利时，`combat_engine.py` 调用 `quest_manager.on_kill(monster_id, monster_tags)`：
- 遍历所有 active 任务
- 检查 objectives 中 type=kill 的目标
- 匹配 monster_id 或 target_tags
- 更新进度

### 收集触发

玩家获得物品时，`player_profile.add_item()` 调用 `quest_manager.on_collect(item_id)`：
- 遍历 active 任务
- 检查 type=collect 的目标
- 进度 = 玩家背包中该物品数量

### 递交触发

玩家与目标NPC交互时，检查是否有 type=deliver 的任务目标：
- 扣除指定物品
- 标记目标完成

### 对话触发

玩家与NPC对话时，`quest_manager.on_talk(npc_id)`：
- 检查 type=talk 的目标
- 自动标记完成

### 探索触发

玩家移动时，前端定期检查位置：
- 调用 `POST /api/quests/progress` 传递位置
- 检查 type=explore 的目标
- 在指定坐标半径内则标记完成

## NPC 交互集成

### 交互面板新增"任务"按钮

NPC 交互面板新增第4个按钮"任务"，快捷键4：

```
┌──────────────────────┐
│  铁匠老王            │
│  ┌────────────────┐  │
│  │ 对话 (1)       │  │
│  │ 任务 (2)       │  │  ← 新增
│  │ 商店 (3)       │  │
│  │ 治疗/技能 (4)  │  │
│  └────────────────┘  │
└──────────────────────┘
```

### 任务面板

点击"任务"后显示该NPC的任务列表：

```
┌──────────────────────────────────┐
│  铁匠老王的任务          [×]    │
│                                  │
│  ★ 铁匠的委托       [接取]     │
│    帮老王收集3个铁矿和5个草药   │
│    奖励: 50经验 100金币         │
│                                  │
│  ✓ 森林危机       [已完成]     │
│    (已完成)                      │
└──────────────────────────────────┘
```

### 任务追踪面板 (HUD)

游戏界面右侧显示当前进行中任务的简要进度：

```
┌─────────────────────┐
│  当前任务           │
│  ─────────────────  │
│  铁匠的委托         │
│  ├ 击杀史莱姆 2/3   │
│  └ 收集草药 3/5     │
│                     │
│  森林探索           │
│  └ 探索森林深处 ✓   │
└─────────────────────┘
```

快捷键 **Q** 打开/关闭完整任务面板。

## 初始任务设计

### 铁匠老王的任务

| 任务ID | 名称 | 类型 | 目标 | 奖励 |
|--------|------|------|------|------|
| blacksmith_ore | 铁匠的委托 | side | 收集3个铁矿 | 30经验, 50金币, 好感+5 |
| blacksmith_wolf | 狼患 | side | 击杀2只野狼 | 50经验, 80金币, 好感+8 |
| blacksmith_bear | 暗熊之威胁 | side | 击杀1只暗熊 | 100经验, 150金币, 好感+15 |

### 杂货婆刘婶的任务

| 任务ID | 名称 | 类型 | 目标 | 奖励 |
|--------|------|------|------|------|
| merchant_herb | 草药收集 | side | 收集5个草药 | 30经验, 40金币, 好感+5 |
| merchant_deliver | 跑腿送货 | side | 将包裹送给祭司阿雅 | 20经验, 30金币, 好感+5 |
| merchant_mushroom | 蘑菇美食 | side | 收集3个蘑菇 | 25经验, 35金币, 好感+5 |

### 采药人老林的任务

| 任务ID | 名称 | 类型 | 目标 | 奖励 |
|--------|------|------|------|------|
| herbalist_herb | 稀有草药 | side | 收集5个草药和2个魔法水晶 | 60经验, 80金币, 好感+10 |
| herbalist_spider | 毒蛛之患 | side | 击杀2只毒蛛 | 50经验, 70金币, 好感+8 |
| herbalist_explore | 森林深处 | side | 探索森林深处区域 | 80经验, 100金币, 好感+12 |

### 祭司阿雅的任务

| 任务ID | 名称 | 类型 | 目标 | 奖励 |
|--------|------|------|------|------|
| priest_purify | 神圣净化 | side | 击杀3只森林怪物(tags:forest) | 40经验, 60金币, 好感+8 |
| priest_deliver | 圣水传递 | side | 将圣水送给采药人老林 | 30经验, 50金币, 好感+10 |

### 导师艾尔文的任务

| 任务ID | 名称 | 类型 | 目标 | 奖励 |
|--------|------|------|------|------|
| skillmaster_test | 初级试炼 | side | 击杀3只史莱姆 | 40经验, 60金币, 好感+5 |
| skillmaster_goblin | 哥布林骚扰 | side | 击杀2只哥布林 | 60经验, 90金币, 好感+10 |
| skillmaster_bone | 骨材收集 | side | 收集2个兽骨 | 50经验, 70金币, 好感+8 |

## 文件清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `config/quests.json` | 任务定义配置 |
| `backend/quest_manager.py` | 任务管理器核心逻辑 |
| `frontend/js/quest.js` | 前端任务UI和交互 |
| `docs/quest_system.md` | 本文档 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `backend/main.py` | 添加任务API端点 |
| `backend/combat_engine.py` | 战斗胜利时触发任务进度更新 |
| `backend/player_profile.py` | 存档中保存任务数据 |
| `backend/npc_agent.py` | 对话时触发talk类型任务进度 |
| `frontend/index.html` | 添加任务面板HTML和script标签 |
| `frontend/css/style.css` | 添加任务相关样式 |
| `frontend/js/npc.js` | NPC交互面板添加"任务"按钮 |
| `frontend/js/game.js` | 集成任务系统初始化 |
| `frontend/js/player.js` | 添加questOpen守卫和Q键绑定 |

## 扩展路线

### 主线任务链

设计完整主线任务链，从新手引导到最终BOSS，每个任务有前置任务要求。

### 每日任务

每日0点重置，提供稳定的经验和金币来源。

### 任务链分支

根据玩家选择（职业、好感度）触发不同的任务分支。

### 隐藏任务

特殊条件触发（如特定时间、特定装备、特定好感度）。
