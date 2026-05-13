// 游戏主逻辑测试

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

describe('游戏主逻辑 (game.js)', () => {
  beforeAll(() => {
    globalThis.initStartScreen = () => {};
    globalThis.initWorldMap = () => {};
    globalThis.getMonsterSprite = () => null;
    loadScript('managers/GameManager.js');
    loadScript('player.js');
    loadScript('map.js');
    loadScript('game.js');
  });

  describe('portalCooldown 初始值', () => {
    it('初始应为 0', () => {
      expect(portalCooldown).toBe(0);
    });
  });

  describe('checkPortalAutoTransfer 传送门自动传送', () => {
    beforeEach(() => {
      portalCooldown = 0;
      currentMap = null;
      worldMapOpen = false;
      combatOpen = false;
      dialogueOpen = false;
    });

    it('冷却中不应触发传送', () => {
      portalCooldown = 10;
      currentMap = {
        id: 'village',
        objects: [{ type: 'portal', x: 5, y: 5, properties: { target_map: 'forest' } }],
      };
      setPlayerPosition(5, 5);
      checkPortalAutoTransfer();
      expect(portalCooldown).toBe(9);
    });

    it('无 currentMap 时不应报错', () => {
      expect(() => checkPortalAutoTransfer()).not.toThrow();
    });

    it('worldMapOpen 时不应触发传送', () => {
      worldMapOpen = true;
      portalCooldown = 0;
      currentMap = {
        id: 'village',
        objects: [{ type: 'portal', x: 5, y: 5, properties: { target_map: 'forest' } }],
      };
      setPlayerPosition(5, 5);
      checkPortalAutoTransfer();
      expect(portalCooldown).toBe(0);
    });
  });

  describe('closeGameMenu 全局函数', () => {
    it('应调用 GameManager.closeGameMenu', () => {
      GameManager.openGameMenu();
      expect(GameManager.isMenuOpen()).toBe(true);
      closeGameMenu();
      expect(GameManager.isMenuOpen()).toBe(false);
    });
  });

  describe('toggleGameMenu 全局函数', () => {
    it('应调用 GameManager.toggleGameMenu', () => {
      GameManager.closeGameMenu();
      toggleGameMenu();
      expect(GameManager.isMenuOpen()).toBe(true);
      toggleGameMenu();
      expect(GameManager.isMenuOpen()).toBe(false);
    });
  });

  describe('saveGame 全局函数', () => {
    it('应关闭菜单', () => {
      GameManager.openGameMenu();
      saveGame();
      expect(GameManager.isMenuOpen()).toBe(false);
    });
  });
});