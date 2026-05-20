let inventoryOpen = false;

// 注册面板
PanelManager.register('inventory',
  () => { inventoryOpen = true; document.getElementById("inventory-panel").classList.add("active"); },
  () => { inventoryOpen = false; document.getElementById("inventory-panel").classList.remove("active"); }
);
let shopOpen = false;

// 注册面板
PanelManager.register('shop',
  () => { shopOpen = true; document.getElementById("shop-panel").classList.add("active"); },
  () => { shopOpen = false; document.getElementById("shop-panel").classList.remove("active"); }
);
let shopNpcId = null;
let ctxMenuEl = null;

const ITEMS_PER_PAGE = 8;
const SHOP_ITEMS_PER_PAGE = 10;
const inventoryPage = { current: 1 };
const shopPage = { current: 1 };
const shopInvPage = { current: 1 };

const inventoryState = {
  items: [],
  gold: 0,
};

const inventoryDisplay = {
  view: "list",
  filter: "all",
  search: "",
  sort: "default",
};

const shopState = {
  name: "",
  items: [],
  gold: 0,
};

const shopDisplay = {
  filter: "all",
  search: "",
  sort: "default",
};

const shopInvDisplay = {
  filter: "all",
  search: "",
  sort: "default",
};

const RARITY_ORDER = { common: 0, uncommon: 1, rare: 2, epic: 3, legendary: 4 };

const STAT_LABELS_INV = {
  attack: "攻",
  defense: "防",
  speed: "速",
  max_hp: "HP",
  max_mp: "MP",
};

const RARITY_DEF = {
  common:    { name: "普通", color: "#aaaaaa" },
  uncommon:  { name: "优秀", color: "#1eff00" },
  rare:      { name: "稀有", color: "#0070dd" },
  epic:      { name: "史诗", color: "#a335ee" },
  legendary: { name: "传说", color: "#ff8000" },
};

const TIER_NAMES = {
  tier1: "初级",
  tier2: "中级",
  tier3: "高级",
};

function formatItemStats(stats) {
  if (!stats) return "";
  const parts = [];
  for (const [key, val] of Object.entries(stats)) {
    if (val === 0) continue;
    const label = STAT_LABELS_INV[key] || key;
    const cls = val < 0 ? "stat-neg" : "";
    parts.push(`<span class="${cls}">${label}${val > 0 ? "+" : ""}${val}</span>`);
  }
  return parts.join(" ");
}

function getRarityColor(rarity) {
  return (RARITY_DEF[rarity] || RARITY_DEF.common).color;
}

function getRarityName(rarity) {
  return (RARITY_DEF[rarity] || RARITY_DEF.common).name;
}

function getTierName(tier) {
  return TIER_NAMES[tier] || "";
}

function getLevelRangeText(item) {
  if (!item.level_range) return "";
  return `Lv.${item.level_range}`;
}

function buildCompareHtml(item) {
  if (!item.equip_slot) return "";
  const equipped = playerInfo.equipment || {};
  const current = equipped[item.equip_slot];
  if (!current || !current.stats) return "";

  const diff = {};
  for (const key of ["attack", "defense", "speed", "max_hp", "max_mp"]) {
    const newVal = (item.stats && item.stats[key]) || 0;
    const oldVal = (current.stats && current.stats[key]) || 0;
    const d = newVal - oldVal;
    if (d !== 0) diff[key] = d;
  }

  if (Object.keys(diff).length === 0) return "";

  const parts = [];
  for (const [key, d] of Object.entries(diff)) {
    const label = STAT_LABELS_INV[key] || key;
    const cls = d > 0 ? "compare-up" : "compare-down";
    parts.push(`<span class="${cls}">${label}${d > 0 ? "+" : ""}${d}</span>`);
  }
  return `<div class="item-compare">对比${current.name}: ${parts.join(" ")}</div>`;
}

function buildCompareBarHtml(item) {
  if (!item.equip_slot) return "";
  const equipped = playerInfo.equipment || {};
  const current = equipped[item.equip_slot];
  if (!current || !current.stats) return "";

  const statKeys = ["attack", "defense", "speed", "max_hp", "max_mp"];
  const statMaxValues = { attack: 100, defense: 80, speed: 30, max_hp: 200, max_mp: 100 };
  let rows = "";

  for (const key of statKeys) {
    const newVal = (item.stats && item.stats[key]) || 0;
    const oldVal = (current.stats && current.stats[key]) || 0;
    if (newVal === 0 && oldVal === 0) continue;

    const label = STAT_LABELS_INV[key] || key;
    const maxVal = statMaxValues[key] || 100;
    const newPct = Math.min(100, Math.max(0, (newVal / maxVal) * 100));
    const oldPct = Math.min(100, Math.max(0, (oldVal / maxVal) * 100));
    const diff = newVal - oldVal;
    const diffCls = diff > 0 ? "bar-diff-up" : diff < 0 ? "bar-diff-down" : "";
    const diffText = diff !== 0 ? `${diff > 0 ? "+" : ""}${diff}` : "";

    rows += `
      <div class="compare-row">
        <span class="compare-label">${label}</span>
        <div class="compare-bar-track">
          <div class="compare-bar-old" style="width:${oldPct}%"></div>
          <div class="compare-bar-new" style="width:${newPct}%"></div>
        </div>
        <span class="compare-val">${newVal}</span>
        <span class="compare-diff ${diffCls}">${diffText}</span>
      </div>`;
  }

  if (!rows) return "";

  return `<div class="compare-bar-section">
    <div class="compare-bar-title">装备对比：${current.name}</div>
    ${rows}
  </div>`;
}

async function fetchInventory() {
  try {
    const resp = await fetch("/api/inventory");
    const data = await resp.json();
    inventoryState.items = data.items || [];
    inventoryState.gold = data.gold || 0;
    updateGoldDisplay();
  } catch (e) {
    console.error("获取背包失败:", e);
  }
}

async function fetchShop(npcId) {
  try {
    const resp = await fetch(`/api/shop?npc_id=${npcId}`);
    const data = await resp.json();
    shopState.name = data.name;
    shopState.items = data.items;
    shopState.gold = data.gold;
  } catch (e) {
    console.error("获取商店失败:", e);
  }
}

function openInventory() {
  if (PanelManager.isAnyOpen() || GameManager.isMenuOpen()) return;
  inventoryPage.current = 1;
  inventoryDisplay.sort = "default";
  const sortEl = document.getElementById("inventory-sort");
  if (sortEl) sortEl.value = "default";
  fetchInventory().then(() => {
    renderInventory();
    setupEquipSlotDropTargets();
  });
  PanelManager.open('inventory');
}

function closeInventory() {
  PanelManager.close('inventory');
}

function getFilteredItems() {
  let items = inventoryState.items;
  items = applyItemFilter(items, inventoryDisplay.filter);
  items = applyItemSearch(items, inventoryDisplay.search);
  items = applyItemSort(items, inventoryDisplay.sort, "sell_price");
  return items;
}

function switchInventoryView(view) {
  inventoryDisplay.view = view;
  document.getElementById("view-list").classList.toggle("active", view === "list");
  document.getElementById("view-grid").classList.toggle("active", view === "grid");
  const container = document.getElementById("inventory-items");
  container.classList.toggle("grid-view", view === "grid");
  inventoryPage.current = 1;
  renderInventory();
}

function filterInventory(filter) {
  inventoryDisplay.filter = filter;
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.filter === filter);
  });
  inventoryPage.current = 1;
  renderInventory();
}

function sortInventory(sort) {
  inventoryDisplay.sort = sort;
  inventoryPage.current = 1;
  renderInventory();
}

function applyItemFilter(items, filter) {
  if (filter === "all") return items;
  if (filter === "armor") {
    return items.filter(it => it.type === "armor" || (it.equip_slot && it.equip_slot !== "weapon" && it.equip_slot !== "accessory"));
  } else if (filter === "weapon") {
    return items.filter(it => it.type === "weapon" || it.equip_slot === "weapon");
  } else {
    return items.filter(it => it.type === filter);
  }
}

function applyItemSearch(items, query) {
  if (!query) return items;
  const q = query.toLowerCase();
  return items.filter(it =>
    (it.name && it.name.toLowerCase().includes(q)) ||
    (it.description && it.description.toLowerCase().includes(q)) ||
    (it.affixes && it.affixes.some(a => {
      const name = typeof a === "object" ? a.name : a;
      return name && name.toLowerCase().includes(q);
    }))
  );
}

function applyItemSort(items, sort, priceKey) {
  if (sort === "default") return items;
  const sorted = [...items];
  if (sort === "rarity") {
    sorted.sort((a, b) => (RARITY_ORDER[b.rarity] || 0) - (RARITY_ORDER[a.rarity] || 0));
  } else if (sort === "price_asc") {
    sorted.sort((a, b) => (a[priceKey] || 0) - (b[priceKey] || 0));
  } else if (sort === "price_desc") {
    sorted.sort((a, b) => (b[priceKey] || 0) - (a[priceKey] || 0));
  } else if (sort === "name") {
    sorted.sort((a, b) => (a.name || "").localeCompare(b.name || "", "zh"));
  }
  return sorted;
}

function searchShop(query) {
  shopDisplay.search = query.trim();
  shopPage.current = 1;
  renderShop();
}

function filterShop(filter) {
  shopDisplay.filter = filter;
  document.querySelectorAll("[data-shop-filter]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.shopFilter === filter);
  });
  shopPage.current = 1;
  renderShop();
}

function sortShop(sort) {
  shopDisplay.sort = sort;
  shopPage.current = 1;
  renderShop();
}

function searchShopInventory(query) {
  shopInvDisplay.search = query.trim();
  shopInvPage.current = 1;
  renderShop();
}

function filterShopInventory(filter) {
  shopInvDisplay.filter = filter;
  document.querySelectorAll("[data-shop-inv-filter]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.shopInvFilter === filter);
  });
  shopInvPage.current = 1;
  renderShop();
}

function sortShopInventory(sort) {
  shopInvDisplay.sort = sort;
  shopInvPage.current = 1;
  renderShop();
}

function adjustQty(prefix, itemId, delta) {
  const input = document.getElementById(`${prefix}_${itemId}`);
  if (!input) return;
  let val = parseInt(input.value) || 1;
  val = Math.max(1, Math.min(parseInt(input.max) || 99, val + delta));
  input.value = val;
}

function getQty(prefix, itemId) {
  const input = document.getElementById(`${prefix}_${itemId}`);
  return input ? (parseInt(input.value) || 1) : 1;
}

function setMaxQty(prefix, itemId) {
  const input = document.getElementById(`${prefix}_${itemId}`);
  if (input) input.value = input.max;
}

function searchInventory(query) {
  inventoryDisplay.search = query.trim();
  inventoryPage.current = 1;
  renderInventory();
}

function renderInventory() {
  const container = document.getElementById("inventory-items");
  container.classList.toggle("grid-view", inventoryDisplay.view === "grid");

  const filteredItems = getFilteredItems();

  if (filteredItems.length === 0) {
    container.innerHTML = '<div class="empty-hint">背包空空如也...</div>';
    renderPagination("inventory-pagination", 0, inventoryPage);
    return;
  }

  const total = filteredItems.length;
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE);
  if (inventoryPage.current > totalPages) inventoryPage.current = totalPages;
  const start = (inventoryPage.current - 1) * ITEMS_PER_PAGE;
  const pageItems = filteredItems.slice(start, start + ITEMS_PER_PAGE);

  const fragment = document.createDocumentFragment();
  if (inventoryDisplay.view === "grid") {
    renderInventoryGrid(fragment, pageItems);
  } else {
    renderInventoryList(fragment, pageItems);
  }

  container.innerHTML = "";
  container.appendChild(fragment);

  document.getElementById("inventory-gold").textContent = inventoryState.gold;
  renderPagination("inventory-pagination", totalPages, inventoryPage);
}

function renderInventoryList(container, pageItems) {
  for (const item of pageItems) {
    const div = document.createElement("div");
    const rarityCls = item.rarity || "common";
    div.className = `item-card ${item.type} rarity-${rarityCls}`;

    const canEquip = item.equip_slot && item.stats;
    const isEquipped = isItemEquipped(item.item_id);

    if (canEquip && !isEquipped) {
      div.draggable = true;
      div.dataset.itemId = item.item_id;
      div.dataset.equipSlot = item.equip_slot;
      div.addEventListener("dragstart", onItemDragStart);
    }

    let statsHtml = "";
    if (canEquip && item.stats) {
      statsHtml = `<div class="item-stats-line">${formatItemStats(item.stats)}</div>`;
    }

    let healHtml = "";
    if (item.heal_value && item.heal_value > 0) {
      healHtml = `<div class="item-heal-value">回复 <span class="heal-num">${item.heal_value}</span> HP</div>`;
    }
    let mpHtml = "";
    if (item.mp_value && item.mp_value > 0) {
      mpHtml = `<div class="item-heal-value">回复 <span class="heal-num">${item.mp_value}</span> MP</div>`;
    }

    let equipBtnHtml = "";
    if (canEquip && !isEquipped) {
      if (canPlayerEquipItem(item)) {
        equipBtnHtml = `<button class="btn-equip" onclick="doEquip('${item.item_id}')">装备</button>`;
      } else {
        const clsName = getClassLabel(item.required_class);
        equipBtnHtml = `<span style="color:#ff6b6b;font-size:11px;">${clsName}专属</span>`;
      }
    } else if (isEquipped) {
      equipBtnHtml = `<span style="color:#6bafff;font-size:11px;font-weight:bold;">已装备</span>`;
    }

    let useBtnHtml = "";
    if ((item.type === "consumable" || item.type === "food") && !isEquipped) {
      useBtnHtml = `<button class="btn-use" onclick="doUseItem('${item.item_id}')">使用</button>`;
    }

    const rarityColor = getRarityColor(rarityCls);
    const rarityName = getRarityName(rarityCls);
    const tierName = item.tier ? getTierName(item.tier) : "";
    const levelText = getLevelRangeText(item);
    const compareHtml = canEquip && !isEquipped ? buildCompareHtml(item) : "";

    let affixesHtml = "";
    if (item.affixes && item.affixes.length > 0) {
      affixesHtml = `<div class="item-affixes">${item.affixes.map(a => {
        if (typeof a === "object" && a.name) {
          const shortDesc = a.description ? a.description.substring(0, 12) : "";
          return `<span class="affix-tag" title="${a.description || ""}">${a.name}${shortDesc ? `<span class="affix-desc">${shortDesc}</span>` : ""}</span>`;
        }
        return `<span class="affix-tag">${a}</span>`;
      }).join("")}</div>`;
    }

    const classRestrictionHtml = getClassRestrictionHtml(item);

    div.innerHTML = `
      <div class="item-header">
        <span class="item-name" style="color:${rarityColor}">${item.name}</span>
        <span class="item-qty">x${item.quantity}</span>
      </div>
      <div class="item-type">${getTypeLabel(item.type)}${canEquip ? ` · ${getSlotLabel(item.equip_slot)}` : ""}${tierName ? ` · ${tierName}` : ""}${levelText ? ` · ${levelText}` : ""} <span style="color:${rarityColor}">[${rarityName}]</span>${classRestrictionHtml}</div>
      ${statsHtml}
      ${healHtml}
      ${mpHtml}
      ${affixesHtml}
      ${compareHtml}
      <div class="item-desc">${item.description}</div>
      <div class="item-actions">
        <span class="item-price">出售价: ${item.sell_price} 金</span>
        ${useBtnHtml}
        ${equipBtnHtml}
      </div>
    `;

    div.addEventListener("dblclick", (e) => {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
      if (canEquip && !isEquipped && canPlayerEquipItem(item)) {
        doEquip(item.item_id);
      } else if ((item.type === "consumable" || item.type === "food") && !isEquipped) {
        doUseItem(item.item_id);
      }
    });

    div.addEventListener("click", (e) => {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
      if (e.shiftKey && shopOpen && item.sell_price && item.sell_price > 0 && !isEquipped) {
        e.preventDefault();
        doTrade("sell", item.item_id, item.quantity);
      }
    });

    div.addEventListener("contextmenu", (e) => {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
      showItemCtxMenu(e, item, "inventory");
    });

    container.appendChild(div);
  }
}

function renderInventoryGrid(container, pageItems) {
  for (const item of pageItems) {
    const div = document.createElement("div");
    const rarityCls = item.rarity || "common";
    div.className = `item-grid-cell ${item.type} rarity-${rarityCls}`;

    const canEquip = item.equip_slot && item.stats;
    const isEquipped = isItemEquipped(item.item_id);

    if (canEquip && !isEquipped) {
      div.draggable = true;
      div.dataset.itemId = item.item_id;
      div.dataset.equipSlot = item.equip_slot;
      div.addEventListener("dragstart", onItemDragStart);
    }
    const rarityColor = getRarityColor(rarityCls);

    let equipMark = "";
    if (isEquipped) {
      equipMark = `<div class="grid-equipped">✓</div>`;
    }

    let qtyBadge = "";
    if (item.quantity > 1) {
      qtyBadge = `<div class="grid-qty">${item.quantity}</div>`;
    }

    let actionBtn = "";
    if (canEquip && !isEquipped) {
      if (canPlayerEquipItem(item)) {
        actionBtn = `<button class="grid-action" onclick="doEquip('${item.item_id}')">装备</button>`;
      } else {
        const clsName = getClassLabel(item.required_class);
        actionBtn = `<span class="grid-action text" style="color:#ff6b6b;">${clsName}专属</span>`;
      }
    } else if (isEquipped) {
      actionBtn = `<span class="grid-action text">已装备</span>`;
    } else if (item.type === "consumable" || item.type === "food") {
      actionBtn = `<button class="grid-action" onclick="doUseItem('${item.item_id}')">使用</button>`;
    }

    const classRestrictionHtml = getClassRestrictionHtml(item);

    div.innerHTML = `
      ${equipMark}
      ${qtyBadge}
      <div class="grid-icon">${getTypeIcon(item.type)}</div>
      <div class="grid-name" style="color:${rarityColor}">${item.name}</div>
      <div class="grid-type">${getTypeLabel(item.type)}${classRestrictionHtml}</div>
      ${actionBtn}
    `;

    div.addEventListener("click", (e) => {
      if (e.target.tagName === "BUTTON") return;
      showItemTooltip(item, div);
    });

    div.addEventListener("contextmenu", (e) => {
      if (e.target.tagName === "BUTTON") return;
      showItemCtxMenu(e, item, "inventory");
    });

    container.appendChild(div);
  }
}

function getTypeIcon(type) {
  const icons = {
    weapon: "⚔️",
    armor: "🛡️",
    consumable: "🧪",
    food: "🍞",
    tool: "🔧",
    material: "💎",
    accessory: "💍",
  };
  return icons[type] || "📦";
}

let tooltipEl = null;

const ITEM_SOURCE_MAP = {};
const ITEM_FORGE_MAP = {};

async function buildItemSourceMap() {
  for (const key of Object.keys(ITEM_SOURCE_MAP)) {
    delete ITEM_SOURCE_MAP[key];
  }

  try {
    const [npcResp, dropMapResp] = await Promise.all([
      fetch("/api/npcs").catch(() => null),
      fetch("/api/monsters/drop_map").catch(() => null)
    ]);

    if (npcResp && npcResp.ok) {
      const npcList = await npcResp.json();
      const npcs = Array.isArray(npcList) ? npcList : [];
      for (const npc of npcs) {
        if (npc.inventory && Array.isArray(npc.inventory)) {
          for (const entry of npc.inventory) {
            const itemId = typeof entry === "string" ? entry : entry.item_id;
            if (!itemId) continue;
            if (!ITEM_SOURCE_MAP[itemId]) ITEM_SOURCE_MAP[itemId] = [];
            const shopName = npc.name || npc.npc_id || "";
            const exists = ITEM_SOURCE_MAP[itemId].some(s => s.type === "shop" && s.name === shopName);
            if (shopName && !exists) {
              ITEM_SOURCE_MAP[itemId].push({ type: "shop", name: shopName });
            }
          }
        }
      }
    }

    if (dropMapResp && dropMapResp.ok) {
      const data = await dropMapResp.json();
      const dropMap = data.drop_map || {};
      for (const [itemId, drops] of Object.entries(dropMap)) {
        if (!ITEM_SOURCE_MAP[itemId]) ITEM_SOURCE_MAP[itemId] = [];
        for (const drop of drops) {
          const exists = ITEM_SOURCE_MAP[itemId].some(
            s => s.type === "monster" && s.monster_id === drop.monster_id
          );
          if (!exists) {
            ITEM_SOURCE_MAP[itemId].push({
              type: "monster",
              name: drop.monster_name,
              monster_id: drop.monster_id,
              chance: drop.chance,
            });
          }
        }
      }
    }
  } catch (e) {
    console.error("构建物品来源映射失败:", e);
  }
}

async function buildItemForgeMap() {
  for (const key of Object.keys(ITEM_FORGE_MAP)) {
    delete ITEM_FORGE_MAP[key];
  }

  try {
    const resp = await fetch("/api/forge/recipes_map");
    if (resp.ok) {
      const data = await resp.json();
      const map = data.recipes_map || {};
      for (const [itemId, recipe] of Object.entries(map)) {
        ITEM_FORGE_MAP[itemId] = recipe;
        if (!ITEM_SOURCE_MAP[itemId]) ITEM_SOURCE_MAP[itemId] = [];
        const exists = ITEM_SOURCE_MAP[itemId].some(s => s.type === "forge");
        if (!exists) {
          ITEM_SOURCE_MAP[itemId].push({ type: "forge", name: recipe.recipe_name || "锻造" });
        }
      }
    }
  } catch (e) {
    console.error("构建锻造配方映射失败:", e);
  }
}

function getItemSourceHtml(itemId) {
  const sources = ITEM_SOURCE_MAP[itemId];
  if (!sources || sources.length === 0) return "";
  const tags = sources.map(s => {
    if (s.type === "shop") {
      return `<span class="tt-source-tag tt-source-shop">${s.name}</span>`;
    } else if (s.type === "monster") {
      const chanceText = s.chance != null ? ` ${Math.round(s.chance * 100)}%` : "";
      return `<span class="tt-source-tag tt-source-monster">${s.name}${chanceText}</span>`;
    } else if (s.type === "forge") {
      return `<span class="tt-source-tag tt-source-forge">${s.name}</span>`;
    }
    return `<span class="tt-source-tag">${s.name}</span>`;
  }).join("");
  return `<div class="tt-source">来源: ${tags}</div>`;
}

function getItemForgeHtml(itemId) {
  const recipe = ITEM_FORGE_MAP[itemId];
  if (!recipe) return "";
  const mats = recipe.materials.map(m => `${m.name}x${m.quantity}`).join("  ");
  const rate = Math.round(recipe.success_rate * 100);
  return `<div class="tt-forge">
    <div class="tt-forge-title">锻造配方</div>
    <div class="tt-forge-mats">材料: ${mats}</div>
    <div class="tt-forge-cost">费用: ${recipe.gold_cost}金  成功率: ${rate}%</div>
  </div>`;
}

function getEffectHtml(item) {
  const effectType = item.effect_type;
  if (!effectType) return "";
  const parts = [];
  if (effectType === "heal" && item.heal_value) {
    parts.push(`<div class="tt-effect">回复 <span class="heal-num">${item.heal_value}</span> HP</div>`);
  }
  if (effectType === "restore_mp" && item.mp_value) {
    parts.push(`<div class="tt-effect">回复 <span class="heal-num">${item.mp_value}</span> MP</div>`);
  }
  if (effectType === "cure") {
    const detail = item.effect_detail;
    const cureLabels = { poison: "中毒", curse: "诅咒", burn: "灼烧", freeze: "冰冻" };
    const label = cureLabels[detail] || detail || "异常";
    parts.push(`<div class="tt-effect">解除${label}状态</div>`);
  }
  return parts.join("");
}

function getPriceHtml(item) {
  const buyPrice = item.buy_price || 0;
  const sellPrice = item.sell_price || 0;
  const parts = [];
  if (buyPrice > 0) {
    parts.push(`购入: ${buyPrice}金`);
  } else {
    parts.push(`<span class="price-unavailable">不可购买</span>`);
  }
  if (sellPrice > 0) {
    parts.push(`出售: ${sellPrice}金`);
  } else {
    parts.push(`<span class="price-unavailable">不可出售</span>`);
  }
  return `<div class="tt-price">${parts.join("  ")}</div>`;
}

function showItemTooltip(item, anchorEl) {
  if (tooltipEl) {
    tooltipEl.remove();
    tooltipEl = null;
  }

  const canEquip = item.equip_slot && item.stats;
  const isEquipped = isItemEquipped(item.item_id);
  const rarityColor = getRarityColor(item.rarity || "common");
  const rarityName = getRarityName(item.rarity || "common");
  const tierName = item.tier ? getTierName(item.tier) : "";
  const levelText = getLevelRangeText(item);
  const stackableText = item.stackable === false ? "唯一" : "可堆叠";

  let statsHtml = "";
  if (canEquip && item.stats) {
    statsHtml = `<div class="tt-stats">${formatItemStats(item.stats)}</div>`;
  }

  const effectHtml = getEffectHtml(item);

  let compareHtml = canEquip && !isEquipped ? buildCompareHtml(item) : "";
  const compareBarHtml = canEquip && !isEquipped ? buildCompareBarHtml(item) : "";
  const classRestrictionHtml = getClassRestrictionHtml(item);

  let affixesFullHtml = "";
  if (item.affixes && item.affixes.length > 0) {
    affixesFullHtml = `<div class="tt-affixes">${item.affixes.map(a => {
      if (typeof a === "object" && a.name) {
        return `<div class="tt-affix"><span class="tt-affix-name">${a.name}</span>${a.description ? `<span class="tt-affix-desc">${a.description}</span>` : ""}</div>`;
      }
      return `<div class="tt-affix"><span class="tt-affix-name">${a}</span></div>`;
    }).join("")}</div>`;
  }

  const forgeHtml = getItemForgeHtml(item.item_id);

  const tt = document.createElement("div");
  tt.className = "item-tooltip";
  tt.innerHTML = `
    <div class="tt-header">
      <span class="tt-name" style="color:${rarityColor}">${item.name}</span>
      <span class="tt-qty">x${item.quantity}</span>
    </div>
    <div class="tt-meta">${getTypeLabel(item.type)}${canEquip ? ` · ${getSlotLabel(item.equip_slot)}` : ""}${tierName ? ` · ${tierName}` : ""}${levelText ? ` · ${levelText}` : ""} · <span class="tt-stackable">${stackableText}</span> <span style="color:${rarityColor}">[${rarityName}]</span>${classRestrictionHtml}</div>
    ${statsHtml}
    ${effectHtml}
    ${affixesFullHtml}
    ${compareHtml}
    ${compareBarHtml}
    <div class="tt-desc">${item.description}</div>
    ${forgeHtml}
    ${getItemSourceHtml(item.item_id)}
    ${getPriceHtml(item)}
  `;

  document.body.appendChild(tt);
  tooltipEl = tt;

  const rect = anchorEl.getBoundingClientRect();
  const ttWidth = tt.offsetWidth;
  const ttHeight = tt.offsetHeight;
  let left = rect.right + 8;
  let top = rect.top;
  if (left + ttWidth + 8 > window.innerWidth) {
    left = rect.left - ttWidth - 8;
  }
  if (top + ttHeight + 8 > window.innerHeight) {
    top = window.innerHeight - ttHeight - 8;
  }
  if (top < 0) top = 4;
  tt.style.left = left + "px";
  tt.style.top = top + "px";

  const closeTooltip = (e) => {
    if (!tt.contains(e.target) && e.target !== anchorEl && !anchorEl.contains(e.target)) {
      tt.remove();
      tooltipEl = null;
      document.removeEventListener("click", closeTooltip);
    }
  };
  setTimeout(() => document.addEventListener("click", closeTooltip), 10);
}

function isItemEquipped(itemId) {
  const equipment = playerInfo.equipment || {};
  for (const slot of ["weapon", "shield", "head", "body", "accessory"]) {
    if (equipment[slot] && equipment[slot].item_id === itemId) {
      return true;
    }
  }
  return false;
}

function getSlotLabel(slot) {
  const labels = {
    weapon: "武器槽",
    shield: "盾牌槽",
    head: "头部槽",
    body: "身体槽",
    accessory: "饰品槽",
  };
  return labels[slot] || slot;
}

function openShop(npcId) {
  if (PanelManager.isOpen('combat')) return;
  shopNpcId = npcId || activeNpcId || "blacksmith";
  shopPage.current = 1;
  shopInvPage.current = 1;
  shopDisplay.filter = "all";
  shopDisplay.search = "";
  shopDisplay.sort = "default";
  shopInvDisplay.filter = "all";
  shopInvDisplay.search = "";
  shopInvDisplay.sort = "default";
  const shopSearchEl = document.getElementById("shop-search");
  if (shopSearchEl) shopSearchEl.value = "";
  const shopInvSearchEl = document.getElementById("shop-inventory-search");
  if (shopInvSearchEl) shopInvSearchEl.value = "";
  const shopSortEl = document.getElementById("shop-sort");
  if (shopSortEl) shopSortEl.value = "default";
  const shopInvSortEl = document.getElementById("shop-inventory-sort");
  if (shopInvSortEl) shopInvSortEl.value = "default";
  document.querySelectorAll("[data-shop-filter]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.shopFilter === "all");
  });
  document.querySelectorAll("[data-shop-inv-filter]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.shopInvFilter === "all");
  });
  fetchShop(shopNpcId).then(() => {
    fetchInventory().then(() => renderShop());
  });
  PanelManager.open('shop');
}

function closeShop() {
  shopNpcId = null;
  PanelManager.close('shop');
}

function renderShop() {
  document.getElementById("shop-title").textContent = shopState.name;
  document.getElementById("shop-gold").textContent = shopState.gold;
  document.getElementById("player-gold-shop").textContent = inventoryState.gold;
  document.getElementById("inventory-gold-shop").textContent = inventoryState.gold;

  renderShopLeft();
  renderShopRight();
}

function getFilteredShopItems() {
  let items = shopState.items;
  items = applyItemFilter(items, shopDisplay.filter);
  items = applyItemSearch(items, shopDisplay.search);
  items = applyItemSort(items, shopDisplay.sort, "buy_price");
  return items;
}

function getFilteredShopInvItems() {
  let items = inventoryState.items;
  items = applyItemFilter(items, shopInvDisplay.filter);
  items = applyItemSearch(items, shopInvDisplay.search);
  items = applyItemSort(items, shopInvDisplay.sort, "sell_price");
  return items;
}

function renderShopLeft() {
  const container = document.getElementById("shop-items");
  container.innerHTML = "";

  const filteredItems = getFilteredShopItems();

  if (filteredItems.length === 0) {
    container.innerHTML = '<div class="empty-hint">没有找到物品</div>';
    renderPagination("shop-pagination", 0, shopPage);
    return;
  }

  const total = filteredItems.length;
  const totalPages = Math.ceil(total / SHOP_ITEMS_PER_PAGE);
  if (shopPage.current > totalPages) shopPage.current = totalPages;
  const start = (shopPage.current - 1) * SHOP_ITEMS_PER_PAGE;
  const pageItems = filteredItems.slice(start, start + SHOP_ITEMS_PER_PAGE);

  for (const item of pageItems) {
    const canEquip = item.equip_slot && item.stats;
    const rarityCls = item.rarity || "common";
    const rarityColor = getRarityColor(rarityCls);
    const rarityName = getRarityName(rarityCls);
    const tierName = item.tier ? getTierName(item.tier) : "";
    const levelText = getLevelRangeText(item);
    const canBuy = item.buy_price && item.buy_price > 0;
    const canBuyEquip = canEquip ? canPlayerEquipItem(item) : true;
    const maxBuy = canBuy ? Math.min(item.quantity, Math.floor(inventoryState.gold / item.buy_price)) : 0;

    let statsHtml = "";
    if (canEquip && item.stats) {
      statsHtml = `<div class="item-stats-line">${formatItemStats(item.stats)}</div>`;
    }

    let healHtml = "";
    if (item.heal_value && item.heal_value > 0) {
      healHtml = `<div class="item-heal-value">回复 <span class="heal-num">${item.heal_value}</span> HP</div>`;
    }
    let mpHtml = "";
    if (item.mp_value && item.mp_value > 0) {
      mpHtml = `<div class="item-heal-value">回复 <span class="heal-num">${item.mp_value}</span> MP</div>`;
    }

    let affixesHtml = "";
    if (item.affixes && item.affixes.length > 0) {
      affixesHtml = `<div class="item-affixes">${item.affixes.map(a => {
        if (typeof a === "object" && a.name) {
          return `<span class="affix-tag" title="${a.description || ""}">${a.name}</span>`;
        }
        return `<span class="affix-tag">${a}</span>`;
      }).join("")}</div>`;
    }

    const classRestrictionHtml = getClassRestrictionHtml(item);
    const compareHtml = canEquip ? buildCompareHtml(item) : "";

    let buyActionHtml = "";
    if (canBuy && canBuyEquip && maxBuy > 0) {
      buyActionHtml = `
        <div class="qty-selector">
          <button class="qty-btn" onclick="adjustQty('buy', '${item.item_id}', -1)">−</button>
          <input class="qty-input" type="number" value="1" min="1" max="${maxBuy}" id="buy_${item.item_id}">
          <button class="qty-btn" onclick="adjustQty('buy', '${item.item_id}', 1)">+</button>
          <button class="btn-buy" onclick="doTrade('buy', '${item.item_id}', getQty('buy', '${item.item_id}'))">购买</button>
        </div>`;
    } else if (canBuy && !canBuyEquip) {
      buyActionHtml = `<span style="color:#ff6b6b;font-size:11px;">${getClassLabel(item.required_class)}专属</span>`;
    } else if (canBuy && maxBuy <= 0) {
      buyActionHtml = `<span style="color:#ff6b6b;font-size:11px;">金币不足</span>`;
    } else {
      buyActionHtml = `<span style="color:#888;font-size:11px;">不出售</span>`;
    }

    const div = document.createElement("div");
    div.className = `item-card shop-item-compact ${item.type} rarity-${rarityCls}`;
    div.innerHTML = `
      <div class="item-header">
        <span class="item-name" style="color:${rarityColor}">${item.name}</span>
        <span class="item-qty">库存: ${item.quantity}</span>
      </div>
      <div class="item-type">${getTypeLabel(item.type)}${canEquip ? ` · ${getSlotLabel(item.equip_slot)}` : ""}${tierName ? ` · ${tierName}` : ""}${levelText ? ` · ${levelText}` : ""} <span style="color:${rarityColor}">[${rarityName}]</span>${classRestrictionHtml}</div>
      ${statsHtml}
      ${healHtml}
      ${mpHtml}
      ${affixesHtml}
      ${compareHtml}
      <div class="item-actions">
        <span class="item-price">售价: ${item.buy_price || "—"} 金</span>
        ${buyActionHtml}
      </div>
    `;

    div.addEventListener("dblclick", (e) => {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
      if (canBuy && canBuyEquip && maxBuy > 0) {
        doTrade("buy", item.item_id, 1);
      }
    });

    div.addEventListener("click", (e) => {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
      if (e.shiftKey && canBuy && canBuyEquip && maxBuy > 0) {
        e.preventDefault();
        doTrade("buy", item.item_id, maxBuy);
      }
    });

    div.addEventListener("contextmenu", (e) => {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
      showItemCtxMenu(e, item, "shop");
    });

    container.appendChild(div);
  }

  renderPagination("shop-pagination", totalPages, shopPage);
}

function renderShopRight() {
  const container = document.getElementById("shop-inventory-items");
  container.innerHTML = "";

  const filteredItems = getFilteredShopInvItems();

  if (filteredItems.length === 0) {
    container.innerHTML = '<div class="empty-hint">背包空空如也...</div>';
    renderPagination("shop-inventory-pagination", 0, shopInvPage);
    return;
  }

  const total = filteredItems.length;
  const totalPages = Math.ceil(total / SHOP_ITEMS_PER_PAGE);
  if (shopInvPage.current > totalPages) shopInvPage.current = totalPages;
  const start = (shopInvPage.current - 1) * SHOP_ITEMS_PER_PAGE;
  const pageItems = filteredItems.slice(start, start + SHOP_ITEMS_PER_PAGE);

  for (const item of pageItems) {
    const canEquip = item.equip_slot && item.stats;
    const isEquipped = isItemEquipped(item.item_id);
    const rarityCls = item.rarity || "common";
    const rarityColor = getRarityColor(rarityCls);
    const rarityName = getRarityName(rarityCls);
    const canSell = item.sell_price && item.sell_price > 0;
    const maxSell = canSell ? item.quantity : 0;

    let statsHtml = "";
    if (canEquip && item.stats) {
      statsHtml = `<div class="item-stats-line">${formatItemStats(item.stats)}</div>`;
    }

    let healHtml = "";
    if (item.heal_value && item.heal_value > 0) {
      healHtml = `<div class="item-heal-value">回复 <span class="heal-num">${item.heal_value}</span> HP</div>`;
    }
    let mpHtml = "";
    if (item.mp_value && item.mp_value > 0) {
      mpHtml = `<div class="item-heal-value">回复 <span class="heal-num">${item.mp_value}</span> MP</div>`;
    }

    let affixesHtml = "";
    if (item.affixes && item.affixes.length > 0) {
      affixesHtml = `<div class="item-affixes">${item.affixes.map(a => {
        if (typeof a === "object" && a.name) {
          return `<span class="affix-tag" title="${a.description || ""}">${a.name}</span>`;
        }
        return `<span class="affix-tag">${a}</span>`;
      }).join("")}</div>`;
    }

    const classRestrictionHtml = getClassRestrictionHtml(item);
    const compareHtml = canEquip && !isEquipped ? buildCompareHtml(item) : "";

    let actionHtml = "";
    if (isEquipped) {
      actionHtml = `<span style="color:#6bafff;font-size:11px;font-weight:bold;">已装备</span>`;
    } else if (canEquip && !canPlayerEquipItem(item)) {
      actionHtml = `<span style="color:#ff6b6b;font-size:11px;">${getClassLabel(item.required_class)}专属</span>`;
    }

    let sellActionHtml = "";
    if (canSell && !isEquipped) {
      sellActionHtml = `
        <div class="qty-selector">
          <button class="qty-btn" onclick="adjustQty('sell', '${item.item_id}', -1)">−</button>
          <input class="qty-input" type="number" value="1" min="1" max="${maxSell}" id="sell_${item.item_id}">
          <button class="qty-btn" onclick="adjustQty('sell', '${item.item_id}', 1)">+</button>
          <button class="btn-sell" onclick="doTrade('sell', '${item.item_id}', getQty('sell', '${item.item_id}'))">出售</button>
        </div>`;
    } else if (!canSell) {
      sellActionHtml = `<span style="color:#888;font-size:11px;">不可出售</span>`;
    }

    let equipBtnHtml = "";
    if (canEquip && !isEquipped && canPlayerEquipItem(item)) {
      equipBtnHtml = `<button class="btn-equip" onclick="doEquip('${item.item_id}')">装备</button>`;
    }

    let useBtnHtml = "";
    if ((item.type === "consumable" || item.type === "food") && !isEquipped) {
      useBtnHtml = `<button class="btn-use" onclick="doUseItem('${item.item_id}')">使用</button>`;
    }

    const div = document.createElement("div");
    div.className = `item-card shop-item-compact ${item.type} rarity-${rarityCls}`;
    div.innerHTML = `
      <div class="item-header">
        <span class="item-name" style="color:${rarityColor}">${item.name}</span>
        <span class="item-qty">x${item.quantity}</span>
      </div>
      <div class="item-type">${getTypeLabel(item.type)}${canEquip ? ` · ${getSlotLabel(item.equip_slot)}` : ""} <span style="color:${rarityColor}">[${rarityName}]</span>${classRestrictionHtml}</div>
      ${statsHtml}
      ${healHtml}
      ${mpHtml}
      ${affixesHtml}
      ${compareHtml}
      <div class="item-actions">
        <span class="item-price">出售价: ${item.sell_price} 金</span>
        ${actionHtml}
        ${equipBtnHtml}
        ${useBtnHtml}
        ${sellActionHtml}
      </div>
    `;

    div.addEventListener("dblclick", (e) => {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
      if (canEquip && !isEquipped && canPlayerEquipItem(item)) {
        doEquip(item.item_id);
      } else if ((item.type === "consumable" || item.type === "food") && !isEquipped) {
        doUseItem(item.item_id);
      } else if (canSell && !isEquipped) {
        doTrade("sell", item.item_id, 1);
      }
    });

    div.addEventListener("click", (e) => {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
      if (e.shiftKey && canSell && !isEquipped) {
        e.preventDefault();
        doTrade("sell", item.item_id, maxSell);
      }
    });

    div.addEventListener("contextmenu", (e) => {
      if (e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
      showItemCtxMenu(e, item, "inventory");
    });

    container.appendChild(div);
  }

  renderPagination("shop-inventory-pagination", totalPages, shopInvPage);
}

function getPlayerItemQty(itemId) {
  const item = inventoryState.items.find(i => i.item_id === itemId);
  return item ? item.quantity : 0;
}

async function doTrade(action, itemId, quantity = 1) {
  if (!shopNpcId) return;
  try {
    const resp = await fetch("/api/trade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, item_id: itemId, quantity, npc_id: shopNpcId }),
    });
    const data = await resp.json();

    showTradeMessage(data.message, data.success);

    if (data.success) {
      inventoryState.items = data.player_inventory;
      inventoryState.gold = data.player_gold;
      shopState.items = data.shop_inventory;
      shopState.gold = data.shop_gold;
      updateGoldDisplay();
      renderShop();
    }
  } catch (e) {
    showTradeMessage("交易失败，请重试", false);
    console.error("交易请求失败:", e);
  }
}

function showTradeMessage(msg, success) {
  if (typeof showToast === "function") {
    showToast(msg, success ? "success" : "error");
  }
  const el = document.getElementById("trade-message");
  el.textContent = msg;
  el.className = `trade-message ${success ? "success" : "fail"}`;
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 2500);
}

function renderPagination(containerId, totalPages, pageState) {
  const bar = document.getElementById(containerId);
  if (totalPages <= 1) {
    bar.style.display = "none";
    return;
  }
  bar.style.display = "flex";
  bar.innerHTML = "";

  const btnPrev = document.createElement("button");
  btnPrev.textContent = "◀ 上一页";
  btnPrev.disabled = pageState.current <= 1;
  btnPrev.onclick = () => { pageState.current--; rerenderByContainer(containerId); };

  const info = document.createElement("span");
  info.className = "page-info";
  info.textContent = `${pageState.current} / ${totalPages}`;

  const btnNext = document.createElement("button");
  btnNext.textContent = "下一页 ▶";
  btnNext.disabled = pageState.current >= totalPages;
  btnNext.onclick = () => { pageState.current++; rerenderByContainer(containerId); };

  bar.appendChild(btnPrev);
  bar.appendChild(info);
  bar.appendChild(btnNext);
}

function rerenderByContainer(containerId) {
  if (containerId === "inventory-pagination") renderInventory();
  else if (containerId === "shop-pagination") renderShop();
  else if (containerId === "shop-inventory-pagination") renderShop();
}

function getTypeLabel(type) {
  const labels = {
    weapon: "武器",
    armor: "防具",
    consumable: "消耗品",
    food: "食物",
    tool: "工具",
    material: "材料",
    accessory: "饰品",
  };
  return labels[type] || type;
}

function getClassLabel(cls) {
  const labels = {
    warrior: "战士",
    rogue: "盗贼",
    mage: "法师",
  };
  return labels[cls] || cls;
}

function getClassRestrictionHtml(item) {
  if (!item.required_class) return "";
  const clsName = getClassLabel(item.required_class);
  return `<span class="class-restriction">[仅限${clsName}]</span>`;
}

function canPlayerEquipItem(item) {
  if (!item.required_class) return true;
  return item.required_class === playerInfo.class_id;
}

let dragItemId = null;
let dragEquipSlot = null;

function onItemDragStart(e) {
  dragItemId = e.currentTarget.dataset.itemId;
  dragEquipSlot = e.currentTarget.dataset.equipSlot;
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", dragItemId);
  e.currentTarget.classList.add("dragging");

  const slots = document.querySelectorAll(".equip-slot");
  slots.forEach(s => {
    if (s.dataset.slot === dragEquipSlot) {
      s.classList.add("equip-slot-highlight");
    }
  });
}

function onItemDragEnd(e) {
  e.currentTarget.classList.remove("dragging");
  dragItemId = null;
  dragEquipSlot = null;
  document.querySelectorAll(".equip-slot-highlight").forEach(s => s.classList.remove("equip-slot-highlight"));
}

function onEquipSlotDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
  const slot = e.currentTarget.dataset.slot;
  if (dragEquipSlot && dragEquipSlot === slot) {
    e.currentTarget.classList.add("equip-slot-dragover");
  }
}

function onEquipSlotDragLeave(e) {
  e.currentTarget.classList.remove("equip-slot-dragover");
}

function onEquipSlotDrop(e) {
  e.preventDefault();
  e.currentTarget.classList.remove("equip-slot-dragover");
  document.querySelectorAll(".equip-slot-highlight").forEach(s => s.classList.remove("equip-slot-highlight"));

  const slot = e.currentTarget.dataset.slot;
  const itemId = e.dataTransfer.getData("text/plain") || dragItemId;
  if (!itemId) return;

  const item = inventoryState.items.find(it => it.item_id === itemId);
  if (!item) return;

  if (item.equip_slot !== slot) return;
  if (!canPlayerEquipItem(item)) return;

  doEquip(itemId);
}

function setupEquipSlotDropTargets() {
  const slots = document.querySelectorAll(".equip-slot");
  slots.forEach(s => {
    s.removeEventListener("dragover", onEquipSlotDragOver);
    s.removeEventListener("dragleave", onEquipSlotDragLeave);
    s.removeEventListener("drop", onEquipSlotDrop);
    s.addEventListener("dragover", onEquipSlotDragOver);
    s.addEventListener("dragleave", onEquipSlotDragLeave);
    s.addEventListener("drop", onEquipSlotDrop);
  });
}

function updateGoldDisplay() {
  const el = document.getElementById("hud-gold");
  if (el) el.textContent = inventoryState.gold;
  const invGold = document.getElementById("inventory-gold");
  if (invGold) invGold.textContent = inventoryState.gold;
  const shopGold = document.getElementById("player-gold-shop");
  if (shopGold) shopGold.textContent = inventoryState.gold;
  const invShopGold = document.getElementById("inventory-gold-shop");
  if (invShopGold) invShopGold.textContent = inventoryState.gold;
}

async function doUseItem(itemId) {
  try {
    const resp = await fetch("/api/use_item", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: itemId }),
    });
    const data = await resp.json();
    if (data.success) {
      if (data.hp !== undefined) playerInfo.hp = data.hp;
      if (data.max_hp !== undefined) playerInfo.max_hp = data.max_hp;
      if (data.mp !== undefined) playerInfo.mp = data.mp;
      if (data.max_mp !== undefined) playerInfo.max_mp = data.max_mp;
      if (data.skills !== undefined) playerInfo.skills = data.skills;
      updatePlayerHUD();
      await fetchInventory();
      renderInventory();
      if (shopOpen) renderShop();
      showEquipMessage(data.message, true);
    } else {
      showEquipMessage(data.message, false);
    }
  } catch (e) {
    showEquipMessage("使用失败", false);
    console.error("使用物品失败:", e);
  }
}

function closeCtxMenu() {
  if (ctxMenuEl) {
    ctxMenuEl.remove();
    ctxMenuEl = null;
  }
}

function showItemCtxMenu(e, item, context) {
  e.preventDefault();
  closeCtxMenu();

  const canEquip = item.equip_slot && item.stats;
  const isEquipped = isItemEquipped(item.item_id);
  const canUse = (item.type === "consumable" || item.type === "food") && !isEquipped;
  const canSell = item.sell_price && item.sell_price > 0 && !isEquipped;
  const canBuy = context === "shop";

  const menu = document.createElement("div");
  menu.className = "item-ctx-menu";

  const items = [];

  if (canBuy) {
    items.push({ label: "购买 x1", action: () => doTrade("buy", item.item_id, 1) });
    items.push({ label: "购买最大数量", action: () => {
      const maxBuy = Math.min(item.quantity || 1, Math.floor(inventoryState.gold / (item.buy_price || 1)));
      if (maxBuy > 0) doTrade("buy", item.item_id, maxBuy);
      else showEquipMessage("金币不足", false);
    }});
  }

  if (canEquip && !isEquipped && canPlayerEquipItem(item)) {
    items.push({ label: "装备", action: () => doEquip(item.item_id) });
  }

  if (canUse) {
    items.push({ label: "使用 x1", action: () => doUseItem(item.item_id) });
  }

  if (canSell && shopOpen) {
    items.push({ label: "出售 x1", action: () => doTrade("sell", item.item_id, 1) });
    items.push({ label: "出售全部", action: () => doTrade("sell", item.item_id, item.quantity || 1) });
  }

  if (items.length > 0) {
    items.push({ separator: true });
  }

  items.push({ label: "详情", action: () => showItemTooltip(item, e.target.closest(".item-card, .shop-item-compact, .item-grid-cell")) });

  for (const mi of items) {
    if (mi.separator) {
      const sep = document.createElement("div");
      sep.className = "ctx-sep";
      menu.appendChild(sep);
      continue;
    }
    const btn = document.createElement("div");
    btn.className = "ctx-item";
    btn.textContent = mi.label;
    btn.addEventListener("click", () => {
      closeCtxMenu();
      mi.action();
    });
    menu.appendChild(btn);
  }

  document.body.appendChild(menu);
  ctxMenuEl = menu;

  let left = e.clientX;
  let top = e.clientY;
  if (left + 160 > window.innerWidth) left = window.innerWidth - 165;
  if (top + menu.offsetHeight > window.innerHeight) top = window.innerHeight - menu.offsetHeight - 5;
  menu.style.left = left + "px";
  menu.style.top = top + "px";

  const closeOnOutside = (ev) => {
    if (!menu.contains(ev.target)) {
      closeCtxMenu();
      document.removeEventListener("click", closeOnOutside);
      document.removeEventListener("contextmenu", closeOnOutside);
    }
  };
  setTimeout(() => {
    document.addEventListener("click", closeOnOutside);
    document.addEventListener("contextmenu", closeOnOutside);
  }, 10);
}


