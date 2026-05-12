# player_profile.py 优化设计

## 一、当前问题分析

### 1.1 文件存档（优先级：高）
**问题**：使用 JSON 文件存储，存档损坏时无自动恢复机制

**影响**：
- 存档文件被意外修改或损坏时，玩家数据丢失
- 无历史版本回滚能力
- 保存过程中断可能导致数据不完整

### 1.2 `_recalc_stats` 频繁调用（优先级：高）
**问题**：每次装备变更都触发全量重算并保存，性能浪费

**影响**：
- 装备/卸下物品时调用 `_recalc_stats()`
- `_recalc_stats()` 内部调用 `_calc_equip_bonus()`，遍历所有装备槽位
- 每个装备槽位调用 `get_item_affixes()`，遍历整个背包查找匹配物品
- 最后调用 `_save()` 写入磁盘
- 连续装备多件物品时，重复计算和保存

### 1.3 装备词条查询效率（优先级：中）
**问题**：`get_item_affixes` 每次遍历整个背包查找匹配物品

**影响**：
- 背包物品数量 N，查询复杂度 O(N)
- 装备 5 个槽位，每次重算调用 5 次查询
- 背包大时（50+ 物品），性能明显下降

### 1.4 属性计算链路长（优先级：中）
**问题**：基础属性 → 等级加成 → 装备加成 → 词条加成 → 天赋加成，链路长且耦合

**影响**：
- 所有计算逻辑集中在 `_recalc_stats()` 方法中
- 难以单独测试各阶段计算
- 新增属性类型需要修改核心方法

### 1.5 缺少属性上限校验（优先级：低）
**问题**：极端情况下属性可能溢出或为负

**影响**：
- 装备/词条/天赋叠加可能导致属性异常
- 战斗中使用异常属性可能破坏游戏平衡

---

## 二、优化目标

| 目标 | 优先级 | 说明 |
|------|--------|------|
| 存档备份与恢复 | 高 | 保存前备份，加载失败时自动恢复 |
| 属性计算缓存 | 高 | 装备未变更时复用计算结果 |
| 物品索引优化 | 中 | 使用物品 ID 索引，避免遍历 |
| 属性计算模块化 | 中 | 拆分计算链路为独立阶段 |
| 属性上限校验 | 低 | 添加合理范围限制 |

---

## 三、设计方案

### 3.1 存档备份与恢复机制

**设计思路**：
- 保存前将当前存档复制为 `.bak` 备份文件
- 加载时若主文件损坏，尝试从备份恢复
- 提供存档完整性校验（简单 checksum）

**实现方案**：
```python
def _save(self):
    # 1. 先备份当前存档
    self._backup_save()
    # 2. 写入新存档
    data = self._to_dict()
    with open(save_path, "w") as f:
        json.dump(data, f)
    # 3. 验证写入完整性
    if not self._verify_save(save_path):
        self._restore_from_backup()

def _backup_save(self):
    src = save_path(self.current_slot)
    bak = save_path(self.current_slot) + ".bak"
    if src.exists():
        shutil.copy2(src, bak)

def _load_from_file(self, slot: int):
    path = save_path(slot)
    if not path.exists():
        return False
    try:
        data = self._load_json(path)
        self._from_dict(data)
        return True
    except (json.JSONDecodeError, KeyError):
        # 尝试从备份恢复
        bak_path = path.with_suffix(".json.bak")
        if bak_path.exists():
            try:
                data = self._load_json(bak_path)
                self._from_dict(data)
                # 恢复成功后重新保存
                self._save()
                return True
            except:
                pass
        return False
```

### 3.2 属性计算缓存机制

**设计思路**：
- 缓存上次计算结果（装备快照、天赋列表、等级）
- 只有当依赖数据变更时才重新计算
- 使用哈希值快速判断是否需要重算

**实现方案**：
```python
class StatsCache:
    def __init__(self):
        self.equipment_hash = None
        self.talents_hash = None
        self.level = None
        self.class_id = None
        self.cached_stats = None

    def needs_recalc(self, player: PlayerProfile) -> bool:
        current_equip_hash = hash(json.dumps(player.equipment, sort_keys=True))
        current_talents_hash = hash(json.dumps(player.talents, sort_keys=True))
        return (
            current_equip_hash != self.equipment_hash or
            current_talents_hash != self.talents_hash or
            player.level != self.level or
            player.class_id != self.class_id
        )

    def update(self, player: PlayerProfile, stats: dict):
        self.equipment_hash = hash(json.dumps(player.equipment, sort_keys=True))
        self.talents_hash = hash(json.dumps(player.talents, sort_keys=True))
        self.level = player.level
        self.class_id = player.class_id
        self.cached_stats = stats
```

**使用方式**：
```python
def _recalc_stats(self):
    if not self._stats_cache.needs_recalc(self):
        # 使用缓存结果
        stats = self._stats_cache.cached_stats
    else:
        # 重新计算
        stats = self._calculate_stats()
        self._stats_cache.update(self, stats)

    self._apply_stats(stats)
    self._save()
```

### 3.3 物品索引优化

**设计思路**：
- 在 PlayerProfile 中维护物品 ID → 数量的映射
- 避免每次查询都遍历背包列表

**实现方案**：
```python
class PlayerProfile:
    def __init__(self):
        self._inventory_index: dict[str, int] = {}

    def _rebuild_inventory_index(self):
        self._inventory_index = {}
        for item in self.inventory:
            item_id = item.get("id") or item.get("item_id")
            qty = item.get("quantity", 1)
            self._inventory_index[item_id] = self._inventory_index.get(item_id, 0) + qty

    def get_item_quantity(self, item_id: str) -> int:
        return self._inventory_index.get(item_id, 0)

    def add_item(self, item_id: str, quantity: int):
        # 更新背包列表
        self.inventory.append({"id": item_id, "quantity": quantity})
        # 更新索引
        self._inventory_index[item_id] = self._inventory_index.get(item_id, 0) + quantity

    def remove_item(self, item_id: str, quantity: int) -> bool:
        if self.get_item_quantity(item_id) < quantity:
            return False
        # 更新背包列表（略）
        # 更新索引
        self._inventory_index[item_id] -= quantity
        if self._inventory_index[item_id] <= 0:
            del self._inventory_index[item_id]
        return True
```

### 3.4 属性计算模块化

**设计思路**：
- 将属性计算拆分为独立阶段
- 每个阶段只关注自己的计算逻辑
- 使用 Pipeline 模式组合各阶段

**实现方案**：
```python
class StatCalculator:
    """属性计算器 - 模块化计算"""

    @staticmethod
    def calc_base_stats(class_id: str, level: int, classes: dict) -> dict:
        """阶段1：基础属性 + 等级加成"""
        cls = classes[class_id]
        level_bonus = level - 1
        return {
            "max_hp": cls["base_hp"] + level_bonus * 10,
            "max_mp": cls.get("base_mp", 30) + level_bonus * 3,
            "attack": cls["base_attack"] + level_bonus * 3,
            "defense": cls["base_defense"] + level_bonus * 2,
            "speed": cls["base_speed"] + level_bonus * 1,
        }

    @staticmethod
    def apply_equipment_bonus(base_stats: dict, equipment: dict, inventory: list) -> dict:
        """阶段2：装备加成 + 词条加成"""
        from item_system import ITEMS_DB
        from affix_system import get_item_affixes, calc_affix_stat_bonus

        bonus = {"max_hp": 0, "max_mp": 0, "attack": 0, "defense": 0, "speed": 0}
        for slot_name, item_id in equipment.items():
            if item_id:
                info = ITEMS_DB.get(item_id, {})
                stats = info.get("stats", {})
                for key in bonus:
                    bonus[key] += stats.get(key, 0)

                affixes = get_item_affixes(item_id, inventory)
                affix_bonus = calc_affix_stat_bonus(affixes, bonus)
                for key in bonus:
                    bonus[key] += affix_bonus.get(key, 0)

        result = dict(base_stats)
        for key in bonus:
            result[key] += bonus[key]
        return result

    @staticmethod
    def apply_talent_multiplier(stats: dict, class_id: str, talents: list) -> dict:
        """阶段3：天赋加成（百分比）"""
        from talent_system import calc_talent_stat_boosts
        boosts = calc_talent_stat_boosts(class_id, talents)

        result = dict(stats)
        for key in boosts:
            if key in result:
                result[key] = int(result[key] * (1 + boosts[key]))
        return result

    @staticmethod
    def validate_stats(stats: dict) -> dict:
        """阶段4：属性校验"""
        validated = dict(stats)
        for key in validated:
            if key in ("max_hp", "max_mp", "attack", "defense", "speed"):
                validated[key] = max(1, min(validated[key], 99999))
        return validated
```

---

## 四、实施计划

### Phase 1：存档备份与恢复（高优先级）
1. 添加 `_backup_save()` 方法
2. 修改 `_save()` 保存前备份
3. 修改 `_load_from_file()` 支持备份恢复
4. 添加 `_verify_save()` 校验方法

### Phase 2：属性计算缓存（高优先级）
1. 创建 `StatsCache` 类
2. 修改 `_recalc_stats()` 使用缓存
3. 添加缓存失效逻辑

### Phase 3：物品索引优化（中优先级）
1. 添加 `_inventory_index` 字典
2. 修改 `add_item()` / `remove_item()` 维护索引
3. 修改 `get_item_quantity()` 使用索引

### Phase 4：属性计算模块化（中优先级）
1. 创建 `StatCalculator` 类
2. 拆分 `_recalc_stats()` 为独立阶段
3. 添加属性校验

### Phase 5：测试验证
1. 单元测试存档备份/恢复
2. 单元测试缓存机制
3. 集成测试装备变更流程
4. 验证前端兼容性

---

## 五、预期效果

| 优化项 | 优化前 | 优化后 | 提升 |
|--------|--------|--------|------|
| 存档安全性 | 无备份 | 自动备份+恢复 | 数据安全性大幅提升 |
| 属性计算 | 每次全量重算 | 缓存复用 | 装备不变时计算量降为 0 |
| 物品查询 | O(N) 遍历 | O(1) 哈希查找 | 背包大时性能提升显著 |
| 代码可维护性 | 单方法 60+ 行 | 模块化分阶段 | 易于测试和扩展 |
| 属性安全性 | 无校验 | 范围限制 | 防止属性异常 |
