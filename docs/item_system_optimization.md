# 物品系统优化设计

## 一、优化目标

### 1.1 当前问题
- **物品效果硬编码**：`ITEM_EFFECTS` 字典写死在代码中，新增物品需修改代码
- **缺少物品分类**：所有物品平铺在一个 JSON 中，缺少分类管理
- **物品堆叠逻辑简单**：只按 `item_id` 堆叠，未区分实例化物品（带词条的装备）

### 1.2 优化目标
- 将物品效果移到 `items.json` 配置中，实现数据驱动
- 添加物品分类系统，支持按类别查询和管理
- 区分可堆叠物品和不可堆叠物品（装备类不堆叠）

## 二、设计方案

### 2.1 物品效果配置化

**设计思路**：
- 将 `ITEM_EFFECTS` 字典移到 `items.json` 中
- 每个物品配置增加 `effect` 字段
- 支持多种效果类型：heal, restore_mp, cure, buff, learn_skill

**实现方案**：
```json
{
  "health_potion": {
    "id": "health_potion",
    "name": "生命药水",
    "type": "consumable",
    "description": "恢复少量生命值。",
    "buy_price": 30,
    "sell_price": 15,
    "stackable": true,
    "effect": {
      "type": "heal",
      "value": 30
    }
  },
  "scroll_heavy_strike": {
    "id": "scroll_heavy_strike",
    "name": "技能书：重击",
    "type": "skill_book",
    "description": "学习重击技能。",
    "buy_price": 100,
    "sell_price": 50,
    "stackable": false,
    "effect": {
      "type": "learn_skill",
      "skill_id": "heavy_strike"
    }
  }
}
```

### 2.2 物品分类系统

**设计思路**：
- 在 `items.json` 中为每个物品添加 `category` 字段
- 支持分类：consumable（消耗品）、equipment（装备）、material（材料）、skill_book（技能书）、food（食物）、quest_item（任务物品）
- 提供按分类查询的 API

**实现方案**：
```python
ITEM_CATEGORIES = {
    "consumable": "消耗品",
    "equipment": "装备",
    "material": "材料",
    "skill_book": "技能书",
    "food": "食物",
    "quest_item": "任务物品",
}

def get_items_by_category(category: str) -> list[dict]:
    """按分类获取物品"""
    return [
        {**item, "id": item_id}
        for item_id, item in ITEMS_DB.items()
        if item.get("category") == category
    ]

def get_all_categories() -> list[dict]:
    """获取所有分类"""
    return [
        {"id": cat_id, "name": cat_name}
        for cat_id, cat_name in ITEM_CATEGORIES.items()
    ]
```

### 2.3 堆叠逻辑优化

**设计思路**：
- 使用 `stackable` 字段区分可堆叠和不可堆叠物品
- 可堆叠物品：消耗品、材料、食物等，按 `item_id` 堆叠
- 不可堆叠物品：装备、技能书等，每个物品独立实例
- 装备类物品支持 `instance_affixes` 和 `instance_rarity` 字段

**实现方案**：
```python
def add_item(self, item_id: str, quantity: int = 1, instance_data: dict = None):
    """添加物品到背包"""
    item_info = ITEMS_DB.get(item_id)
    if not item_info:
        return False
    
    stackable = item_info.get("stackable", True)
    
    if stackable and instance_data is None:
        # 可堆叠物品：合并数量
        for item in self.items:
            if item["item_id"] == item_id:
                item["quantity"] += quantity
                return True
        self.items.append({"item_id": item_id, "quantity": quantity})
    else:
        # 不可堆叠物品：每个实例独立
        for _ in range(quantity):
            item_instance = {
                "item_id": item_id,
                "quantity": 1,
            }
            if instance_data:
                item_instance.update(instance_data)
            self.items.append(item_instance)
    
    return True

def remove_item(self, item_id: str, quantity: int = 1) -> bool:
    """从背包移除物品"""
    item_info = ITEMS_DB.get(item_id)
    if not item_info:
        return False
    
    stackable = item_info.get("stackable", True)
    
    if stackable:
        # 可堆叠物品：减少数量
        for item in self.items:
            if item["item_id"] == item_id:
                if item["quantity"] < quantity:
                    return False
                item["quantity"] -= quantity
                if item["quantity"] == 0:
                    self.items.remove(item)
                return True
    else:
        # 不可堆叠物品：移除指定数量的实例
        removed = 0
        items_to_remove = []
        for item in self.items:
            if item["item_id"] == item_id:
                items_to_remove.append(item)
                removed += 1
                if removed >= quantity:
                    break
        
        if removed < quantity:
            return False
        
        for item in items_to_remove:
            self.items.remove(item)
    
    return True
```

## 三、架构设计

### 3.1 模块划分
```
item_system.py
├── ITEMS_DB          # 物品数据库（从 items.json 加载）
├── ITEM_CATEGORIES   # 物品分类定义
├── Inventory         # 背包类（优化堆叠逻辑）
├── TradeResult       # 交易结果
├── buy_item()        # 购买物品
├── sell_item()       # 出售物品
├── get_item_info()   # 查询物品信息
├── get_items_by_category()  # 按分类查询
└── get_all_categories()     # 获取所有分类
```

### 3.2 数据流
```
玩家操作 → 检查物品类型 → 可堆叠？ → 合并数量
                        ↓ 否
                    创建独立实例（带词条/稀有度）
                        ↓
                    添加到背包
```

## 四、实现阶段

### Phase 1: 物品效果配置化
- 将 `ITEM_EFFECTS` 数据迁移到 `items.json`
- 修改 `item_system.py` 从配置读取效果
- 更新 `Inventory.to_list()` 使用配置中的效果

### Phase 2: 物品分类系统
- 为所有物品添加 `category` 字段
- 实现按分类查询功能
- 添加分类 API 路由

### Phase 3: 堆叠逻辑优化
- 修改 `Inventory.add_item()` 支持实例化物品
- 修改 `Inventory.remove_item()` 区分堆叠逻辑
- 更新前端显示逻辑

## 五、预期效果

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 物品效果管理 | 代码硬编码 | 配置驱动 | 新增物品无需改代码 |
| 物品分类 | 无 | 6 大分类 | 支持按类别查询 |
| 堆叠逻辑 | 简单按 ID | 区分可堆叠/不可堆叠 | 装备独立实例化 |
| 配置维护性 | 低（需改代码） | 高（仅改 JSON） | 维护成本降低 80% |

---

## 六、完成状态

> 更新日期：2026-05-18
> 状态：✅ 全部完成

| 优化项 | 状态 | 说明 |
|--------|------|------|
| 物品效果配置化 | ✅ 完成 | `ITEM_EFFECTS` 移至 `items.json` 的 `effect` 字段，新增 `get_item_effect()` 辅助函数 |
| 物品分类系统 | ✅ 完成 | 添加 `category` 字段（consumable/food/skill_book/material/equipment/quest_item），支持 `get_items_by_category()` |
| 堆叠逻辑优化 | ✅ 完成 | `Inventory.add_item()` 区分可堆叠/不可堆叠物品，装备类不堆叠独立实例化 |
| 代码兼容 | ✅ 完成 | 更新 `combat_engine.py`、`player_profile.py`、`combat/turn.py`、`test_backend_logic.py` 中的引用 |

**新增文件**：无（仅在 `items.json` 和 `item_system.py` 中修改）
