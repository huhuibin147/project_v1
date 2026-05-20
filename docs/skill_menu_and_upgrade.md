# 技能菜单界面与技能系统扩展

> 版本：v1.0
> 日期：2026-05-20

---

## 一、当前问题分析

### 1.1 缺少技能菜单界面

| 问题 | 影响 |
|------|------|
| 没有独立的技能菜单面板 | 玩家无法在非战斗状态下查看已学技能详情 |
| 角色信息面板中技能只显示名称+MP | 缺少冷却、伤害类型、AOE、等级等关键信息 |
| 技能学习面板依赖NPC交互 | 必须找到技能导师才能查看可学技能，无全局视角 |
| 没有快捷键打开技能面板 | 其他面板都有快捷键（I背包/P角色/Q任务/T天赋），技能面板缺失 |

### 1.2 技能系统功能缺失

| 问题 | 影响 |
|------|------|
| 技能无法升级 | 设计文档中列为扩展方向，但尚未实现 |
| 没有 `GET /api/skills` 路由 | 天赋有独立路由，技能没有，只能通过NPC或战斗获取技能数据 |
| `skill_system.py` 功能单薄 | 仅有 `get_skill`、`get_class_skills`、`can_learn_skill`、`format_skill_for_frontend`，缺少升级逻辑 |
| `skills.json` 无升级相关字段 | 缺少 `max_level`、`level_scaling` 等字段 |

### 1.3 现有架构

```
后端：
  skill_system.py     → 基础查询（get_skill, get_class_skills, can_learn_skill, format_skill_for_frontend）
  combat/skills.py    → 战斗中技能执行（execute_skill, AOE支持）
  routes/npc.py       → NPC技能教学（/npc/service/skills, /npc/service/learn_skill）
  routes/quest.py     → 天赋路由（/talents, /talents/learn, /talents/reset）
  config/skills.json  → 18个技能配置（11单目标+7AOE）

前端：
  combat.js           → 战斗中技能选择面板（openCombatSkillSelect）
  npc.js              → NPC技能学习面板（openSkillLearnPanel）
  talent.js           → 天赋面板（openTalentPanel，快捷键T）
  player_info.js      → 角色信息面板技能标签（pi-skills，仅名称+MP）
```

---

## 二、优化目标

| 目标 | 优先级 | 说明 |
|------|--------|------|
| 独立技能菜单面板 | P0 | 非战斗状态下查看所有技能详情 |
| 快捷键 K 打开技能面板 | P0 | 与其他面板快捷键对齐 |
| `GET /api/skills` 路由 | P0 | 独立于NPC的技能数据接口 |
| 技能升级系统 | P1 | 已学技能可升级，提升威力/降低消耗 |
| 技能面板显示升级信息 | P1 | 显示当前等级、下一级效果、升级费用 |
| 角色信息面板技能增强 | P2 | 点击技能标签跳转到技能菜单 |

---

## 三、设计方案

### 3.1 技能菜单面板 UI

```
┌─────────────────────────────────────────────────────┐
│  ✨ 技能菜单                              [×] 关闭 │
├─────────────────────────────────────────────────────┤
│  职业: 战士  等级: 8  已学: 5/7                      │
├─────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────┐  │
│  │ ⚔ 重击          Lv.2/3     物理伤害          │  │
│  │   全力一击，造成 1.8 倍物理伤害               │  │
│  │   MP: 10  冷却: 0回合  目标: 敌人             │  │
│  │   [升级 50金币 → Lv.3 威力2.0]               │  │
│  └───────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────┐  │
│  │ 🛡 盾墙          Lv.1/3     增益              │  │
│  │   举起盾牌防御，3 回合内防御 +50%             │  │
│  │   MP: 15  冷却: 3回合  目标: 自身             │  │
│  │   [升级 80金币 → Lv.2 防御+60%]              │  │
│  └───────────────────────────────────────────────┘  │
│  ...                                                │
├─────────────────────────────────────────────────────┤
│  ── 未学习 ──                                       │
│  ┌───────────────────────────────────────────────┐  │
│  │ 🔥 狂暴          🔒 需要等级 5                │  │
│  │   激发潜能，3 回合内攻击 +30%，防御 -20%      │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 3.2 技能升级数据结构

在 `skills.json` 中为每个技能新增 `level_scaling` 字段：

```json
{
  "heavy_strike": {
    "skill_id": "heavy_strike",
    "name": "重击",
    "description": "全力一击，造成 {power} 倍物理伤害",
    "mp_cost": 10,
    "cooldown": 0,
    "type": "damage",
    "target": "enemy",
    "damage_type": "physical",
    "power": 1.5,
    "max_level": 3,
    "level_scaling": {
      "2": {"power": 1.8, "upgrade_cost": 50, "description_change": "造成 1.8 倍物理伤害"},
      "3": {"power": 2.0, "upgrade_cost": 120, "description_change": "造成 2.0 倍物理伤害，暴击率+10%"}
    },
    "effects": [],
    "class_requirement": ["warrior"],
    "level_requirement": 1
  }
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `max_level` | int | 技能最大等级，默认 1（不可升级） |
| `level_scaling` | dict | key 为等级(str)，value 为该等级的属性覆盖 |
| `level_scaling[N].upgrade_cost` | int | 升到该等级所需金币 |
| `level_scaling[N].power` | float | 覆盖基础 power |
| `level_scaling[N].mp_cost` | int | 可选，覆盖 MP 消耗 |
| `level_scaling[N].description_change` | string | 可选，升级后的描述变更 |
| `level_scaling[N].effects` | list | 可选，覆盖效果列表 |

### 3.3 玩家数据扩展

在 `player_profile.py` 的存档数据中新增 `skill_levels` 字段：

```python
# 现有
self.skills = ["heavy_strike", "shield_wall", ...]      # 已学技能ID列表
self.learned_skills = ["heavy_strike", "shield_wall", ...] # 通过NPC学习的技能

# 新增
self.skill_levels = {"heavy_strike": 2, "shield_wall": 1, ...}  # 技能等级
```

### 3.4 API 设计

#### GET /api/skills

获取玩家所有技能信息（已学+可学）：

```json
{
  "class_id": "warrior",
  "level": 8,
  "learned_skills": [
    {
      "skill_id": "heavy_strike",
      "name": "重击",
      "description": "全力一击，造成 1.8 倍物理伤害",
      "mp_cost": 10,
      "cooldown": 0,
      "type": "damage",
      "target": "enemy",
      "damage_type": "physical",
      "power": 1.8,
      "effects": [],
      "aoe": false,
      "current_level": 2,
      "max_level": 3,
      "can_upgrade": true,
      "upgrade_cost": 120,
      "next_level_preview": {
        "power": 2.0,
        "description_change": "造成 2.0 倍物理伤害，暴击率+10%"
      }
    }
  ],
  "available_skills": [
    {
      "skill_id": "berserk",
      "name": "狂暴",
      "description": "激发潜能，3 回合内攻击 +30%，防御 -20%",
      "mp_cost": 20,
      "cooldown": 5,
      "type": "buff",
      "target": "self",
      "damage_type": "physical",
      "power": 0,
      "effects": [...],
      "aoe": false,
      "current_level": 0,
      "max_level": 3,
      "can_learn": false,
      "reason": "需要等级 5",
      "level_requirement": 5,
      "class_requirement": ["warrior"]
    }
  ]
}
```

#### POST /api/skills/upgrade

升级技能：

请求体：
```json
{"skill_id": "heavy_strike"}
```

响应：
```json
{
  "success": true,
  "message": "重击 升级到 Lv.3！",
  "cost": 120,
  "skill_info": {
    "skill_id": "heavy_strike",
    "current_level": 3,
    "power": 2.0
  }
}
```

### 3.5 技能升级公式

升级时，`skill_system.py` 根据当前等级合并基础属性和 `level_scaling` 中的覆盖值：

```python
def get_skill_at_level(skill_id: str, level: int) -> dict:
    """获取技能在指定等级的完整属性。"""
    base = SKILLS_DB[skill_id].copy()
    for lvl in range(2, level + 1):
        scaling = base.get("level_scaling", {}).get(str(lvl), {})
        for key, value in scaling.items():
            if key not in ("upgrade_cost", "description_change"):
                base[key] = value
    if level > 1:
        scaling = base.get("level_scaling", {}).get(str(level), {})
        if "description_change" in scaling:
            base["description"] = scaling["description_change"]
    base["current_level"] = level
    return base
```

战斗中执行技能时，使用升级后的属性：

```python
# combat/skills.py 中 execute_skill 修改
skill_level = session.skill_levels.get(skill_id, 1)
skill = get_skill_at_level(skill_id, skill_level)
```

### 3.6 前端文件结构

```
frontend/js/skill_menu.js    — 技能菜单面板交互逻辑（新建）
frontend/index.html          — 新增技能菜单面板 DOM
frontend/css/style.css       — 新增技能菜单样式
```

### 3.7 快捷键

- `K` — 打开/关闭技能菜单面板
- `Escape` — 关闭技能菜单面板

---

## 四、实施计划

### Phase 1：后端 API 与数据扩展 ✅ 已完成

1. `config/skills.json` — 为所有 18 个技能添加 `max_level` 和 `level_scaling` ✅
2. `backend/skill_system.py` — 新增 `get_skill_at_level`、`get_player_skills_info`、`can_upgrade_skill` ✅
3. `backend/player_profile.py` — 新增 `skill_levels` 字段、`get_skills_info`、`upgrade_skill` 方法 ✅
4. `backend/routes/quest.py` — 新增 `GET /api/skills`、`POST /api/skills/upgrade` 路由 ✅
5. `backend/combat/skills.py` + `combat_engine.py` — 战斗执行时使用升级后的技能属性 ✅

### Phase 2：前端技能菜单面板 ✅ 已完成

1. `frontend/index.html` — 新增技能菜单面板 DOM ✅
2. `frontend/css/style.css` — 新增技能菜单样式 ✅
3. `frontend/js/skill_menu.js` — 技能菜单交互逻辑 ✅
4. 快捷键 K 注册 + 面板互斥状态管理 ✅
5. `frontend/js/player_info.js` — 角色信息面板技能标签增强 ✅
6. 游戏菜单和帮助面板添加技能系统入口 ✅

### Phase 3：测试与文档 ✅ 已完成

1. 后端单元测试 — skill_system 核心函数测试通过 ✅
2. player_profile upgrade_skill 集成测试通过 ✅
3. 更新 `docs/todolist.md` ✅

---

## 五、预期效果

| 维度 | 优化前 | 优化后 |
|------|--------|--------|
| 技能查看 | 只能在战斗中或角色信息面板看简单标签 | 独立面板，完整信息，快捷键K |
| 技能升级 | 不支持 | 金币升级，最高3级，属性提升 |
| 技能API | 无独立路由 | GET /api/skills + POST /api/skills/upgrade |
| 技能数据 | skills.json 无等级信息 | 支持 max_level + level_scaling |
| 战斗技能 | 固定属性 | 根据技能等级动态计算 |
