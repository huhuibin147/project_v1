# 属性克制系统接入战斗 — 设计文档

> 创建日期：2026-05-18
> 优先级：P0
> 状态：开发中

---

## 一、当前问题分析

`damage.py` 的 `calc_damage` 已实现 `火 > 草 > 水 > 火` 三角克制（克制 ×1.5，被克制 ×0.67），但以下环节未传入元素属性参数，导致克制系统形同虚设：

| 位置 | 问题 |
|------|------|
| `turn.py` → `resolve_turn` → `action == "attack"` | 调用 `calc_damage` 时未传 `attacker_element` / `defender_element` |
| `skills.py` → `_execute_damage_skill` | 同上 |
| `skills.py` → `_execute_aoe_damage_skill` | 同上 |
| `monster_ai.py` → `execute_action` → `"attack"` | 同上 |
| `monster_ai.py` → `execute_action` → `"special"` → `"apply_effect"` | 同上 |
| `monsters.json` | 怪物配置缺少 `element` 字段 |
| `player_profile.py` | 玩家缺少 `element` 属性 |
| `routes/combat.py` | `player_snapshot` 缺少 `element` |
| `combat.js` | 前端无克制/被克制提示 |

---

## 二、优化目标

1. 所有伤害计算调用点传入元素属性参数
2. 怪物配置添加 `element` 字段
3. 玩家属性增加 `element`（默认 `"none"`，法师 → `"fire"`，战士 → `"none"`，盗贼 → `"none"`）
4. 技能可覆盖角色默认元素（如 `fireball` → `"fire"`，`frost_bolt` → `"water"`，`blizzard` → `"water"`）
5. 前端战斗日志显示克制/被克制提示
6. 前端怪物卡片显示元素属性图标

---

## 三、设计方案

### 3.1 元素属性定义

```
火(fire) > 草(grass) > 水(water) > 火(fire)

克制倍率: 1.5x
被克制倍率: 0.67x
同属性/无属性: 1.0x
```

### 3.2 怪物元素分配

| 怪物 | 元素 | 理由 |
|------|------|------|
| 史莱姆 | grass | 森林植物系 |
| 野狼 | none | 普通野兽 |
| 毒蛛 | grass | 森林生物 |
| 哥布林 | none | 普通人形 |
| 暗熊 | none | 普通野兽 |
| 洞穴蝙蝠 | none | 普通野兽 |
| 洞穴蜘蛛 | grass | 洞穴生物 |
| 骷髅兵 | none | 亡灵 |
| 腐尸 | none | 亡灵 |
| 黑暗骑士 | none | 亡灵 |
| 骷髅王 | none | 亡灵 BOSS |
| 沙漠蝎 | grass | 沙漠生物 |
| 沙虫 | grass | 沙漠生物 |
| 木乃伊 | none | 亡灵 |
| 沙漠蛇蜥 | fire | 沙漠蜥蜴 |
| 叛变卫兵 | none | 普通人形 |
| 暗影法师 | fire | 法师系 |
| 暗影树精 | grass | 植物系 BOSS |

### 3.3 技能元素覆盖

| 技能 | 元素 | 理由 |
|------|------|------|
| fireball | fire | 火球术 |
| flame_storm | fire | 烈焰风暴 |
| frost_bolt | water | 冰冻术 → 水属性 |
| blizzard | water | 暴风雪 → 水属性 |
| 其他技能 | 继承角色默认元素 | — |

### 3.4 数据流

```
monsters.json (element 字段)
        ↓
MonsterInstance.config["element"]
        ↓
turn.py: resolve_turn → calc_damage(attacker_element=..., defender_element=...)
skills.py: execute_skill → calc_damage(attacker_element=skill_element, defender_element=...)
monster_ai.py: execute_action → calc_damage(attacker_element=monster_element, defender_element=player_element)
```

### 3.5 API 响应变更

`calc_damage` 返回值已包含 `element_multiplier`，需要在战斗日志中添加克制提示：

```python
# 克制
{"type": "element_advantage", "text": "🔥 属性克制！伤害 ×1.5", "element_multiplier": 1.5}

# 被克制
{"type": "element_disadvantage", "text": "💧 属性不利！伤害 ×0.67", "element_multiplier": 0.67}
```

### 3.6 前端显示

1. **怪物卡片**：显示元素图标（🔥火 / 💧水 / 🌿草）
2. **战斗日志**：克制/被克制时显示特殊颜色提示
3. **伤害数字**：克制时伤害数字显示为橙色，被克制时显示为蓝色

---

## 四、实施计划

| 步骤 | 内容 | 涉及文件 |
|------|------|----------|
| ① | `monsters.json` 添加 `element` 字段 | `config/monsters.json` |
| ② | `skills.json` 添加 `element` 字段 | `config/skills.json` |
| ③ | `player_profile.py` 添加 `element` 属性 | `backend/player_profile.py` |
| ④ | `session.py` 的 `CombatSession` 保存 `player_element` | `backend/combat/session.py` |
| ⑤ | `routes/combat.py` 的 `player_snapshot` 传入 `element` | `backend/routes/combat.py` |
| ⑥ | `turn.py` 的 `resolve_turn` 传入元素参数 | `backend/combat/turn.py` |
| ⑦ | `skills.py` 的 `execute_skill` 使用技能元素 | `backend/combat/skills.py` |
| ⑧ | `monster_ai.py` 的 `execute_action` 传入元素参数 | `backend/combat/monster_ai.py` |
| ⑨ | 战斗日志添加克制/被克制提示 | `backend/combat/turn.py` + `monster_ai.py` + `skills.py` |
| ⑩ | `session.py` 的 `MonsterInstance.to_dict` 输出 `element` | `backend/combat/session.py` |
| ⑪ | 前端 `combat.js` 显示元素图标和克制提示 | `frontend/js/combat.js` |

---

## 五、测试用例清单

| 用例 | 类型 | 描述 |
|------|------|------|
| test_element_counter_chain | 单元 | 火>草>水>火 三角克制链 |
| test_element_disadvantage | 单元 | 被克制倍率 0.67 |
| test_element_neutral | 单元 | 无属性/同属性倍率 1.0 |
| test_calc_damage_with_element_advantage | 单元 | calc_damage 克制时伤害更高 |
| test_calc_damage_with_element_disadvantage | 单元 | calc_damage 被克制时伤害更低 |
| test_monsters_have_element_field | 配置 | 所有怪物配置包含 element 字段 |
| test_skills_element_override | 配置 | 有元素技能的 element 字段正确 |
| test_resolve_turn_passes_element | 功能 | resolve_turn 正确传入元素参数 |
| test_execute_skill_uses_skill_element | 功能 | 技能使用技能自身的元素属性 |
| test_monster_attack_passes_element | 功能 | 怪物攻击传入怪物元素 |
| test_combat_log_shows_element_advantage | 功能 | 克制时日志包含 element_advantage |
| test_combat_log_shows_element_disadvantage | 功能 | 被克制时日志包含 element_disadvantage |
| test_player_element_in_snapshot | 集成 | player_snapshot 包含 element |
| test_monster_to_dict_includes_element | 集成 | MonsterInstance.to_dict 包含 element |

---

## 六、完成状态

> 更新日期：2026-05-18
> 状态：已完成 ✅

| 优化项 | 状态 | 说明 |
|--------|------|------|
| 怪物配置添加 element | ✅ 已完成 | monsters.json 所有怪物已添加 element 字段 |
| 技能配置添加 element | ✅ 已完成 | fireball/flame_storm→fire, frost_bolt/blizzard→water |
| 玩家 element 属性 | ✅ 已完成 | player_profile.py 添加 element 属性（mage→fire, rogue→grass, warrior→water） |
| CombatSession 保存 player_element | ✅ 已完成 | session.py 从 player_snapshot 读取 element |
| turn.py 传入元素参数 | ✅ 已完成 | resolve_turn 普通攻击传入 attacker/defender element |
| skills.py 使用技能元素 | ✅ 已完成 | 单体/AOE 技能均使用 skill.element 或 player_element |
| monster_ai.py 传入元素参数 | ✅ 已完成 | 怪物普通攻击和 special 均传入元素参数 |
| 战斗日志克制提示 | ✅ 已完成 | 克制/被克制时添加 element_advantage/disadvantage 日志 |
| MonsterInstance.to_dict 输出 element | ✅ 已完成 | to_dict 包含 element 字段 |
| 前端显示元素图标和克制提示 | ✅ 已完成 | combat.js 添加 ELEMENT_MAP + 怪物卡片元素图标 + 日志样式 |
| 自动化测试 | ✅ 已完成 | 12 个属性克制测试用例全部通过，全量 157 测试零回归 |
