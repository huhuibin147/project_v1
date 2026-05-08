# 装备系统设计文档

## 一、系统概述

装备系统让玩家可以将武器、防具等物品装备到角色身上，装备后直接影响角色属性（攻击、防御、速度）。与现有物品系统和背包系统无缝集成。

## 二、核心概念

### 2.1 装备槽位

| 槽位 | key | 说明 | 可装备类型 |
|------|-----|------|-----------|
| 武器 | `weapon` | 主手武器 | weapon |
| 盾牌 | `shield` | 副手盾牌 | armor（shield子类） |
| 头部 | `head` | 头盔/帽子 | armor（head子类） |
| 身体 | `body` | 铠甲/衣服 | armor（body子类） |
| 饰品 | `accessory` | 戒指/项链 | accessory |

### 2.2 装备属性加成

每件装备定义 `stats` 字段，包含属性加成：

```json
{
  "attack": 5,
  "defense": 3,
  "speed": -1,
  "max_hp": 0
}
```

- 正值表示增加，负值表示减少（如重甲降低速度）
- 装备后加成叠加到角色基础属性
- 卸下装备后减去加成

### 2.3 属性计算公式

```
实际属性 = 职业基础属性 + 等级成长 + 装备加成总和
```

示例：
```
战士 Lv.3
基础攻击 = 15 + (3-1)*3 = 21
装备加成 = 铁剑(+8) + 铁盾(+2) = +10
实际攻击 = 21 + 10 = 31
```

## 三、数据结构

### 3.1 物品配置扩展（items.json）

在现有物品定义中新增 `equip_slot` 和 `stats` 字段：

```json
{
  "iron_sword": {
    "id": "iron_sword",
    "name": "铁剑",
    "type": "weapon",
    "description": "一把坚固的铁剑，适合初级冒险者。",
    "buy_price": 80,
    "sell_price": 40,
    "stackable": false,
    "equip_slot": "weapon",
    "stats": {
      "attack": 8,
      "defense": 0,
      "speed": 0,
      "max_hp": 0
    }
  },
  "steel_sword": {
    "id": "steel_sword",
    "name": "精钢剑",
    "type": "weapon",
    "description": "用精钢打造的利剑，锋利无比。",
    "buy_price": 200,
    "sell_price": 100,
    "stackable": false,
    "equip_slot": "weapon",
    "stats": {
      "attack": 15,
      "defense": 0,
      "speed": 0,
      "max_hp": 0
    }
  },
  "iron_dagger": {
    "id": "iron_dagger",
    "name": "铁匕首",
    "type": "weapon",
    "description": "轻便的匕首，适合快速攻击。",
    "buy_price": 50,
    "sell_price": 25,
    "stackable": false,
    "equip_slot": "weapon",
    "stats": {
      "attack": 5,
      "defense": 0,
      "speed": 3,
      "max_hp": 0
    }
  },
  "iron_shield": {
    "id": "iron_shield",
    "name": "铁盾",
    "type": "armor",
    "description": "厚实的铁盾，能挡住不少伤害。",
    "buy_price": 120,
    "sell_price": 60,
    "stackable": false,
    "equip_slot": "shield",
    "stats": {
      "attack": 0,
      "defense": 6,
      "speed": -2,
      "max_hp": 0
    }
  },
  "leather_armor": {
    "id": "leather_armor",
    "name": "皮甲",
    "type": "armor",
    "description": "轻便的皮甲，提供基础防护。",
    "buy_price": 100,
    "sell_price": 50,
    "stackable": false,
    "equip_slot": "body",
    "stats": {
      "attack": 0,
      "defense": 4,
      "speed": 0,
      "max_hp": 10
    }
  },
  "iron_helmet": {
    "id": "iron_helmet",
    "name": "铁盔",
    "type": "armor",
    "description": "沉重的铁盔，保护头部。",
    "buy_price": 90,
    "sell_price": 45,
    "stackable": false,
    "equip_slot": "head",
    "stats": {
      "attack": 0,
      "defense": 3,
      "speed": -1,
      "max_hp": 5
    }
  },
  "ring_of_power": {
    "id": "ring_of_power",
    "name": "力量戒指",
    "type": "accessory",
    "description": "蕴含力量的神秘戒指。",
    "buy_price": 300,
    "sell_price": 150,
    "stackable": false,
    "equip_slot": "accessory",
    "stats": {
      "attack": 3,
      "defense": 1,
      "speed": 1,
      "max_hp": 0
    }
  }
}
```

不可装备的物品（消耗品、食物、工具、材料）不包含 `equip_slot` 和 `stats` 字段。

### 3.2 玩家存档扩展（player.json）

新增 `equipment` 字段：

```json
{
  "name": "冒险者",
  "class_id": "warrior",
  "level": 3,
  "equipment": {
    "weapon": "iron_sword",
    "shield": "iron_shield",
    "head": null,
    "body": "leather_armor",
    "accessory": null
  }
}
```

- 每个槽位存储物品ID或null
- 装备时从背包移除，卸下时归还背包

### 3.3 NPC商店扩展（npcs.json）

为铁匠和商人添加新的装备类物品到商店库存。

## 四、后端API

### 4.1 装备物品

```
POST /api/equip
Body: { "item_id": "iron_sword" }
Response: {
  "success": true,
  "message": "装备了铁剑",
  "equipment": { "weapon": "iron_sword", ... },
  "unequipped": { "slot": "weapon", "item_id": "old_sword" },  // 如果有替换
  "player_attack": 23,
  "player_defense": 14,
  "player_speed": 8,
  "player_max_hp": 120,
  "player_inventory": [...]
}
```

逻辑：
1. 检查物品是否在背包中
2. 检查物品是否可装备（有equip_slot字段）
3. 如果目标槽位已有装备，先卸下旧装备归还背包
4. 从背包移除新装备
5. 装备到目标槽位
6. 重新计算属性

### 4.2 卸下装备

```
POST /api/unequip
Body: { "slot": "weapon" }
Response: {
  "success": true,
  "message": "卸下了铁剑",
  "equipment": { "weapon": null, ... },
  "player_attack": 15,
  "player_defense": 12,
  "player_speed": 8,
  "player_max_hp": 120,
  "player_inventory": [...]
}
```

逻辑：
1. 检查槽位是否有装备
2. 将装备归还背包
3. 清空槽位
4. 重新计算属性

### 4.3 获取装备信息

```
GET /api/equipment
Response: {
  "equipment": {
    "weapon": { "item_id": "iron_sword", "name": "铁剑", "stats": {...} },
    "shield": null,
    "head": null,
    "body": { "item_id": "leather_armor", "name": "皮甲", "stats": {...} },
    "accessory": null
  },
  "base_stats": { "attack": 21, "defense": 16, "speed": 10, "max_hp": 140 },
  "equip_bonus": { "attack": 8, "defense": 10, "speed": -2, "max_hp": 10 },
  "total_stats": { "attack": 29, "defense": 26, "speed": 8, "max_hp": 150 }
}
```

### 4.4 修改现有API

`GET /api/player` 和 `GET /api/inventory` 返回中增加装备信息。

## 五、后端实现

### 5.1 PlayerProfile 修改

```python
# 新增属性
self.equipment = {
    "weapon": None,
    "shield": None,
    "head": None,
    "body": None,
    "accessory": None,
}

# 新增方法
def equip_item(self, item_id: str) -> dict:
    """装备物品"""
    
def unequip_slot(self, slot: str) -> dict:
    """卸下装备"""
    
def get_equipment(self) -> dict:
    """获取装备信息"""
    
def _calc_equip_bonus(self) -> dict:
    """计算装备加成总和"""
    
def _recalc_stats(self):
    """重新计算属性 = 基础 + 等级成长 + 装备加成"""
```

### 5.2 属性重算逻辑

```python
def _recalc_stats(self):
    cls = self.classes[self.class_id]
    level_bonus = self.level - 1
    
    base_attack = cls["base_attack"] + level_bonus * 3
    base_defense = cls["base_defense"] + level_bonus * 2
    base_speed = cls["base_speed"] + level_bonus * 1
    base_max_hp = cls["base_hp"] + level_bonus * 10
    
    bonus = self._calc_equip_bonus()
    
    self.attack = base_attack + bonus["attack"]
    self.defense = base_defense + bonus["defense"]
    self.speed = base_speed + bonus["speed"]
    self.max_hp = base_max_hp + bonus["max_hp"]
    self.hp = min(self.hp, self.max_hp)
```

### 5.3 存档兼容

旧存档没有 `equipment` 字段，加载时使用默认空装备：

```python
self.equipment = data.get("equipment", {
    "weapon": None, "shield": None,
    "head": None, "body": None, "accessory": None,
})
```

## 六、前端UI

### 6.1 装备面板

在角色信息面板（P键）中新增装备区域，位于属性区域上方：

```
┌─────────────────────────────────┐
│  角色信息                    ×  │
├─────────────────────────────────┤
│  [剑] 冒险者    Lv.3  战士     │
├─────────────────────────────────┤
│  ── 装备 ──                     │
│  武器: [铁剑    ] 攻+8    [卸] │
│  盾牌: [空      ]         [  ] │
│  头部: [铁盔    ] 防+3    [卸] │
│  身体: [皮甲    ] 防+4 HP+10 [卸] │
│  饰品: [空      ]         [  ] │
├─────────────────────────────────┤
│  HP  ████████████ 120/130      │
│  EXP ██████       45/150       │
├─────────────────────────────────┤
│  攻击: 29 (+8)  防御: 26 (+10) │
│  速度: 8  (-2)  HP:   130(+10) │
└─────────────────────────────────┘
```

### 6.2 背包面板增强

背包中的可装备物品显示「装备」按钮：

```
┌─────────────────────────────────┐
│  铁剑                           │
│  武器 | 攻+8 速+0               │
│  一把坚固的铁剑...              │
│  [装备]  出售价: 40金           │
└─────────────────────────────────┘
```

### 6.3 商店面板增强

商店中的装备物品显示属性加成：

```
┌─────────────────────────────────┐
│  精钢剑                         │
│  武器 | 攻+15                   │
│  用精钢打造的利剑...            │
│  售价: 200金  [购买]            │
└─────────────────────────────────┘
```

### 6.4 装备提示

- 装备成功：绿色提示「装备了铁剑」
- 卸下成功：绿色提示「卸下了铁剑」
- 装备替换：黄色提示「卸下了旧剑，装备了铁剑」
- 装备失败：红色提示「该物品无法装备」

## 七、新增物品清单

为铁匠商店和商人商店添加更多装备：

| 物品ID | 名称 | 类型 | 槽位 | 属性加成 | 售价 |
|--------|------|------|------|---------|------|
| leather_armor | 皮甲 | armor | body | 防+4 HP+10 | 100 |
| iron_helmet | 铁盔 | armor | head | 防+3 速-1 HP+5 | 90 |
| ring_of_power | 力量戒指 | accessory | accessory | 攻+3 防+1 速+1 | 300 |
| steel_shield | 精钢盾 | armor | shield | 防+10 速-3 | 250 |
| mage_staff | 法师杖 | weapon | weapon | 攻+10 速+2 | 150 |
| hunter_bow | 猎人弓 | weapon | weapon | 攻+7 速+4 | 120 |
| cloth_robe | 布袍 | armor | body | 防+1 速+1 HP+5 | 60 |
| iron_armor | 铁甲 | armor | body | 防+8 速-3 HP+20 | 280 |

## 八、NPC商店更新

### 铁匠老王（blacksmith）

```json
"inventory": [
  {"item_id": "iron_sword", "quantity": 3},
  {"item_id": "steel_sword", "quantity": 1},
  {"item_id": "iron_dagger", "quantity": 2},
  {"item_id": "iron_shield", "quantity": 2},
  {"item_id": "steel_shield", "quantity": 1},
  {"item_id": "iron_helmet", "quantity": 2},
  {"item_id": "iron_armor", "quantity": 1},
  {"item_id": "leather_armor", "quantity": 2},
  {"item_id": "health_potion", "quantity": 10}
]
```

### 刘婶（merchant）

```json
"inventory": [
  {"item_id": "bread", "quantity": 20},
  {"item_id": "dried_meat", "quantity": 10},
  {"item_id": "wine", "quantity": 5},
  {"item_id": "bandage", "quantity": 15},
  {"item_id": "antidote", "quantity": 8},
  {"item_id": "cloth_robe", "quantity": 2},
  {"item_id": "torch", "quantity": 10},
  {"item_id": "rope", "quantity": 5}
]
```

## 九、实现步骤

1. ~~**items.json** - 为现有物品添加 `equip_slot` 和 `stats`，新增装备物品~~ ✅
2. ~~**player_profile.py** - 添加 `equipment` 属性、装备/卸载方法、属性重算~~ ✅
3. ~~**main.py** - 添加 `/api/equip`、`/api/unequip`、`/api/equipment` 接口~~ ✅
4. ~~**npcs.json** - 更新NPC商店库存~~ ✅
5. ~~**index.html** - 添加装备面板HTML结构~~ ✅
6. ~~**style.css** - 装备面板样式~~ ✅
7. ~~**player_info.js** - 装备面板渲染和交互逻辑~~ ✅
8. ~~**inventory.js** - 背包中添加装备按钮~~ ✅
9. ~~**测试** - 装备/卸载/替换/属性计算/存档兼容~~ ✅

## 十、实现记录

### 后端实现

**player_profile.py** 修改：
- 新增 `EQUIP_SLOTS` 和 `DEFAULT_EQUIPMENT` 常量
- 新增 `equipment` 属性（5个槽位：weapon/shield/head/body/accessory）
- 新增 `_calc_equip_bonus()` 计算装备加成总和
- 新增 `_recalc_stats()` 重新计算属性 = 基础 + 等级成长 + 装备加成
- 新增 `equip_item(item_id)` 装备物品，支持替换旧装备
- 新增 `unequip_slot(slot)` 卸下装备，归还背包
- 新增 `_get_equipment_detail()` 获取装备详情
- 新增 `get_equipment_info()` 获取完整装备信息（含基础/加成/总计属性）
- 存档兼容：旧存档无 `equipment` 字段时使用默认空装备

**main.py** 修改：
- 新增 `EquipRequest` 和 `UnequipRequest` 请求模型
- 新增 `GET /api/equipment` 获取装备信息
- 新增 `POST /api/equip` 装备物品
- 新增 `POST /api/unequip` 卸下装备

**item_system.py** 修改：
- `Inventory.to_list()` 新增 `equip_slot` 和 `stats` 字段返回

**items.json** 修改：
- 所有武器/防具/饰品新增 `equip_slot` 和 `stats` 字段
- 新增物品：steel_sword、iron_dagger、mage_staff、hunter_bow、steel_shield、iron_helmet、leather_armor、iron_armor、cloth_robe、ring_of_power

**npcs.json** 修改：
- 铁匠老王商店新增：mage_staff、hunter_bow、steel_shield、iron_helmet、leather_armor、iron_armor、ring_of_power
- 刘婶杂货铺新增：cloth_robe

### 前端实现

**index.html** 修改：
- 角色信息面板新增装备区域（5个槽位，每个含名称、属性加成、卸下按钮）
- 属性区域新增装备加成显示（攻击/防御/速度后的绿色/红色括号数值）

**style.css** 修改：
- 新增装备槽样式（equip-grid、equip-slot、equip-slot-label 等）
- 新增装备/卸下按钮样式（btn-equip、btn-unequip）
- 新增属性加成显示样式（pi-stat-bonus、stat-neg）
- 新增物品属性行样式（item-stats-line）
- 角色信息面板宽度从 340px 调整为 380px，支持滚动

**player_info.js** 重写：
- 新增 `equipBonus` 状态对象跟踪装备加成
- 新增 `fetchEquipmentInfo()` 从 `/api/equipment` 获取装备数据
- 新增 `renderEquipment()` 渲染5个装备槽位
- 新增 `renderStatBonus()` 渲染属性加成显示
- 新增 `formatStatsText()` 格式化属性加成文本
- 新增 `doEquip(itemId)` 调用装备API
- 新增 `doUnequip(slot)` 调用卸下API
- 新增 `showEquipMessage()` 显示装备操作反馈

**inventory.js** 修改：
- 背包物品卡片新增装备按钮（可装备物品显示"装备"按钮，已装备物品显示"已装备"标签）
- 背包物品卡片新增属性加成显示
- 商店物品卡片新增属性加成显示和槽位信息
- 新增 `isItemEquipped()` 判断物品是否已装备
- 新增 `getSlotLabel()` 获取槽位中文名
- 新增 `formatItemStats()` 格式化物品属性
- `getTypeLabel()` 新增 accessory 类型
