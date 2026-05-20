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

describe('锻造模块 (forge.js)', () => {
  beforeAll(() => {
    document.body.innerHTML = `
      <div id="forge-panel">
        <div id="forge-message" style="display:none"></div>
        <div id="forge-recipes"></div>
        <div id="forge-pagination"></div>
        <span id="player-gold-forge">0</span>
        <input type="text" id="forge-search" />
      </div>
      <div id="forge-result-overlay">
        <div id="forge-result-content"></div>
      </div>
    `;
    loadScript('managers/PanelManager.js');
    loadScript('managers/GameManager.js');
    loadScript('map.js');
    loadScript('player.js');
    loadScript('npc.js');
    loadScript('inventory.js');
    loadScript('forge.js');
  });

  describe('FRG-01: 锻造状态初始值', () => {
    it('forgePanelOpen 初始应为 false', () => {
      expect(forgePanelOpen).toBe(false);
    });

    it('forgeAnimating 初始应为 false', () => {
      expect(forgeAnimating).toBe(false);
    });

    it('forgeSearchQuery 初始应为空字符串', () => {
      expect(forgeSearchQuery).toBe('');
    });

    it('forgeFilter 初始应为 "all"', () => {
      expect(forgeFilter).toBe('all');
    });

    it('FORGE_PER_PAGE 应为 6', () => {
      expect(FORGE_PER_PAGE).toBe(6);
    });
  });

  describe('FRG-02: FORGE_TIER_NAMES 等级名称', () => {
    it('应包含 basic/intermediate/advanced/master', () => {
      expect(FORGE_TIER_NAMES.basic).toBe('初级');
      expect(FORGE_TIER_NAMES.intermediate).toBe('中级');
      expect(FORGE_TIER_NAMES.advanced).toBe('高级');
      expect(FORGE_TIER_NAMES.master).toBe('大师');
    });
  });

  describe('FRG-03: FORGE_TIER_COLORS 等级颜色', () => {
    it('应包含各等级颜色', () => {
      expect(FORGE_TIER_COLORS.basic).toBeDefined();
      expect(FORGE_TIER_COLORS.intermediate).toBeDefined();
      expect(FORGE_TIER_COLORS.advanced).toBeDefined();
      expect(FORGE_TIER_COLORS.master).toBeDefined();
    });
  });

  describe('FRG-04: getFilteredForgeRecipes 搜索与筛选', () => {
    beforeEach(() => {
      forgeRecipes = [
        { recipe_id: 'r1', name: '铁剑', category: 'weapon', output: { name: '铁剑' }, materials: [{ name: '铁矿石' }] },
        { recipe_id: 'r2', name: '皮甲', category: 'armor', output: { name: '皮甲' }, materials: [{ name: '皮革' }] },
        { recipe_id: 'r3', name: '铜戒指', category: 'accessory', output: { name: '铜戒指' }, materials: [{ name: '铜矿石' }] },
        { recipe_id: 'r4', name: '钢剑', category: 'weapon', output: { name: '精钢长剑' }, materials: [{ name: '钢锭' }] },
      ];
      forgeFilter = 'all';
      forgeSearchQuery = '';
    });

    it('无筛选时应返回全部配方', () => {
      const result = getFilteredForgeRecipes();
      expect(result.length).toBe(4);
    });

    it('按分类筛选应返回对应配方', () => {
      forgeFilter = 'weapon';
      const result = getFilteredForgeRecipes();
      expect(result.length).toBe(2);
      expect(result.every(r => r.category === 'weapon')).toBe(true);
    });

    it('按配方名搜索应返回匹配结果', () => {
      forgeSearchQuery = '剑';
      const result = getFilteredForgeRecipes();
      expect(result.length).toBe(2);
    });

    it('按产出物品名搜索应返回匹配结果', () => {
      forgeSearchQuery = '精钢';
      const result = getFilteredForgeRecipes();
      expect(result.length).toBe(1);
      expect(result[0].recipe_id).toBe('r4');
    });

    it('按材料名搜索应返回匹配结果', () => {
      forgeSearchQuery = '皮革';
      const result = getFilteredForgeRecipes();
      expect(result.length).toBe(1);
      expect(result[0].recipe_id).toBe('r2');
    });

    it('搜索与分类筛选可叠加', () => {
      forgeFilter = 'weapon';
      forgeSearchQuery = '铁';
      const result = getFilteredForgeRecipes();
      expect(result.length).toBe(1);
      expect(result[0].recipe_id).toBe('r1');
    });

    it('无匹配结果应返回空数组', () => {
      forgeSearchQuery = '不存在的物品';
      const result = getFilteredForgeRecipes();
      expect(result.length).toBe(0);
    });
  });

  describe('FRG-05: searchForgeRecipes 搜索函数', () => {
    it('应更新 forgeSearchQuery 并重置页码', () => {
      forgePage.current = 3;
      searchForgeRecipes('测试');
      expect(forgeSearchQuery).toBe('测试');
      expect(forgePage.current).toBe(1);
    });

    it('空搜索应清空 forgeSearchQuery', () => {
      forgeSearchQuery = '旧搜索';
      searchForgeRecipes('  ');
      expect(forgeSearchQuery).toBe('');
    });
  });

  describe('FRG-06: filterForgeRecipes 分类筛选', () => {
    it('应更新 forgeFilter 并重置页码', () => {
      forgePage.current = 3;
      filterForgeRecipes('weapon');
      expect(forgeFilter).toBe('weapon');
      expect(forgePage.current).toBe(1);
    });
  });

  describe('FRG-07: closeForgePanel 关闭面板', () => {
    it('应重置锻造状态', () => {
      forgePanelOpen = true;
      forgeNpcId = 'blacksmith';
      closeForgePanel();
      expect(forgePanelOpen).toBe(false);
      expect(forgeNpcId).toBeNull();
    });
  });

  describe('FRG-08: doForge 防重复锻造', () => {
    it('forgeAnimating 为 true 时应直接返回', async () => {
      forgeAnimating = true;
      forgeNpcId = 'blacksmith';
      const result = await doForge('test_recipe');
      expect(result).toBeUndefined();
      forgeAnimating = false;
      forgeNpcId = null;
    });

    it('forgeNpcId 为 null 时应直接返回', async () => {
      forgeNpcId = null;
      const result = await doForge('test_recipe');
      expect(result).toBeUndefined();
    });
  });

  describe('FRG-09: createForgeProgress / removeForgeProgress', () => {
    it('createForgeProgress 应创建进度覆盖层', () => {
      const card = document.createElement('div');
      card.className = 'forge-recipe-card';
      document.body.appendChild(card);
      const overlay = createForgeProgress(card);
      expect(overlay).not.toBeNull();
      expect(overlay.classList.contains('forge-progress-overlay')).toBe(true);
      expect(card.querySelector('.forge-progress-bar')).not.toBeNull();
      expect(card.querySelector('.forge-progress-fill')).not.toBeNull();
      expect(card.querySelector('.forge-progress-text')).not.toBeNull();
    });

    it('removeForgeProgress 应移除进度覆盖层', () => {
      const card = document.createElement('div');
      card.className = 'forge-recipe-card';
      document.body.appendChild(card);
      const overlay = createForgeProgress(card);
      expect(card.contains(overlay)).toBe(true);
      removeForgeProgress(overlay);
      expect(card.contains(overlay)).toBe(false);
    });
  });

  describe('FRG-10: showForgeResult 锻造结果展示', () => {
    it('应展示锻造成功结果', () => {
      const result = {
        name: '精钢长剑',
        rarity: 'rare',
        affixes: [
          { name: '锋利', description: '攻击力+10' },
        ],
      };
      showForgeResult(result);
      const overlay = document.getElementById('forge-result-overlay');
      expect(overlay.classList.contains('active')).toBe(true);
      const content = document.getElementById('forge-result-content');
      expect(content.innerHTML).toContain('精钢长剑');
      expect(content.innerHTML).toContain('锋利');
    });

    it('closeForgeResult 应关闭结果弹窗', () => {
      closeForgeResult();
      const overlay = document.getElementById('forge-result-overlay');
      expect(overlay.classList.contains('active')).toBe(false);
    });
  });
});
