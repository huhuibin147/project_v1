// 战斗模块测试

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

describe('战斗模块 (combat.js)', () => {
  beforeAll(() => {
    loadScript('managers/GameManager.js');
    loadScript('player.js');
    loadScript('map.js');
    loadScript('combat.js');
  });

  describe('CBT-01: combatOpen 初始状态', () => {
    it('combatOpen 初始应为 false', () => {
      expect(combatOpen).toBe(false);
    });

    it('combatSessionId 初始应为 null', () => {
      expect(combatSessionId).toBeNull();
    });

    it('combatState 初始应为 null', () => {
      expect(combatState).toBeNull();
    });

    it('combatAnimating 初始应为 false', () => {
      expect(combatAnimating).toBe(false);
    });
  });

  describe('CBT-02~05: checkMonsterCollision 怪物碰撞', () => {
    beforeEach(() => {
      combatOpen = false;
      mapMonsters = [];
      setPlayerPosition(10, 10);
    });

    it('CBT-02: mapMonsters 为空时应返回 null', () => {
      expect(checkMonsterCollision()).toBeNull();
    });

    it('CBT-03: combatOpen 为 true 时应返回 null', () => {
      combatOpen = true;
      mapMonsters = [{
        monster_id: 'slime',
        instance_id: 'slime_0',
        x: 10 * TILE_SIZE,
        y: 10 * TILE_SIZE,
        alive: true,
        inCombat: false,
      }];
      expect(checkMonsterCollision()).toBeNull();
    });

    it('CBT-04: 怪物在1格内应被检测到', () => {
      mapMonsters = [{
        monster_id: 'slime',
        instance_id: 'slime_0',
        x: 11 * TILE_SIZE,
        y: 10 * TILE_SIZE,
        alive: true,
        inCombat: false,
      }];
      const result = checkMonsterCollision();
      expect(result).not.toBeNull();
      expect(result.monster_id).toBe('slime');
    });

    it('CBT-05: 怪物距离超过1格应返回 null', () => {
      mapMonsters = [{
        monster_id: 'slime',
        instance_id: 'slime_0',
        x: 15 * TILE_SIZE,
        y: 15 * TILE_SIZE,
        alive: true,
        inCombat: false,
      }];
      expect(checkMonsterCollision()).toBeNull();
    });

    it('死亡怪物不应被检测到', () => {
      mapMonsters = [{
        monster_id: 'slime',
        instance_id: 'slime_0',
        x: 10 * TILE_SIZE,
        y: 10 * TILE_SIZE,
        alive: false,
        inCombat: false,
      }];
      expect(checkMonsterCollision()).toBeNull();
    });

    it('战斗中怪物不应被检测到', () => {
      mapMonsters = [{
        monster_id: 'slime',
        instance_id: 'slime_0',
        x: 10 * TILE_SIZE,
        y: 10 * TILE_SIZE,
        alive: true,
        inCombat: true,
      }];
      expect(checkMonsterCollision()).toBeNull();
    });
  });

  describe('CBT-06~07: getNearestMonster 最近怪物', () => {
    beforeEach(() => {
      combatOpen = false;
      mapMonsters = [];
      setPlayerPosition(10, 10);
    });

    it('CBT-06: 应返回2格内最近的怪物', () => {
      mapMonsters = [
        {
          monster_id: 'slime', instance_id: 'slime_0',
          x: 11 * TILE_SIZE, y: 10 * TILE_SIZE,
          alive: true, inCombat: false,
        },
        {
          monster_id: 'goblin', instance_id: 'goblin_0',
          x: 12 * TILE_SIZE, y: 10 * TILE_SIZE,
          alive: true, inCombat: false,
        },
      ];
      const nearest = getNearestMonster();
      expect(nearest).not.toBeNull();
      expect(nearest.monster_id).toBe('slime');
    });

    it('CBT-07: combatOpen 为 true 时应返回 null', () => {
      combatOpen = true;
      mapMonsters = [{
        monster_id: 'slime', instance_id: 'slime_0',
        x: 11 * TILE_SIZE, y: 10 * TILE_SIZE,
        alive: true, inCombat: false,
      }];
      expect(getNearestMonster()).toBeNull();
    });

    it('无怪物时应返回 null', () => {
      expect(getNearestMonster()).toBeNull();
    });
  });

  describe('CBT-08~10: updateMonsters 巡逻移动', () => {
    beforeEach(() => {
      mapMonsters = [];
    });

    it('CBT-08: 怪物应向巡逻点移动', () => {
      var monster = {
        monster_id: 'slime',
        instance_id: 'slime_0',
        x: 0,
        y: 0,
        alive: true,
        inCombat: false,
        patrol: [
          { x: 100, y: 0 },
          { x: 0, y: 0 },
        ],
        patrolIndex: 0,
        patrolSpeed: 0.5,
        animFrame: 0,
        direction: 'down',
      };
      mapMonsters = [monster];
      var beforeX = monster.x;
      updateMonsters(16);
      expect(monster.x).toBeGreaterThan(beforeX);
    });

    it('CBT-09: 到达巡逻点应切换目标', () => {
      var monster = {
        monster_id: 'slime',
        instance_id: 'slime_0',
        x: 100,
        y: 0,
        alive: true,
        inCombat: false,
        patrol: [
          { x: 100, y: 0 },
          { x: 0, y: 0 },
        ],
        patrolIndex: 0,
        patrolSpeed: 0.5,
        animFrame: 0,
        direction: 'down',
      };
      mapMonsters = [monster];
      updateMonsters(16);
      expect(monster.patrolIndex).toBe(1);
    });

    it('CBT-10: 死亡怪物不应移动', () => {
      var monster = {
        monster_id: 'slime',
        instance_id: 'slime_0',
        x: 0, y: 0,
        alive: false,
        inCombat: false,
        patrol: [{ x: 100, y: 0 }, { x: 0, y: 0 }],
        patrolIndex: 0,
        patrolSpeed: 0.5,
        animFrame: 0,
        direction: 'down',
      };
      mapMonsters = [monster];
      var beforeX = monster.x;
      updateMonsters(16);
      expect(monster.x).toBe(beforeX);
    });

    it('CBT-10: 战斗中怪物不应移动', () => {
      var monster = {
        monster_id: 'slime',
        instance_id: 'slime_0',
        x: 0, y: 0,
        alive: true,
        inCombat: true,
        patrol: [{ x: 100, y: 0 }, { x: 0, y: 0 }],
        patrolIndex: 0,
        patrolSpeed: 0.5,
        animFrame: 0,
        direction: 'down',
      };
      mapMonsters = [monster];
      var beforeX = monster.x;
      updateMonsters(16);
      expect(monster.x).toBe(beforeX);
    });

    it('巡逻点少于2个时不应移动', () => {
      var monster = {
        monster_id: 'slime',
        instance_id: 'slime_0',
        x: 0, y: 0,
        alive: true,
        inCombat: false,
        patrol: [{ x: 100, y: 0 }],
        patrolIndex: 0,
        patrolSpeed: 0.5,
        animFrame: 0,
        direction: 'down',
      };
      mapMonsters = [monster];
      var beforeX = monster.x;
      updateMonsters(16);
      expect(monster.x).toBe(beforeX);
    });
  });

  describe('renderEffects 状态效果渲染', () => {
    it('空 effects 应清空容器', () => {
      var container = document.getElementById('combat-player-effects');
      container.innerHTML = '<span>old</span>';
      renderEffects('combat-player-effects', []);
      expect(container.innerHTML).toBe('');
    });

    it('应渲染中毒效果', () => {
      renderEffects('combat-player-effects', [{ type: 'poison', duration: 3 }]);
      var container = document.getElementById('combat-player-effects');
      expect(container.innerHTML).toContain('poison');
      expect(container.innerHTML).toContain('3');
    });

    it('应渲染多个效果', () => {
      renderEffects('combat-player-effects', [
        { type: 'poison', duration: 3 },
        { type: 'burn', duration: 2 },
      ]);
      var container = document.getElementById('combat-player-effects');
      expect(container.innerHTML).toContain('poison');
      expect(container.innerHTML).toContain('burn');
    });
  });

  describe('sleep 工具函数', () => {
    it('应返回 Promise', () => {
      var result = sleep(10);
      expect(result).toBeInstanceOf(Promise);
    });
  });
});