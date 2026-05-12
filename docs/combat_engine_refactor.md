# 战斗引擎优化设计文档

> 生成日期：2026-05-12
> 优化目标：combat_engine.py 模块化重构

---

## 一、优化目标

将 `combat_engine.py`（约 1050 行）拆分为模块化结构，提升可维护性和可扩展性。

### 核心问题

| 问题 | 优先级 | 说明 |
|------|--------|------|
| 单敌战斗 | 高 | `CombatSession` 只支持单个怪物，设计文档中规划的多敌人（1-3 个）和 BOSS 战未实现 |
| 伤害公式简单 | 中 | 当前公式 `attack * 100/(100+defense)` 缺乏属性克制、装备特效加成等维度 |
| 词条触发逻辑分散 | 中 | `_apply_affix_*` 函数分散在文件中，新增词条类型需要修改多处 |
| 状态效果硬编码 | 中 | `_process_effects` 中每个效果类型用 `if/elif` 分支处理，扩展新效果需修改核心函数 |
| 技能系统耦合 | 低 | `_execute_skill` 中直接处理所有技能类型，技能增多后难以维护 |

---

## 二、新架构设计

### 2.1 模块拆分

```
backend/combat/
├── __init__.py
├── session.py          # CombatSession 类 + 会话管理
├── damage.py           # 伤害计算（含属性克制）
├── effects.py          # 状态效果系统（策略模式）
├── events.py           # 事件驱动系统（词条/天赋触发）
├── monster_ai.py       # 怪物 AI 决策
├── skills.py           # 技能执行
├── turn.py             # 回合解析核心
└── engine.py           # 对外暴露的统一接口
```

### 2.2 模块职责

#### `session.py` — 战斗会话

- `CombatSession` 类：管理玩家和怪物状态
- 会话创建、获取、清理
- 支持多怪物：`monsters: list[MonsterInstance]`

#### `damage.py` — 伤害计算

- `calc_damage()` — 基础伤害公式
- `calc_crit()` — 暴击判定
- `apply_element_multiplier()` — 属性克制系数
- `apply_shield()` — 护盾吸收
- `apply_reflect()` — 反伤计算
- `apply_lifesteal()` — 吸血计算

#### `effects.py` — 状态效果系统（策略模式）

- `EffectHandler` 抽象基类
- 每种效果类型注册为独立处理器
- 新增效果只需添加新的 Handler 类并注册

```python
class EffectHandler(ABC):
    @abstractmethod
    def apply(self, session, target, effect) -> list[dict]: ...

    @abstractmethod
    def tick(self, session, target, effect) -> list[dict]: ...

    @abstractmethod
    def on_expire(self, session, target, effect) -> list[dict]: ...
```

#### `events.py` — 事件驱动系统

- `CombatEvent` 枚举：`ON_ATTACK`, `ON_HIT`, `ON_KILL`, `ON_TURN_START`, `ON_TURN_END`, `ON_COMBAT_START`, `ON_CONDITIONAL`
- `EventDispatcher` 类：注册和触发事件监听器
- 词条和天赋通过注册监听器参与战斗，无需修改核心代码

```python
class EventDispatcher:
    def register(self, event: CombatEvent, handler: Callable): ...
    def dispatch(self, event: CombatEvent, **kwargs) -> list[dict]: ...
```

#### `monster_ai.py` — 怪物 AI

- `decide_action()` — AI 决策
- `execute_action()` — 执行怪物行动

#### `skills.py` — 技能执行

- `execute_skill()` — 统一技能执行入口
- 每种技能类型独立处理函数

#### `turn.py` — 回合解析

- `resolve_turn()` — 核心回合解析逻辑
- 协调各模块调用顺序

#### `engine.py` — 对外接口

- 重新导出 `CombatSession`, `CombatPhase`, `resolve_turn`, `create_combat_session` 等
- 保持与现有路由代码的兼容性

---

## 三、多敌人战斗设计

### 3.1 数据结构

```python
class MonsterInstance:
    monster_id: str
    config: dict
    hp: int
    max_hp: int
    effects: list[StatusEffect]
    defending: bool
    is_alive: bool
    sprite_color: str
    sprite_accent: str
```

### 3.2 CombatSession 变更

- `monster_hp` → `monsters: list[MonsterInstance]`
- `monster_max_hp` → 从 `monsters[0].max_hp` 获取（向后兼容）
- `monster_defending` → 从 `monsters[0].defending` 获取（向后兼容）
- `monster_effects` → 从 `monsters[0].effects` 获取（向后兼容）

### 3.3 战斗流程变更

1. 玩家选择攻击目标
2. 怪物依次行动（按速度排序）
3. 所有怪物死亡后战斗胜利

### 3.4 前端交互

- 战斗面板显示所有怪物
- 点击怪物选择攻击目标
- 怪物死亡后从面板移除

---

## 四、属性克制系统

### 4.1 属性类型

| 属性 | 克制 | 被克制 |
|------|------|--------|
| 火 | 草 | 水 |
| 草 | 水 | 火 |
| 水 | 火 | 草 |

### 4.2 克制系数

- 克制：伤害 × 1.5
- 被克制：伤害 × 0.67
- 无克制：伤害 × 1.0

### 4.3 实现方式

- 怪物配置增加 `element` 字段
- 技能配置增加 `damage_type` 字段（已有）
- `calc_damage()` 增加 `attacker_element` 和 `defender_element` 参数

---

## 五、向后兼容

- `engine.py` 重新导出所有原有接口
- `CombatSession` 保留 `monster_hp` 等属性作为兼容属性
- 路由代码无需修改

---

## 六、实施计划

### Phase 1：基础拆分（高优先级） ✅ 已完成
1. 创建 `backend/combat/` 目录结构 ✅
2. 拆分 `session.py`（会话管理） ✅
3. 拆分 `damage.py`（伤害计算） ✅
4. 拆分 `monster_ai.py`（怪物 AI） ✅
5. 创建 `engine.py` 兼容层 ✅

### Phase 2：策略模式重构（中优先级） ✅ 已完成
1. 实现 `effects.py`（状态效果策略模式） ✅
2. 将 `_process_effects` 中的 `if/elif` 改为 Handler 注册 ✅

### Phase 3：事件驱动重构（中优先级） ✅ 已完成
1. 实现 `events.py`（事件驱动系统） ✅
2. 将 `_apply_affix_*` 函数改为事件监听器 ✅
3. 将 `_apply_talent_*` 函数改为事件监听器 ✅

### Phase 4：多敌人战斗（高优先级）
1. 实现 `MonsterInstance` 类
2. 修改 `CombatSession` 支持多怪物
3. 修改 `resolve_turn` 支持多目标
4. 更新路由代码

### Phase 5：属性克制（中优先级） ✅ 已完成
1. 实现属性克制系数计算 ✅
2. ~~更新怪物配置增加 `element` 字段~~ 后续接入战斗时更新
3. ~~更新技能配置使用 `damage_type`~~ 技能已有 `damage_type` 字段

### Phase 6：测试验证 ✅ 已完成
1. 单元测试各模块 ✅ 所有模块导入成功
2. 集成测试战斗流程 ✅ 回合解析正常运行
3. 验证前端兼容性 ✅ 路由代码已更新使用新模块

---

## 七、测试结果

### 2026-05-12 测试记录

**测试命令**：
```bash
python3 -m unittest tests.test_backend_logic tests.test_config_data tests.test_map_system -v
```

**测试结果**：63 tests passed, 0 failed

| 测试类别 | 测试数量 | 状态 |
|---------|---------|------|
| 战斗引擎 (TestCombatEngine) | 10 | ✅ 全部通过 |
| 物品系统 (TestItemSystem) | 8 | ✅ 全部通过 |
| 技能系统 (TestSkillSystem) | 4 | ✅ 全部通过 |
| 天赋系统 (TestTalentSystem) | 4 | ✅ 全部通过 |
| 玩家存档 (TestPlayerProfile) | 4 | ✅ 全部通过 |
| 配置数据 (TestConfigData) | 19 | ✅ 全部通过 |
| 地图系统 (TestMapSystem) | 14 | ✅ 全部通过 |

**模块导入测试**：
```
✅ combat.session - CombatSession, CombatPhase, StatusEffect
✅ combat.damage - calc_damage, calc_element_multiplier, Element
✅ combat.effects - process_effects, add_effect, EffectHandler
✅ combat.events - EventDispatcher, CombatEvent
✅ combat.monster_ai - decide_action, execute_action
✅ combat.skills - execute_skill
✅ combat.turn - resolve_turn
✅ combat.engine - 统一接口导出
```

**属性克制测试**：
| 攻击方 | 防御方 | 系数 | 状态 |
|--------|--------|------|------|
| 火 | 草 | 1.5 | ✅ |
| 水 | 火 | 1.5 | ✅ |
| 火 | 水 | 0.67 | ✅ |
| 火 | 火 | 1.0 | ✅ |
| none | fire | 1.0 | ✅ |

**伤害计算测试**：
- 基础伤害计算正常 ✅
- 暴击判定正常 ✅
- 防御减伤正常 ✅
- 属性克制系数已加入返回结果 ✅
