// 战斗系统 - 多敌人支持

let combatOpen = false;
let combatSessionId = null;
let combatState = null;
let combatAnimating = false;
let combatItemSelectOpen = false;
let combatMonsterInstanceId = null;
let currentTargetIndex = 0;

let mapMonsters = [];
let monstersConfig = {};

async function loadMonstersConfig() {
  try {
    const resp = await fetch("/api/monsters");
    if (resp.ok) {
      monstersConfig = await resp.json();
    }
  } catch (e) {
    console.error("加载怪物配置失败:", e);
  }
}

function loadMapMonsters() {
  mapMonsters = [];
  if (!currentMap || !currentMap.monsters) return;

  currentMap.monsters.forEach((spawn, idx) => {
    const config = monstersConfig[spawn.monster_id];
    if (!config) return;

    mapMonsters.push({
      monster_id: spawn.monster_id,
      instance_id: `${spawn.monster_id}_${idx}`,
      x: spawn.x * TILE_SIZE,
      y: spawn.y * TILE_SIZE,
      config: config,
      alive: true,
      inCombat: false,
      patrol: (spawn.patrol || []).map(p => ({ x: p.x * TILE_SIZE, y: p.y * TILE_SIZE })),
      patrolIndex: 0,
      patrolSpeed: 0.5,
      animFrame: 0,
      direction: "down",
    });
  });

  if (currentMap.monster_groups) {
    currentMap.monster_groups.forEach((group) => {
      const firstMonster = group.monsters[0];
      if (!firstMonster) return;
      const config = monstersConfig[firstMonster.monster_id];
      if (!config) return;

      mapMonsters.push({
        monster_id: firstMonster.monster_id,
        instance_id: group.group_id,
        group_id: group.group_id,
        x: group.x * TILE_SIZE,
        y: group.y * TILE_SIZE,
        config: config,
        alive: true,
        inCombat: false,
        patrol: [],
        patrolIndex: 0,
        patrolSpeed: 0,
        animFrame: 0,
        direction: "down",
        isGroup: true,
        groupData: group,
      });
    });
  }
}

function updateMonsters(dt) {
  for (const m of mapMonsters) {
    if (!m.alive || m.inCombat || m.patrol.length < 2) continue;

    m.animFrame++;
    const target = m.patrol[m.patrolIndex];
    const dx = target.x - m.x;
    const dy = target.y - m.y;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (dist < 2) {
      m.patrolIndex = (m.patrolIndex + 1) % m.patrol.length;
    } else {
      const speed = m.patrolSpeed;
      m.x += (dx / dist) * speed;
      m.y += (dy / dist) * speed;
      if (Math.abs(dx) > Math.abs(dy)) {
        m.direction = dx > 0 ? "right" : "left";
      } else {
        m.direction = dy > 0 ? "down" : "up";
      }
    }
  }
}

function drawMapMonster(ctx, monster) {
  if (!monster.alive) return;

  const x = Math.round(monster.x);
  const y = Math.round(monster.y);
  const s = TILE_SIZE;
  const p = s / 8;
  const config = monster.config;
  const bounce = Math.sin(monster.animFrame * 0.1) * 2;

  const alpha = monster.inCombat ? 0.4 : 1.0;
  ctx.globalAlpha = alpha;

  ctx.fillStyle = "rgba(0,0,0,0.2)";
  ctx.fillRect(x + p * 2, y + s - p * 2, p * 4, p * 1);

  const type = monster.monster_id;
  const color = config.sprite_color;
  const accent = config.sprite_accent;

  if (type === "slime") {
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 1, y + p * 4 + bounce, p * 6, p * 3);
    ctx.fillRect(x + p * 2, y + p * 3 + bounce, p * 4, p * 1);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 2, y + p * 3 + bounce, p * 4, p * 1);
    ctx.fillStyle = "#fff";
    ctx.fillRect(x + p * 3, y + p * 5 + bounce, p, p);
    ctx.fillRect(x + p * 5, y + p * 5 + bounce, p, p);
    ctx.fillStyle = "#000";
    ctx.fillRect(x + p * 3, y + p * 5 + bounce, p * 0.5, p * 0.5);
    ctx.fillRect(x + p * 5, y + p * 5 + bounce, p * 0.5, p * 0.5);
  } else if (type === "wild_wolf") {
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 1, y + p * 5 + bounce, p * 6, p * 2);
    ctx.fillRect(x + p * 0, y + p * 4 + bounce, p * 2, p * 2);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 0, y + p * 4 + bounce, p * 2, p * 2);
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 2, y + p * 7 + bounce, p, p);
    ctx.fillRect(x + p * 5, y + p * 7 + bounce, p, p);
    ctx.fillStyle = "#ff0";
    ctx.fillRect(x + p * 1, y + p * 4 + bounce, p * 0.5, p * 0.5);
  } else if (type === "forest_spider") {
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 3, y + p * 4 + bounce, p * 2, p * 2);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 1, y + p * 3 + bounce, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 3 + bounce, p * 2, p);
    ctx.fillRect(x + p * 1, y + p * 6 + bounce, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 6 + bounce, p * 2, p);
    ctx.fillStyle = "#f00";
    ctx.fillRect(x + p * 3, y + p * 4 + bounce, p * 0.5, p * 0.5);
    ctx.fillRect(x + p * 4.5, y + p * 4 + bounce, p * 0.5, p * 0.5);
  } else if (type === "goblin") {
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 2, y + p * 3 + bounce, p * 4, p * 4);
    ctx.fillRect(x + p * 3, y + p * 1 + bounce, p * 2, p * 3);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 2, y + p * 1 + bounce, p, p * 2);
    ctx.fillRect(x + p * 5, y + p * 1 + bounce, p, p * 2);
    ctx.fillStyle = "#f00";
    ctx.fillRect(x + p * 3, y + p * 3 + bounce, p, p);
    ctx.fillRect(x + p * 5, y + p * 3 + bounce, p, p);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 2, y + p * 7 + bounce, p * 2, p);
    ctx.fillRect(x + p * 4, y + p * 7 + bounce, p * 2, p);
  } else if (type === "dark_bear") {
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 0, y + p * 3 + bounce, p * 8, p * 4);
    ctx.fillRect(x + p * 0, y + p * 2 + bounce, p * 3, p * 2);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 0, y + p * 2 + bounce, p * 3, p * 2);
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 1, y + p * 7 + bounce, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 7 + bounce, p * 2, p);
    ctx.fillStyle = "#f00";
    ctx.fillRect(x + p * 1, y + p * 2 + bounce, p * 0.5, p * 0.5);
  } else if (type === "shadow_tree_spirit") {
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 1, y + p * 2 + bounce, p * 6, p * 5);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 2, y + p * 1 + bounce, p * 4, p * 2);
    ctx.fillStyle = "#4a0e4a";
    ctx.fillRect(x + p * 2, y + p * 3 + bounce, p * 1.5, p * 1.5);
    ctx.fillRect(x + p * 4.5, y + p * 3 + bounce, p * 1.5, p * 1.5);
    ctx.fillStyle = "#0f0";
    ctx.fillRect(x + p * 2.5, y + p * 3.5 + bounce, p * 0.5, p * 0.5);
    ctx.fillRect(x + p * 5, y + p * 3.5 + bounce, p * 0.5, p * 0.5);
    ctx.fillStyle = "#1a3a1a";
    ctx.fillRect(x + p * 1, y + p * 7 + bounce, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 7 + bounce, p * 2, p);
  } else {
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 2, y + p * 3 + bounce, p * 4, p * 4);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 3, y + p * 1 + bounce, p * 2, p * 3);
  }

  ctx.globalAlpha = 1.0;

  if (!monster.inCombat) {
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    ctx.font = "10px monospace";
    let displayName = config.name;
    if (monster.isGroup) {
      const count = monster.groupData.monsters.reduce((s, m) => s + (m.count || 1), 0);
      if (count > 1) displayName = `${displayName} x${count}`;
    }
    const nameWidth = ctx.measureText(displayName).width + 10;
    ctx.fillRect(x + s / 2 - nameWidth / 2, y - 14, nameWidth, 14);
    ctx.fillStyle = "#ff8888";
    ctx.textAlign = "center";
    ctx.fillText(displayName, x + s / 2, y - 4);

    const maxHp = config.stats?.hp || 100;
    const barWidth = s - p * 2;
    const barHeight = 3;
    const barY = y - 18;
    const barX = x + p;
    ctx.fillStyle = "#333";
    ctx.fillRect(barX, barY, barWidth, barHeight);
    const hpRatio = Math.min(1, maxHp / 500);
    ctx.fillStyle = "#44cc44";
    ctx.fillRect(barX, barY, barWidth * hpRatio, barHeight);
  }

  if (config.type === "elite") {
    ctx.fillStyle = "#ff0";
    ctx.font = "bold 10px monospace";
    ctx.textAlign = "center";
    ctx.fillText("★", x + s / 2, y - 18);
  } else if (config.type === "boss") {
    ctx.fillStyle = "#f44";
    ctx.font = "bold 10px monospace";
    ctx.textAlign = "center";
    ctx.fillText("♛", x + s / 2, y - 18);
  }
}

function drawMonsterSpriteOnCanvas(canvas, monsterId, isBoss, currentPhase) {
  if (!canvas) return;
  const mCtx = canvas.getContext("2d");
  mCtx.clearRect(0, 0, canvas.width, canvas.height);

  const config = monstersConfig[monsterId];
  if (!config) return;

  const s = canvas.width;
  const p = s / 8;
  const color = config.sprite_color;
  const accent = config.sprite_accent;

  mCtx.fillStyle = "rgba(0,0,0,0.2)";
  mCtx.fillRect(p * 2, s - p * 2, p * 4, p * 1);

  if (monsterId === "slime") {
    mCtx.fillStyle = color;
    mCtx.fillRect(p * 1, p * 4, p * 6, p * 3);
    mCtx.fillRect(p * 2, p * 3, p * 4, p * 1);
    mCtx.fillStyle = accent;
    mCtx.fillRect(p * 2, p * 3, p * 4, p * 1);
    mCtx.fillStyle = "#fff";
    mCtx.fillRect(p * 3, p * 5, p, p);
    mCtx.fillRect(p * 5, p * 5, p, p);
    mCtx.fillStyle = "#000";
    mCtx.fillRect(p * 3, p * 5, p * 0.5, p * 0.5);
    mCtx.fillRect(p * 5, p * 5, p * 0.5, p * 0.5);
  } else if (monsterId === "wild_wolf") {
    mCtx.fillStyle = color;
    mCtx.fillRect(p * 1, p * 5, p * 6, p * 2);
    mCtx.fillRect(p * 0, p * 4, p * 2, p * 2);
    mCtx.fillStyle = accent;
    mCtx.fillRect(p * 0, p * 4, p * 2, p * 2);
    mCtx.fillStyle = color;
    mCtx.fillRect(p * 2, p * 7, p, p);
    mCtx.fillRect(p * 5, p * 7, p, p);
    mCtx.fillStyle = "#ff0";
    mCtx.fillRect(p * 1, p * 4, p * 0.5, p * 0.5);
  } else if (monsterId === "forest_spider") {
    mCtx.fillStyle = color;
    mCtx.fillRect(p * 3, p * 4, p * 2, p * 2);
    mCtx.fillStyle = accent;
    mCtx.fillRect(p * 1, p * 3, p * 2, p);
    mCtx.fillRect(p * 5, p * 3, p * 2, p);
    mCtx.fillRect(p * 1, p * 6, p * 2, p);
    mCtx.fillRect(p * 5, p * 6, p * 2, p);
    mCtx.fillStyle = "#f00";
    mCtx.fillRect(p * 3, p * 4, p * 0.5, p * 0.5);
    mCtx.fillRect(p * 4.5, p * 4, p * 0.5, p * 0.5);
  } else if (monsterId === "goblin") {
    mCtx.fillStyle = color;
    mCtx.fillRect(p * 2, p * 3, p * 4, p * 4);
    mCtx.fillRect(p * 3, p * 1, p * 2, p * 3);
    mCtx.fillStyle = accent;
    mCtx.fillRect(p * 2, p * 1, p, p * 2);
    mCtx.fillRect(p * 5, p * 1, p, p * 2);
    mCtx.fillStyle = "#f00";
    mCtx.fillRect(p * 3, p * 3, p, p);
    mCtx.fillRect(p * 5, p * 3, p, p);
    mCtx.fillStyle = accent;
    mCtx.fillRect(p * 2, p * 7, p * 2, p);
    mCtx.fillRect(p * 4, p * 7, p * 2, p);
  } else if (monsterId === "dark_bear") {
    mCtx.fillStyle = color;
    mCtx.fillRect(p * 0, p * 3, p * 8, p * 4);
    mCtx.fillRect(p * 0, p * 2, p * 3, p * 2);
    mCtx.fillStyle = accent;
    mCtx.fillRect(p * 0, p * 2, p * 3, p * 2);
    mCtx.fillStyle = color;
    mCtx.fillRect(p * 1, p * 7, p * 2, p);
    mCtx.fillRect(p * 5, p * 7, p * 2, p);
    mCtx.fillStyle = "#f00";
    mCtx.fillRect(p * 1, p * 2, p * 0.5, p * 0.5);
  } else if (monsterId === "shadow_tree_spirit") {
    mCtx.fillStyle = color;
    mCtx.fillRect(p * 1, p * 2, p * 6, p * 5);
    mCtx.fillStyle = accent;
    mCtx.fillRect(p * 2, p * 1, p * 4, p * 2);
    mCtx.fillStyle = "#4a0e4a";
    mCtx.fillRect(p * 2, p * 3, p * 1.5, p * 1.5);
    mCtx.fillRect(p * 4.5, p * 3, p * 1.5, p * 1.5);
    mCtx.fillStyle = "#0f0";
    mCtx.fillRect(p * 2.5, p * 3.5, p * 0.5, p * 0.5);
    mCtx.fillRect(p * 5, p * 3.5, p * 0.5, p * 0.5);
    mCtx.fillStyle = "#1a3a1a";
    mCtx.fillRect(p * 1, p * 7, p * 2, p);
    mCtx.fillRect(p * 5, p * 7, p * 2, p);
  } else {
    mCtx.fillStyle = color;
    mCtx.fillRect(p * 2, p * 3, p * 4, p * 4);
    mCtx.fillStyle = accent;
    mCtx.fillRect(p * 3, p * 1, p * 2, p * 3);
  }

  if (isBoss && currentPhase >= 2) {
    mCtx.fillStyle = "rgba(255, 0, 0, 0.15)";
    mCtx.fillRect(0, 0, s, s);
  }
}

function checkMonsterCollision() {
  if (combatOpen || !mapMonsters.length) return null;

  const playerTile = getPlayerTilePosition();
  for (const m of mapMonsters) {
    if (!m.alive || m.inCombat) continue;
    const mx = Math.floor((m.x + TILE_SIZE / 2) / TILE_SIZE);
    const my = Math.floor((m.y + TILE_SIZE / 2) / TILE_SIZE);
    if (Math.abs(playerTile.x - mx) <= 1 && Math.abs(playerTile.y - my) <= 1) {
      return m;
    }
  }
  return null;
}

function getNearestMonster() {
  if (combatOpen || !mapMonsters.length) return null;

  const px = player.x + PLAYER_SIZE / 2;
  const py = player.y + PLAYER_SIZE / 2;
  let nearest = null;
  let minDist = Infinity;

  for (const m of mapMonsters) {
    if (!m.alive || m.inCombat) continue;
    const mx = m.x + TILE_SIZE / 2;
    const my = m.y + TILE_SIZE / 2;
    const dist = Math.sqrt((px - mx) ** 2 + (py - my) ** 2);
    if (dist < TILE_SIZE * 2 && dist < minDist) {
      minDist = dist;
      nearest = m;
    }
  }
  return nearest;
}

async function initiateCombat(monsterInstanceId) {
  if (combatOpen || dialogueOpen || inventoryOpen || shopOpen || playerInfoOpen || npcInteractOpen || GameManager.isMenuOpen() || talentPanelOpen) return;

  await savePlayerPosition();

  const mapMonster = mapMonsters.find(m => m.instance_id === monsterInstanceId);
  const isGroup = mapMonster && mapMonster.isGroup;

  try {
    const body = { map_id: currentMap.id };
    if (isGroup) {
      body.monster_group_id = monsterInstanceId;
    } else {
      body.monster_instance_id = monsterInstanceId;
    }

    const resp = await fetch("/api/combat/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (!resp.ok) {
      showInteractMessage(data.detail || "无法开始战斗");
      return;
    }

    combatSessionId = data.session_id;
    combatState = {
      ...data,
      monster_name: data.monster?.name || "",
      monster_hp: data.monster?.hp || 0,
      monster_max_hp: data.monster?.max_hp || 0,
      player_hp: data.player?.hp || 0,
      player_max_hp: data.player?.max_hp || 0,
      player_mp: data.player?.mp || 0,
      player_max_mp: data.player?.max_mp || 0,
      skills: data.player?.skills || [],
      turn_count: 1,
    };
    currentTargetIndex = data.target_index || 0;
    combatOpen = true;
    combatMonsterInstanceId = monsterInstanceId;

    const monster = mapMonsters.find(m => m.instance_id === monsterInstanceId);
    if (monster) monster.inCombat = true;

    document.getElementById("combat-panel").classList.add("active");
    renderCombat();
    renderMonsterSlots();
  } catch (e) {
    console.error("战斗请求失败:", e);
  }
}

function selectTarget(index) {
  if (!combatState || !combatState.monsters) return;
  const m = combatState.monsters[index];
  if (!m || !m.alive) return;
  currentTargetIndex = index;
  renderMonsterSlots();
}

function renderMonsterSlots() {
  const container = document.getElementById("combat-monsters-container");
  if (!container || !combatState) return;

  const monsters = combatState.monsters || [];
  container.innerHTML = "";

  monsters.forEach((m, idx) => {
    const slot = document.createElement("div");
    slot.className = "combat-monster-slot";
    if (idx === currentTargetIndex && m.alive) {
      slot.className += " selected";
    }
    if (!m.alive) {
      slot.className += " defeated";
    }
    if (m.is_boss) {
      slot.className += " boss";
    }
    slot.setAttribute("data-index", idx);
    slot.onclick = () => selectTarget(idx);

    const canvas = document.createElement("canvas");
    canvas.className = "monster-sprite-canvas";
    canvas.width = 64;
    canvas.height = 64;
    slot.appendChild(canvas);

    const nameDiv = document.createElement("div");
    nameDiv.className = "combat-monster-name";
    let nameText = m.name || "";
    if (m.is_boss && m.phase_name) {
      nameText += ` [${m.phase_name}]`;
    }
    nameDiv.textContent = nameText;
    slot.appendChild(nameDiv);

    const hpRow = document.createElement("div");
    hpRow.className = "combat-hp-bar-row";
    const hpLabel = document.createElement("span");
    hpLabel.className = "combat-hp-label";
    hpLabel.textContent = "HP";
    hpRow.appendChild(hpLabel);
    const hpBarOuter = document.createElement("div");
    hpBarOuter.className = "combat-hp-bar";
    const hpFill = document.createElement("div");
    hpFill.className = "combat-hp-fill monster-hp";
    const hpPct = m.max_hp > 0 ? (m.hp / m.max_hp) * 100 : 0;
    hpFill.style.width = hpPct + "%";
    if (m.is_boss && hpPct < 30) {
      hpFill.className += " boss-enraged";
    }
    hpBarOuter.appendChild(hpFill);
    hpRow.appendChild(hpBarOuter);
    const hpText = document.createElement("span");
    hpText.className = "combat-hp-text";
    hpText.textContent = `${m.hp}/${m.max_hp}`;
    hpRow.appendChild(hpText);
    slot.appendChild(hpRow);

    if (m.effects && m.effects.length > 0) {
      const effectsDiv = document.createElement("div");
      effectsDiv.className = "combat-monster-effects";
      effectsDiv.innerHTML = m.effects.map(e => {
        const color = e.type === "poison" ? "#88ff88" : e.type === "burn" ? "#ff8844" : e.type === "stun" ? "#ffff44" : e.type === "freeze" ? "#44ddff" : "#aaaaff";
        return `<span class="combat-effect" style="color:${color}">${e.type}(${e.duration})</span>`;
      }).join(" ");
      slot.appendChild(effectsDiv);
    }

    if (idx === currentTargetIndex && m.alive) {
      const targetLabel = document.createElement("div");
      targetLabel.className = "target-label";
      targetLabel.textContent = "目标";
      slot.appendChild(targetLabel);
    }

    if (!m.alive) {
      const defeatOverlay = document.createElement("div");
      defeatOverlay.className = "defeat-overlay";
      defeatOverlay.textContent = "击败";
      slot.appendChild(defeatOverlay);
    }

    container.appendChild(slot);

    drawMonsterSpriteOnCanvas(canvas, m.monster_id, m.is_boss, m.current_phase || 0);
  });

  const hint = document.getElementById("combat-target-hint");
  if (hint) {
    hint.style.display = monsters.filter(m => m.alive).length > 1 ? "block" : "none";
  }
}

function renderCombat() {
  if (!combatState) return;

  document.getElementById("combat-turn-info").textContent = `第 ${combatState.turn_count || 1} 回合`;

  const playerHpPct = (combatState.player_hp / combatState.player_max_hp) * 100;
  document.getElementById("combat-player-hp-bar").style.width = playerHpPct + "%";
  document.getElementById("combat-player-hp-text").textContent = `${combatState.player_hp}/${combatState.player_max_hp}`;

  const playerMpPct = ((combatState.player_mp || 0) / (combatState.player_max_mp || 1)) * 100;
  document.getElementById("combat-player-mp-bar").style.width = playerMpPct + "%";
  document.getElementById("combat-player-mp-text").textContent = `${combatState.player_mp || 0}/${combatState.player_max_mp || 0}`;

  renderEffects("combat-player-effects", combatState.player_effects || []);

  const isPlayerTurn = combatState.phase === "player_turn";
  document.getElementById("btn-combat-attack").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-defend").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-skill").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-item").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-flee").disabled = !isPlayerTurn;
}

function renderEffects(containerId, effects) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (!effects || effects.length === 0) {
    container.innerHTML = "";
    return;
  }
  container.innerHTML = effects.map(e => {
    const color = e.type === "poison" ? "#88ff88" : e.type === "burn" ? "#ff8844" : "#aaaaff";
    return `<span class="combat-effect" style="color:${color}">${e.type}(${e.duration})</span>`;
  }).join(" ");
}

const MAX_LOG_ENTRIES = 50;
const VISIBLE_LOG_ENTRIES = 15;

let combatLogBuffer = [];

function appendCombatLog(logEntries) {
  const logDiv = document.getElementById("combat-log");
  if (!logDiv) return;

  for (const entry of logEntries) {
    combatLogBuffer.push(entry);
  }

  while (combatLogBuffer.length > MAX_LOG_ENTRIES) {
    combatLogBuffer.shift();
  }

  renderCombatLog();
}

function renderCombatLog() {
  const logDiv = document.getElementById("combat-log");
  if (!logDiv) return;

  const startIdx = Math.max(0, combatLogBuffer.length - VISIBLE_LOG_ENTRIES);
  const visibleEntries = combatLogBuffer.slice(startIdx);

  const fragment = document.createDocumentFragment();
  for (const entry of visibleEntries) {
    const div = document.createElement("div");
    div.className = "combat-log-entry";

    if (entry.type === "player_attack") {
      div.className += entry.crit ? " log-crit" : " log-player";
    } else if (entry.type === "monster_attack") {
      div.className += entry.crit ? " log-crit" : " log-monster";
    } else if (entry.type === "player_defend") {
      div.className += " log-defend";
    } else if (entry.type === "monster_defend") {
      div.className += " log-defend";
    } else if (entry.type === "victory") {
      div.className += " log-victory";
    } else if (entry.type === "defeat") {
      div.className += " log-defeat";
    } else if (entry.type === "flee") {
      div.className += entry.fled ? " log-victory" : " log-monster";
    } else if (entry.type === "use_item") {
      div.className += entry.success ? " log-item" : " log-monster";
    } else if (entry.type === "skill") {
      div.className += entry.success ? " log-skill" : " log-monster";
    } else if (entry.type === "effect") {
      div.className += " log-effect";
    } else if (entry.type === "monster_special") {
      div.className += " log-special";
    } else if (entry.type === "boss_phase") {
      div.className += " log-crit";
    }

    div.textContent = entry.text || "";
    fragment.appendChild(div);
  }

  logDiv.innerHTML = "";
  logDiv.appendChild(fragment);
  logDiv.scrollTop = logDiv.scrollHeight;
}

async function combatAction(action, itemId) {
  if (combatAnimating || !combatOpen) return;
  if (combatState.phase !== "player_turn") return;

  combatAnimating = true;
  disableCombatButtons();

  if (combatItemSelectOpen) {
    closeCombatItemSelect();
  }
  if (combatSkillSelectOpen) {
    closeCombatSkillSelect();
  }

  try {
    const body = { session_id: combatSessionId, action: action, target_index: currentTargetIndex };
    if (action === "use_item" && itemId) {
      body.item_id = itemId;
    }
    if (action === "skill" && itemId) {
      body.skill_id = itemId;
    }

    const resp = await fetch("/api/combat/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();

    if (!resp.ok) {
      showInteractMessage(data.detail || "动作失败");
      combatAnimating = false;
      enableCombatButtons();
      return;
    }

    if (action === "attack") {
      await playCombatAnimation("player");
    }

    combatState = { ...combatState, ...data };

    if (data.target_index !== undefined) {
      currentTargetIndex = data.target_index;
    }

    const monsters = data.monsters || [];
    if (monsters.length > 0) {
      const currentTarget = monsters[currentTargetIndex];
      if (!currentTarget || !currentTarget.alive) {
        const firstAlive = monsters.findIndex(m => m.alive);
        if (firstAlive >= 0) {
          currentTargetIndex = firstAlive;
        }
      }
    }

    renderCombat();
    renderMonsterSlots();
    appendCombatLog(data.log || []);

    showDamageNumbers(data.log || []);

    const hasBossPhase = (data.log || []).some(l => l.type === "boss_phase");
    if (hasBossPhase) {
      await playBossPhaseAnimation(data.log.find(l => l.type === "boss_phase"));
    }

    const hasMonsterAttack = (data.log || []).some(l =>
      l.type === "monster_attack" || l.type === "monster_special"
    );
    if (hasMonsterAttack) {
      await playCombatAnimation("monster");
    }

    if (data.phase === "victory") {
      await showCombatResult(data, true);
    } else if (data.phase === "defeat") {
      await showCombatResult(data, false);
    }

    if (typeof fetchPlayerInfo === "function") {
      await fetchPlayerInfo();
    }
    if (typeof fetchInventory === "function") {
      fetchInventory();
    }

  } catch (e) {
    console.error("战斗动作失败:", e);
  } finally {
    combatAnimating = false;
    if (combatState && combatState.phase === "player_turn") {
      enableCombatButtons();
    }
  }
}

function showDamageNumbers(logEntries) {
  for (const entry of logEntries) {
    if (entry.type === "player_attack" && entry.damage) {
      const targetIdx = entry.target_index !== undefined ? entry.target_index : currentTargetIndex;
      spawnDamageNumber(targetIdx, entry.damage, entry.crit ? "crit" : "player");
    } else if (entry.type === "monster_attack" && entry.damage) {
      spawnDamageNumber("player", entry.damage, entry.crit ? "crit" : "monster");
    } else if (entry.type === "skill" && entry.damage) {
      if (entry.aoe) {
        const monsters = combatState.monsters || [];
        monsters.forEach((m, idx) => {
          if (m.alive) spawnDamageNumber(idx, entry.damage, "skill");
        });
      } else {
        const targetIdx = entry.target_index !== undefined ? entry.target_index : currentTargetIndex;
        spawnDamageNumber(targetIdx, entry.damage, "skill");
      }
    } else if (entry.type === "effect" && entry.damage) {
      if (entry.target === "player") {
        spawnDamageNumber("player", entry.damage, "effect");
      } else if (entry.target_index !== undefined) {
        spawnDamageNumber(entry.target_index, entry.damage, "effect");
      }
    }
  }
}

function spawnDamageNumber(target, value, type) {
  const panel = document.getElementById("combat-panel");
  if (!panel) return;

  const numEl = document.createElement("div");
  numEl.className = "damage-number";
  if (type === "crit") {
    numEl.className += " damage-crit";
    numEl.textContent = `${value}!`;
  } else if (type === "monster") {
    numEl.className += " damage-monster";
    numEl.textContent = `-${value}`;
  } else if (type === "skill") {
    numEl.className += " damage-skill";
    numEl.textContent = `${value}`;
  } else if (type === "effect") {
    numEl.className += " damage-effect";
    numEl.textContent = `-${value}`;
  } else if (type === "heal") {
    numEl.className += " damage-heal";
    numEl.textContent = `+${value}`;
  } else {
    numEl.textContent = `-${value}`;
  }

  let x, y;
  if (target === "player") {
    const playerArea = document.getElementById("combat-player-area");
    if (playerArea) {
      const rect = playerArea.getBoundingClientRect();
      const panelRect = panel.getBoundingClientRect();
      x = rect.left - panelRect.left + rect.width / 2 + (Math.random() - 0.5) * 30;
      y = rect.top - panelRect.top + 10;
    }
  } else {
    const slot = panel.querySelector(`.combat-monster-slot[data-index="${target}"]`);
    if (slot) {
      const rect = slot.getBoundingClientRect();
      const panelRect = panel.getBoundingClientRect();
      x = rect.left - panelRect.left + rect.width / 2 + (Math.random() - 0.5) * 30;
      y = rect.top - panelRect.top + 20;
    }
  }

  if (x !== undefined && y !== undefined) {
    numEl.style.left = x + "px";
    numEl.style.top = y + "px";
    panel.appendChild(numEl);
    setTimeout(() => {
      if (numEl.parentNode) numEl.parentNode.removeChild(numEl);
    }, 900);
  }
}

function animateEffectApplication(containerId, effectType) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const effectSpans = container.querySelectorAll(".combat-effect");
  for (const span of effectSpans) {
    if (span.textContent.startsWith(effectType)) {
      span.classList.add("effect-apply");
      setTimeout(() => span.classList.remove("effect-apply"), 600);
    }
  }
}

async function playCombatAnimation(who) {
  const panel = document.getElementById("combat-panel");
  if (!panel) return;

  if (who === "player") {
    const monsterArea = document.getElementById("combat-monster-area");
    monsterArea.classList.add("combat-shake");
    monsterArea.classList.add("combat-flash");
    if (typeof playPlayerAttackAnim === "function") playPlayerAttackAnim();
    await sleep(300);
    monsterArea.classList.remove("combat-shake");
    monsterArea.classList.remove("combat-flash");
  } else {
    const playerArea = document.getElementById("combat-player-area");
    playerArea.classList.add("combat-shake");
    panel.classList.add("combat-hit-flash");
    if (typeof playPlayerHitAnim === "function") playPlayerHitAnim();
    await sleep(300);
    playerArea.classList.remove("combat-shake");
    panel.classList.remove("combat-hit-flash");
  }
}

async function playBossPhaseAnimation(phaseLog) {
  const panel = document.getElementById("combat-panel");
  if (!panel) return;

  panel.classList.add("boss-phase-flash");
  await sleep(600);
  panel.classList.remove("boss-phase-flash");
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function showCombatResult(data, isVictory) {
  const overlay = document.getElementById("combat-result-overlay");
  const content = document.getElementById("combat-result-content");
  if (!overlay || !content) return;

  if (isVictory) {
    let html = `<div class="result-title victory-title">战斗胜利！</div>`;
    html += `<div class="result-rewards">`;
    html += `<div class="result-line">经验值: +${data.exp_reward || 0}</div>`;
    html += `<div class="result-line">金币: +${data.gold_reward || 0}</div>`;
    if (data.drops && data.drops.length > 0) {
      html += `<div class="result-line">掉落物品:</div>`;
      for (const drop of data.drops) {
        const name = drop.name || drop.item_id;
        html += `<div class="result-drop">- ${name} x${drop.quantity}</div>`;
      }
    }
    if (data.level_up && (data.level_up.leveled === true || data.level_up === true)) {
      html += `<div class="result-levelup">等级提升！</div>`;
    }
    if (data.fled) {
      html = `<div class="result-title flee-title">逃跑成功！</div>`;
    }
    html += `</div>`;
    html += `<button class="btn-result-continue" onclick="endCombat()">继续</button>`;
    content.innerHTML = html;
  } else {
    let html = `<div class="result-title defeat-title">战斗失败</div>`;
    html += `<div class="result-rewards">`;
    html += `<div class="result-line">你倒下了...</div>`;
    if (data.gold_lost > 0) {
      html += `<div class="result-line">损失金币: -${data.gold_lost}</div>`;
    }
    html += `</div>`;
    html += `<button class="btn-result-continue" onclick="endCombat()">继续</button>`;
    content.innerHTML = html;
  }

  overlay.style.display = "flex";
}

async function endCombat() {
  const overlay = document.getElementById("combat-result-overlay");
  if (overlay) overlay.style.display = "none";

  try {
    await fetch("/api/combat/end", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: combatSessionId }),
    });
  } catch (e) {
    console.error("结束战斗失败:", e);
  }

  if (combatMonsterInstanceId) {
    const monster = mapMonsters.find(m => m.instance_id === combatMonsterInstanceId);
    if (monster) {
      monster.alive = false;
      monster.inCombat = false;
    }
  }

  document.getElementById("combat-panel").classList.remove("active");
  combatOpen = false;
  combatSessionId = null;
  combatState = null;
  combatItemSelectOpen = false;
  combatMonsterInstanceId = null;
  currentTargetIndex = 0;

  const logDiv = document.getElementById("combat-log");
  if (logDiv) logDiv.innerHTML = "";

  combatLogBuffer = [];

  const container = document.getElementById("combat-monsters-container");
  if (container) container.innerHTML = "";

  if (typeof fetchPlayerInfo === "function") {
    await fetchPlayerInfo();
  }
  if (typeof updatePlayerHUD === "function") {
    updatePlayerHUD();
  }
}

let combatSkillSelectOpen = false;

function openCombatSkillSelect() {
  if (!combatOpen || combatState.phase !== "player_turn") return;

  combatSkillSelectOpen = true;
  const container = document.getElementById("combat-skills");
  container.innerHTML = "";

  const skills = combatState.skills || [];

  if (skills.length === 0) {
    container.innerHTML = '<div class="empty-hint">没有可用的技能</div>';
  } else {
    for (const skill of skills) {
      const div = document.createElement("div");
      const disabled = (skill.cooldown_remaining || 0) > 0 || (combatState.player_mp || 0) < (skill.mp_cost || 0);
      const cdText = (skill.cooldown_remaining || 0) > 0 ? ` [CD:${skill.cooldown_remaining}]` : "";
      const aoeTag = skill.aoe ? ' <span class="aoe-tag">群体</span>' : "";
      div.className = "combat-skill-row";
      div.innerHTML = `
        <span class="combat-skill-name">${skill.name}${cdText}${aoeTag}</span>
        <span class="combat-skill-cost">${skill.mp_cost}MP</span>
        <button class="btn-combat-use" ${disabled ? "disabled" : ""} onclick="combatAction('skill', '${skill.skill_id}')">使用</button>
      `;
      container.appendChild(div);
    }
  }

  document.getElementById("combat-skill-panel").classList.add("active");
}

function closeCombatSkillSelect() {
  combatSkillSelectOpen = false;
  document.getElementById("combat-skill-panel").classList.remove("active");
}

function openCombatItemSelect() {
  if (!combatOpen || combatState.phase !== "player_turn") return;

  combatItemSelectOpen = true;
  const container = document.getElementById("combat-items");
  container.innerHTML = "";

  const consumables = (inventoryState.items || []).filter(i => i.type === "consumable" || i.type === "food");

  if (consumables.length === 0) {
    container.innerHTML = '<div class="empty-hint">没有可用的物品</div>';
  } else {
    for (const item of consumables) {
      const div = document.createElement("div");
      div.className = "combat-item-row";
      div.innerHTML = `
        <span class="combat-item-name">${item.name}</span>
        <span class="combat-item-qty">x${item.quantity}</span>
        <button class="btn-combat-use" onclick="combatAction('use_item', '${item.item_id}')">使用</button>
      `;
      container.appendChild(div);
    }
  }

  document.getElementById("combat-item-panel").classList.add("active");
}

function closeCombatItemSelect() {
  combatItemSelectOpen = false;
  document.getElementById("combat-item-panel").classList.remove("active");
}

function disableCombatButtons() {
  document.getElementById("btn-combat-attack").disabled = true;
  document.getElementById("btn-combat-defend").disabled = true;
  document.getElementById("btn-combat-skill").disabled = true;
  document.getElementById("btn-combat-item").disabled = true;
  document.getElementById("btn-combat-flee").disabled = true;
}

function enableCombatButtons() {
  document.getElementById("btn-combat-attack").disabled = false;
  document.getElementById("btn-combat-defend").disabled = false;
  document.getElementById("btn-combat-skill").disabled = false;
  document.getElementById("btn-combat-item").disabled = false;
  document.getElementById("btn-combat-flee").disabled = false;
}

document.addEventListener("keydown", (e) => {
  if (!combatOpen || combatAnimating) return;

  if (combatItemSelectOpen) {
    if (e.key === "Escape") {
      closeCombatItemSelect();
    }
    return;
  }

  if (combatSkillSelectOpen) {
    if (e.key === "Escape") {
      closeCombatSkillSelect();
    }
    return;
  }

  if (combatState && combatState.phase === "player_turn") {
    if (e.key === "1") combatAction("attack");
    else if (e.key === "2") combatAction("defend");
    else if (e.key === "3") openCombatSkillSelect();
    else if (e.key === "4") openCombatItemSelect();
    else if (e.key === "5") combatAction("flee");
    else if (e.key === "Tab") {
      e.preventDefault();
      const monsters = combatState.monsters || [];
      const aliveIndices = monsters.map((m, i) => m.alive ? i : -1).filter(i => i >= 0);
      if (aliveIndices.length > 1) {
        const currentPos = aliveIndices.indexOf(currentTargetIndex);
        const nextPos = (currentPos + 1) % aliveIndices.length;
        selectTarget(aliveIndices[nextPos]);
      }
    }
  }
});
