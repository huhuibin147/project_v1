// 背包模块测试

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

describe('背包模块 (inventory.js)', () => {
  beforeAll(() => {
    loadScript('managers/GameManager.js');
    loadScript('inventory.js');
  });

  describe('INV-01~02: formatItemStats 格式化属性', () => {
    it('INV-01: 空 stats 应返回空字符串', () => {
      expect(formatItemStats(null)).toBe('');
      expect(formatItemStats(undefined)).toBe('');
      expect(formatItemStats({})).toBe('');
    });

    it('INV-02: 应正确格式化单个属性', () => {
      var result = formatItemStats({ attack: 10 });
      expect(result).toContain('攻');
      expect(result).toContain('10');
    });

    it('INV-02: 应正确格式化多个属性', () => {
      var result = formatItemStats({ attack: 10, defense: 5 });
      expect(result).toContain('攻+10');
      expect(result).toContain('防+5');
    });

    it('应格式化所有支持的属性类型', () => {
      var result = formatItemStats({
        attack: 10,
        defense: 5,
        speed: 3,
        max_hp: 20,
        max_mp: 10,
      });
      expect(result).toContain('攻+10');
      expect(result).toContain('防+5');
      expect(result).toContain('速+3');
      expect(result).toContain('HP+20');
      expect(result).toContain('MP+10');
    });
  });

  describe('INV-03: RARITY_DEF 稀有度定义', () => {
    it('应包含5个稀有度等级', () => {
      var keys = Object.keys(RARITY_DEF);
      expect(keys).toHaveLength(5);
      expect(keys).toContain('common');
      expect(keys).toContain('uncommon');
      expect(keys).toContain('rare');
      expect(keys).toContain('epic');
      expect(keys).toContain('legendary');
    });

    it('每个稀有度应有 name 和 color', () => {
      Object.values(RARITY_DEF).forEach(rarity => {
        expect(rarity).toHaveProperty('name');
        expect(rarity).toHaveProperty('color');
        expect(typeof rarity.name).toBe('string');
        expect(typeof rarity.color).toBe('string');
      });
    });
  });

  describe('INV-04: STAT_LABELS_INV 属性标签', () => {
    it('应包含5个属性标签', () => {
      var keys = Object.keys(STAT_LABELS_INV);
      expect(keys).toHaveLength(5);
      expect(keys).toContain('attack');
      expect(keys).toContain('defense');
      expect(keys).toContain('speed');
      expect(keys).toContain('max_hp');
      expect(keys).toContain('max_mp');
    });

    it('每个标签应为非空字符串', () => {
      Object.values(STAT_LABELS_INV).forEach(label => {
        expect(typeof label).toBe('string');
        expect(label.length).toBeGreaterThan(0);
      });
    });
  });

  describe('INV-05: TIER_NAMES 等级段名称', () => {
    it('应包含3个等级段', () => {
      var keys = Object.keys(TIER_NAMES);
      expect(keys).toHaveLength(3);
      expect(keys).toContain('tier1');
      expect(keys).toContain('tier2');
      expect(keys).toContain('tier3');
    });
  });

  describe('INV-06: ITEMS_PER_PAGE 常量', () => {
    it('应等于 8', () => {
      expect(ITEMS_PER_PAGE).toBe(8);
    });
  });

  describe('INV-07~08: 面板初始状态', () => {
    it('INV-07: inventoryOpen 初始应为 false', () => {
      expect(inventoryOpen).toBe(false);
    });

    it('INV-08: shopOpen 初始应为 false', () => {
      expect(shopOpen).toBe(false);
    });

    it('shopNpcId 初始应为 null', () => {
      expect(shopNpcId).toBeNull();
    });
  });

  describe('inventoryState 初始值', () => {
    it('items 应为空数组', () => {
      expect(inventoryState.items).toEqual([]);
    });

    it('gold 应为 0', () => {
      expect(inventoryState.gold).toBe(0);
    });
  });

  describe('inventoryDisplay 初始值', () => {
    it('view 应为 "list"', () => {
      expect(inventoryDisplay.view).toBe('list');
    });

    it('filter 应为 "all"', () => {
      expect(inventoryDisplay.filter).toBe('all');
    });
  });

  describe('inventoryPage 初始值', () => {
    it('current 应为 1', () => {
      expect(inventoryPage.current).toBe(1);
    });
  });

  describe('shopPage 初始值', () => {
    it('current 应为 1', () => {
      expect(shopPage.current).toBe(1);
    });
  });
});