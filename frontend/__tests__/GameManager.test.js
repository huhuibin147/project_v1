// GameManager 模块测试

const fs = require('fs');
const path = require('path');

function loadScript(relativePath) {
  const fullPath = path.resolve(__dirname, '..', 'js', relativePath);
  let code = fs.readFileSync(fullPath, 'utf-8');
  code = code.replace(/"use strict";?/g, '');
  code = code.replace(/'use strict';?/g, '');
  code = code.replace(/\bconst\b/g, 'var');
  code = code.replace(/\blet\b/g, 'var');
  (0, eval)(code);
}

describe('GameManager 模块 (GameManager.js)', () => {
  beforeAll(() => {
    loadScript('managers/GameManager.js');
  });

  describe('GM-01: isStarted 初始状态', () => {
    it('初始应返回 false', () => {
      expect(GameManager.isStarted()).toBe(false);
    });
  });

  describe('GM-02~04: 菜单状态管理', () => {
    it('GM-02: isMenuOpen 初始应返回 false', () => {
      expect(GameManager.isMenuOpen()).toBe(false);
    });

    it('GM-03: openGameMenu 后 isMenuOpen 应返回 true', () => {
      GameManager.openGameMenu();
      expect(GameManager.isMenuOpen()).toBe(true);
    });

    it('GM-03: openGameMenu 应添加 active class', () => {
      GameManager.openGameMenu();
      var panel = document.getElementById('game-menu-panel');
      expect(panel.classList.contains('active')).toBe(true);
    });

    it('GM-04: closeGameMenu 后 isMenuOpen 应返回 false', () => {
      GameManager.openGameMenu();
      GameManager.closeGameMenu();
      expect(GameManager.isMenuOpen()).toBe(false);
    });

    it('GM-04: closeGameMenu 应移除 active class', () => {
      GameManager.openGameMenu();
      GameManager.closeGameMenu();
      var panel = document.getElementById('game-menu-panel');
      expect(panel.classList.contains('active')).toBe(false);
    });
  });

  describe('GM-05: toggleGameMenu 切换', () => {
    beforeEach(() => {
      GameManager.closeGameMenu();
    });

    it('关闭状态切换后应打开', () => {
      GameManager.toggleGameMenu();
      expect(GameManager.isMenuOpen()).toBe(true);
    });

    it('打开状态切换后应关闭', () => {
      GameManager.openGameMenu();
      GameManager.toggleGameMenu();
      expect(GameManager.isMenuOpen()).toBe(false);
    });

    it('连续切换应交替开关', () => {
      expect(GameManager.isMenuOpen()).toBe(false);
      GameManager.toggleGameMenu();
      expect(GameManager.isMenuOpen()).toBe(true);
      GameManager.toggleGameMenu();
      expect(GameManager.isMenuOpen()).toBe(false);
      GameManager.toggleGameMenu();
      expect(GameManager.isMenuOpen()).toBe(true);
    });
  });

  describe('GM-06: stopGame', () => {
    it('stopGame 后 isStarted 应返回 false', () => {
      GameManager.stop();
      expect(GameManager.isStarted()).toBe(false);
    });
  });

  describe('GM-07: getCanvas', () => {
    it('应返回 canvas 元素或 null/undefined（未初始化时）', () => {
      var canvas = GameManager.getCanvas();
      expect(canvas == null || canvas.tagName === 'CANVAS').toBe(true);
    });
  });

  describe('getContext', () => {
    it('应返回 2d context', () => {
      var ctx = GameManager.getContext();
      expect(ctx).not.toBeNull();
    });
  });

  describe('init', () => {
    it('应存在 init 方法', () => {
      expect(typeof GameManager.init).toBe('function');
    });
  });

  describe('start', () => {
    it('应存在 start 方法', () => {
      expect(typeof GameManager.start).toBe('function');
    });
  });

  describe('saveGame', () => {
    it('应关闭菜单', () => {
      GameManager.openGameMenu();
      GameManager.saveGame();
      expect(GameManager.isMenuOpen()).toBe(false);
    });
  });
});