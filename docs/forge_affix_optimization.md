# 锻造与词条系统优化设计

## 一、当前问题分析

### 1.1 词条权重固定（优先级：中）
**问题**：`affixes.json` 中权重写死，无法根据玩家等级动态调整

**影响**：
- 低级玩家可能 roll 到不适合当前阶段的词条
- 高级玩家缺少专属词条激励
- 权重固定导致后期词条分布单一

### 1.2 锻造无保底机制（优先级：高）
**问题**：连续失败无补偿，玩家体验可能不佳

**影响**：
- 成功率 50% 的配方，极端情况下可能连续失败 10+ 次
- 消耗大量材料后一无所获，玩家挫败感强
- 缺少正向反馈循环

### 1.3 缺少词条洗练（优先级：高）
**问题**：无法替换或重 roll 装备上的词条

**影响**：
- 玩家锻造出好装备但词条不理想时无法调整
- 装备利用率低，大量装备被闲置
- 缺少后期追求目标

### 1.4 配方无解锁进度（优先级：低）
**问题**：所有配方一开始就可见，缺少探索感

**影响**：
- 玩家缺少长期目标
- 配方可见但材料难获取，产生挫败感

---

## 二、优化目标

| 目标 | 优先级 | 说明 |
|------|--------|------|
| 锻造保底机制 | 高 | 连续 N 次失败后下次必成功，或逐步提升成功率 |
| 词条洗练功能 | 高 | 消耗金币重 roll 装备上的词条 |
| 词条权重动态调整 | 中 | 根据玩家等级调整词条权重 |
| 配方解锁进度 | 低 | 配方与地图进度/等级挂钩 |

---

## 三、设计方案

### 3.1 锻造保底机制

**设计思路**：
- 记录每个玩家的锻造失败次数（按配方分类）
- 连续失败时，每次增加额外成功率
- 达到保底次数后必成功
- 成功后重置计数器

**实现方案**：
```python
# 玩家存档中新增字段
self.forge_streaks = {}  # {recipe_id: consecutive_fails}

# 保底参数
FORGE_PITY_THRESHOLD = 5  # 连续 5 次失败后保底
FORGE_PITY_BONUS_PER_FAIL = 0.1  # 每次失败增加 10% 成功率

def execute_forge_with_pity(recipe_id, player, ...):
    recipe = RECIPES_DB[recipe_id]
    base_rate = recipe.get("success_rate", 1.0)
    
    # 获取连续失败次数
    streak = player.forge_streaks.get(recipe_id, 0)
    
    # 计算保底加成
    pity_bonus = min(streak * FORGE_PITY_BONUS_PER_FAIL, 1.0 - base_rate)
    effective_rate = min(1.0, base_rate + pity_bonus)
    
    success = random.random() < effective_rate
    
    if success:
        player.forge_streaks[recipe_id] = 0  # 重置
        # ... 正常成功逻辑
    else:
        player.forge_streaks[recipe_id] = streak + 1
        # ... 正常失败逻辑
```

### 3.2 词条洗练功能

**设计思路**：
- 玩家选择已装备的装备进行洗练
- 消耗金币，随机替换一个词条
- 保留装备的其他属性不变
- 洗练后原词条消失，新词条从池中随机选取

**实现方案**：
```python
def reroll_affix(item_id: str, inventory: list, player_gold: int, 
                 slot: str = None) -> dict:
    # 查找装备
    item = _find_equipment_instance(item_id, inventory, slot)
    if not item:
        return {"success": False, "message": "未找到装备"}
    
    current_affixes = item.get("instance_affixes", [])
    if not current_affixes:
        return {"success": False, "message": "该装备没有可洗练的词条"}
    
    # 计算洗练费用（根据稀有度）
    rarity = item.get("instance_rarity", "common")
    cost = REROLL_COSTS.get(rarity, 100)
    if player_gold < cost:
        return {"success": False, "message": f"金币不足，需要 {cost} 金币"}
    
    # 随机选择一个词条替换
    replace_idx = random.randint(0, len(current_affixes) - 1)
    old_affix = current_affixes[replace_idx]
    
    # 生成新词条
    equip_slot = item.get("equip_slot", "")
    player_level = item.get("player_level", 1)
    new_affixes = generate_affixes(equip_slot, rarity, player_level, count=1)
    
    if not new_affixes:
        return {"success": False, "message": "无法生成新词条"}
    
    # 替换
    current_affixes[replace_idx] = new_affixes[0]
    
    return {
        "success": True,
        "message": f"洗练成功！{old_affix['name']} → {new_affixes[0]['name']}",
        "old_affix": old_affix,
        "new_affix": new_affixes[0],
        "cost": cost,
        "affixes": current_affixes,
    }
```

### 3.3 词条权重动态调整

**设计思路**：
- 词条配置中增加 `level_weight_multipliers` 字段
- 根据玩家等级动态调整权重
- 低级词条在低级时权重高，高级词条在高级时权重高

**实现方案**：
```python
# affixes.json 新增字段
{
    "affix_id": "fire_damage",
    "name": "火焰伤害",
    "weight": 10,
    "level_range": {"min": 1, "max": 99},
    "level_weight_multipliers": {
        "1-10": 1.5,   # 1-10 级时权重 x1.5
        "11-20": 1.0,  # 11-20 级时权重 x1.0
        "21-30": 0.5,  # 21-30 级时权重 x0.5
        "31+": 0.2,    # 31+ 级时权重 x0.2
    }
}

def _get_dynamic_weight(affix: dict, player_level: int) -> float:
    base_weight = affix.get("weight", 1)
    multipliers = affix.get("level_weight_multipliers", {})
    
    for range_str, multiplier in multipliers.items():
        if _level_in_range(player_level, range_str):
            return base_weight * multiplier
    
    return base_weight
```

---

## 四、配置变更

### 4.1 玩家存档新增字段
```json
{
    "forge_streaks": {
        "iron_sword": 0,
        "steel_armor": 2
    }
}
```

### 4.2 洗练费用配置
```json
{
    "reroll_costs": {
        "common": 50,
        "uncommon": 100,
        "rare": 200,
        "epic": 500,
        "legendary": 1000
    }
}
```

### 4.3 保底参数配置
```json
{
    "forge_pity": {
        "threshold": 5,
        "bonus_per_fail": 0.1
    }
}
```

---

## 五、实施计划

### Phase 1：锻造保底机制（高优先级）
1. 在 `player_profile.py` 中添加 `forge_streaks` 字段
2. 修改 `forge_system.py` 的 `execute_forge` 支持保底
3. 添加保底状态查询接口
4. 前端显示保底进度

### Phase 2：词条洗练功能（高优先级）
1. 实现 `reroll_affix()` 函数
2. 添加洗练费用配置
3. 添加 API 路由 `/api/forge/reroll`
4. 前端添加洗练按钮和面板

### Phase 3：词条权重动态调整（中优先级）
1. 修改 `affixes.json` 添加 `level_weight_multipliers`
2. 修改 `generate_affixes` 使用动态权重
3. 测试不同等级下的词条分布

### Phase 4：测试验证
1. 单元测试保底机制
2. 单元测试洗练功能
3. 集成测试锻造流程
4. 验证前端兼容性

---

## 六、预期效果

| 优化项 | 优化前 | 优化后 | 提升 |
|--------|--------|--------|------|
| 锻造体验 | 无保底，可能连续失败 | 5 次失败后保底成功 | 玩家挫败感大幅降低 |
| 词条调整 | 无法修改已生成词条 | 消耗金币洗练 | 装备利用率提升 |
| 词条分布 | 固定权重 | 动态权重 | 各等级词条更合理 |
| 玩家目标 | 缺少长期追求 | 洗练+保底进度 | 游戏粘性提升 |

---

## 七、完成状态

> 更新日期：2026-05-18
> 状态：✅ 已完成（除配方解锁外）

| 优化项 | 状态 | 说明 |
|--------|------|------|
| 锻造保底机制 | ✅ 完成 | `FORGE_PITY_THRESHOLD=5`，连续失败每次 +10% 成功率，5 次失败后保底成功 |
| 词条洗练功能 | ✅ 完成 | API `/api/forge/reroll`，消耗金币随机替换装备词条，费用按稀有度递增（50→1000） |
| 词条权重动态 | ✅ 完成 | `level_weight_multipliers` 配置，`_get_dynamic_weight()` / `_level_in_range()` |
| 存档字段扩展 | ✅ 完成 | 玩家存档新增 `forge_streaks` 字段记录各配方连续失败次数 |
| 配方解锁机制 | ❌ 未实现 | 所有配方一开始就可见（P2 低优先级） |

**新增类/方法/配置**：
- `FORGE_PITY_THRESHOLD` / `FORGE_PITY_BONUS_PER_FAIL`：保底参数
- `REROLL_COSTS`：洗练费用配置
- `execute_forge()` 新增 `forge_streaks` 参数
- `reroll_single_affix()`：词条洗练函数
