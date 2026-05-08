// 玩家信息面板

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
  attack: 15,
  defense: 12,
  speed: 8,
  status_effects: [],
};

const classNames = {
  warrior: { icon: "剑", color: "#ff6b6b" },
  rogue:   { icon: "匕", color: "#ffd76b" },
  mage:    { icon: "法", color: "#6bafff" },
};

async function fetchPlayerInfo() {
  try {
    const resp = await fetch("/api/player");
    const data = await resp.json();
    Object.assign(playerInfo, data);
    // 同步名字到 player 对象用于地图显示
    if (data.name) {
      player.name = data.name;
    }
    // 恢复玩家位置
    if (data.player_x !== undefined && data.player_y !== undefined) {
      setPlayerPosition(data.player_x, data.player_y);
    }
    updatePlayerHUD();
    // 同步金币到背包显示
    if (data.gold !== undefined) {
      inventoryState.gold = data.gold;
      updateGoldDisplay();
    }
  } catch (e) {
    console.error("获取玩家信息失败:", e);
  }
}

function openPlayerInfo() {
  if (dialogueOpen || shopOpen || gameMenuOpen) return;
  playerInfoOpen = true;
  fetchPlayerInfo().then(() => renderPlayerInfo());
  document.getElementById("player-info-panel").classList.add("active");
}

function closePlayerInfo() {
  playerInfoOpen = false;
  document.getElementById("player-info-panel").classList.remove("active");
}

function renderPlayerInfo() {
  const panel = document.getElementById("player-info-panel");
  const cls = classNames[playerInfo.class_id] || { icon: "?", color: "#fff" };
  const expPercent = playerInfo.exp_to_next > 0
    ? Math.floor(playerInfo.exp / playerInfo.exp_to_next * 100) : 0;
  const hpPercent = playerInfo.max_hp > 0
    ? Math.floor(playerInfo.hp / playerInfo.max_hp * 100) : 0;

  const hpBarColor = hpPercent > 50 ? "#4CAF50" : hpPercent > 20 ? "#FF9800" : "#f44336";

  document.getElementById("pi-name").textContent = playerInfo.name;
  document.getElementById("pi-class").textContent = `${cls.icon} ${playerInfo.class_name}`;
  document.getElementById("pi-class").style.color = cls.color;
  document.getElementById("pi-level").textContent = playerInfo.level;

  // HP 条
  document.getElementById("pi-hp-bar").style.width = `${hpPercent}%`;
  document.getElementById("pi-hp-bar").style.backgroundColor = hpBarColor;
  document.getElementById("pi-hp-text").textContent = `${playerInfo.hp} / ${playerInfo.max_hp}`;

  // 经验条
  document.getElementById("pi-exp-bar").style.width = `${expPercent}%`;
  document.getElementById("pi-exp-text").textContent = `${playerInfo.exp} / ${playerInfo.exp_to_next}`;

  // 属性
  document.getElementById("pi-attack").textContent = playerInfo.attack;
  document.getElementById("pi-defense").textContent = playerInfo.defense;
  document.getElementById("pi-speed").textContent = playerInfo.speed;

  // 状态效果
  const effectsEl = document.getElementById("pi-effects");
  if (playerInfo.status_effects.length === 0) {
    effectsEl.innerHTML = '<span class="no-effects">无</span>';
  } else {
    effectsEl.innerHTML = playerInfo.status_effects
      .map(e => `<span class="effect-tag">${e}</span>`)
      .join("");
  }
}

function updatePlayerHUD() {
  // 更新 HUD 上的生命值和等级
  const hpEl = document.getElementById("hud-hp");
  const lvlEl = document.getElementById("hud-level");
  if (hpEl) hpEl.textContent = `${playerInfo.hp}/${playerInfo.max_hp}`;
  if (lvlEl) lvlEl.textContent = `Lv.${playerInfo.level}`;
}

// 事件绑定
document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() === "p" && !dialogueOpen && !gameMenuOpen) {
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
