# 前端游戏主循环优化设计

## 当前问题分析

### 1. 全局变量过多
- **问题**：大量 `let` 全局变量（canvas, ctx, lastTime, gameStarted, gameMenuOpen 等）
- **影响**：命名空间污染，变量冲突风险，难以维护
- **现状**：所有变量直接声明在全局作用域

### 2. 无模块化
- **问题**：所有逻辑在全局作用域，难以维护和测试
- **影响**：代码耦合度高，无法单独测试某个子系统
- **现状**：game.js 包含主循环、渲染、输入处理、菜单管理等所有逻辑

### 3. 渲染性能
- **问题**：每帧全量重绘，未使用脏矩形优化
- **影响**：CPU 占用高，帧率不稳定
- **现状**：`render()` 函数每帧清除画布并重绘所有元素

### 4. 输入处理耦合
- **问题**：键盘事件直接绑定到全局函数，缺少输入管理器
- **影响**：输入逻辑分散，难以添加新输入方式（如触摸、手柄）
- **现状**：`document.addEventListener("keydown", ...)` 分散在各处

### 5. 缺少加载状态
- **问题**：资源加载时无 Loading 提示
- **影响**：用户不知道游戏是否在加载
- **现状**：`startGame()` 异步加载资源但无视觉反馈

## 优化目标

1. **模块化管理器**：引入模块模式，封装各子系统
2. **输入管理器**：统一处理键盘/触摸事件
3. **脏矩形渲染优化**：减少不必要的重绘
4. **加载状态反馈**：添加 Loading 提示

## 优化方案

### 1. 模块化管理器

#### 方案：使用 ES6 模块模式创建管理器

```javascript
// GameManager - 游戏核心管理器
const GameManager = (() => {
  let canvas, ctx;
  let lastTime = 0;
  let gameStarted = false;
  let gameMenuOpen = false;
  
  return {
    init() { /* 初始化 */ },
    start() { /* 启动游戏 */ },
    update(dt) { /* 更新逻辑 */ },
    render() { /* 渲染 */ },
    isStarted() { return gameStarted; },
    // ...
  };
})();

// InputManager - 输入管理器
const InputManager = (() => {
  const keys = {};
  const handlers = {};
  
  function init() {
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("keyup", onKeyUp);
  }
  
  function onKeyDown(e) {
    keys[e.key] = true;
    if (handlers[e.key]) {
      handlers[e.key](e);
    }
  }
  
  function onKeyUp(e) {
    keys[e.key] = false;
  }
  
  function register(key, handler) {
    handlers[key] = handler;
  }
  
  function isPressed(key) {
    return keys[key] === true;
  }
  
  return { init, register, isPressed };
})();

// RenderManager - 渲染管理器
const RenderManager = (() => {
  let dirty = true;
  let lastRenderedState = {};
  
  function markDirty() {
    dirty = true;
  }
  
  function shouldRender() {
    return dirty;
  }
  
  function render() {
    if (!dirty) return;
    // 渲染逻辑
    dirty = false;
  }
  
  return { markDirty, shouldRender, render };
})();

// LoadingManager - 加载管理器
const LoadingManager = (() => {
  let loadingCount = 0;
  
  function startLoading() {
    loadingCount++;
    showLoadingUI();
  }
  
  function finishLoading() {
    loadingCount--;
    if (loadingCount <= 0) {
      loadingCount = 0;
      hideLoadingUI();
    }
  }
  
  function showLoadingUI() {
    // 显示加载 UI
  }
  
  function hideLoadingUI() {
    // 隐藏加载 UI
  }
  
  return { startLoading, finishLoading };
})();
```

### 2. 输入管理器

#### 方案：集中管理所有输入事件

```javascript
// 在游戏初始化时注册输入
function registerInputs() {
  InputManager.register("o", () => {
    if (GameManager.isStarted() && !combatOpen) {
      toggleGameMenu();
    }
  });
  
  InputManager.register("m", () => {
    if (GameManager.isStarted()) {
      toggleWorldMap();
    }
  });
  
  InputManager.register("Escape", () => {
    if (worldMapOpen) {
      closeWorldMap();
    }
  });
}
```

### 3. 脏矩形渲染优化

#### 方案：只在状态变化时重绘

```javascript
const RenderManager = (() => {
  let dirty = true;
  let lastPlayerPos = { x: 0, y: 0 };
  let lastCameraPos = { x: 0, y: 0 };
  
  function checkDirty() {
    // 玩家移动
    if (player.x !== lastPlayerPos.x || player.y !== lastPlayerPos.y) {
      dirty = true;
      lastPlayerPos = { x: player.x, y: player.y };
    }
    
    // 摄像机移动
    if (camera.x !== lastCameraPos.x || camera.y !== lastCameraPos.y) {
      dirty = true;
      lastCameraPos = { x: camera.x, y: camera.y };
    }
    
    // NPC/怪物移动
    // ...
  }
  
  function render() {
    checkDirty();
    if (!dirty) return;
    
    // 执行渲染
    dirty = false;
  }
  
  return { render };
})();
```

### 4. 加载状态反馈

#### 方案：添加 Loading 遮罩层

```html
<!-- 在 index.html 中添加 -->
<div id="loading-overlay" class="hidden">
  <div class="loading-spinner"></div>
  <div class="loading-text">加载中...</div>
</div>
```

```css
/* 在 game.css 中添加 */
#loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

#loading-overlay.hidden {
  display: none;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #333;
  border-top: 4px solid #f0c060;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #f0c060;
  margin-top: 20px;
  font-size: 18px;
}
```

## 实施步骤

### Phase 1: 创建管理器模块
1. 创建 `frontend/js/managers/` 目录
2. 创建 `GameManager.js`、`InputManager.js`、`RenderManager.js`、`LoadingManager.js`
3. 在 `index.html` 中引入新模块

### Phase 2: 迁移输入处理
1. 将所有键盘事件迁移到 InputManager
2. 统一输入处理逻辑

### Phase 3: 实现脏矩形渲染
1. 在 RenderManager 中实现脏检查
2. 优化 render() 函数

### Phase 4: 添加加载状态
1. 在 index.html 中添加 Loading 遮罩
2. 在 startGame() 中使用 LoadingManager

## 测试计划

1. 测试管理器初始化：
   - GameManager 正确初始化游戏
   - InputManager 正确注册和处理输入
   - RenderManager 正确执行脏检查
   - LoadingManager 正确显示/隐藏加载状态

2. 测试输入处理：
   - 键盘事件正确触发
   - 多个按键同时按下正确处理
   - 输入管理器在面板打开时正确屏蔽输入

3. 测试渲染性能：
   - 玩家静止时不重绘
   - 玩家移动时正确重绘
   - 帧率稳定

4. 测试加载状态：
   - 资源加载时显示 Loading
   - 加载完成后隐藏 Loading
   - 多个资源同时加载时正确计数

---

## 附录：战斗 UI 优化记录

> 日期：2026-05-15
> 状态：已实现

### 优化内容

#### 1. 怪物卡片增强
- 等级显示：`Lv.X` 显示怪物等级
- 类型标记：精英 ★（金色）、BOSS ♛（红色）
- 意图图标：⚔️/🛡️/✨ 预判怪物下回合行动
- 状态效果中文化：☠️中毒(3)、🔥灼烧(2) 等图标+中文名
- 选中指示器：底部箭头 ▲ 替代右上角标签

#### 2. 玩家状态栏增强
- 玩家头像：48×48 像素风格头像（根据职业显示不同颜色）
- 名称+等级：显示玩家名称和等级
- 护盾条：金色护盾条，有护盾时显示
- HP 颜色渐变：>50% 绿色，25-50% 黄色，<25% 红色
- 状态效果图标：彩色图标+中文名称

#### 3. 战斗日志优化
- 与玩家状态栏并排显示（右侧），占据约 60% 宽度
- 日志条目增加类型图标前缀：⚔玩家攻击、🗡怪物攻击、✨技能、🧪物品、☠状态效果、🏆胜利、💀失败

#### 4. 战斗结果面板增强
- 增加战斗统计：总回合数、总伤害、最大单次伤害、暴击次数
- 奖励区域增加图标：✨经验值、💰金币、📦掉落
- 等级提升时显示 🎉 等级提升！

#### 5. 怪物意图系统
- 后端在 `_build_state()` 中预计算每个存活怪物的 `next_action`
- `MonsterInstance.to_dict(next_action)` 将意图数据包含在返回的怪物信息中
- 前端优先使用后端返回的 `next_action`，回退到前端 `guessMonsterIntent()` 猜测

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `frontend/js/combat.js` | 新增 EFFECT_MAP/INTENT_ICONS/LOG_ICONS 映射，更新 renderMonsterSlots/renderCombat/renderEffects/showCombatResult/renderCombatLog |
| `frontend/css/style.css` | 新增 .combat-monster-meta/.monster-level/.monster-type-badge/.monster-intent/.target-indicator 等样式 |
| `frontend/index.html` | 新增玩家头像 canvas、怪物数量显示、重构战斗面板 HTML 结构 |
| `backend/combat/session.py` | MonsterInstance.to_dict() 新增 level/monster_type/next_action 字段 |
| `backend/combat/turn.py` | _build_state() 预计算怪物意图 |
| `backend/routes/combat.py` | 战斗开始 API 返回怪物意图数据 |

#### 6. 文字颜色修复（2026-05-15）
- `#combat-panel` 添加默认 `color: #ccc`，解决未指定颜色的文字在深色背景下显示为黑色
- `.combat-log-entry` 添加默认 `color: #ccc`
- 怪物槽位 `.combat-bar-text` 和 `.combat-bar-label` 添加颜色
- `renderCombatLog` 新增 reflect/lifesteal/affix/talent/effect_end/monster_idle 日志类型 class 分配

| 文件 | 修改内容 |
|------|----------|
| `frontend/css/style.css` | #combat-panel/.combat-log-entry/.combat-monster-slot .combat-bar-text/.combat-monster-slot .combat-bar-label 添加 color |
| `frontend/js/combat.js` | renderCombatLog 新增 6 种日志类型 class 分配 |

---

## 附录 B：群体技能系统优化记录

> 日期：2026-05-15
> 状态：已实现

### 优化内容

#### 1. 群体技能配置
- 新增 7 个 AOE 技能到 `skills.json`：旋风斩、战吼、毒雾、影袭、烈焰风暴、暴风雪、神圣祈祷
- 每个职业 2 个 AOE 技能（战士/盗贼/法师），覆盖群体伤害/群体增益/群体治疗/群体debuff
- AOE 伤害递减：1目标100%、2目标80%、3目标65%、4+目标50%

#### 2. AOE 日志格式改进
- `_execute_aoe_damage_skill()` 新增 `targets` 数组，按目标分别返回 `monster_index`/`damage`/`crit`/`effects`
- 前端可精确显示每个怪物的伤害数字，而非对所有怪物显示相同数值

#### 3. 前端 AOE 适配
- 伤害数字：按 `targets` 数组分别显示每个怪物的伤害和暴击
- AOE 动画：新增 `playAoeAnimation()` 函数，群体技能释放时所有怪物同时闪烁
- CSS 动画：新增 `.aoe-hit-flash` 和 `@keyframes aoeFlash` 样式
- 怪物 AOE 特殊技能伤害数字：`monster_special` 类型带 `damage` 时显示玩家受击数字

#### 4. 怪物特殊技能扩展
- 新增 `aoe_attack` 类型：群体攻击+可选效果（骷髅王亡灵风暴/暗影树精暗焰风暴）
- 新增 `self_heal` 类型：自我治疗（按 max_hp 百分比恢复）
- BOSS 阶段配置更新：骷髅王和暗影树精的后期阶段使用 AOE 技能

#### 5. 效果系统完善
- 新增 fear（恐惧）效果处理器：BlockActionHandler，阻止行动
- 新增 attack_down/evasion_up/damage_reduction 效果处理器
- EFFECT_NAMES 补充 fear/attack_down/evasion_up/damage_reduction 中文名
- `is_blocked_by_effect()` 支持 fear 效果

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `config/skills.json` | 新增 7 个 AOE 技能（whirlwind/war_cry/poison_mist/shadow_raid/flame_storm/blizzard/holy_prayer） |
| `config/monsters.json` | 骷髅王/暗影树精 BOSS 阶段配置更新，添加 aoe_attack 特殊技能 |
| `backend/combat/skills.py` | `_execute_aoe_damage_skill()` 新增 targets 数组返回 |
| `backend/combat/monster_ai.py` | `execute_action()` 新增 aoe_attack/self_heal 特殊技能类型 |
| `backend/combat/effects.py` | 新增 fear/attack_down/evasion_up/damage_reduction 效果处理器和中文名 |
| `frontend/js/combat.js` | AOE 伤害数字精确显示、AOE 动画、怪物特殊技能伤害数字 |
| `frontend/css/style.css` | 新增 .aoe-hit-flash 和 @keyframes aoeFlash 样式 |
| `docs/skill_and_talent_system.md` | 新增群体技能系统设计章节 |
| `docs/combat_system.md` | 新增群体技能系统/怪物特殊技能扩展章节，更新AOE递减数据 |
| `docs/optimization_analysis.md` | combat.js 已完成优化列表新增群体技能相关条目 |
