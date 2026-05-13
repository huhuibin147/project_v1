// 任务模块测试

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

describe('任务模块 (quest.js)', () => {
  beforeAll(() => {
    loadScript('managers/GameManager.js');
    loadScript('player.js');
    loadScript('map.js');
    loadScript('npc.js');
    loadScript('quest.js');
  });

  describe('QST-01~03: 面板初始状态', () => {
    it('QST-01: questOpen 初始应为 false', () => {
      expect(questOpen).toBe(false);
    });

    it('QST-02: questManagerOpen 初始应为 false', () => {
      expect(questManagerOpen).toBe(false);
    });

    it('QST-03: currentQuestTab 初始应为 "active"', () => {
      expect(currentQuestTab).toBe('active');
    });

    it('questNpcId 初始应为 null', () => {
      expect(questNpcId).toBeNull();
    });

    it('questListData 初始应为空数组', () => {
      expect(questListData).toEqual([]);
    });
  });

  describe('QST-04~05: getNpcNameById NPC名称查找', () => {
    it('QST-04: 已知 NPC ID 应返回对应名称', () => {
      expect(getNpcNameById('blacksmith')).toBe('铁匠老王');
      expect(getNpcNameById('merchant')).toBe('杂货婆刘婶');
      expect(getNpcNameById('herbalist')).toBe('采药人老林');
      expect(getNpcNameById('priest')).toBe('祭司阿雅');
      expect(getNpcNameById('skill_master')).toBe('导师艾尔文');
    });

    it('QST-05: 未知 NPC ID 应返回原始 ID', () => {
      expect(getNpcNameById('unknown_npc')).toBe('unknown_npc');
    });

    it('npcs 数组中存在时应优先使用 npcs 数据', () => {
      npcs = [{ npc_id: 'test_npc', name: '测试NPC' }];
      expect(getNpcNameById('test_npc')).toBe('测试NPC');
      npcs = [];
    });
  });

  describe('QST-06: switchQuestTab 切换标签', () => {
    it('应更新 currentQuestTab', () => {
      switchQuestTab('available');
      expect(currentQuestTab).toBe('available');
    });

    it('应支持切换到 completed', () => {
      switchQuestTab('completed');
      expect(currentQuestTab).toBe('completed');
    });

    it('应支持切换回 active', () => {
      switchQuestTab('available');
      switchQuestTab('active');
      expect(currentQuestTab).toBe('active');
    });
  });

  describe('showQuestMessage 消息提示', () => {
    it('应显示成功消息', () => {
      showQuestMessage('任务完成', true);
      var el = document.getElementById('quest-message');
      expect(el.style.display).toBe('block');
      expect(el.textContent).toBe('任务完成');
      expect(el.className).toContain('success');
    });

    it('应显示错误消息', () => {
      showQuestMessage('任务失败', false);
      var el = document.getElementById('quest-message');
      expect(el.style.display).toBe('block');
      expect(el.textContent).toBe('任务失败');
      expect(el.className).toContain('error');
    });
  });

  describe('buildQuestItemHtml 任务项HTML构建', () => {
    it('应包含任务名称', () => {
      var html = buildQuestItemHtml({
        id: 'q1',
        name: '测试任务',
        description: '测试描述',
        status: 'available',
        objectives: [],
        rewards: { exp: 10, gold: 5, items: [], affinity: null },
      });
      expect(html).toContain('测试任务');
    });

    it('available 状态应显示接取按钮', () => {
      var html = buildQuestItemHtml({
        id: 'q1',
        name: '测试',
        description: '',
        status: 'available',
        objectives: [],
        rewards: { exp: 0, gold: 0, items: [], affinity: null },
      });
      expect(html).toContain('接取');
    });

    it('active 状态应显示交付和放弃按钮', () => {
      var html = buildQuestItemHtml({
        id: 'q1',
        name: '测试',
        description: '',
        status: 'active',
        can_complete: true,
        objectives: [],
        rewards: { exp: 0, gold: 0, items: [], affinity: null },
      });
      expect(html).toContain('交付');
      expect(html).toContain('放弃');
    });

    it('completed 状态不应有操作按钮', () => {
      var html = buildQuestItemHtml({
        id: 'q1',
        name: '测试',
        description: '',
        status: 'completed',
        objectives: [],
        rewards: { exp: 0, gold: 0, items: [], affinity: null },
      });
      expect(html).not.toContain('btn-quest-action');
    });

    it('应渲染任务目标', () => {
      var html = buildQuestItemHtml({
        id: 'q1',
        name: '测试',
        description: '',
        status: 'active',
        objectives: [
          { description: '击败史莱姆', count: 3, progress: 1, completed: false },
        ],
        rewards: { exp: 0, gold: 0, items: [], affinity: null },
      });
      expect(html).toContain('击败史莱姆');
      expect(html).toContain('1/3');
    });

    it('应渲染奖励信息', () => {
      var html = buildQuestItemHtml({
        id: 'q1',
        name: '测试',
        description: '',
        status: 'available',
        objectives: [],
        rewards: { exp: 100, gold: 50, items: [], affinity: null },
      });
      expect(html).toContain('100经验');
      expect(html).toContain('50金币');
    });
  });
});