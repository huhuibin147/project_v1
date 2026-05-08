# 物品生成器

`tools/item_generator.py` — 用于批量生成游戏物品和NPC商店库存。

## 功能概览

1. **装备生成**：按等级段（初级/中级/高级）生成武器、防具、饰品
2. **消耗品/材料/食物/工具生成**：批量生成非装备物品
3. **NPC商店分配**：根据NPC角色自动分配对应等级段的物品
4. **数据验证**：检查物品数据完整性
5. **预览**：查看物品属性分布和价格

## 使用方法

```bash
cd tools

# 生成装备（预览，不写入文件）
python item_generator.py generate equip tier1       # 初级装备
python item_generator.py generate equip tier2       # 中级装备
python item_generator.py generate equip tier3       # 高级装备
python item_generator.py generate equip all         # 所有等级段装备

# 生成其他类型物品
python item_generator.py generate consumable        # 消耗品
python item_generator.py generate material          # 材料
python item_generator.py generate food              # 食物
python item_generator.py generate tool              # 工具
python item_generator.py generate all               # 所有类型

# 应用到 items.json（跳过已存在的物品）
python item_generator.py apply

# 更新NPC商店库存
python item_generator.py shop blacksmith            # 铁匠老王
python item_generator.py shop merchant              # 杂货婆刘婶
python item_generator.py shop herbalist             # 采药人老林
python item_generator.py shop all                   # 所有NPC

# 验证和预览
python item_generator.py validate                   # 验证数据
python item_generator.py list                       # 列出所有物品
python item_generator.py preview                    # 属性分布预览
```

## 等级段定义

| 等级段 | key | 适用等级 | 价格倍率 | 典型材质 |
|--------|-----|---------|---------|---------|
| 初级 | tier1 | 1-4 | ×1.0 | 木、石、铜、铁、皮 |
| 中级 | tier2 | 5-9 | ×2.5 | 精钢、银、硬皮、合金、青铜 |
| 高级 | tier3 | 10-15 | ×6.0 | 秘银、暗金、龙皮、魔晶、玄铁 |

## 属性计算公式

```
总预算 = 等级中值 × 1.5
单项属性 = 总预算 × 权重（max_hp 额外 ×3）
价格 = (攻击×10 + 防御×8 + 速度×6 + HP×2 - 负面属性×3) × 等级倍率
```

## 装备模板

每个装备模板指定了名称、ID、等级段、类型、槽位、属性权重和描述，避免不合理的组合（如"皮剑"）。

### 武器（20件）

| 初级 | 中级 | 高级 |
|------|------|------|
| 木剑、石剑、铜剑、铁剑 | 精钢剑、银匕首、银弓 | 秘银剑、暗金匕首、玄铁弓 |
| 铁匕首、猎人弓、法师杖、铁斧 | 合金法杖、精钢斧、青铜锤 | 魔晶法杖、玄铁斧、暗金锤 |

### 防具（23件）

| 槽位 | 初级 | 中级 | 高级 |
|------|------|------|------|
| 盾牌 | 木盾、铁盾 | 精钢盾、银圆盾 | 秘银盾、暗金圆盾 |
| 头部 | 皮帽、铁盔 | 硬皮帽、银盔、青铜冠 | 龙皮帽、秘银盔、魔晶冠 |
| 身体 | 布袍、皮甲、铁甲 | 硬皮衣、银袍、精钢甲 | 龙皮衣、魔晶袍、玄铁甲 |

### 饰品（9件）

| 初级 | 中级 | 高级 |
|------|------|------|
| 力量戒指、生命项链、疾风护符 | 银戒指、守护项链、迅捷护符 | 暗金戒指、永恒项链、幻影护符 |

## NPC商店分配规则

| NPC | 装备等级段 | 装备类型 | 特殊物品 |
|-----|-----------|---------|---------|
| 铁匠老王 | tier1 + tier2 | 武器、盾牌、头部、身体 | 药水、火把、绳索、铁矿石 |
| 杂货婆刘婶 | tier1 | 身体 | 食物、日用品、布料 |
| 采药人老林 | tier1 | 头部、身体、饰品 | 草药、高级药水、魔法水晶 |

## 扩展指南

### 添加新装备

在 `item_generator.py` 的对应模板列表中添加条目：

```python
WEAPON_TEMPLATES = [
    ...
    {"name": "新武器", "id": "new_weapon", "tier": "tier2", "type": "weapon", "equip_slot": "weapon",
     "stat_weights": {"attack": 1.0, "defense": 0.0, "speed": 0.0, "max_hp": 0.0},
     "desc": "新武器的描述。"},
]
```

然后运行：
```bash
python item_generator.py apply
python item_generator.py shop all
```

### 添加新NPC商店

在 `SHOP_TEMPLATES` 中添加新条目，指定装备等级段、类型和各类物品ID。

### 添加新等级段

在 `TIERS` 字典中添加新等级段，然后在模板中引用即可。
