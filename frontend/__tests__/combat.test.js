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
    loadScript('managers/PanelManager.js');
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
      PanelManager.closeAll();
      combatOpen = false;
      mapMonsters = [];
      setPlayerPosition(10, 10);
    });

    it('CBT-02: mapMonsters 为空时应返回 null', () => {
      expect(checkMonsterCollision()).toBeNull();
    });

    it('CBT-03: combatOpen 为 true 时应返回 null', () => {
      PanelManager._forceOpen('combat');
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
      PanelManager.closeAll();
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
      PanelManager._forceOpen('combat');
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

  describe('CBT-11~14: 战斗日志虚拟滚动', () => {
    beforeEach(() => {
      combatLogBuffer = [];
      var logDiv = document.getElementById('combat-log');
      if (logDiv) logDiv.innerHTML = '';
    });

    it('CBT-11: combatLogBuffer 初始应为空数组', () => {
      expect(Array.isArray(combatLogBuffer)).toBe(true);
      expect(combatLogBuffer.length).toBe(0);
    });

    it('CBT-12: appendCombatLog 应向缓冲区添加条目', () => {
      appendCombatLog([{ type: 'player_attack', text: '你攻击了史莱姆！' }]);
      expect(combatLogBuffer.length).toBe(1);
    });

    it('CBT-13: 日志超过 MAX_LOG_ENTRIES 时应裁剪旧条目', () => {
      var entries = [];
      for (var i = 0; i < 60; i++) {
        entries.push({ type: 'player_attack', text: '攻击 ' + i });
      }
      appendCombatLog(entries);
      expect(combatLogBuffer.length).toBeLessThanOrEqual(50);
    });

    it('CBT-14: renderCombatLog 应只渲染最近 VISIBLE_LOG_ENTRIES 条', () => {
      for (var i = 0; i < 30; i++) {
        combatLogBuffer.push({ type: 'player_attack', text: '攻击 ' + i });
      }
      renderCombatLog();
      var logDiv = document.getElementById('combat-log');
      var entries = logDiv.querySelectorAll('.combat-log-entry');
      expect(entries.length).toBeLessThanOrEqual(15);
    });
  });

  describe('CBT-15~17: 伤害数字弹出动画', () => {
    it('CBT-15: showDamageNumbers 应为玩家攻击调用 spawnDamageNumber', () => {
      var panel = document.getElementById('combat-panel');
      if (!panel) return;
      combatState = { monsters: [{ alive: true }] };
      currentTargetIndex = 0;
      var monsterArea = document.getElementById('combat-monster-area');
      if (monsterArea) {
        var slot = document.createElement('div');
        slot.className = 'combat-monster-slot';
        slot.setAttribute('data-index', '0');
        monsterArea.appendChild(slot);
      }
      showDamageNumbers([{ type: 'player_attack', damage: 25 }]);
      var numEl = panel.querySelector('.damage-number');
      expect(numEl).not.toBeNull();
    });

    it('CBT-16: showDamageNumbers 暴击应使用 damage-crit 类', () => {
      var panel = document.getElementById('combat-panel');
      if (!panel) return;
      combatState = { monsters: [{ alive: true }] };
      currentTargetIndex = 0;
      var monsterArea = document.getElementById('combat-monster-area');
      if (monsterArea) {
        var slot = document.createElement('div');
        slot.className = 'combat-monster-slot';
        slot.setAttribute('data-index', '0');
        monsterArea.appendChild(slot);
      }
      showDamageNumbers([{ type: 'player_attack', damage: 50, crit: true }]);
      var critEl = panel.querySelector('.damage-crit');
      expect(critEl).not.toBeNull();
    });

    it('CBT-17: showDamageNumbers 无 damage 字段不应生成数字', () => {
      var panel = document.getElementById('combat-panel');
      if (!panel) return;
      var beforeCount = panel.querySelectorAll('.damage-number').length;
      showDamageNumbers([{ type: 'player_defend', text: '你防御了' }]);
      var afterCount = panel.querySelectorAll('.damage-number').length;
      expect(afterCount).toBe(beforeCount);
    });
  });

  describe('CBT-18~19: 目标选择', () => {
    beforeEach(() => {
      combatState = {
        monsters: [
          { name: '史莱姆', hp: 50, max_hp: 50, alive: true, is_boss: false, monster_id: 'slime', effects: [] },
          { name: '哥布林', hp: 40, max_hp: 40, alive: true, is_boss: false, monster_id: 'goblin', effects: [] },
        ],
        phase: 'player_turn',
      };
      currentTargetIndex = 0;
    });

    it('CBT-18: selectTarget 应切换 currentTargetIndex', () => {
      selectTarget(1);
      expect(currentTargetIndex).toBe(1);
    });

    it('CBT-19: selectTarget 不应选择死亡怪物', () => {
      combatState.monsters[1].alive = false;
      selectTarget(1);
      expect(currentTargetIndex).toBe(0);
    });
  });
});