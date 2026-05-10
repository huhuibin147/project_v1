let inventoryOpen = false;
let shopOpen = false;
let shopNpcId = null;

const ITEMS_PER_PAGE = 8;
const inventoryPage = { current: 1 };
const shopPage = { current: 1 };

const inventoryState = {
  items: [],
  gold: 0,
};

const inventoryDisplay = {
  view: "list",
  filter: "all",
};

const shopState = {
  name: "",
  items: [],
  gold: 0,
};

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
  if (dialogueOpen || gameMenuOpen || combatOpen) return;
  inventoryOpen = true;
  inventoryPage.current = 1;
  fetchInventory().then(() => renderInventory());
  document.getElementById("inventory-panel").classList.add("active");
}

function closeInventory() {
  inventoryOpen = false;
  document.getElementById("inventory-panel").classList.remove("active");
}

function getFilteredItems() {
  let items = inventoryState.items;
  const filter = inventoryDisplay.filter;
  if (filter !== "all") {
    if (filter === "armor") {
      items = items.filter(it => it.type === "armor" || (it.equip_slot && it.equip_slot !== "weapon" && it.equip_slot !== "accessory"));
    } else if (filter === "weapon") {
      items = items.filter(it => it.type === "weapon" || it.equip_slot === "weapon");
    } else {
      items = items.filter(it => it.type === filter);
    }
  }
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

function renderInventory() {
  const container = document.getElementById("inventory-items");
  container.innerHTML = "";
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

  if (inventoryDisplay.view === "grid") {
    renderInventoryGrid(container, pageItems);
  } else {
    renderInventoryList(container, pageItems);
  }

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
      affixesHtml = `<div class="item-affixes">${item.affixes.map(a => `<span class="affix-tag">${a}</span>`).join("")}</div>`;
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

  let statsHtml = "";
  if (canEquip && item.stats) {
    statsHtml = `<div class="tt-stats">${formatItemStats(item.stats)}</div>`;
  }

  let healHtml = "";
  if (item.heal_value && item.heal_value > 0) {
    healHtml = `<div class="tt-heal">回复 <span class="heal-num">${item.heal_value}</span> HP</div>`;
  }
  let mpHtml = "";
  if (item.mp_value && item.mp_value > 0) {
    mpHtml = `<div class="tt-heal">回复 <span class="heal-num">${item.mp_value}</span> MP</div>`;
  }

  let compareHtml = canEquip && !isEquipped ? buildCompareHtml(item) : "";
  const classRestrictionHtml = getClassRestrictionHtml(item);

  const tt = document.createElement("div");
  tt.className = "item-tooltip";
  tt.innerHTML = `
    <div class="tt-header">
      <span class="tt-name" style="color:${rarityColor}">${item.name}</span>
      <span class="tt-qty">x${item.quantity}</span>
    </div>
    <div class="tt-meta">${getTypeLabel(item.type)}${canEquip ? ` · ${getSlotLabel(item.equip_slot)}` : ""}${tierName ? ` · ${tierName}` : ""}${levelText ? ` · ${levelText}` : ""} <span style="color:${rarityColor}">[${rarityName}]</span>${classRestrictionHtml}</div>
    ${statsHtml}
    ${healHtml}
    ${mpHtml}
    ${compareHtml}
    <div class="tt-desc">${item.description}</div>
    <div class="tt-price">出售价: ${item.sell_price} 金</div>
  `;

  document.body.appendChild(tt);
  tooltipEl = tt;

  const rect = anchorEl.getBoundingClientRect();
  const panelRect = document.getElementById("inventory-panel").getBoundingClientRect();
  let left = rect.right + 8;
  let top = rect.top;
  if (left + 220 > window.innerWidth) {
    left = rect.left - 228;
  }
  if (top + 200 > window.innerHeight) {
    top = window.innerHeight - 200;
  }
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
  if (combatOpen) return;
  shopOpen = true;
  shopNpcId = npcId || activeNpcId || "blacksmith";
  shopPage.current = 1;
  fetchShop(shopNpcId).then(() => {
    fetchInventory().then(() => renderShop());
  });
  document.getElementById("shop-panel").classList.add("active");
}

function closeShop() {
  shopOpen = false;
  shopNpcId = null;
  document.getElementById("shop-panel").classList.remove("active");
}

function renderShop() {
  document.getElementById("shop-title").textContent = shopState.name;
  document.getElementById("shop-gold").textContent = shopState.gold;
  document.getElementById("player-gold-shop").textContent = inventoryState.gold;

  const container = document.getElementById("shop-items");
  container.innerHTML = "";

  if (shopState.items.length === 0) {
    container.innerHTML = '<div class="empty-hint">商店暂无货物</div>';
    renderPagination("shop-pagination", 0, shopPage);
    return;
  }

  const total = shopState.items.length;
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE);
  if (shopPage.current > totalPages) shopPage.current = totalPages;
  const start = (shopPage.current - 1) * ITEMS_PER_PAGE;
  const pageItems = shopState.items.slice(start, start + ITEMS_PER_PAGE);

  for (const item of pageItems) {
    const playerQty = getPlayerItemQty(item.item_id);
    const canEquip = item.equip_slot && item.stats;
    const rarityCls = item.rarity || "common";
    const rarityColor = getRarityColor(rarityCls);
    const rarityName = getRarityName(rarityCls);
    const tierName = item.tier ? getTierName(item.tier) : "";
    const levelText = getLevelRangeText(item);

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

    const compareHtml = canEquip ? buildCompareHtml(item) : "";

    let affixesHtml = "";
    if (item.affixes && item.affixes.length > 0) {
      affixesHtml = `<div class="item-affixes">${item.affixes.map(a => `<span class="affix-tag">${a}</span>`).join("")}</div>`;
    }

    const classRestrictionHtml = getClassRestrictionHtml(item);
    const canBuy = item.buy_price && item.buy_price > 0;
    const canBuyEquip = canEquip ? canPlayerEquipItem(item) : true;

    const div = document.createElement("div");
    div.className = `item-card shop-item ${item.type} rarity-${rarityCls}`;
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
      <div class="item-desc">${item.description}</div>
      <div class="item-actions">
        <span class="item-price">售价: ${item.buy_price || "—"} 金</span>
        ${canBuy && canBuyEquip ? `<button class="btn-buy" onclick="doTrade('buy', '${item.item_id}')">购买</button>` : (canBuy && !canBuyEquip ? `<span style="color:#ff6b6b;font-size:11px;">${getClassLabel(item.required_class)}专属</span>` : (canBuy ? "" : `<span style="color:#888;font-size:11px;">不出售</span>`))}
        ${playerQty > 0 ? `<button class="btn-sell" onclick="doTrade('sell', '${item.item_id}')">出售 (${playerQty})</button>` : ""}
      </div>
    `;
    container.appendChild(div);
  }

  renderPagination("shop-pagination", totalPages, shopPage);
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

function updateGoldDisplay() {
  const el = document.getElementById("hud-gold");
  if (el) el.textContent = inventoryState.gold;
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
      showEquipMessage(data.message, true);
    } else {
      showEquipMessage(data.message, false);
    }
  } catch (e) {
    showEquipMessage("使用失败", false);
    console.error("使用物品失败:", e);
  }
}

document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() === "i" && !dialogueOpen && !gameMenuOpen && !combatOpen) {
    if (inventoryOpen) {
      closeInventory();
    } else {
      if (shopOpen) closeShop();
      openInventory();
    }
  }
  if (e.key === "Escape") {
    if (gameMenuOpen) closeGameMenu();
    else if (npcInteractOpen) closeNpcInteract();
    else if (shopOpen) closeShop();
    else if (inventoryOpen) closeInventory();
  }
});
