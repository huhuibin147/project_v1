// 战斗系统 - 多敌人支持

const EFFECT_MAP = {
  poison:      { name: "中毒",   icon: "☠️",  color: "#88ff88" },
  burn:        { name: "灼烧",   icon: "🔥",  color: "#ff8844" },
  freeze:      { name: "冻结",   icon: "❄️",  color: "#44ddff" },
  stun:        { name: "眩晕",   icon: "💫",  color: "#ffff44" },
  silence:     { name: "沉默",   icon: "🤐",  color: "#aaaaff" },
  bleed:       { name: "流血",   icon: "🩸",  color: "#ff4444" },
  speed_down:  { name: "减速",   icon: "🐌",  color: "#cc88ff" },
  shield:      { name: "护盾",   icon: "🛡️",  color: "#ffcc00" },
  regen:       { name: "再生",   icon: "💚",  color: "#44ff88" },
  reflect:     { name: "反伤",   icon: "🔄",  color: "#ff88ff" },
  lifesteal:   { name: "吸血",   icon: "🧛",  color: "#cc44ff" },
  attack_up:   { name: "攻击↑", icon: "⚔️",  color: "#ff6644" },
  defense_up:  { name: "防御↑", icon: "🛡️",  color: "#4488ff" },
  speed_up:    { name: "速度↑", icon: "💨",  color: "#44ffcc" },
  defense_down:{ name: "防御↓", icon: "💔",  color: "#ff4488" },
  fear:        { name: "恐惧",   icon: "👻",  color: "#aa44ff" },
};

const ELEMENT_MAP = {
  fire:  { name: "火", icon: "🔥", color: "#ff6644" },
  water: { name: "水", icon: "💧", color: "#44aaff" },
  grass: { name: "草", icon: "🌿", color: "#44cc44" },
  none:  { name: "",   icon: "",   color: "#aaaaaa" },
};

const INTENT_ICONS = {
  attack: "⚔️",
  defend: "🛡️",
  special: "✨",
  summon: "👻",
  shield: "🔰",
  elemental_attack: "🔥",
  buff_self: "💪",
  drain: "🧛",
  aoe_attack: "💥",
  self_heal: "💚",
  apply_effect: "☠️",
};

function getEffectDisplay(effectType) {
  return EFFECT_MAP[effectType] || { name: effectType, icon: "❓", color: "#aaaaff" };
}

function getIntentIcon(intent) {
  if (typeof intent === "object" && intent !== null) {
    if (intent.action === "special" && intent.special_type) {
      return INTENT_ICONS[intent.special_type] || INTENT_ICONS["special"];
    }
    return INTENT_ICONS[intent.action] || "⚔️";
  }
  return INTENT_ICONS[intent] || "⚔️";
}

function guessMonsterIntent(m) {
  if (!m.alive) return "";
  if (m.defending) return "defend";
  const config = monstersConfig[m.monster_id];
  if (!config) return "attack";
  const ai = config.ai || {};
  const special = ai.special;
  if (special) {
    return {"action": "special", "special_type": special.type || "apply_effect"};
  }
  return "attack";
}

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
  if (!currentMap) return;

  const groups = currentMap.monster_groups || [];
  groups.forEach((group) => {
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
      patrol: (group.patrol || []).map(p => ({ x: p.x * TILE_SIZE, y: p.y * TILE_SIZE })),
      patrolIndex: 0,
      patrolSpeed: group.patrol ? 0.5 : 0,
      animFrame: 0,
      direction: "down",
      isGroup: group.monsters.length > 1 || !!group.group_id,
      groupData: group,
    });
  });
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

function drawSpritePart(ctx, p, part, bodyConfig) {
  const bodyColor = bodyConfig ? bodyConfig.color : "#888";
  switch (part.type) {
    case "rect":
      ctx.fillStyle = part.color || bodyColor;
      ctx.fillRect(p * part.x, p * part.y, p * part.w, p * part.h);
      break;
    case "rounded_rect": {
      ctx.fillStyle = part.color || bodyColor;
      const rx = p * part.x, ry = p * part.y;
      const rw = p * part.w, rh = p * part.h;
      const r = p * (part.radius || 1);
      ctx.beginPath();
      ctx.moveTo(rx + r, ry);
      ctx.lineTo(rx + rw - r, ry);
      ctx.quadraticCurveTo(rx + rw, ry, rx + rw, ry + r);
      ctx.lineTo(rx + rw, ry + rh - r);
      ctx.quadraticCurveTo(rx + rw, ry + rh, rx + rw - r, ry + rh);
      ctx.lineTo(rx + r, ry + rh);
      ctx.quadraticCurveTo(rx, ry + rh, rx, ry + rh - r);
      ctx.lineTo(rx, ry + r);
      ctx.quadraticCurveTo(rx, ry, rx + r, ry);
      ctx.closePath();
      ctx.fill();
      break;
    }
    case "circle":
      ctx.fillStyle = part.color || bodyColor;
      ctx.beginPath();
      ctx.arc(p * part.cx, p * part.cy, p * part.r, 0, Math.PI * 2);
      ctx.fill();
      break;
    case "ellipse":
      ctx.fillStyle = part.color || bodyColor;
      ctx.beginPath();
      ctx.ellipse(p * part.cx, p * part.cy, p * part.rx, p * part.ry, 0, 0, Math.PI * 2);
      ctx.fill();
      break;
    case "triangle":
      ctx.fillStyle = part.color || bodyColor;
      ctx.beginPath();
      ctx.moveTo(p * part.x1, p * part.y1);
      ctx.lineTo(p * part.x2, p * part.y2);
      ctx.lineTo(p * part.x3, p * part.y3);
      ctx.closePath();
      ctx.fill();
      break;
    case "eyes": {
      const ey = p * part.y;
      const spacing = p * (part.spacing || 2);
      const eyeSize = p * (part.size || 1);
      const pupilSize = p * (part.pupil_size || 0.5);
      const centerX = p * (bodyConfig ? (bodyConfig.x + bodyConfig.w / 2) : 4);
      const leftX = centerX - spacing / 2;
      const rightX = centerX + spacing / 2;
      const style = part.style || "round";
      ctx.fillStyle = part.eye_color || "#fff";
      if (style === "slit") {
        ctx.fillRect(leftX - eyeSize / 2, ey - eyeSize / 2, eyeSize, eyeSize);
        ctx.fillRect(rightX - eyeSize / 2, ey - eyeSize / 2, eyeSize, eyeSize);
      } else {
        ctx.beginPath();
        ctx.arc(leftX, ey, eyeSize / 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(rightX, ey, eyeSize / 2, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.fillStyle = part.pupil_color || "#000";
      if (style === "slit") {
        ctx.fillRect(leftX - pupilSize / 4, ey - eyeSize / 2, pupilSize / 2, eyeSize);
        ctx.fillRect(rightX - pupilSize / 4, ey - eyeSize / 2, pupilSize / 2, eyeSize);
      } else {
        ctx.beginPath();
        ctx.arc(leftX, ey, pupilSize / 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(rightX, ey, pupilSize / 2, 0, Math.PI * 2);
        ctx.fill();
      }
      break;
    }
    case "legs": {
      const ly = p * part.y;
      const count = part.count || 2;
      const lSpacing = p * (part.spacing || 2);
      const lw = p * (part.w || 1);
      const lh = p * (part.h || 1);
      const lColor = part.color || bodyColor;
      const centerX = p * (bodyConfig ? (bodyConfig.x + bodyConfig.w / 2) : 4);
      ctx.fillStyle = lColor;
      for (let i = 0; i < count; i++) {
        const lx = centerX - (p * (part.spacing || 2) * (count - 1)) / 2 + i * lSpacing;
        ctx.fillRect(lx - lw / 2, ly, lw, lh);
      }
      break;
    }
    case "horns": {
      const hy = p * part.y;
      const hSpacing = p * (part.spacing || 2);
      const hw = p * (part.w || 1);
      const hh = p * (part.h || 2);
      const hColor = part.color || bodyColor;
      const centerX = p * (bodyConfig ? (bodyConfig.x + bodyConfig.w / 2) : 4);
      ctx.fillStyle = hColor;
      if (part.style === "round") {
        ctx.beginPath();
        ctx.arc(centerX - hSpacing / 2, hy, hw / 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(centerX + hSpacing / 2, hy, hw / 2, 0, Math.PI * 2);
        ctx.fill();
      } else {
        ctx.beginPath();
        ctx.moveTo(centerX - hSpacing / 2 - hw / 2, hy + hh);
        ctx.lineTo(centerX - hSpacing / 2, hy);
        ctx.lineTo(centerX - hSpacing / 2 + hw / 2, hy + hh);
        ctx.closePath();
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(centerX + hSpacing / 2 - hw / 2, hy + hh);
        ctx.lineTo(centerX + hSpacing / 2, hy);
        ctx.lineTo(centerX + hSpacing / 2 + hw / 2, hy + hh);
        ctx.closePath();
        ctx.fill();
      }
      break;
    }
  }
}

function drawSprite(ctx, spriteConfig, p) {
  const shadow = spriteConfig.shadow !== false;
  if (shadow) {
    const sx = spriteConfig.shadow_x || 2;
    const sy = spriteConfig.shadow_y || 6;
    const sw = spriteConfig.shadow_w || 4;
    const sh = spriteConfig.shadow_h || 1;
    ctx.fillStyle = "rgba(0,0,0,0.2)";
    ctx.fillRect(p * sx, p * sy, p * sw, p * sh);
  }

  const body = spriteConfig.body;
  if (body) {
    drawSpritePart(ctx, p, { type: body.shape || "rect", ...body }, body);
  }

  const parts = spriteConfig.parts || [];
  for (const part of parts) {
    drawSpritePart(ctx, p, part, body);
  }
}

function getDefaultSprite(color, accent) {
  return {
    body: { shape: "rect", color: color, x: 2, y: 3, w: 4, h: 4 },
    parts: [
      { type: "rect", color: accent, x: 3, y: 1, w: 2, h: 3 }
    ]
  };
}

function deepMergeSprite(base, override) {
  if (!override) return base;
  const result = JSON.parse(JSON.stringify(base));
  if (override.body) {
    result.body = { ...result.body, ...override.body };
  }
  if (override.parts) {
    result.parts = override.parts;
  }
  if (override.tint) {
    result.tint = override.tint;
  }
  return result;
}

function drawMonsterSpriteOnCanvas(canvas, monsterId, isBoss, currentPhase) {
  if (!canvas) return;
  const mCtx = canvas.getContext("2d");
  mCtx.clearRect(0, 0, canvas.width, canvas.height);

  const config = monstersConfig[monsterId];
  if (!config) return;

  const s = canvas.width;
  const p = s / 8;

  let spriteConfig = config.sprite || getDefaultSprite(config.sprite_color, config.sprite_accent);

  if (isBoss && currentPhase >= 2 && config.sprite_phases && config.sprite_phases[String(currentPhase)]) {
    spriteConfig = deepMergeSprite(spriteConfig, config.sprite_phases[String(currentPhase)]);
  }

  drawSprite(mCtx, spriteConfig, p);

  if (isBoss && currentPhase >= 2 && !spriteConfig.tint) {
    mCtx.fillStyle = "rgba(255, 0, 0, 0.15)";
    mCtx.fillRect(0, 0, s, s);
  } else if (spriteConfig.tint) {
    mCtx.fillStyle = spriteConfig.tint;
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
  if (combatOpen || dialogueOpen || inventoryOpen || shopOpen || playerInfoOpen || npcInteractOpen || GameManager.isMenuOpen() || talentPanelOpen || skillMenuOpen) return;

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
      player_shield: data.player_shield || 0,
      player_name: (typeof playerInfo !== "undefined" && playerInfo.name) || "冒险者",
      player_level: (typeof playerInfo !== "undefined" && playerInfo.level) || 1,
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

  const monsterCountEl = document.getElementById("combat-monster-count");
  if (monsterCountEl) {
    const aliveCount = monsters.filter(m => m.alive).length;
    monsterCountEl.textContent = aliveCount > 1 ? `存活: ${aliveCount}/${monsters.length}` : "";
  }

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

    const nameDiv = document.createElement("div");
    nameDiv.className = "combat-monster-name";
    let nameText = m.name || "";
    if (m.is_boss && m.phase_name) {
      nameText += ` [${m.phase_name}]`;
    }
    nameDiv.textContent = nameText;
    slot.appendChild(nameDiv);

    const metaDiv = document.createElement("div");
    metaDiv.className = "combat-monster-meta";
    const config = monstersConfig[m.monster_id];
    const level = m.level || (config && config.level) || "?";
    const monsterType = m.monster_type || (config && config.type) || "normal";
    let metaHtml = `<span class="monster-level">Lv.${level}</span>`;
    const elementKey = m.element || (config && config.element) || "none";
    const elemInfo = ELEMENT_MAP[elementKey];
    if (elemInfo && elemInfo.icon) {
      metaHtml += `<span class="monster-element" style="color:${elemInfo.color}">${elemInfo.icon}${elemInfo.name}</span>`;
    }
    if (monsterType === "boss") {
      metaHtml += `<span class="monster-type-badge boss-badge">BOSS</span>`;
    } else if (monsterType === "elite") {
      metaHtml += `<span class="monster-type-badge elite-badge">精英</span>`;
    }
    if (m.alive) {
      const intent = m.next_action || guessMonsterIntent(m);
      metaHtml += `<span class="monster-intent">${getIntentIcon(intent)}</span>`;
    }
    metaDiv.innerHTML = metaHtml;
    slot.appendChild(metaDiv);

    const canvas = document.createElement("canvas");
    canvas.className = "monster-sprite-canvas";
    canvas.width = 64;
    canvas.height = 64;
    slot.appendChild(canvas);

    const hpRow = document.createElement("div");
    hpRow.className = "combat-bar-row";
    const hpLabel = document.createElement("span");
    hpLabel.className = "combat-bar-label hp-label";
    hpLabel.textContent = "HP";
    hpRow.appendChild(hpLabel);
    const hpBarOuter = document.createElement("div");
    hpBarOuter.className = "combat-bar";
    const hpFill = document.createElement("div");
    hpFill.className = "combat-bar-fill monster-hp";
    const hpPct = m.max_hp > 0 ? (m.hp / m.max_hp) * 100 : 0;
    hpFill.style.width = hpPct + "%";
    if (m.is_boss && hpPct < 30) {
      hpFill.className += " boss-enraged";
    }
    hpBarOuter.appendChild(hpFill);
    hpRow.appendChild(hpBarOuter);
    const hpText = document.createElement("span");
    hpText.className = "combat-bar-text";
    hpText.textContent = `${m.hp}/${m.max_hp}`;
    hpRow.appendChild(hpText);
    slot.appendChild(hpRow);

    if (m.effects && m.effects.length > 0) {
      const effectsDiv = document.createElement("div");
      effectsDiv.className = "combat-monster-effects";
      effectsDiv.innerHTML = m.effects.map(e => {
        const display = getEffectDisplay(e.type);
        const stackText = e.stack > 1 ? `x${e.stack}` : "";
        return `<span class="combat-effect" style="color:${display.color}">${display.icon}${display.name}${stackText}(${e.duration})</span>`;
      }).join(" ");
      slot.appendChild(effectsDiv);
    }

    if (idx === currentTargetIndex && m.alive) {
      const targetLabel = document.createElement("div");
      targetLabel.className = "target-indicator";
      targetLabel.textContent = "▶ 目标";
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
}

function renderCombat() {
  if (!combatState) return;

  document.getElementById("combat-turn-info").textContent = `第 ${combatState.turn_count || 1} 回合`;

  const playerNameEl = document.getElementById("combat-player-name");
  if (playerNameEl && combatState.player_name) {
    playerNameEl.textContent = combatState.player_name;
  }

  const playerLevelEl = document.getElementById("combat-player-level");
  if (playerLevelEl && combatState.player_level) {
    playerLevelEl.textContent = `Lv.${combatState.player_level}`;
  }

  const playerHpPct = (combatState.player_hp / combatState.player_max_hp) * 100;
  const hpBar = document.getElementById("combat-player-hp-bar");
  hpBar.style.width = playerHpPct + "%";
  hpBar.classList.remove("hp-low", "hp-mid");
  if (playerHpPct < 25) {
    hpBar.classList.add("hp-low");
  } else if (playerHpPct < 50) {
    hpBar.classList.add("hp-mid");
  }
  document.getElementById("combat-player-hp-text").textContent = `${combatState.player_hp}/${combatState.player_max_hp}`;

  const playerMpPct = ((combatState.player_mp || 0) / (combatState.player_max_mp || 1)) * 100;
  document.getElementById("combat-player-mp-bar").style.width = playerMpPct + "%";
  document.getElementById("combat-player-mp-text").textContent = `${combatState.player_mp || 0}/${combatState.player_max_mp || 0}`;

  const shieldRow = document.getElementById("combat-shield-row");
  const shieldBar = document.getElementById("combat-player-shield-bar");
  const shieldText = document.getElementById("combat-player-shield-text");
  const playerShield = combatState.player_shield || 0;
  if (playerShield > 0) {
    shieldRow.style.display = "flex";
    const shieldPct = Math.min(100, (playerShield / combatState.player_max_hp) * 100);
    shieldBar.style.width = shieldPct + "%";
    shieldText.textContent = `${playerShield}`;
  } else {
    shieldRow.style.display = "none";
  }

  renderEffects("combat-player-effects", combatState.player_effects || []);

  drawPlayerAvatar();

  const isPlayerTurn = combatState.phase === "player_turn";
  document.getElementById("btn-combat-attack").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-defend").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-skill").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-item").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-flee").disabled = !isPlayerTurn;
}

function drawPlayerAvatar() {
  const canvas = document.getElementById("combat-player-avatar");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, 48, 48);

  const s = 48;
  const p = s / 8;

  ctx.fillStyle = "rgba(0,100,255,0.1)";
  ctx.fillRect(0, 0, s, s);

  ctx.fillStyle = "#4488cc";
  ctx.fillRect(p * 2, p * 1, p * 4, p * 3);
  ctx.fillRect(p * 1, p * 4, p * 6, p * 3);

  ctx.fillStyle = "#336699";
  ctx.fillRect(p * 3, p * 1, p * 2, p * 2);

  ctx.fillStyle = "#ffcc88";
  ctx.fillRect(p * 3, p * 3, p * 2, p * 1);

  ctx.fillStyle = "#fff";
  ctx.fillRect(p * 3.5, p * 3.5, p * 0.5, p * 0.5);
  ctx.fillRect(p * 5, p * 3.5, p * 0.5, p * 0.5);

  ctx.fillStyle = "#555";
  ctx.fillRect(p * 1, p * 7, p * 2, p);
  ctx.fillRect(p * 5, p * 7, p * 2, p);

  const cls = (typeof playerInfo !== "undefined" && playerInfo.class_id) || "warrior";
  if (cls === "mage") {
    ctx.fillStyle = "#8844cc";
    ctx.fillRect(p * 1, p * 0, p * 1, p * 4);
    ctx.fillStyle = "#aa66ff";
    ctx.fillRect(p * 0.5, p * 0, p * 2, p * 1);
  } else if (cls === "ranger") {
    ctx.fillStyle = "#44aa44";
    ctx.fillRect(p * 6, p * 2, p * 1.5, p * 0.5);
    ctx.fillRect(p * 7, p * 1.5, p * 0.5, p * 1.5);
  } else {
    ctx.fillStyle = "#aaa";
    ctx.fillRect(p * 0, p * 2, p * 1, p * 4);
    ctx.fillStyle = "#888";
    ctx.fillRect(p * 0.5, p * 1.5, p * 0.5, p * 1);
  }
}

function renderEffects(containerId, effects) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (!effects || effects.length === 0) {
    container.innerHTML = "";
    return;
  }
  container.innerHTML = effects.map(e => {
    const display = getEffectDisplay(e.type);
    const stackText = e.stack > 1 ? `x${e.stack}` : "";
    return `<span class="combat-effect" style="color:${display.color}">${display.icon}${display.name}${stackText}(${e.duration})</span>`;
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

const LOG_ICONS = {
  player_attack: "⚔️",
  monster_attack: "🗡️",
  player_defend: "🛡️",
  monster_defend: "🛡️",
  victory: "🏆",
  defeat: "💀",
  flee: "🏃",
  use_item: "🧪",
  skill: "✨",
  effect: "☠️",
  monster_special: "⚡",
  boss_phase: "🔥",
  reflect: "🔄",
  lifesteal: "🧛",
  talent: "⭐",
  affix: "💎",
  element_advantage: "🔥",
  element_disadvantage: "💧",
};

const SPECIAL_TYPE_ICONS = {
  summon: "👻",
  shield: "🔰",
  elemental_attack: "🔥",
  buff_self: "💪",
  drain: "🧛",
  aoe_attack: "💥",
  self_heal: "💚",
  apply_effect: "☠️",
};

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
    } else if (entry.type === "reflect") {
      div.className += " log-reflect";
    } else if (entry.type === "lifesteal") {
      div.className += " log-lifesteal";
    } else if (entry.type === "affix") {
      div.className += " log-affix";
    } else if (entry.type === "talent") {
      div.className += " log-talent";
    } else if (entry.type === "effect_end") {
      div.className += " log-effect";
    } else if (entry.type === "monster_idle") {
      div.className += " log-monster";
    } else if (entry.type === "element_advantage") {
      div.className += " log-element-advantage";
    } else if (entry.type === "element_disadvantage") {
      div.className += " log-element-disadvantage";
    }

    let icon = LOG_ICONS[entry.type] || "";
    if (entry.type === "monster_special" && entry.special_type) {
      icon = SPECIAL_TYPE_ICONS[entry.special_type] || icon;
    }
    div.textContent = icon ? `${icon} ${entry.text || ""}` : (entry.text || "");
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
    } else if (action === "skill") {
      const skillData = combatState.skills?.find(s => s.skill_id === itemId);
      if (skillData?.aoe) {
        await playAoeAnimation();
      } else {
        await playCombatAnimation("player");
      }
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
    } else if (entry.type === "monster_special" && entry.damage) {
      spawnDamageNumber("player", entry.damage, entry.aoe || entry.special_type === "elemental_attack" ? "crit" : "monster");
      if (entry.heal) {
        const monsterIdx = entry.monster_index !== undefined ? entry.monster_index : 0;
        spawnDamageNumber(monsterIdx, entry.heal, "heal");
      }
    } else if (entry.type === "skill" && (entry.damage || entry.aoe)) {
      if (entry.aoe && entry.targets) {
        for (const t of entry.targets) {
          spawnDamageNumber(t.monster_index, t.damage, t.crit ? "crit" : "skill");
        }
      } else if (entry.aoe) {
        const monsters = combatState.monsters || [];
        monsters.forEach((m, idx) => {
          if (m.alive) spawnDamageNumber(idx, entry.damage, "skill");
        });
      } else {
        const targetIdx = entry.target_index !== undefined ? entry.target_index : currentTargetIndex;
        spawnDamageNumber(targetIdx, entry.damage, entry.crit ? "crit" : "skill");
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

async function playAoeAnimation() {
  const monsterSlots = document.querySelectorAll(".combat-monster-slot");
  monsterSlots.forEach(slot => {
    slot.classList.add("aoe-hit-flash");
  });
  if (typeof playPlayerAttackAnim === "function") playPlayerAttackAnim();
  await sleep(400);
  monsterSlots.forEach(slot => {
    slot.classList.remove("aoe-hit-flash");
  });
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

  const totalTurns = combatState.turn_count || 1;
  const totalDamage = combatLogBuffer.reduce((sum, e) => {
    if (e.type === "player_attack" || (e.type === "skill" && e.damage)) return sum + (e.damage || 0);
    return sum;
  }, 0);
  const critCount = combatLogBuffer.filter(e => e.crit).length;
  const maxHit = combatLogBuffer.reduce((max, e) => {
    if ((e.type === "player_attack" || e.type === "skill") && e.damage) return Math.max(max, e.damage);
    return max;
  }, 0);

  if (isVictory) {
    let html = `<div class="result-title victory-title">🏆 战斗胜利！</div>`;

    html += `<div class="result-section">`;
    html += `<div class="result-section-title">── 战斗统计 ──</div>`;
    html += `<div class="result-stat"><span>总回合数</span><span class="result-stat-value">${totalTurns}</span></div>`;
    if (totalDamage > 0) {
      html += `<div class="result-stat"><span>总伤害</span><span class="result-stat-value">${totalDamage}</span></div>`;
    }
    if (maxHit > 0) {
      html += `<div class="result-stat"><span>最大单次伤害</span><span class="result-stat-value">${maxHit}${critCount > 0 ? ' (暴击)' : ''}</span></div>`;
    }
    if (critCount > 0) {
      html += `<div class="result-stat"><span>暴击次数</span><span class="result-stat-value">${critCount}</span></div>`;
    }
    html += `</div>`;

    html += `<div class="result-section">`;
    html += `<div class="result-section-title">── 获得奖励 ──</div>`;
    html += `<div class="result-line">✨ 经验值: +${data.exp_reward || 0}</div>`;
    html += `<div class="result-line">💰 金币: +${data.gold_reward || 0}</div>`;
    if (data.drops && data.drops.length > 0) {
      html += `<div class="result-line">📦 掉落:</div>`;
      for (const drop of data.drops) {
        const name = drop.name || drop.item_id;
        html += `<div class="result-drop">- ${name} x${drop.quantity}</div>`;
      }
    }
    html += `</div>`;

    if (data.level_up && (data.level_up.leveled === true || data.level_up === true)) {
      html += `<div class="result-levelup">🎉 等级提升！</div>`;
    }
    if (data.fled) {
      html = `<div class="result-title flee-title">🏃 逃跑成功！</div>`;
    }
    html += `<div class="result-buttons">`;
    html += `<button class="btn-result-continue" onclick="viewCombatLog()">📜 查看记录</button>`;
    html += `<button class="btn-result-close" onclick="endCombat()">✕ 关闭</button>`;
    html += `</div>`;
    content.innerHTML = html;
  } else {
    let html = `<div class="result-title defeat-title">💀 战斗失败</div>`;
    html += `<div class="result-rewards">`;
    html += `<div class="result-line">你倒下了...</div>`;
    if (data.gold_lost > 0) {
      html += `<div class="result-line">损失金币: -${data.gold_lost}</div>`;
    }
    html += `</div>`;
    html += `<div class="result-buttons">`;
    html += `<button class="btn-result-continue" onclick="viewCombatLog()">📜 查看记录</button>`;
    html += `<button class="btn-result-close" onclick="endCombat()">✕ 关闭</button>`;
    html += `</div>`;
    content.innerHTML = html;
  }

  overlay.style.display = "flex";
}

function viewCombatLog() {
  const overlay = document.getElementById("combat-result-overlay");
  if (overlay) overlay.style.display = "none";

  // 禁用战斗操作按钮
  const actionButtons = document.querySelectorAll("#combat-action-main .btn-combat, .btn-flee");
  actionButtons.forEach(btn => {
    btn.disabled = true;
    btn.style.opacity = "0.3";
  });

  // 显示关闭按钮
  const closeBtn = document.getElementById("btn-combat-close");
  if (closeBtn) closeBtn.style.display = "inline-block";
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

  // 恢复按钮状态
  const actionButtons = document.querySelectorAll("#combat-action-main .btn-combat, .btn-flee");
  actionButtons.forEach(btn => {
    btn.disabled = false;
    btn.style.opacity = "";
  });
  const closeBtn = document.getElementById("btn-combat-close");
  if (closeBtn) closeBtn.style.display = "none";

  if (typeof fetchPlayerInfo === "function") {
    await fetchPlayerInfo();
  }
  if (typeof updatePlayerHUD === "function") {
    updatePlayerHUD();
  }
  if (typeof updateQuestTracker === "function") {
    updateQuestTracker();
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
