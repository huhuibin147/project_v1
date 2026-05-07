// 物品系统：背包、商店、交易 UI（支持多 NPC）

let inventoryOpen = false;
let shopOpen = false;
let shopNpcId = null; // 当前商店所属 NPC
let npcShopSelectOpen = false;

const inventoryState = {
  items: [],
  gold: 0,
};

const shopState = {
  name: "",
  items: [],
  gold: 0,
};

// ===== 数据获取 =====

async function fetchInventory(npcId) {
  try {
    const resp = await fetch(`/api/inventory?npc_id=${npcId || activeNpcId || "blacksmith"}`);
    const data = await resp.json();
    inventoryState.items = data.items;
    inventoryState.gold = data.gold;
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

// ===== 背包面板 =====

function openInventory() {
  if (dialogueOpen) return;
  inventoryOpen = true;
  fetchInventory(activeNpcId || "blacksmith").then(() => renderInventory());
  document.getElementById("inventory-panel").classList.add("active");
}

function closeInventory() {
  inventoryOpen = false;
  hideNpcShopSelect();
  document.getElementById("inventory-panel").classList.remove("active");
}

function renderInventory() {
  const container = document.getElementById("inventory-items");
  container.innerHTML = "";

  if (inventoryState.items.length === 0) {
    container.innerHTML = '<div class="empty-hint">背包空空如也...</div>';
    return;
  }

  for (const item of inventoryState.items) {
    const div = document.createElement("div");
    div.className = `item-card ${item.type}`;
    div.innerHTML = `
      <div class="item-header">
        <span class="item-name">${item.name}</span>
        <span class="item-qty">x${item.quantity}</span>
      </div>
      <div class="item-type">${getTypeLabel(item.type)}</div>
      <div class="item-desc">${item.description}</div>
      <div class="item-price">出售价: ${item.sell_price} 金</div>
    `;
    container.appendChild(div);
  }

  document.getElementById("inventory-gold").textContent = inventoryState.gold;
}

// ===== 商店面板 =====

function openShop(npcId) {
  shopOpen = true;
  shopNpcId = npcId || activeNpcId || "blacksmith";
  fetchShop(shopNpcId).then(() => {
    fetchInventory(shopNpcId).then(() => renderShop());
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
    return;
  }

  for (const item of shopState.items) {
    const playerQty = getPlayerItemQty(item.item_id);
    const div = document.createElement("div");
    div.className = `item-card shop-item ${item.type}`;
    div.innerHTML = `
      <div class="item-header">
        <span class="item-name">${item.name}</span>
        <span class="item-qty">库存: ${item.quantity}</span>
      </div>
      <div class="item-type">${getTypeLabel(item.type)}</div>
      <div class="item-desc">${item.description}</div>
      <div class="item-actions">
        <span class="item-price">售价: ${item.buy_price} 金</span>
        <button class="btn-buy" onclick="doTrade('buy', '${item.item_id}')">购买</button>
        ${playerQty > 0 ? `<button class="btn-sell" onclick="doTrade('sell', '${item.item_id}')">出售 (${playerQty})</button>` : ""}
      </div>
    `;
    container.appendChild(div);
  }
}

function getPlayerItemQty(itemId) {
  const item = inventoryState.items.find(i => i.item_id === itemId);
  return item ? item.quantity : 0;
}

// ===== 交易 =====

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

// ===== 工具函数 =====

function getTypeLabel(type) {
  const labels = {
    weapon: "武器",
    armor: "防具",
    consumable: "消耗品",
    food: "食物",
    tool: "工具",
    material: "材料",
  };
  return labels[type] || type;
}

function updateGoldDisplay() {
  const el = document.getElementById("hud-gold");
  if (el) el.textContent = inventoryState.gold;
}

// ===== NPC 商店选择 =====

function showNpcShopSelect() {
  npcShopSelectOpen = true;
  const container = document.getElementById("npc-shop-list");
  container.innerHTML = "";

  for (const npc of npcs) {
    const div = document.createElement("div");
    div.className = "npc-shop-card";
    div.onclick = () => {
      hideNpcShopSelect();
      closeInventory();
      openShop(npc.npc_id);
    };
    div.innerHTML = `
      <div class="npc-shop-icon ${npc.npc_id}">${npc.name[0]}</div>
      <div class="npc-shop-info">
        <div class="npc-shop-name">${npc.name}</div>
        <div class="npc-shop-role">${npc.role || ""}</div>
      </div>
    `;
    container.appendChild(div);
  }

  document.getElementById("npc-shop-select").classList.add("active");
}

function hideNpcShopSelect() {
  npcShopSelectOpen = false;
  document.getElementById("npc-shop-select").classList.remove("active");
}

// ===== 事件绑定 =====

document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() === "i" && !dialogueOpen) {
    if (inventoryOpen) {
      closeInventory();
    } else {
      if (shopOpen) closeShop();
      openInventory();
    }
  }
  if (e.key === "Escape") {
    if (npcShopSelectOpen) hideNpcShopSelect();
    else if (shopOpen) closeShop();
    else if (inventoryOpen) closeInventory();
  }
});
