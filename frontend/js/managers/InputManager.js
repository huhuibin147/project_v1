// 输入管理器 - 统一处理键盘/触摸事件
// 支持优先级处理器链：同一按键可注册多个处理器，按优先级从高到低执行
// 高优先级处理器返回 true 时阻止低优先级处理器执行

const InputManager = (() => {
  const keys = {};
  // 每个按键对应一个处理器数组，按优先级降序排列
  const handlers = {};
  let enabled = true;

  function init() {
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("keyup", onKeyUp);
  }

  function onKeyDown(e) {
    if (!enabled) return;

    keys[e.key] = true;
    keys[e.key.toLowerCase()] = true;

    // 按优先级从高到低执行处理器
    const list = handlers[e.key.toLowerCase()];
    if (list) {
      for (const entry of list) {
        try {
          // 处理器返回 true 表示消费了该按键，阻止后续低优先级处理器
          if (entry.handler(e) === true) break;
        } catch (err) {
          console.error(`InputManager handler error [${e.key}]:`, err);
        }
      }
    }
  }

  function onKeyUp(e) {
    keys[e.key] = false;
    keys[e.key.toLowerCase()] = false;
  }

  /**
   * 注册按键处理器
   * @param {string} key - 按键（不区分大小写）
   * @param {function} handler - 处理函数，返回 true 可阻止低优先级处理器
   * @param {number} [priority=0] - 优先级，数值越大越先执行
   *   推荐优先级：
   *   100 - 战斗内操作（战斗中按键优先级最高）
   *   50  - NPC 交互选项（NPC面板内的数字键）
   *   10  - 面板快捷键（I/P/K/T/Q/H/E 等开关面板）
   *   0   - 全局操作（O 菜单、M 地图）
   *   -10 - Escape 关闭面板
   */
  function register(key, handler, priority = 0) {
    const k = key.toLowerCase();
    if (!handlers[k]) handlers[k] = [];
    handlers[k].push({ handler, priority });
    // 按优先级降序排列
    handlers[k].sort((a, b) => b.priority - a.priority);
  }

  /**
   * 注销按键处理器
   * @param {string} key - 按键
   * @param {function} handler - 要移除的处理器引用
   */
  function unregister(key, handler) {
    const k = key.toLowerCase();
    if (!handlers[k]) return;
    handlers[k] = handlers[k].filter(entry => entry.handler !== handler);
  }

  function isPressed(key) {
    return keys[key] === true;
  }

  function enable() {
    enabled = true;
  }

  function disable() {
    enabled = false;
  }

  function destroy() {
    document.removeEventListener("keydown", onKeyDown);
    document.removeEventListener("keyup", onKeyUp);
  }

  // 测试辅助：模拟按键按下
  function simulateKeyDown(key) {
    keys[key] = true;
    keys[key.toLowerCase()] = true;
  }

  // 测试辅助：模拟按键释放
  function simulateKeyUp(key) {
    keys[key] = false;
    keys[key.toLowerCase()] = false;
  }

  // 测试辅助：清除所有按键状态
  function clearKeys() {
    for (const k in keys) delete keys[k];
  }

  return {
    init,
    register,
    unregister,
    isPressed,
    enable,
    disable,
    destroy,
    simulateKeyDown,
    simulateKeyUp,
    clearKeys,
  };
})();
