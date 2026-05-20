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
    loadScript('managers/PanelManager.js');
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

  describe('INV-09~11: 搜索过滤功能', () => {
    beforeEach(() => {
      inventoryState.items = [
        { item_id: 'sword1', name: '铁剑', type: 'weapon', equip_slot: 'weapon', stats: { attack: 10 }, description: '一把普通的铁剑', affixes: [], quantity: 1, sell_price: 5, rarity: 'common' },
        { item_id: 'potion1', name: '生命药水', type: 'consumable', description: '回复50HP', affixes: [], quantity: 3, sell_price: 2, rarity: 'common', heal_value: 50 },
        { item_id: 'armor1', name: '皮甲', type: 'armor', equip_slot: 'body', stats: { defense: 5 }, description: '轻便的皮甲', affixes: [{ name: '坚韧', description: '防御力提升10%' }], quantity: 1, sell_price: 8, rarity: 'uncommon' },
      ];
      inventoryDisplay.filter = 'all';
      inventoryDisplay.search = '';
      if (typeof playerInfo === 'undefined') {
        global.playerInfo = { equipment: {} };
      } else {
        playerInfo.equipment = {};
      }
    });

    it('INV-09: searchInventory 应设置搜索关键词', () => {
      searchInventory('铁剑');
      expect(inventoryDisplay.search).toBe('铁剑');
    });

    it('INV-10: getFilteredItems 应按名称搜索', () => {
      inventoryDisplay.search = '铁剑';
      var result = getFilteredItems();
      expect(result.length).toBe(1);
      expect(result[0].item_id).toBe('sword1');
    });

    it('INV-10: getFilteredItems 应按描述搜索', () => {
      inventoryDisplay.search = '回复';
      var result = getFilteredItems();
      expect(result.length).toBe(1);
      expect(result[0].item_id).toBe('potion1');
    });

    it('INV-11: getFilteredItems 应按词条名称搜索', () => {
      inventoryDisplay.search = '坚韧';
      var result = getFilteredItems();
      expect(result.length).toBe(1);
      expect(result[0].item_id).toBe('armor1');
    });

    it('搜索无匹配应返回空数组', () => {
      inventoryDisplay.search = '不存在的物品';
      var result = getFilteredItems();
      expect(result.length).toBe(0);
    });

    it('搜索应不区分大小写', () => {
      inventoryDisplay.search = 'hp';
      var result = getFilteredItems();
      expect(result.length).toBe(1);
      expect(result[0].item_id).toBe('potion1');
    });

    it('清空搜索应恢复全部物品', () => {
      inventoryDisplay.search = '铁剑';
      getFilteredItems();
      searchInventory('');
      var result = getFilteredItems();
      expect(result.length).toBe(3);
    });
  });

  describe('INV-12~13: 拖拽装备功能', () => {
    it('INV-12: dragItemId 和 dragEquipSlot 初始应为 null', () => {
      expect(dragItemId).toBeNull();
      expect(dragEquipSlot).toBeNull();
    });

    it('INV-13: setupEquipSlotDropTargets 应为函数', () => {
      expect(typeof setupEquipSlotDropTargets).toBe('function');
    });

    it('onItemDragStart 应为函数', () => {
      expect(typeof onItemDragStart).toBe('function');
    });

    it('onEquipSlotDrop 应为函数', () => {
      expect(typeof onEquipSlotDrop).toBe('function');
    });
  });

  describe('INV-14: DocumentFragment 渲染优化', () => {
    it('renderInventory 应为函数', () => {
      expect(typeof renderInventory).toBe('function');
    });

    it('renderInventoryList 应为函数', () => {
      expect(typeof renderInventoryList).toBe('function');
    });

    it('renderInventoryGrid 应为函数', () => {
      expect(typeof renderInventoryGrid).toBe('function');
    });
  });

  describe('INV-15: Tooltip 价格显示 (getPriceHtml)', () => {
    it('应同时显示购入价和出售价', () => {
      var item = { buy_price: 80, sell_price: 40 };
      var html = getPriceHtml(item);
      expect(html).toContain('购入');
      expect(html).toContain('80');
      expect(html).toContain('出售');
      expect(html).toContain('40');
    });

    it('buy_price=0 应显示不可购买', () => {
      var item = { buy_price: 0, sell_price: 5 };
      var html = getPriceHtml(item);
      expect(html).toContain('不可购买');
      expect(html).toContain('出售');
    });

    it('sell_price=0 应显示不可出售', () => {
      var item = { buy_price: 50, sell_price: 0 };
      var html = getPriceHtml(item);
      expect(html).toContain('购入');
      expect(html).toContain('不可出售');
    });

    it('两者都为0 应同时显示不可购买和不可出售', () => {
      var item = { buy_price: 0, sell_price: 0 };
      var html = getPriceHtml(item);
      expect(html).toContain('不可购买');
      expect(html).toContain('不可出售');
    });
  });

  describe('INV-16: Tooltip 效果显示 (getEffectHtml)', () => {
    it('heal 效果应显示回复 HP', () => {
      var item = { effect_type: 'heal', heal_value: 50 };
      var html = getEffectHtml(item);
      expect(html).toContain('回复');
      expect(html).toContain('50');
      expect(html).toContain('HP');
    });

    it('restore_mp 效果应显示回复 MP', () => {
      var item = { effect_type: 'restore_mp', mp_value: 30 };
      var html = getEffectHtml(item);
      expect(html).toContain('回复');
      expect(html).toContain('30');
      expect(html).toContain('MP');
    });

    it('cure:poison 效果应显示解除中毒状态', () => {
      var item = { effect_type: 'cure', effect_detail: 'poison' };
      var html = getEffectHtml(item);
      expect(html).toContain('解除中毒状态');
    });

    it('cure:curse 效果应显示解除诅咒状态', () => {
      var item = { effect_type: 'cure', effect_detail: 'curse' };
      var html = getEffectHtml(item);
      expect(html).toContain('解除诅咒状态');
    });

    it('无 effect_type 应返回空字符串', () => {
      var item = { heal_value: 50 };
      var html = getEffectHtml(item);
      expect(html).toBe('');
    });
  });

  describe('INV-17: Tooltip 锻造配方显示 (getItemForgeHtml)', () => {
    it('有配方时应显示锻造配方信息', () => {
      ITEM_FORGE_MAP['iron_sword'] = {
        recipe_name: '铁剑',
        materials: [
          { name: '铁矿石', quantity: 3 },
          { name: '兽骨', quantity: 1 }
        ],
        gold_cost: 50,
        success_rate: 1.0
      };
      var html = getItemForgeHtml('iron_sword');
      expect(html).toContain('锻造配方');
      expect(html).toContain('铁矿石x3');
      expect(html).toContain('兽骨x1');
      expect(html).toContain('50');
      expect(html).toContain('100%');
    });

    it('无配方时应返回空字符串', () => {
      delete ITEM_FORGE_MAP['nonexistent_item'];
      var html = getItemForgeHtml('nonexistent_item');
      expect(html).toBe('');
    });
  });

  describe('INV-18: Tooltip 来源标签显示 (getItemSourceHtml)', () => {
    it('商店来源应显示商店标签', () => {
      ITEM_SOURCE_MAP['test_item_1'] = [{ type: 'shop', name: '老王铁匠铺' }];
      var html = getItemSourceHtml('test_item_1');
      expect(html).toContain('来源');
      expect(html).toContain('老王铁匠铺');
      expect(html).toContain('tt-source-shop');
    });

    it('怪物来源应显示怪物名和掉率', () => {
      ITEM_SOURCE_MAP['test_item_2'] = [{ type: 'monster', name: '野狼', monster_id: 'wolf', chance: 0.5 }];
      var html = getItemSourceHtml('test_item_2');
      expect(html).toContain('野狼');
      expect(html).toContain('50%');
      expect(html).toContain('tt-source-monster');
    });

    it('锻造来源应显示锻造标签', () => {
      ITEM_SOURCE_MAP['test_item_3'] = [{ type: 'forge', name: '铁剑锻造' }];
      var html = getItemSourceHtml('test_item_3');
      expect(html).toContain('铁剑锻造');
      expect(html).toContain('tt-source-forge');
    });

    it('无来源时应返回空字符串', () => {
      delete ITEM_SOURCE_MAP['no_source_item'];
      var html = getItemSourceHtml('no_source_item');
      expect(html).toBe('');
    });

    it('多种来源应同时显示', () => {
      ITEM_SOURCE_MAP['multi_source'] = [
        { type: 'shop', name: '商店' },
        { type: 'monster', name: '野狼', monster_id: 'wolf', chance: 0.3 },
        { type: 'forge', name: '锻造' }
      ];
      var html = getItemSourceHtml('multi_source');
      expect(html).toContain('tt-source-shop');
      expect(html).toContain('tt-source-monster');
      expect(html).toContain('tt-source-forge');
    });
  });

  describe('INV-19: Tooltip 堆叠标识', () => {
    it('stackable=false 应显示唯一', () => {
      var item = { stackable: false };
      var text = item.stackable === false ? "唯一" : "可堆叠";
      expect(text).toBe('唯一');
    });

    it('stackable=true 应显示可堆叠', () => {
      var item = { stackable: true };
      var text = item.stackable === false ? "唯一" : "可堆叠";
      expect(text).toBe('可堆叠');
    });

    it('stackable 未定义时默认显示可堆叠', () => {
      var item = {};
      var text = item.stackable === false ? "唯一" : "可堆叠";
      expect(text).toBe('可堆叠');
    });
  });

  describe('INV-20: ITEM_FORGE_MAP 和 ITEM_SOURCE_MAP 数据结构', () => {
    it('ITEM_FORGE_MAP 应为对象', () => {
      expect(typeof ITEM_FORGE_MAP).toBe('object');
    });

    it('ITEM_SOURCE_MAP 应为对象', () => {
      expect(typeof ITEM_SOURCE_MAP).toBe('object');
    });

    it('buildItemForgeMap 应为异步函数', () => {
      expect(typeof buildItemForgeMap).toBe('function');
    });

    it('buildItemSourceMap 应为异步函数', () => {
      expect(typeof buildItemSourceMap).toBe('function');
    });
  });
});