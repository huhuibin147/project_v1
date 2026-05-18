# 怪物技能类型扩展设计

> 创建日期：2026-05-18
> 优先级：P1 中
> 状态：✅ 已完成

---

## 一、当前问题分析

### 问题清单

| # | 问题 | 影响 |
|---|------|------|
| 1 | 怪物特殊技能仅支持 3 种类型：`apply_effect`、`aoe_attack`、`self_heal` | 战斗体验单一，缺乏策略深度 |
| 2 | 大部分普通怪物 `special: null`，只会普攻/防御 | 战斗重复感强，玩家无需针对不同怪物调整策略 |
| 3 | 缺少召唤、护盾、属性攻击、自我增益、吸血等常见 RPG 怪物技能 | 怪物行为模式同质化严重 |
| 4 | 前端意图图标仅支持 attack/defend/special 三种 | 无法区分怪物具体技能类型，玩家无法预判 |

### 影响范围

- 战斗系统趣味性不足，后期怪物缺乏差异化
- BOSS 战虽有阶段系统，但技能类型仍然有限
- 玩家体验：战斗过程可预测，缺少"需要针对性应对"的紧迫感

---

## 二、优化目标

| 目标 | 优先级 | 说明 |
|------|--------|------|
| 新增 5 种怪物技能类型 | P0 | summon、shield、elemental_attack、buff_self、drain |
| 更新怪物配置使用新技能 | P0 | 为现有 15 种怪物分配差异化技能 |
| 前端意图显示细化 | P1 | 区分不同技能类型的意图图标 |
| 新增测试覆盖 | P0 | 每种新技能类型至少 1 个单元测试 |

---

## 三、设计方案

### 3.1 新增技能类型定义

#### ① `summon` — 召唤小怪

怪物召唤 1-2 个低级小怪加入战斗。

```json
{
  "type": "summon",
  "summon_ids": ["slime", "cave_bat"],
  "summon_count": [1, 2],
  "message": "骷髅王召唤了亡灵仆从！"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `summon_ids` | `list[str]` | 可召唤的怪物 ID 列表，随机选择 |
| `summon_count` | `[int, int]` | 召唤数量范围 [min, max] |
| `message` | `str` | 战斗日志文本 |

**限制**：
- 战斗中怪物总数上限 3 只（含 BOSS），超出则召唤失败，改为普攻
- 召唤出的怪物 HP 为原配置的 50%
- BOSS 专属技能，普通怪物不使用

#### ② `shield` — 获得护盾

怪物为自己添加护盾，吸收一定伤害。

```json
{
  "type": "shield",
  "shield_value": 30,
  "duration": 2,
  "message": "黑暗骑士举起黑暗护盾！"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `shield_value` | `int` | 护盾吸收量（固定值或 max_hp 百分比） |
| `shield_pct` | `float` | 护盾为 max_hp 的百分比（与 shield_value 二选一） |
| `duration` | `int` | 护盾持续回合数 |
| `message` | `str` | 战斗日志文本 |

**实现**：复用现有 `StatusEffect("shield", duration, value=shield_value)` 系统，怪物已有 shield 效果处理逻辑。

#### ③ `elemental_attack` — 属性攻击

怪物发动带属性的强力攻击，触发属性克制计算。

```json
{
  "type": "elemental_attack",
  "element": "fire",
  "damage_multiplier": 1.3,
  "effect": "burn",
  "effect_chance": 0.4,
  "effect_duration": 2,
  "message": "暗影法师释放了暗影火球！"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `element` | `str` | 攻击属性（fire/water/grass），覆盖怪物默认属性 |
| `damage_multiplier` | `float` | 伤害倍率（默认 1.0） |
| `effect` | `str?` | 附加状态效果（可选） |
| `effect_chance` | `float` | 效果触发概率 |
| `effect_duration` | `int` | 效果持续回合 |
| `message` | `str` | 战斗日志文本 |

**与 `aoe_attack` 的区别**：
- `elemental_attack` 是单体攻击，强调属性克制和附加效果
- `aoe_attack` 是群体攻击，强调范围伤害

#### ④ `buff_self` — 自我增益

怪物为自己施加增益效果（攻击提升、防御提升、速度提升）。

```json
{
  "type": "buff_self",
  "buffs": [
    {"effect": "attack_up", "value": 8, "duration": 3},
    {"effect": "defense_up", "value": 5, "duration": 3}
  ],
  "message": "暗熊发出怒吼，力量大增！"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `buffs` | `list[dict]` | 增益效果列表 |
| `buffs[].effect` | `str` | 效果类型：attack_up / defense_up / speed_up |
| `buffs[].value` | `int` | 增益数值 |
| `buffs[].duration` | `int` | 持续回合 |
| `message` | `str` | 战斗日志文本 |

**实现**：复用现有 `StatusEffect` 系统，为怪物添加 buff 效果。需要在 `effects.py` 中为怪物的 buff 效果添加 tick 处理。

#### ⑤ `drain` — 吸血攻击

怪物攻击玩家并恢复自身 HP。

```json
{
  "type": "drain",
  "damage_multiplier": 0.8,
  "heal_pct": 0.5,
  "message": "洞穴蝙蝠吸取了你的生命！"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `damage_multiplier` | `float` | 伤害倍率（默认 0.8） |
| `heal_pct` | `float` | 回复造成伤害的百分比（默认 0.5） |
| `message` | `str` | 战斗日志文本 |

---

### 3.2 怪物 AI 决策扩展

当前 `decide_action` 返回 `"attack"` / `"defend"` / `"special"` 三种动作。新增技能类型不需要修改决策逻辑，因为它们都属于 `"special"` 动作的子类型。

**扩展点**：在 `execute_action` 的 `"special"` 分支中，根据 `special["type"]` 路由到不同的执行函数。

### 3.3 怪物 Buff 效果处理

当前 `effects.py` 中的 `StatBuffHandler` 仅处理玩家 buff，需要扩展支持怪物 buff。

**方案**：在 `StatBuffHandler.tick` 中增加对怪物的 buff 处理：

```python
# 怪物 buff 处理
if not target_is_player and monster:
    if effect.effect_type == "attack_up":
        monster.config["stats"]["attack"] = monster.base_attack + effect.value
    elif effect.effect_type == "defense_up":
        monster.config["stats"]["defense"] = monster.base_defense + effect.value
    elif effect.effect_type == "speed_up":
        monster.config["stats"]["speed"] = monster.base_speed + effect.value
```

**buff 过期时重置**：在 `on_expire` 中重置怪物属性到基础值。

### 3.4 召唤系统实现

在 `CombatSession` 中新增方法：

```python
def add_summoned_monster(self, monster_id: str, hp_pct: float = 0.5) -> MonsterInstance | None:
    if len(self.monsters) >= 3:
        return None
    config = load_monster_config(monster_id)
    if not config:
        return None
    config["stats"]["hp"] = int(config["stats"]["hp"] * hp_pct)
    idx = len(self.monsters)
    instance = MonsterInstance(idx, monster_id, config)
    self.monsters.append(instance)
    return instance
```

### 3.5 前端意图图标扩展

新增意图图标映射：

```javascript
const INTENT_ICONS = {
  attack: "⚔️",
  defend: "🛡️",
  special: "✨",
  summon: "👻",
  shield: "🔰",
  elemental_attack: "🔥",
  buff_self: "💪",
  drain: "🧛",
};
```

**方案**：后端在 `_build_state` 中，将怪物的 `next_action` 从简单字符串扩展为包含技能类型的对象：

```python
# 之前
next_action = "special"

# 之后
next_action = {"action": "special", "special_type": "summon"}
```

前端根据 `special_type` 显示对应图标。

---

## 四、实施计划

### Phase 1：后端核心 — 新增技能执行逻辑

**修改文件**：
- `backend/combat/monster_ai.py` — 在 `execute_action` 中新增 5 种技能类型处理
- `backend/combat/effects.py` — 扩展 `StatBuffHandler` 支持怪物 buff
- `backend/combat/session.py` — 新增 `add_summoned_monster` 方法

### Phase 2：怪物配置更新

**修改文件**：
- `config/monsters.json` — 为 15 种怪物分配差异化特殊技能

### Phase 3：前端显示支持

**修改文件**：
- `frontend/js/combat.js` — 扩展意图图标、next_action 解析、战斗日志显示

### Phase 4：测试与文档

**修改文件**：
- `tests/test_backend_logic.py` — 新增怪物技能测试
- `docs/game_design.md` — 更新完成状态

---

## 五、预期效果

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 怪物技能类型数 | 3 种 | 8 种 |
| 拥有特殊技能的怪物比例 | 5/15 (33%) | 13/15 (87%) |
| 怪物行为差异化 | 低（大部分只会普攻） | 高（每种怪物有独特技能） |
| 战斗策略深度 | 低 | 中（需针对不同怪物调整策略） |
| BOSS 战趣味性 | 中 | 高（召唤+属性攻击+多阶段技能） |

---

## 六、测试用例清单

| 用例 | 类型 | 描述 |
|------|------|------|
| test_monster_shield_skill | 单元 | 怪物使用护盾技能，获得 shield 效果 |
| test_monster_elemental_attack | 单元 | 怪物属性攻击，触发属性克制计算 |
| test_monster_buff_self | 单元 | 怪物自我增益，属性提升 |
| test_monster_drain_skill | 单元 | 怪物吸血攻击，造成伤害并恢复 HP |
| test_monster_summon_skill | 单元 | BOSS 召唤小怪，怪物数量增加 |
| test_monster_summon_limit | 单元 | 怪物数达上限时召唤失败，改为普攻 |
| test_monster_buff_expire | 单元 | 怪物 buff 过期后属性恢复基础值 |

---

## 七、完成状态

> 更新日期：2026-05-18
> 状态：✅ 已完成

| 优化项 | 状态 | 说明 |
|--------|------|------|
| summon 召唤技能 | ✅ | monster_ai.py + session.add_summoned_monster |
| shield 护盾技能 | ✅ | monster_ai.py + effects.py 怪物护盾支持 |
| elemental_attack 属性攻击 | ✅ | monster_ai.py + 属性克制计算 |
| buff_self 自我增益 | ✅ | monster_ai.py + effects.py 怪物buff重算 |
| drain 吸血攻击 | ✅ | monster_ai.py 伤害+回血 |
| 怪物配置更新 | ✅ | 15种怪物全部配置差异化技能 |
| 前端意图图标 | ✅ | combat.js INTENT_ICONS + SPECIAL_TYPE_ICONS |
| 测试覆盖 | ✅ | 10个测试用例全部通过 |
