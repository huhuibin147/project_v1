// 输入管理器 - 统一处理键盘/触摸事件

const InputManager = (() => {
  const keys = {};
  const keyHandlers = {};
  const keyDownHandlers = {};
  const keyUpHandlers = {};
  let enabled = true;

  function init() {
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("keyup", onKeyUp);
    registerDefaultInputs();
  }

  function onKeyDown(e) {
    if (!enabled) return;
    
    keys[e.key] = true;
    
    if (keyDownHandlers[e.key]) {
      keyDownHandlers[e.key](e);
    }
  }

  function onKeyUp(e) {
    keys[e.key] = false;
    
    if (keyUpHandlers[e.key]) {
      keyUpHandlers[e.key](e);
    }
  }

  function registerDefaultInputs() {
    registerKeyDown("o", (e) => {
      if (GameManager.isStarted() && !GameManager.isMenuOpen()) {
        if (typeof combatOpen === 'undefined' || !combatOpen) {
          GameManager.toggleGameMenu();
        }
      }
    });

    registerKeyDown("O", (e) => {
      if (GameManager.isStarted() && !GameManager.isMenuOpen()) {
        if (typeof combatOpen === 'undefined' || !combatOpen) {
          GameManager.toggleGameMenu();
        }
      }
    });

    registerKeyDown("m", (e) => {
      if (GameManager.isStarted() && typeof toggleWorldMap === 'function') {
        toggleWorldMap();
      }
    });

    registerKeyDown("M", (e) => {
      if (GameManager.isStarted() && typeof toggleWorldMap === 'function') {
        toggleWorldMap();
      }
    });

    registerKeyDown("Escape", (e) => {
      if (typeof worldMapOpen !== 'undefined' && worldMapOpen && typeof closeWorldMap === 'function') {
        closeWorldMap();
      }
    });
  }

  function registerKeyDown(key, handler) {
    keyDownHandlers[key] = handler;
  }

  function registerKeyUp(key, handler) {
    keyUpHandlers[key] = handler;
  }

  function registerKey(key, handler) {
    keyHandlers[key] = handler;
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

  return {
    init,
    registerKeyDown,
    registerKeyUp,
    registerKey,
    isPressed,
    enable,
    disable,
    destroy
  };
})();
