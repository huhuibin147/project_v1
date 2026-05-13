// 天赋模块测试

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

describe('天赋模块 (talent.js)', () => {
  beforeAll(() => {
    loadScript('managers/GameManager.js');
    loadScript('talent.js');
  });

  describe('TAL-01: TREE_NAMES 天赋树名称', () => {
    it('应包含6个天赋树', () => {
      var keys = Object.keys(TREE_NAMES);
      expect(keys).toHaveLength(6);
      expect(keys).toContain('berserk');
      expect(keys).toContain('guard');
      expect(keys).toContain('assassin');
      expect(keys).toContain('trick');
      expect(keys).toContain('element');
      expect(keys).toContain('holy');
    });

    it('每个天赋树名称应为非空字符串', () => {
      Object.values(TREE_NAMES).forEach(name => {
        expect(typeof name).toBe('string');
        expect(name.length).toBeGreaterThan(0);
      });
    });
  });

  describe('TAL-02: TREE_COLORS 天赋树颜色', () => {
    it('应包含6个颜色', () => {
      var keys = Object.keys(TREE_COLORS);
      expect(keys).toHaveLength(6);
    });

    it('每个颜色应为有效的颜色值', () => {
      Object.values(TREE_COLORS).forEach(color => {
        expect(typeof color).toBe('string');
        expect(color).toMatch(/^#[0-9a-fA-F]{6}$/);
      });
    });

    it('TREE_NAMES 和 TREE_COLORS 的 key 应一致', () => {
      expect(Object.keys(TREE_NAMES).sort()).toEqual(Object.keys(TREE_COLORS).sort());
    });
  });

  describe('TAL-03: talentPanelOpen 初始状态', () => {
    it('talentPanelOpen 初始应为 false', () => {
      expect(talentPanelOpen).toBe(false);
    });

    it('talentData 初始应为 null', () => {
      expect(talentData).toBeNull();
    });
  });
});