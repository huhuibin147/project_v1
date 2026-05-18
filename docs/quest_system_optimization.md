# 任务系统优化设计

## 当前问题分析

### 1. 任务进度检查手动触发
- **问题**：需要前端主动调用 `/api/quests/progress` 更新进度
- **影响**：前端容易遗漏调用，导致任务进度不同步
- **现状**：`on_kill`, `on_collect`, `on_talk`, `on_explore` 等方法需要手动调用

### 2. 缺少任务链
- **问题**：任务之间无关联，无法形成任务线
- **影响**：玩家体验割裂，缺少叙事连贯性
- **现状**：虽然 `prerequisites` 有 `quests_completed` 字段，但没有自动接续机制

### 3. 每日任务重置逻辑简单
- **问题**：基于日期字符串比较，跨时区可能有问题
- **影响**：不同地区玩家可能在不同时间看到每日任务重置
- **现状**：使用 `datetime.now().strftime("%Y-%m-%d")` 比较

## 优化目标

1. **自动进度触发**：在关键事件发生时自动更新任务进度，无需前端主动调用
2. **任务链系统**：支持任务自动接续，完成后自动解锁后续任务
3. **跨时区每日重置**：使用 UTC 时间戳 + 固定重置时间点

## 优化方案

### 1. 自动进度触发

#### 方案：在关键操作后自动调用进度更新

在以下位置自动触发任务进度更新：
- 战斗结束后（击杀怪物）
- 物品拾取后（收集物品）
- NPC 对话后（与 NPC 交互）
- 地图传送后（探索新区域）

#### 实现位置

修改 `backend/routes/combat.py` 中的战斗结束逻辑：
```python
# 战斗结束后自动更新任务进度
if result.get("success") and result.get("player_won"):
    monster_id = result.get("monster_id", "")
    monster_tags = result.get("monster_tags", [])
    quest_updates = quest_manager.on_kill(monster_id, monster_tags)
    if quest_updates:
        result["quest_updates"] = quest_updates
```

修改 `backend/routes/npc.py` 中的交易/对话逻辑：
```python
# 对话/交易后自动更新任务进度
quest_updates = quest_manager.on_talk(npc_id)
if quest_updates:
    response["quest_updates"] = quest_updates
```

### 2. 任务链系统

#### 方案：在 quests.json 中添加 `chain` 字段

```json
{
  "blacksmith_ore": {
    "id": "blacksmith_ore",
    "name": "铁匠的委托",
    "chain": "blacksmith_questline",
    "chain_order": 1,
    "next_in_chain": "blacksmith_wolf",
    ...
  },
  "blacksmith_wolf": {
    "id": "blacksmith_wolf",
    "name": "狼患",
    "chain": "blacksmith_questline",
    "chain_order": 2,
    "next_in_chain": "blacksmith_bear",
    ...
  }
}
```

#### 自动接续逻辑

在 `complete_quest` 方法中添加：
```python
def complete_quest(self, quest_id: str) -> dict:
    # ... 原有完成逻辑 ...
    
    # 任务链自动接续
    cfg = get_quest_config(quest_id)
    next_quest_id = cfg.get("next_in_chain")
    if next_quest_id:
        next_cfg = get_quest_config(next_quest_id)
        if next_cfg and self._check_prerequisites(next_cfg):
            # 自动接取下一个任务
            self.accept_quest(next_quest_id)
            result["next_quest"] = {
                "quest_id": next_quest_id,
                "quest_name": next_cfg.get("name"),
                "message": next_cfg.get("dialogue", {}).get("offer", "")
            }
    
    return result
```

### 3. 跨时区每日重置

#### 方案：使用 UTC 时间 + 固定重置时间点

```python
from datetime import datetime, timezone, timedelta

def _should_reset_daily(self) -> bool:
    """检查是否需要重置每日任务"""
    now_utc = datetime.now(timezone.utc)
    # 使用 UTC 时间 00:00 作为重置时间点
    reset_time = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    
    last_reset_str = self.player.quests.get("daily_reset", "")
    if not last_reset_str:
        return True
    
    try:
        last_reset = datetime.fromisoformat(last_reset_str)
        return now_utc >= reset_time and last_reset < reset_time
    except ValueError:
        return True

def reset_daily_quests(self):
    """重置每日任务"""
    if not self._should_reset_daily():
        return []
    
    self.player.quests["daily_reset"] = datetime.now(timezone.utc).isoformat()
    reset_quests = []
    
    for quest_id, quest_data in list(self.player.quests.get("active", {}).items()):
        cfg = get_quest_config(quest_id)
        if cfg and cfg.get("type") == "daily":
            # 重置每日任务进度
            quest_data["objectives_progress"] = [0] * len(cfg.get("objectives", []))
            quest_data["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            reset_quests.append(quest_id)
    
    self._save()
    return reset_quests
```

## 实施步骤

### Phase 1: 自动进度触发
1. 修改战斗路由，战斗结束后自动更新任务进度
2. 修改 NPC 路由，对话/交易后自动更新任务进度
3. 修改地图路由，传送后自动更新任务进度

### Phase 2: 任务链系统
1. 在 quests.json 中添加 `chain`, `chain_order`, `next_in_chain` 字段
2. 修改 `complete_quest` 方法，添加自动接续逻辑
3. 添加获取任务链信息的路由

### Phase 3: 跨时区每日重置
1. 修改每日任务重置逻辑，使用 UTC 时间
2. 添加每日任务自动重置检查
3. 在玩家登录时检查并重置每日任务

## 测试计划

1. 测试自动进度触发：
   - 击杀怪物后任务进度自动更新
   - 收集物品后任务进度自动更新
   - 与 NPC 对话后任务进度自动更新

2. 测试任务链：
   - 完成任务后自动接取下一个任务
   - 任务链前置条件检查
   - 任务链信息正确返回

3. 测试每日重置：
   - 跨时区重置时间点正确
   - 每日任务进度正确重置
   - 不会重复重置

---

## 完成状态

> 更新日期：2026-05-18
> 状态：✅ 全部完成

| 优化项 | 状态 | 说明 |
|--------|------|------|
| 自动进度触发 | ✅ 完成 | 战斗结束/NPC 对话/地图传送/物品拾取时自动更新任务进度 |
| 任务链系统 | ✅ 完成 | `quests.json` 新增 `chain`/`chain_order`/`next_in_chain` 字段，完成后自动接取下一个 |
| 跨时区每日重置 | ✅ 完成 | UTC 时间 + 固定重置时间点 |
| API 路由 | ✅ 完成 | `/api/quests/chain/{quest_id}` 获取任务链，`/api/quests/daily/reset` 重置每日任务 |

**涉及修改**：
- `quests.json` — 铁匠任务线添加任务链信息
- `quest_manager.py` — `on_kill`/`on_collect`/`on_talk`/`on_explore` 自动触发，任务链自动接续
- `routes/combat.py` / `routes/npc.py` / `routes/map.py` — 关键事件后自动更新任务进度
