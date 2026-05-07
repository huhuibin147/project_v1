# 物品系统设计文档

## 一、系统概述

物品系统为 LLM NPC 游戏增加了经济循环：玩家拥有金币和背包，NPC 拥有商店库存，双方可通过对话驱动或直接操作进行交易。

## 二、核心概念

### 2.1 物品（Item）

物品定义在 `config/items.json` 中，是全局的物品字典。每个 NPC 的商店从这个字典中选取自己要卖的物品。

| 字段 | 说明 |
|------|------|
| `id` | 唯一标识，如 `iron_sword` |
| `name` | 显示名称，如「铁剑」 |
| `type` | 类型：weapon / armor / consumable / food / tool / material |
| `description` | 物品描述 |
| `buy_price` | 商店售价（玩家买入价），0 表示不可购买 |
| `sell_price` | 收购价（玩家卖出价），0 表示不可出售 |
| `stackable` | 是否可叠加 |

### 2.2 NPC 商店（per-NPC 隔离）

每个 NPC 在 `config/npcs.json` 中定义自己的商店，包括：
- 商店名称
- 初始金币
- 初始库存（只包含该 NPC 卖的物品）

**物品不是全局共享的**——铁匠卖武器，杂货婆卖日用品，各自独立。

LLM Prompt 中只注入该 NPC 商店实际有的物品 ID，确保 NPC 不会卖自己没有的东西。

### 2.3 背包（Inventory）

玩家和 NPC 各自拥有独立的背包，包含：
- `items`：物品列表 `[{item_id, quantity}]`
- `gold`：金币数量

每个 NPC 的存档独立：`data/{npc_id}_save.json`，包含该 NPC 对应的玩家背包和商店库存。

### 2.3 交易（Trade）

两种交易方向：
- **购买（buy）**：玩家支付金币，从 NPC 商店获得物品
- **出售（sell）**：玩家交出物品，从 NPC 获得金币

交易前校验：
- 金币是否充足
- 库存是否足够
- 物品是否可买/可卖（价格 > 0）

## 三、配置文件

### 3.1 物品定义：`config/items.json`

所有物品的静态数据，全局共享。

```json
{
  "iron_sword": {
    "id": "iron_sword",
    "name": "铁剑",
    "type": "weapon",
    "description": "一把坚固的铁剑，适合初级冒险者。",
    "buy_price": 80,
    "sell_price": 40,
    "stackable": false
  }
}
```

### 3.2 NPC 商店配置：`config/npcs.json`

每个 NPC 可配置商店库存和初始金币。

```json
{
  "blacksmith": {
    ...
    "shop": {
      "name": "老王铁匠铺",
      "gold": 500,
      "inventory": [
        {"item_id": "iron_sword", "quantity": 3},
        {"item_id": "health_potion", "quantity": 10}
      ]
    },
    "default_gold": 200
  }
}
```

- `shop.gold`：NPC 商店初始金币
- `shop.inventory`：NPC 商店初始库存
- `default_gold`：玩家初始金币

## 四、交易方式

### 4.1 对话驱动交易

玩家在对话中表达交易意图，LLM 自动识别并执行。

**流程**：
1. 玩家输入：「我想买一把铁剑」
2. LLM 返回 `trade_action: {"action": "buy", "item_id": "iron_sword", "quantity": 1}`
3. 后端自动执行交易，返回结果
4. 前端显示交易结果，更新金币和背包

**优点**：沉浸感强，NPC 可以根据好感度调整态度
**示例对话**：

| 玩家说 | NPC 回复（示例） | 交易结果 |
|--------|-----------------|---------|
| 我想买把铁剑 | 行！铁剑 80 金币，给你！ | 购买成功 |
| 有没有好一点的剑 | 精钢剑 200 金币，绝对值！ | 展示商品 |
| 这个太贵了便宜点 | 好吧好吧，看在你是老顾客的份上... | 好感度影响 |
| 我卖你一张狼皮 | 狼皮不错，20 金币收了！ | 出售成功 |

### 4.2 商店面板交易

玩家可通过两种方式打开商店：

**方式一：对话触发**。对话意图为 `trade` 时，对话面板出现「打开商店」按钮，点击后直接打开该 NPC 的商店。

**方式二：背包入口**。按 I 打开背包，点击右上角「商店」按钮，弹出 NPC 选择面板，选择想访问的 NPC 即可打开对应商店。

**流程**：
1. 通过对话或背包入口打开商店面板
2. 点击「购买」或「出售」按钮直接交易
3. 交易结果实时显示

## 五、数据持久化

NPC 和玩家的数据保存在 `data/{npc_id}_save.json`：

```json
{
  "npc_id": "blacksmith",
  "name": "铁匠老王",
  "mood": "高兴",
  "affinity": 65,
  "history": [...],
  "player_inventory": {
    "items": [
      {"item_id": "iron_sword", "quantity": 1},
      {"item_id": "health_potion", "quantity": 3}
    ],
    "gold": 120
  },
  "shop_inventory": {
    "items": [
      {"item_id": "iron_sword", "quantity": 2},
      {"item_id": "health_potion", "quantity": 7}
    ],
    "gold": 580
  }
}
```

## 六、API 接口

所有涉及 NPC 的接口都需要传 `npc_id` 参数（默认 `blacksmith`），实现 NPC 隔离。

### GET /api/npcs

获取所有可用 NPC 列表。

### GET /api/inventory?npc_id=xxx

获取玩家背包（每个 NPC 独立存档）。

**响应**：
```json
{
  "items": [
    {"item_id": "iron_sword", "name": "铁剑", "type": "weapon", "description": "...", "quantity": 1, "buy_price": 80, "sell_price": 40}
  ],
  "gold": 120
}
```

### GET /api/shop?npc_id=xxx

获取指定 NPC 商店库存。

**响应**：
```json
{
  "name": "老王铁匠铺",
  "items": [...],
  "gold": 500
}
```

### POST /api/trade

直接交易接口（不经过 LLM）。

**请求**：
```json
{
  "action": "buy",
  "item_id": "iron_sword",
  "quantity": 1,
  "npc_id": "blacksmith"
}
```

### POST /api/chat

对话接口（扩展版），需要传 `npc_id`。

**请求**：
```json
{
  "message": "我想买把铁剑",
  "npc_id": "blacksmith"
}
```

## 七、物品清单

### 武器
| ID | 名称 | 售价 | 收购价 |
|----|------|------|--------|
| iron_sword | 铁剑 | 80 | 40 |
| steel_sword | 精钢剑 | 200 | 100 |
| iron_dagger | 铁匕首 | 50 | 25 |

### 防具
| ID | 名称 | 售价 | 收购价 |
|----|------|------|--------|
| iron_shield | 铁盾 | 120 | 60 |

### 消耗品
| ID | 名称 | 售价 | 收购价 |
|----|------|------|--------|
| health_potion | 生命药水 | 30 | 15 |
| antidote | 解毒药 | 25 | 12 |
| bandage | 绷带 | 8 | 4 |

### 食物
| ID | 名称 | 售价 | 收购价 |
|----|------|------|--------|
| bread | 面包 | 5 | 2 |
| dried_meat | 肉干 | 12 | 6 |
| wine | 米酒 | 20 | 10 |

### 工具
| ID | 名称 | 售价 | 收购价 |
|----|------|------|--------|
| torch | 火把 | 10 | 5 |
| rope | 绳索 | 15 | 7 |
| candle | 蜡烛 | 5 | 2 |

### 材料（仅可出售给对应 NPC）
| ID | 名称 | 收购价 |
|----|------|--------|
| wolf_pelt | 狼皮 | 20 |
| iron_ore | 铁矿石 | 15 |
| cloth | 棉布 | 7 |
| herb | 草药 | 10 |
| mushroom | 蘑菇 | 8 |

### NPC 商店分配

| NPC | 商店名 | 卖什么 |
|-----|--------|--------|
| 铁匠老王 | 老王铁匠铺 | 武器、防具、工具、药水 |
| 刘婶 | 刘婶杂货铺 | 食物、布料、绷带、蜡烛、工具 |

## 八、前端操作

| 按键 | 功能 |
|------|------|
| I | 打开/关闭背包面板（含商店入口） |
| E | 与 NPC 对话 |
| ESC | 关闭当前面板 |

### 背包面板
- 显示所有持有物品及数量
- 显示当前金币
- 按类型分色：武器(红)、防具(蓝)、消耗品(绿)、工具(黄)、材料(紫)

### 商店面板
- 显示 NPC 商店库存和价格
- 每个物品有「购买」按钮
- 玩家持有的物品额外显示「出售」按钮
- 顶部显示双方金币
- 交易结果实时反馈

## 九、扩展方向

- **装备系统**：物品可装备到角色身上，影响属性
- **物品使用**：消耗品可在背包中直接使用
- **稀有度系统**：普通/稀有/史诗/传说，影响掉率和价格
- **随机掉落**：击败怪物后随机获得物品
- **锻造系统**：收集材料，找铁匠打造高级装备
- **好感度折扣**：好感度越高，NPC 给的折扣越大
