/**
 * PanelManager - 面板状态集中管理器
 * 
 * 解决问题：之前每个面板都需要知道所有其他面板的 open 状态，
 * 新增面板时需要修改所有其他面板的互斥检查代码（散弹枪修改反模式）。
 * 
 * 用法：
 *   PanelManager.register('inventory', { open: openInventory, close: closeInventory });
 *   PanelManager.open('inventory');  // 自动关闭其他互斥面板
 *   PanelManager.isOpen('inventory');
 *   PanelManager.close('inventory');
 *   PanelManager.isAnyOpen();        // 是否有任何面板打开
 *   PanelManager.closeAll();         // 关闭所有面板
 */

const PanelManager = (() => {
  // 面板注册表：{ name: { open: fn, close: fn, exclusive: bool } }
  const panels = {};
  // 当前打开的面板集合
  const openSet = new Set();

  /**
   * 注册面板
   * @param {string} name - 面板唯一标识
   * @param {function} openFn - 打开面板的函数
   * @param {function} closeFn - 关闭面板的函数
   * @param {object} [options] - 配置项
   * @param {boolean} [options.exclusive=true] - 是否互斥（打开时自动关闭其他面板）
   */
  function register(name, openFn, closeFn, options = {}) {
    panels[name] = {
      open: openFn,
      close: closeFn,
      exclusive: options.exclusive !== false,
    };
  }

  /**
   * 打开面板
   * 如果面板是互斥的，会先关闭其他互斥面板
   */
  function open(name) {
    const panel = panels[name];
    if (!panel) return;

    if (panel.exclusive) {
      // 关闭其他互斥面板
      for (const openName of openSet) {
        const openPanel = panels[openName];
        if (openPanel && openName !== name) {
          openPanel.close();
          openSet.delete(openName);
        }
      }
    }

    panel.open();
    openSet.add(name);
  }

  /**
   * 关闭面板
   */
  function close(name) {
    const panel = panels[name];
    if (!panel) return;

    panel.close();
    openSet.delete(name);
  }

  /**
   * 切换面板
   */
  function toggle(name) {
    if (isOpen(name)) {
      close(name);
    } else {
      open(name);
    }
  }

  /**
   * 查询面板是否打开
   */
  function isOpen(name) {
    return openSet.has(name);
  }

  /**
   * 是否有任何面板打开（用于阻止玩家移动等）
   */
  function isAnyOpen() {
    return openSet.size > 0;
  }

  /**
   * 关闭所有面板
   */
  function closeAll() {
    for (const name of openSet) {
      const panel = panels[name];
      if (panel) panel.close();
    }
    openSet.clear();
  }

  /**
   * 检查是否可以打开新面板（没有任何互斥面板打开）
   * 用于快捷键判断
   */
  function canOpen(name) {
    if (isOpen(name)) return false;
    const panel = panels[name];
    if (!panel) return false;
    if (!panel.exclusive) return true;
    // 互斥面板：检查是否有其他互斥面板打开
    for (const openName of openSet) {
      const openPanel = panels[openName];
      if (openPanel && openPanel.exclusive) return false;
    }
    return true;
  }

  /**
   * 获取当前所有打开的面板名称
   */
  function getOpenPanels() {
    return Array.from(openSet);
  }

  /**
   * 测试辅助：直接将面板标记为打开（不调用 open 回调）
   */
  function _forceOpen(name) {
    openSet.add(name);
  }

  /**
   * 测试辅助：直接将面板标记为关闭（不调用 close 回调）
   */
  function _forceClose(name) {
    openSet.delete(name);
  }

  return {
    register,
    open,
    close,
    toggle,
    isOpen,
    isAnyOpen,
    canOpen,
    closeAll,
    getOpenPanels,
    _forceOpen,
    _forceClose,
  };
})();
