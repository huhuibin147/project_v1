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
