# 项目开发流程规范

> 文档版本：v1.0
> 更新日期：2026-05-18

---

## 目录

- [项目开发流程规范](#项目开发流程规范)
  - [目录](#目录)
  - [一、概述](#一概述)
  - [二、开发流程四步走](#二开发流程四步走)
    - [2.1 需求分析与设计](#21-需求分析与设计)
    - [2.2 编写设计文档](#22-编写设计文档)
    - [2.3 代码开发实现](#23-代码开发实现)
    - [2.4 更新文档与测试](#24-更新文档与测试)
  - [三、自动化测试规范](#三自动化测试规范)
    - [3.1 测试框架与目录](#31-测试框架与目录)
    - [3.2 测试分层策略](#32-测试分层策略)
    - [3.3 何时编写测试](#33-何时编写测试)
    - [3.4 测试编写规范](#34-测试编写规范)
      - [后端测试（Python unittest）](#后端测试python-unittest)
      - [前端测试（Jest）](#前端测试jest)
    - [3.5 测试与开发流程集成](#35-测试与开发流程集成)
    - [3.6 测试示例：新增属性克制系统的完整 TDD 流程](#36-测试示例新增属性克制系统的完整-tdd-流程)
  - [四、文档编写规范](#四文档编写规范)
    - [4.1 文档目录](#41-文档目录)
    - [4.2 链接规范](#42-链接规范)
    - [4.3 状态标记规范](#43-状态标记规范)
    - [4.4 地图修改规范](#44-地图修改规范)
  - [五、代码提交规范](#五代码提交规范)
    - [5.1 提交信息格式](#51-提交信息格式)
    - [5.2 提交粒度](#52-提交粒度)
  - [六、示例：实战流程](#六示例实战流程)
    - [示例：添加"属性克制接入战斗"](#示例添加属性克制接入战斗)
  - [七、当前迭代模式](#七当前迭代模式)
  - [八、工具支持](#八工具支持)
    - [8.1 测试运行与验证](#81-测试运行与验证)
    - [8.2 运行命令速查](#82-运行命令速查)
  - [九、常见问题](#九常见问题)

---

## 一、概述

本项目采用**文档驱动开发**（Document-Driven Development）模式：先设计，再编码，后更新文档。

核心原则：
1. **先设计，后编码** — 避免边写边改导致架构混乱
2. **文档先行** — 设计文档完成后再开始编码
3. **文档同步** — 编码完成后立即更新文档记录完成状态
4. **持续迭代** — 优化方向保存在 `game_design.md` 的「模块优化分析」章节中，按优先级逐步完成

---

## 二、开发流程四步走

```
┌─────────────────┐
│  需求分析与设计  │ ← 第一步：理清问题和方案
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   编写设计文档   │ ← 第二步：写入 `docs/` 目录，清晰记录方案
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    代码开发实现   │ ← 第三步：根据文档实现功能
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  更新文档与测试   │ ← 第四步：记录完成状态，标记剩余问题
└─────────────────┘
```

---

### 2.1 需求分析与设计

**输入**：新功能需求 / 性能优化 / 问题修复

**输出**：
- 问题分析（当前问题是什么，影响是什么）
- 设计目标（要达到什么效果）
- 解决方案（具体怎么做，分哪些步骤）
- 影响范围（涉及哪些文件，哪些模块需要修改）

**思考点**：
| 问题 | 思考 |
|------|------|
| ❓ 为什么要做这个？ | 是否提升用户体验？是否提升可维护性？是否解决 bug？ |
| ❓ 不做行不行？ | 这个优化是否值得投入时间？优先级是否足够？ |
| ❓ 有几种方案？ | 各方案优缺点是什么？选哪个？ |
| ❓ 影响哪些模块？ | 哪些现有代码需要修改？API 是否需要兼容？ |
| ❓ 测试点有哪些？ | 实现后需要验证哪些场景？ |

---

### 2.2 编写设计文档

设计文档放在 `docs/` 目录，命名规则：`{feature}_{optimization}.md`

**必填章节**：

```markdown
## 一、当前问题分析
- 列出问题清单，说明影响范围

## 二、优化目标
- 明确要达到的效果，表格列出优先级

## 三、设计方案
- 详细说明解决方案
- 数据结构 / API 设计 / 配置格式
- 代码结构示意图

## 四、实施计划
- 分 Phase 说明步骤
- 列出每个阶段要改哪些文件

## 五、预期效果
- 优化前后对比表格

## 六、（实现后添加）完成状态
- 更新日期，标记哪些完成，哪些未完成
- 列表记录每个优化项的状态 ✅/❌
```

**示例文件名**：
- `combat_engine_refactor.md` — 战斗引擎重构设计
- `frontend_gamejs_optimization.md` — 前端 game.js 优化设计
- `npc_agent_optimization.md` — NPC 对话系统优化设计

---

### 2.3 代码开发实现

**遵循原则**：
1. **严格按文档实现** — 文档已想好，不要边写边改设计
2. **保持现有代码风格** — 不要随便引入新依赖
3. **增量修改** — 尽量不破坏现有 API，保持兼容
4. **边写边测** — 写完一个模块跑一遍测试

**检查清单**：
- [ ] 是否破坏了现有 API？
- [ ] 是否更新了所有相关代码引用？
- [ ] 是否通过了现有单元测试？
- [ ] 新增功能是否需要添加新测试？

---

### 2.4 更新文档与测试

**开发完成后必须做**：

| 步骤 | 操作 |
|------|------|
| ① | 在设计文档末尾添加「完成状态」章节 |
| ② | 表格记录每个优化项 ✅ 完成 / ❌ 未实现 |
| ③ | 更新 `game_design.md` 中的优先级和状态 |
| ④ | 运行所有测试，确保全绿 |
| ⑤ | 记录修改过的所有文件，方便 review |

**「完成状态」章节模板**：

```markdown
---

## 六、完成状态

> 更新日期：YYYY-MM-DD
> 状态：✅ 已完成 / ⚠️ 部分完成 / ❌ 未完成

| 优化项 | 状态 | 说明 |
|--------|------|------|
| Item 1 | ✅ 完成 | 描述 |
| Item 2 | ❌ 未实现 | 原因（P2 低优先级 / 后续迭代） |

**涉及修改文件**：
- `path/to/file1.py` — 修改了...
- `path/to/file2.js` — 添加了...
```

---

## 三、自动化测试规范

自动化测试是开发流程的核心环节，必须与编码同步进行，不允许"先写功能后补测试"。

### 3.1 测试框架与目录

| 层 | 框架 | 目录 | 运行命令 |
|----|------|------|----------|
| 后端 | Python `unittest` | `tests/` | `python tests/run_tests.py` |
| 前端 | Jest + jsdom | `frontend/__tests__/` | `cd frontend && npm test` |

**后端测试文件**：

```
tests/
├── __init__.py
├── run_tests.py              # 一键运行入口
├── test_config_data.py       # 配置数据完整性测试
├── test_backend_logic.py     # 后端核心逻辑测试
├── test_map_system.py        # 地图系统测试
├── test_api_integration.py   # API 集成测试
└── test_multi_enemy_boss.py  # 多敌人与 BOSS 战测试
```

**前端测试文件**：

```
frontend/__tests__/
├── setup.js                  # 测试环境初始化
├── GameManager.test.js       # 游戏管理器测试
├── combat.test.js            # 战斗 UI 测试
├── dialogue.test.js          # 对话系统测试
├── forge.test.js             # 锻造系统测试
├── inventory.test.js         # 背包系统测试
├── map.test.js               # 地图系统测试
├── player.test.js            # 玩家系统测试
├── quest.test.js             # 任务系统测试
├── talent.test.js            # 天赋系统测试
└── game.test.js              # 游戏主逻辑测试
```

### 3.2 测试分层策略

```
        ┌──────────────┐
        │  集成测试     │  ← API 端到端流程（test_api_integration.py）
        │  (E2E / API) │
        ├──────────────┤
        │  功能测试     │  ← 模块间联动（test_backend_logic.py / 前端 *.test.js）
        │  (Feature)   │
        ├──────────────┤
        │  单元测试     │  ← 单个函数/类（各 test 文件中的独立测试方法）
        │  (Unit)      │
        ├──────────────┤
        │  配置测试     │  ← JSON 数据完整性（test_config_data.py）
        │  (Config)    │
        └──────────────┘
```

| 层级 | 覆盖范围 | 运行频率 | 要求 |
|------|----------|----------|------|
| 配置测试 | 所有 JSON 配置文件的格式、引用完整性、数值范围 | 每次提交 | 必须全通过 |
| 单元测试 | 单个函数/方法的输入输出 | 每次提交 | 覆盖核心逻辑 |
| 功能测试 | 跨模块业务流程（战斗/锻造/交易/NPC 对话） | 每次提交 | 覆盖主要流程 |
| 集成测试 | 完整 API 请求→响应链路 | 合并前 | 覆盖关键 API |

### 3.3 何时编写测试

| 场景 | 必须写测试 | 建议写测试 | 可不写 |
|------|:----------:|:----------:|:------:|
| 新增核心业务逻辑函数 | ✅ | - | - |
| 新增 API 路由 | ✅ | - | - |
| 修改伤害/属性计算公式 | ✅ | - | - |
| 新增配置数据（物品/怪物/技能） | ✅ 配置测试自动覆盖 | - | - |
| 新增状态效果类型 | ✅ | - | - |
| 重构代码结构 | - | ✅ | - |
| 修复 bug | ✅ 回归测试 | - | - |
| CSS 样式调整 | - | - | ✅ 视觉变更 |
| 文案修改 | - | - | ✅ 无逻辑影响 |

### 3.4 测试编写规范

#### 后端测试（Python unittest）

```python
import unittest
from backend.combat.damage import calc_damage, calc_element_multiplier, Element

class TestElementSystem(unittest.TestCase):
    """属性克制系统测试"""

    def test_element_counter_chain(self):
        """火 > 草 > 水 > 火 三角克制"""
        self.assertEqual(calc_element_multiplier(Element.FIRE, Element.GRASS), 1.5)
        self.assertEqual(calc_element_multiplier(Element.WATER, Element.FIRE), 1.5)
        self.assertEqual(calc_element_multiplier(Element.FIRE, Element.WATER), 0.67)
        self.assertEqual(calc_element_multiplier(Element.FIRE, Element.FIRE), 1.0)

    def test_neutral_element(self):
        self.assertEqual(calc_element_multiplier(Element.NONE, Element.FIRE), 1.0)

    def test_calc_damage_with_element(self):
        base = calc_damage(attack=100, defense=50)
        with_element = calc_damage(
            attack=100, defense=50,
            attacker_element=Element.FIRE,
            defender_element=Element.GRASS
        )
        self.assertAlmostEqual(with_element / base, 1.5, places=2)
```

**命名规范**：
- 测试类：`Test{模块名}`，如 `TestCombatDamage`、`TestForgeSystem`
- 测试方法：`test_{功能描述}`，如 `test_element_counter_chain`、`test_pity_guarantees_success`

#### 前端测试（Jest）

```javascript
describe('Combat UI — 怪物意图显示', () => {
    test('next_action 为 attack 时显示 ⚔️', () => {
        const monster = { monster_type: 'normal', next_action: { type: 'attack' } };
        expect(getActionIcon(monster)).toBe('⚔️');
    });

    test('next_action 为 defend 时显示 🛡️', () => {
        const monster = { monster_type: 'normal', next_action: { type: 'defend' } };
        expect(getActionIcon(monster)).toBe('🛡️');
    });

    test('BOSS 怪物显示 ♛ 标记', () => {
        const monster = { monster_type: 'boss', next_action: null };
        expect(getMonsterTypeTag(monster)).toBe('♛');
    });
});
```

### 3.5 测试与开发流程集成

```
需求分析 → 设计文档 → 编写测试用例 → 代码实现 → 运行全量测试 → 更新文档
                 ↑                                              │
                 └────────── 测试失败则修复 ─────────────────────┘
```

**TDD 微循环**（核心逻辑推荐使用）：

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  RED         │     │  GREEN       │     │  REFACTOR    │
│ 先写失败的测试 │ ──▶ │ 用最少代码通过 │ ──▶ │ 重构优化代码  │
└──────────────┘     └──────────────┘     └──────────────┘
        ◀─────────────────── 循环 ────────────────────
```

**各阶段测试嵌入**：

```
Phase 1: 需求分析            Phase 2: 设计文档            Phase 3: 编码
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ 列出测试场景      │   │ 设计文档附录      │   │ TDD: Red→Green   │
│ - 正常流程       │   │ "测试用例清单"    │   │ →Refactor        │
│ - 边界条件       │   │ - 各场景输入/输出 │   │                  │
│ - 异常情况       │   │ - 优先级标记     │   │ 每个 Phase 编码  │
└──────────────────┘   └──────────────────┘   │ 完成后跑:        │
                                               │ python run_tests │
         Phase 4: 验收                           │ npm test         │
┌──────────────────────────────┐               └──────────────────┘
│ ① 跑全量测试，确保全绿        │
│ ② 新增测试加入 run_tests.py  │
│ ③ 更新文档 + 记录测试覆盖     │
└──────────────────────────────┘
```

**提交前必做检查**（不可跳过）：

```bash
# 1. 后端全部测试
cd tests && python run_tests.py
# 要求：ALL PASS，0 failures, 0 errors

# 2. 前端全部测试
cd frontend && npm test
# 要求：ALL PASS，0 failures

# 3. 配置文件验证
python tools/validate_all.py
# 要求：所有 JSON 配置格式正确，引用完整
```

### 3.6 测试示例：新增属性克制系统的完整 TDD 流程

**Step 1 — 测试场景分析**

| 场景 | 输入 | 预期输出 |
|------|------|----------|
| 火克制草 | `element=fire, target=grass` | 倍率 1.5 |
| 水克制火 | `element=water, target=fire` | 倍率 1.5 |
| 火被水克 | `element=fire, target=water` | 倍率 0.67 |
| 无属性对抗 | `element=none, target=fire` | 倍率 1.0 |
| 同属性对抗 | `element=fire, target=fire` | 倍率 1.0 |

**Step 2 — 设计文档中列出测试清单**

在对应的设计文档中追加：

```markdown
## 测试用例清单

| 用例 | 类型 | 描述 |
|------|------|------|
| test_element_counter_chain | 单元 | 三角克制链——火>草>水>火 |
| test_calc_damage_with_element | 单元 | calc_damage 包含元素系数 |
| test_monsters_have_element_field | 配置 | 怪物配置包含 element 字段 |
| test_combat_api_returns_element_info | 集成 | 战斗 API 返回克制提示 |
```

**Step 3 — 先写测试（RED）**

```python
# tests/test_backend_logic.py
class TestElementalCombat(unittest.TestCase):
    def test_element_counter_chain(self):
        self.assertEqual(calc_element_multiplier(Element.FIRE, Element.GRASS), 1.5)
        self.assertEqual(calc_element_multiplier(Element.WATER, Element.FIRE), 1.5)
        self.assertEqual(calc_element_multiplier(Element.FIRE, Element.WATER), 0.67)
```

**Step 4 — 实现代码（GREEN）**

```python
# backend/combat/damage.py
ELEMENT_COUNTER = {Element.FIRE: Element.GRASS, Element.WATER: Element.FIRE}

def calc_element_multiplier(attacker, defender):
    if ELEMENT_COUNTER.get(attacker) == defender:
        return 1.5
    if ELEMENT_COUNTER.get(defender) == attacker:
        return 0.67
    return 1.0
```

**Step 5 — 运行验证**

```bash
$ python tests/run_tests.py backend
============================================================
  🧪 后端逻辑测试
============================================================
TestElementalCombat
  test_element_counter_chain ........................ ✅ PASS
  test_calc_damage_with_element ...................... ✅ PASS
--------------------------------------------------
Ran 2 tests in 0.015s — OK
```

**Step 6 — 更新文档**

- 对应设计文档末尾追加「测试覆盖」表格
- `game_design.md` 中该项标记 ✅

---

## 四、文档编写规范

### 4.1 文档目录

```
docs/
├── 系统设计文档
│   ├── game_design.md              # 整体游戏设计
│   ├── combat_system.md            # 战斗系统
│   ├── items_and_economy_system.md # 物品与经济系统
│   ├── exploration_and_map_system.md # 探索与地图系统
│   ├── npc_system.md               # NPC 系统
│   ├── quest_and_story_system.md   # 任务与剧情系统
│   ├── skill_and_talent_system.md  # 技能与天赋系统
│   └── peripheral_systems.md       # 周边系统
│
├── 重构/优化设计文档
│   ├── combat_engine_refactor.md       # 战斗引擎模块化重构
│   ├── item_system_optimization.md     # 物品系统优化
│   ├── player_profile_refactor.md      # player_profile 重构
│   ├── npc_agent_optimization.md       # NPC 对话系统优化
│   ├── frontend_gamejs_optimization.md # 前端 game.js 优化
│   ├── quest_system_optimization.md    # 任务系统优化
│   ├── forge_affix_optimization.md      # 锻造与词条优化
│   ├── combat_ui_redesign.md           # 战斗 UI 重构
│   ├── multi_enemy_boss_design.md      # 多敌人与 BOSS 战设计
│   └── game_design.md               # 游戏设计与优化方向总览（定期更新）
│
├── 开发文档
│   └── DEVELOPMENT_WORKFLOW.md    ← 本文档
│
└── 测试文档
    └── test_plan.md               # 测试计划
```

### 4.2 链接规范

文档中引用代码文件使用相对链接：

```markdown
[combat.js](file:///absolute/path/to/project/docs/...)
[backend/combat/turn.py](file:///Users/huhuibin/code/aiproj/project_v1/backend/combat/turn.py)
```

这样在 IDE 中可以直接点击跳转。

### 4.3 状态标记规范

| 标记 | 含义 |
|------|------|
| ✅ | 已完成 |
| ⚠️ | 部分完成 |
| ❌ | 未实现 |
| 🔥 | P0 高优先级 |
| ⚡ | P1 中优先级 |
| 💡 | P2 低优先级 |

### 4.4 地图修改规范

**核心原则：地图修改必须用代码自动化处理，禁止手动推理地图瓦片布局。**

| 规则 | 说明 |
|------|------|
| 禁止手动推理 | 不允许人眼分析地图 JSON 数据来决定修改哪个瓦片 |
| 必须写脚本 | 所有地图变更（开放化、封闭修复、对象放置等）都应编写 Python 脚本 |
| 可重复执行 | 脚本应支持多次运行，结果可验证 |
| 使用配置驱动 | 脚本应读取 `config/tiles.json` 判断瓦片属性，不要硬编码 |

**工具脚本位置**：`tools/fix_maps.py` — 自动修复封闭区域、开放地图、恢复交互数据

---

## 五、代码提交规范

### 5.1 提交信息格式

```
<type>(<scope>): <description>

<body>

<footer>
```

**type** 可选值：
- `feat` — 新功能
- `fix` — 修复 bug
- `refactor` — 重构（不影响功能）
- `docs` — 更新文档
- `perf` — 性能优化
- `test` — 添加测试
- `chore` — 构建/工具相关

**示例**：

```
feat(combat): 实现多敌人战斗与 BOSS 阶段系统

- 支持 1-3 个怪物同时战斗
- 支持 BOSS HP 阈值触发阶段转换
- 支持 AOE 技能伤害递减
- 前端支持点击/Tab 切换目标

Closes: #issue-number
```

### 5.2 提交粒度

- 一个提交只做一件事
- 不要混着多个不相关的修改
- 大功能拆成多个提交逐步提交

---

## 六、示例：实战流程

### 示例：添加"属性克制接入战斗"

**Step 1: 需求分析 → 写入 game_design.md**

在 `game_design.md` 的 P0 中列出：
- 当前问题：`calc_damage` 已实现属性克制，但 `turn.py`/`skills.py` 未传入参数
- 影响：克制系统形同虚设
- 优先级：P0 高

**Step 2: 如果需要详细设计 → 新建设计文档**

如果是大功能，新建 `elemental_system_design.md`，包含：
- 当前问题分析
- 设计方案
- 实施计划（分步骤）

**Step 3: 编码**

按文档步骤实现：
1. 在 `monsters.json` 为怪物添加 `element` 字段
2. 在 `turn.py` 的 `resolve_turn` 传入 `attacker_element` / `defender_element`
3. 在 `skills.py` 的 `execute_skill` 透传参数
4. 在 `routes/combat.py` 透传
5. 前端 `combat.js` 显示克制提示

**Step 4: 更新文档**

1. 在设计文档末尾添加「完成状态」章节
2. 更新 `game_design.md`，将该项从"待处理"标记为"已完成"
3. 运行测试，确保全绿

**Step 5: 提交代码**

```
perf(combat): 属性克制系统接入战斗流程

- 在 resolve_turn / execute_skill / execute_action 中传入元素属性参数
- 前端 combat.js 显示克制/被克制提示
- 更新 documentation 完成状态

Closes: #issue
```

---

## 七、当前迭代模式

我们采用的迭代方式：

1. **优先级排序** — `game_design.md` 按 P0/P1/P2 排序
2. **批量更新文档** — 先梳理所有已完成功能，更新所有设计文档
3. **逐个实现** — 从 P0 开始，一个一个做，做完一个更新一个文档
4. **定期回顾** — 完成一批后，重新评估优先级，更新 `game_design.md`

**好处**：
- 文档始终与代码同步
- 新来的开发者可以通过文档快速了解项目
- 设计问题在编码前暴露，减少返工
- 优化方向清晰，不会遗漏

---

## 八、工具支持

### 8.1 测试运行与验证

**后端测试**：

```bash
# 全部后端测试
cd tests && python run_tests.py

# 单独运行某个测试文件
python -m pytest tests/test_backend_logic.py -v

# 单独运行某个测试类
python -m pytest tests/test_backend_logic.py::TestElementSystem -v

# 单独运行某个测试方法
python -m pytest tests/test_backend_logic.py::TestElementSystem::test_element_counter_chain -v
```

**前端测试**：

```bash
cd frontend

# 全部前端测试
npm test

# 监听模式（修改后自动运行）
npm run test:watch

# 覆盖率报告
npm run test:coverage
```

**配置完整性校验**：

```bash
# 验证所有 JSON 配置格式和引用完整性
python tools/validate_all.py
```

### 8.2 运行命令速查

```bash
# 后端测试
cd tests
python run_tests.py

# 前端测试
cd frontend
npm test
```

---

## 九、常见问题

**Q: 小修改也要写文档吗？**

A: 小修改（如修复 typo、调整样式）可以直接改，不用新建文档。但如果是功能变更或架构调整，必须写文档。

**Q: 优化方向存在哪里？**

A: 所有待优化项统一整理在 [`game_design.md`](file:///Users/huhuibin/code/aiproj/project_v1/docs/game_design.md) 的「模块优化分析」章节中，按 P0/P1/P2 优先级排列。

**Q: 设计错了怎么办？**

A: 更新设计文档，重新走流程。文档就是用来记录当前最佳设计的，错了就改文档，再改代码。

**Q: 测试写多少才算够？**

A: 最低要求：核心业务逻辑 100% 覆盖、新增 API 必有集成测试、配置变更通过 validate_all. 不要求 100% 覆盖率，但关键路径不能缺失。

**Q: 测试跑不过能不能先提交？**

A: 不能。提交前必须跑全量测试且全部通过。如果测试本身有误，先修测试再提交代码。

**Q: 前端测试怎么写？很多函数在全局作用域。**

A: 当前项目的 JS 模块使用 IIFE 模式暴露到全局。测试时通过 jest.config.js 的 `setupFiles` 加载必要的 JS 文件，确保全局函数可用。参考现有 `__tests__/` 下的测试文件写法。

---

**EOF**
