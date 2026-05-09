let playerInfoOpen = false;

const playerInfo = {
  name: "冒险者",
  class_id: "warrior",
  class_name: "战士",
  class_desc: "",
  level: 1,
  exp: 0,
  exp_to_next: 100,
  hp: 120,
  max_hp: 120,
  mp: 50,
  max_mp: 50,
  attack: 15,
  defense: 12,
  speed: 8,
  status_effects: [],
  equipment: {},
};

const equipBonus = {
  attack: 0,
  defense: 0,
  speed: 0,
  max_hp: 0,
  max_mp: 0,
};

const classNames = {
  warrior: { icon: "剑", color: "#ff6b6b" },
  rogue:   { icon: "匕", color: "#ffd76b" },
  mage:    { icon: "法", color: "#6bafff" },
};

const SLOT_LABELS = {
  weapon: "武器",
  shield: "盾牌",
  head: "头部",
  body: "身体",
  accessory: "饰品",
};

const STAT_LABELS = {
  attack: "攻",
  defense: "防",
  speed: "速",
  max_hp: "HP",
  max_mp: "MP",
};

const RARITY_DEF_PI = {
  common:    { name: "普通", color: "#aaaaaa" },
  uncommon:  { name: "优秀", color: "#1eff00" },
  rare:      { name: "稀有", color: "#0070dd" },
  epic:      { name: "史诗", color: "#a335ee" },
  legendary: { name: "传说", color: "#ff8000" },
};

const TIER_NAMES_PI = {
  tier1: "初级",
  tier2: "中级",
  tier3: "高级",
};

async function fetchPlayerInfo() {
  try {
    const resp = await fetch("/api/player");
    const data = await resp.json();
    Object.assign(playerInfo, data);
    if (data.name) {
      player.name = data.name;
    }
    if (data.player_x !== undefined && data.player_y !== undefined) {
      setPlayerPosition(data.player_x, data.player_y);
    }
    updatePlayerHUD();
    if (data.gold !== undefined) {
      inventoryState.gold = data.gold;
      updateGoldDisplay();
    }
  } catch (e) {
    console.error("获取玩家信息失败:", e);
  }
}

async function fetchEquipmentInfo() {
  try {
    const resp = await fetch("/api/equipment");
    const data = await resp.json();
    if (data.equipment) {
      playerInfo.equipment = data.equipment;
    }
    if (data.equip_bonus) {
      Object.assign(equipBonus, data.equip_bonus);
    }
  } catch (e) {
    console.error("获取装备信息失败:", e);
  }
}

function openPlayerInfo() {
  if (dialogueOpen || shopOpen || gameMenuOpen || combatOpen) return;
  playerInfoOpen = true;
  Promise.all([fetchPlayerInfo(), fetchEquipmentInfo()]).then(() => renderPlayerInfo());
  document.getElementById("player-info-panel").classList.add("active");
}

function closePlayerInfo() {
  playerInfoOpen = false;
  document.getElementById("player-info-panel").classList.remove("active");
}

function formatStatsText(stats) {
  if (!stats) return "";
  const parts = [];
  for (const [key, val] of Object.entries(stats)) {
    if (val === 0) continue;
    const label = STAT_LABELS[key] || key;
    const cls = val < 0 ? "stat-neg" : "";
    parts.push(`<span class="${cls}">${label}${val > 0 ? "+" : ""}${val}</span>`);
  }
  return parts.join(" ");
}

function renderPlayerInfo() {
  const cls = classNames[playerInfo.class_id] || { icon: "?", color: "#fff" };
  const expPercent = playerInfo.exp_to_next > 0
    ? Math.floor(playerInfo.exp / playerInfo.exp_to_next * 100) : 0;
  const hpPercent = playerInfo.max_hp > 0
    ? Math.floor(playerInfo.hp / playerInfo.max_hp * 100) : 0;
  const mpPercent = (playerInfo.max_mp || 1) > 0
    ? Math.floor((playerInfo.mp || 0) / (playerInfo.max_mp || 1) * 100) : 0;

  const hpBarColor = hpPercent > 50 ? "#4CAF50" : hpPercent > 20 ? "#FF9800" : "#f44336";

  document.getElementById("pi-name").textContent = playerInfo.name;
  document.getElementById("pi-class").textContent = `${cls.icon} ${playerInfo.class_name}`;
  document.getElementById("pi-class").style.color = cls.color;
  document.getElementById("pi-level").textContent = playerInfo.level;

  document.getElementById("pi-hp-bar").style.width = `${hpPercent}%`;
  document.getElementById("pi-hp-bar").style.backgroundColor = hpBarColor;
  document.getElementById("pi-hp-text").textContent = `${playerInfo.hp} / ${playerInfo.max_hp}`;

  document.getElementById("pi-mp-bar").style.width = `${mpPercent}%`;
  document.getElementById("pi-mp-text").textContent = `${playerInfo.mp || 0} / ${playerInfo.max_mp || 0}`;

  document.getElementById("pi-exp-bar").style.width = `${expPercent}%`;
  document.getElementById("pi-exp-text").textContent = `${playerInfo.exp} / ${playerInfo.exp_to_next}`;

  document.getElementById("pi-attack").textContent = playerInfo.attack;
  document.getElementById("pi-defense").textContent = playerInfo.defense;
  document.getElementById("pi-speed").textContent = playerInfo.speed;

  renderStatBonus("pi-attack-bonus", equipBonus.attack);
  renderStatBonus("pi-defense-bonus", equipBonus.defense);
  renderStatBonus("pi-speed-bonus", equipBonus.speed);
  renderStatBonus("pi-max-hp-bonus", equipBonus.max_hp);
  renderStatBonus("pi-max-mp-bonus", equipBonus.max_mp);

  renderEquipment();

  const skillsEl = document.getElementById("pi-skills");
  if (playerInfo.skills && playerInfo.skills.length > 0) {
    skillsEl.innerHTML = playerInfo.skills
      .map(s => `<div class="skill-tag" title="${s.description || ''}\n消耗: ${s.mp_cost || 0} MP"><b>${s.name}</b> <span class="skill-mp">${s.mp_cost}MP</span></div>`)
      .join("");
  } else {
    skillsEl.innerHTML = '<span class="no-effects">无</span>';
  }

  const effectsEl = document.getElementById("pi-effects");
  if (playerInfo.status_effects.length === 0) {
    effectsEl.innerHTML = '<span class="no-effects">无</span>';
  } else {
    effectsEl.innerHTML = playerInfo.status_effects
      .map(e => `<span class="effect-tag">${e}</span>`)
      .join("");
  }
}

function renderStatBonus(elId, value) {
  const el = document.getElementById(elId);
  if (!el) return;
  if (value === 0) {
    el.textContent = "";
    el.className = "pi-stat-bonus";
  } else {
    el.textContent = `(${value > 0 ? "+" : ""}${value})`;
    el.className = `pi-stat-bonus${value < 0 ? " neg" : ""}`;
  }
}

function renderEquipment() {
  const equipment = playerInfo.equipment || {};
  const slots = ["weapon", "shield", "head", "body", "accessory"];

  for (const slot of slots) {
    const itemEl = document.getElementById(`equip-${slot}`);
    const statsEl = document.getElementById(`equip-${slot}-stats`);
    const btnEl = document.getElementById(`btn-unequip-${slot}`);
    const slotData = equipment[slot];

    if (slotData && slotData.item_id) {
      const rarity = slotData.rarity || "common";
      const rarityColor = (RARITY_DEF_PI[rarity] || RARITY_DEF_PI.common).color;
      const rarityName = (RARITY_DEF_PI[rarity] || RARITY_DEF_PI.common).name;
      const tierName = slotData.tier ? (TIER_NAMES_PI[slotData.tier] || "") : "";
      const levelText = slotData.level_range ? `Lv.${slotData.level_range}` : "";

      itemEl.textContent = slotData.name;
      itemEl.className = "equip-slot-item equipped";
      itemEl.style.color = rarityColor;

      let detailParts = [];
      if (tierName) detailParts.push(tierName);
      if (levelText) detailParts.push(levelText);
      detailParts.push(`[${rarityName}]`);
      const detailStr = detailParts.join(" ");

      statsEl.innerHTML = `${detailStr} ${formatStatsText(slotData.stats)}`;
      statsEl.style.color = rarityColor;
      btnEl.style.display = "inline-block";
    } else {
      itemEl.textContent = "-";
      itemEl.className = "equip-slot-item";
      itemEl.style.color = "";
      statsEl.innerHTML = "";
      statsEl.style.color = "";
      btnEl.style.display = "none";
    }
  }
}

async function doEquip(itemId) {
  try {
    const resp = await fetch("/api/equip", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: itemId }),
    });
    const data = await resp.json();

    showEquipMessage(data.message, data.success);

    if (data.success) {
      if (data.equipment) {
        playerInfo.equipment = data.equipment;
      }
      playerInfo.attack = data.player_attack;
      playerInfo.defense = data.player_defense;
      playerInfo.speed = data.player_speed;
      playerInfo.max_hp = data.player_max_hp;
      playerInfo.hp = data.player_hp;

      if (data.player_inventory) {
        inventoryState.items = data.player_inventory;
      }
      if (data.player_gold !== undefined) {
        inventoryState.gold = data.player_gold;
        updateGoldDisplay();
      }

      await fetchEquipmentInfo();
      renderPlayerInfo();
      if (inventoryOpen) renderInventory();
      updatePlayerHUD();
    }
  } catch (e) {
    showEquipMessage("装备失败，请重试", false);
    console.error("装备请求失败:", e);
  }
}

async function doUnequip(slot) {
  try {
    const resp = await fetch("/api/unequip", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slot: slot }),
    });
    const data = await resp.json();

    showEquipMessage(data.message, data.success);

    if (data.success) {
      if (data.equipment) {
        playerInfo.equipment = data.equipment;
      }
      playerInfo.attack = data.player_attack;
      playerInfo.defense = data.player_defense;
      playerInfo.speed = data.player_speed;
      playerInfo.max_hp = data.player_max_hp;
      playerInfo.hp = data.player_hp;

      if (data.player_inventory) {
        inventoryState.items = data.player_inventory;
      }
      if (data.player_gold !== undefined) {
        inventoryState.gold = data.player_gold;
        updateGoldDisplay();
      }

      await fetchEquipmentInfo();
      renderPlayerInfo();
      if (inventoryOpen) renderInventory();
      updatePlayerHUD();
    }
  } catch (e) {
    showEquipMessage("卸下失败，请重试", false);
    console.error("卸下请求失败:", e);
  }
}

function showEquipMessage(msg, success) {
  const old = document.getElementById("equip-message");
  if (old) old.remove();

  const el = document.createElement("div");
  el.id = "equip-message";
  el.className = "interact-message";
  el.textContent = msg;
  el.style.color = success ? "#66BB6A" : "#EF5350";
  el.style.borderColor = success ? "#66BB6A" : "#EF5350";
  document.getElementById("game-container").appendChild(el);
  el.addEventListener("animationend", () => el.remove());
}

function updatePlayerHUD() {
  const hpEl = document.getElementById("hud-hp");
  const mpEl = document.getElementById("hud-mp");
  const lvlEl = document.getElementById("hud-level");
  if (hpEl) hpEl.textContent = `${playerInfo.hp}/${playerInfo.max_hp}`;
  if (mpEl) mpEl.textContent = `${playerInfo.mp || 0}/${playerInfo.max_mp || 0}`;
  if (lvlEl) lvlEl.textContent = `Lv.${playerInfo.level}`;
}

document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() === "p" && !dialogueOpen && !gameMenuOpen && !combatOpen) {
    if (playerInfoOpen) {
      closePlayerInfo();
    } else {
      if (inventoryOpen) closeInventory();
      if (shopOpen) closeShop();
      openPlayerInfo();
    }
  }
  if (e.key === "Escape" && playerInfoOpen) {
    closePlayerInfo();
  }
});
