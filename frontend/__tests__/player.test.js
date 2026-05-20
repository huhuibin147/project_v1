// 玩家模块测试

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

// 辅助：模拟按键按下
function pressKey(key) {
  InputManager.simulateKeyDown(key);
}

// 辅助：释放按键
function releaseKey(key) {
  InputManager.simulateKeyUp(key);
}

// 辅助：清除所有按键状态
function clearAllKeys() {
  InputManager.clearKeys();
}

describe('玩家模块 (player.js)', () => {
  beforeAll(() => {
    loadScript('managers/PanelManager.js');
    loadScript('managers/InputManager.js');
    loadScript('managers/GameManager.js');
    loadScript('map.js');
    loadScript('player.js');
  });

  describe('PLY-01: getPlayerSpeed 返回恒定速度', () => {
    it('应返回 BASE_PLAYER_SPEED 的值', () => {
      expect(typeof getPlayerSpeed).toBe('function');
      const speed = getPlayerSpeed();
      expect(speed).toBe(6);
    });

    it('多次调用应返回相同值', () => {
      expect(getPlayerSpeed()).toBe(getPlayerSpeed());
    });
  });

  describe('PLY-02: setPlayerPosition 设置瓦片坐标', () => {
    it('应将瓦片坐标转换为像素坐标', () => {
      setPlayerPosition(10, 15);
      expect(player.x).toBe(10 * TILE_SIZE);
      expect(player.y).toBe(15 * TILE_SIZE);
    });

    it('应正确处理原点坐标', () => {
      setPlayerPosition(0, 0);
      expect(player.x).toBe(0);
      expect(player.y).toBe(0);
    });
  });

  describe('PLY-03: getPlayerTilePosition 返回瓦片坐标', () => {
    it('应返回玩家中心点的瓦片坐标', () => {
      setPlayerPosition(10, 15);
      const pos = getPlayerTilePosition();
      expect(pos.x).toBe(10);
      expect(pos.y).toBe(15);
    });

    it('应使用 Math.floor 向下取整', () => {
      player.x = 10 * TILE_SIZE + TILE_SIZE / 2 - 1;
      player.y = 15 * TILE_SIZE + TILE_SIZE / 2 - 1;
      const pos = getPlayerTilePosition();
      expect(pos.x).toBe(10);
      expect(pos.y).toBe(15);
    });
  });

  describe('PLY-04~07: 方向键移动', () => {
    beforeEach(() => {
      setPlayerPosition(10, 10);
      player.direction = 'down';
      clearAllKeys();
      PanelManager.closeAll();
      currentMap = {
        id: 'test',
        width: 20,
        height: 20,
        layers: { ground: Array.from({ length: 20 }, () => Array(20).fill(0)) },
      };
      tileConfig = { '0': { id: 0, name: 'grass', walkable: true } };
    });

    it('PLY-04: 按 W 键应向上移动', () => {
      pressKey('w');
      const beforeY = player.y;
      updatePlayer();
      expect(player.direction).toBe('up');
      expect(player.y).toBeLessThan(beforeY);
    });

    it('PLY-05: 按 S 键应向下移动', () => {
      pressKey('s');
      const beforeY = player.y;
      updatePlayer();
      expect(player.direction).toBe('down');
      expect(player.y).toBeGreaterThan(beforeY);
    });

    it('PLY-06: 按 A 键应向左移动', () => {
      pressKey('a');
      const beforeX = player.x;
      updatePlayer();
      expect(player.direction).toBe('left');
      expect(player.x).toBeLessThan(beforeX);
    });

    it('PLY-07: 按 D 键应向右移动', () => {
      pressKey('d');
      const beforeX = player.x;
      updatePlayer();
      expect(player.direction).toBe('right');
      expect(player.x).toBeGreaterThan(beforeX);
    });

    it('方向键 ArrowUp 应与 W 等效', () => {
      pressKey('ArrowUp');
      const beforeY = player.y;
      updatePlayer();
      expect(player.direction).toBe('up');
      expect(player.y).toBeLessThan(beforeY);
    });
  });

  describe('PLY-08~09: moving 状态', () => {
    beforeEach(() => {
      setPlayerPosition(10, 10);
      player.direction = 'down';
      clearAllKeys();
      PanelManager.closeAll();
      currentMap = {
        id: 'test',
        width: 20,
        height: 20,
        layers: { ground: Array.from({ length: 20 }, () => Array(20).fill(0)) },
      };
      tileConfig = { '0': { id: 0, name: 'grass', walkable: true } };
    });

    it('PLY-08: 无按键时 moving 应为 false', () => {
      player.moving = true;
      updatePlayer();
      expect(player.moving).toBe(false);
    });

    it('PLY-09: 有按键时 moving 应为 true', () => {
      pressKey('w');
      updatePlayer();
      expect(player.moving).toBe(true);
    });
  });

  describe('PLY-10: 面板打开时阻止移动', () => {
    beforeEach(() => {
      setPlayerPosition(10, 10);
      player.direction = 'down';
      clearAllKeys();
      pressKey('w');
      currentMap = {
        id: 'test',
        width: 20,
        height: 20,
        layers: { ground: Array.from({ length: 20 }, () => Array(20).fill(0)) },
      };
      tileConfig = { '0': { id: 0, name: 'grass', walkable: true } };
    });

    const panels = [
      ['dialogue', '对话面板'],
      ['inventory', '背包面板'],
      ['shop', '商店面板'],
      ['playerInfo', '角色信息面板'],
      ['npcInteract', 'NPC交互面板'],
      ['combat', '战斗面板'],
      ['quest', '任务面板'],
      ['heal', '治疗面板'],
      ['skillLearn', '技能学习面板'],
      ['talent', '天赋面板'],
      ['worldMap', '世界地图面板'],
    ];

    panels.forEach(([panelName, label]) => {
      it(`${label}打开时应阻止移动`, () => {
        PanelManager.closeAll();
        PanelManager._forceOpen(panelName);
        const beforeY = player.y;
        updatePlayer();
        expect(player.y).toBe(beforeY);
        PanelManager._forceClose(panelName);
      });
    });

    it('GameManager.isMenuOpen() 为 true 时应阻止移动', () => {
      PanelManager.closeAll();
      GameManager.openGameMenu();
      const beforeY = player.y;
      updatePlayer();
      expect(player.y).toBe(beforeY);
      GameManager.closeGameMenu();
    });
  });

  describe('PLY-11~12: 碰撞检测', () => {
    beforeEach(() => {
      setPlayerPosition(10, 10);
      player.direction = 'down';
      clearAllKeys();
      PanelManager.closeAll();
    });

    it('PLY-11: isWalkable 返回 false 时不应移动', () => {
      currentMap = {
        id: 'test',
        width: 20,
        height: 20,
        layers: { ground: Array.from({ length: 20 }, () => Array(20).fill(1)) },
      };
      tileConfig = { '1': { id: 1, name: 'wall', walkable: false } };
      pressKey('w');
      const beforeY = player.y;
      updatePlayer();
      expect(player.y).toBe(beforeY);
    });

    it('PLY-12: isWalkable 返回 true 时应允许移动', () => {
      currentMap = {
        id: 'test',
        width: 20,
        height: 20,
        layers: { ground: Array.from({ length: 20 }, () => Array(20).fill(0)) },
      };
      tileConfig = { '0': { id: 0, name: 'grass', walkable: true } };
      pressKey('w');
      const beforeY = player.y;
      updatePlayer();
      expect(player.y).toBeLessThan(beforeY);
    });
  });

  describe('player 对象初始值', () => {
    beforeAll(() => {
      loadScript('managers/PanelManager.js');
      loadScript('managers/InputManager.js');
      loadScript('managers/GameManager.js');
      loadScript('map.js');
      loadScript('player.js');
    });

    it('初始方向应为 down', () => {
      expect(player.direction).toBe('down');
    });

    it('初始 frame 应为 0', () => {
      expect(player.frame).toBeGreaterThanOrEqual(0);
    });

    it('应有 name 属性', () => {
      expect(player.name).toBeTruthy();
    });

    it('应有 color 属性', () => {
      expect(player.color).toBeTruthy();
    });

    it('应有 animState 属性', () => {
      expect(player.animState).toBeDefined();
    });

    it('应有 animTimer 属性', () => {
      expect(typeof player.animTimer).toBe('number');
    });

    it('应有 hitFlash 属性', () => {
      expect(typeof player.hitFlash).toBe('number');
    });
  });

  describe('PLY-13~15: 攻击与受击动画', () => {
    beforeEach(() => {
      player.animState = 'idle';
      player.animTimer = 0;
      player.hitFlash = 0;
    });

    it('PLY-13: playPlayerAttackAnim 应设置攻击状态', () => {
      playPlayerAttackAnim();
      expect(player.animState).toBe('attack');
      expect(player.animTimer).toBe(12);
    });

    it('PLY-14: playPlayerHitAnim 应设置受击闪烁', () => {
      playPlayerHitAnim();
      expect(player.hitFlash).toBe(10);
    });

    it('PLY-15: 攻击动画应随帧递减并回到 idle', () => {
      playPlayerAttackAnim();
      expect(player.animState).toBe('attack');
      for (var i = 0; i < 12; i++) {
        updatePlayer();
      }
      expect(player.animState).toBe('idle');
      expect(player.animTimer).toBe(0);
    });

    it('受击闪烁应随帧递减', () => {
      playPlayerHitAnim();
      expect(player.hitFlash).toBe(10);
      for (var i = 0; i < 10; i++) {
        updatePlayer();
      }
      expect(player.hitFlash).toBe(0);
    });
  });
});
