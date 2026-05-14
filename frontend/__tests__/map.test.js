// 地图模块测试

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

describe('地图模块 (map.js)', () => {
  beforeAll(() => {
    loadScript('managers/GameManager.js');
    loadScript('player.js');
    loadScript('map.js');
  });

  describe('MAP-10: TILE_SIZE 常量', () => {
    it('应等于 32', () => {
      expect(TILE_SIZE).toBe(32);
    });
  });

  describe('MAP-01~04: isWalkable 碰撞检测', () => {
    beforeEach(() => {
      currentMap = {
        id: 'test_map',
        width: 10,
        height: 10,
        layers: {
          ground: [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
          ],
        },
      };
      tileConfig = {
        '0': { id: 0, name: 'grass', walkable: true, color: '#4a8c3f' },
        '1': { id: 1, name: 'wall', walkable: false, color: '#7a5c3a' },
      };
    });

    it('MAP-01: col 超出左边界应返回 false', () => {
      expect(isWalkable(-1, 5)).toBe(false);
    });

    it('MAP-01: col 超出右边界应返回 false', () => {
      expect(isWalkable(10, 5)).toBe(false);
    });

    it('MAP-01: row 超出上边界应返回 false', () => {
      expect(isWalkable(5, -1)).toBe(false);
    });

    it('MAP-01: row 超出下边界应返回 false', () => {
      expect(isWalkable(5, 10)).toBe(false);
    });

    it('MAP-02: 可行走瓦片应返回 true', () => {
      expect(isWalkable(0, 0)).toBe(true);
    });

    it('MAP-03: 不可行走瓦片应返回 false', () => {
      currentMap.layers.ground[5][5] = 1;
      expect(isWalkable(5, 5)).toBe(false);
    });

    it('MAP-04: currentMap 为 null 时应返回 false', () => {
      currentMap = null;
      expect(isWalkable(5, 5)).toBe(false);
    });

    it('MAP-04: ground 层不存在时应返回 false', () => {
      currentMap = { id: 'test', width: 10, height: 10, layers: {} };
      expect(isWalkable(5, 5)).toBe(false);
    });

    it('tileId 不在 tileConfig 中时应返回 false', () => {
      currentMap.layers.ground[5][5] = 99;
      expect(isWalkable(5, 5)).toBe(false);
    });
  });

  describe('MAP-05~06: checkPortalCollision 传送门碰撞', () => {
    beforeEach(() => {
      currentMap = {
        id: 'test_map',
        width: 10,
        height: 10,
      };
      mapObjects = [
        { type: 'portal', x: 5, y: 5, properties: { target_map: 'forest' } },
        { type: 'chest', x: 3, y: 3 },
      ];
      setPlayerPosition(5, 5);
    });

    it('MAP-05: 玩家在传送门上应返回传送门对象', () => {
      const portal = checkPortalCollision();
      expect(portal).not.toBeNull();
      expect(portal.type).toBe('portal');
      expect(portal.properties.target_map).toBe('forest');
    });

    it('MAP-06: 玩家不在传送门上应返回 null', () => {
      setPlayerPosition(0, 0);
      const portal = checkPortalCollision();
      expect(portal).toBeNull();
    });

    it('无 currentMap 时应返回 null', () => {
      currentMap = null;
      expect(checkPortalCollision()).toBeNull();
    });
  });

  describe('MAP-07~09: getNearbyInteractableObject 附近物件', () => {
    beforeEach(() => {
      currentMap = {
        id: 'test_map',
        width: 10,
        height: 10,
      };
      mapObjects = [
        { type: 'chest', x: 5, y: 5 },
        { type: 'portal', x: 6, y: 6, properties: { target_map: 'forest' } },
        { type: 'gather', x: 8, y: 8, properties: { item_id: 'herb' } },
      ];
    });

    it('MAP-07: 玩家在物件旁边1格内应返回物件', () => {
      setPlayerPosition(4, 5);
      const obj = getNearbyInteractableObject();
      expect(obj).not.toBeNull();
      expect(obj.type).toBe('chest');
    });

    it('MAP-07: 玩家在物件对角1格内应返回物件', () => {
      setPlayerPosition(4, 4);
      const obj = getNearbyInteractableObject();
      expect(obj).not.toBeNull();
      expect(obj.type).toBe('chest');
    });

    it('MAP-08: 玩家距离物件超过1格应返回 null', () => {
      setPlayerPosition(0, 0);
      const obj = getNearbyInteractableObject();
      expect(obj).toBeNull();
    });

    it('MAP-09: 传送门不应参与 E 键交互', () => {
      mapObjects = [
        { type: 'portal', x: 6, y: 6, properties: { target_map: 'forest' } },
      ];
      setPlayerPosition(6, 6);
      const obj = getNearbyInteractableObject();
      expect(obj).toBeNull();
    });

    it('无 currentMap 时应返回 null', () => {
      currentMap = null;
      expect(getNearbyInteractableObject()).toBeNull();
    });
  });

  describe('camera 摄像机初始值', () => {
    it('初始位置应为 (0, 0)', () => {
      expect(camera.x).toBe(0);
      expect(camera.y).toBe(0);
    });

    it('应有 smoothing 属性', () => {
      expect(camera.smoothing).toBeDefined();
      expect(typeof camera.smoothing).toBe('number');
      expect(camera.smoothing).toBeGreaterThan(0);
      expect(camera.smoothing).toBeLessThanOrEqual(1);
    });

    it('应有 targetX 和 targetY 属性', () => {
      expect(camera.targetX).toBeDefined();
      expect(camera.targetY).toBeDefined();
    });
  });

  describe('MAP-11~12: 离屏 Canvas 缓存', () => {
    it('groundCanvasDirty 初始应为 true', () => {
      expect(groundCanvasDirty).toBe(true);
    });

    it('groundCanvasMapId 初始应为 null', () => {
      expect(groundCanvasMapId).toBeNull();
    });

    it('rebuildGroundCanvas 应为函数', () => {
      expect(typeof rebuildGroundCanvas).toBe('function');
    });
  });

  describe('MAP-13: 摄像机平滑跟随', () => {
    it('updateCamera 应平滑插值摄像机位置', () => {
      currentMap = { id: 'test', width: 40, height: 30, layers: { ground: [] } };
      camera.viewportWidth = 800;
      camera.viewportHeight = 600;
      camera.x = 0;
      camera.y = 0;
      camera.smoothing = 0.08;
      player.x = 500;
      player.y = 400;
      updateCamera();
      expect(camera.x).toBeGreaterThan(0);
      expect(camera.y).toBeGreaterThan(0);
      expect(camera.x).toBeLessThan(camera.targetX + 1);
      expect(camera.y).toBeLessThan(camera.targetY + 1);
    });
  });

  describe('particleSystem 粒子系统', () => {
    it('初始 particles 应为空数组', () => {
      expect(particleSystem.particles).toEqual([]);
    });

    it('emit 应添加粒子', () => {
      particleSystem.emit('leaf', 100, 100, 3);
      expect(particleSystem.particles.length).toBe(3);
      particleSystem.particles = [];
    });

    it('update 应移除生命值耗尽的粒子', () => {
      particleSystem.emit('sparkle', 100, 100, 2);
      expect(particleSystem.particles.length).toBe(2);
      particleSystem.update(99999);
      expect(particleSystem.particles.length).toBe(0);
    });
  });
});