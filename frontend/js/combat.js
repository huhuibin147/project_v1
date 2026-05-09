// 战斗系统

let combatOpen = false;
let combatSessionId = null;
let combatState = null;
let combatAnimating = false;
let combatItemSelectOpen = false;
let combatMonsterInstanceId = null;

// 地图上的怪物
let mapMonsters = [];
let monstersConfig = {};

// 加载怪物配置
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

// 加载当前地图的怪物
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
}

// 更新怪物巡逻
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

// 绘制怪物（地图上）
function drawMapMonster(ctx, monster) {
  if (!monster.alive) return;

  const x = Math.round(monster.x);
  const y = Math.round(monster.y);
  const s = TILE_SIZE;
  const p = s / 8;
  const config = monster.config;
  const bounce = Math.sin(monster.animFrame * 0.1) * 2;

  // 战斗中灰化
  const alpha = monster.inCombat ? 0.4 : 1.0;
  ctx.globalAlpha = alpha;

  // 阴影
  ctx.fillStyle = "rgba(0,0,0,0.2)";
  ctx.fillRect(x + p * 2, y + s - p * 2, p * 4, p * 1);

  // 根据怪物类型绘制不同形状
  const type = monster.monster_id;
  const color = config.sprite_color;
  const accent = config.sprite_accent;

  if (type === "slime") {
    // 史莱姆：弹跳球
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 1, y + p * 4 + bounce, p * 6, p * 3);
    ctx.fillRect(x + p * 2, y + p * 3 + bounce, p * 4, p * 1);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 2, y + p * 3 + bounce, p * 4, p * 1);
    // 眼睛
    ctx.fillStyle = "#fff";
    ctx.fillRect(x + p * 3, y + p * 5 + bounce, p, p);
    ctx.fillRect(x + p * 5, y + p * 5 + bounce, p, p);
    ctx.fillStyle = "#000";
    ctx.fillRect(x + p * 3, y + p * 5 + bounce, p * 0.5, p * 0.5);
    ctx.fillRect(x + p * 5, y + p * 5 + bounce, p * 0.5, p * 0.5);
  } else if (type === "wild_wolf") {
    // 野狼：低矮四足
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 1, y + p * 5 + bounce, p * 6, p * 2);
    ctx.fillRect(x + p * 0, y + p * 4 + bounce, p * 2, p * 2);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 0, y + p * 4 + bounce, p * 2, p * 2);
    // 腿
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 2, y + p * 7 + bounce, p, p);
    ctx.fillRect(x + p * 5, y + p * 7 + bounce, p, p);
    // 眼睛
    ctx.fillStyle = "#ff0";
    ctx.fillRect(x + p * 1, y + p * 4 + bounce, p * 0.5, p * 0.5);
  } else if (type === "forest_spider") {
    // 毒蛛：多腿
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 3, y + p * 4 + bounce, p * 2, p * 2);
    // 腿
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 1, y + p * 3 + bounce, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 3 + bounce, p * 2, p);
    ctx.fillRect(x + p * 1, y + p * 6 + bounce, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 6 + bounce, p * 2, p);
    // 眼睛
    ctx.fillStyle = "#f00";
    ctx.fillRect(x + p * 3, y + p * 4 + bounce, p * 0.5, p * 0.5);
    ctx.fillRect(x + p * 4.5, y + p * 4 + bounce, p * 0.5, p * 0.5);
  } else if (type === "goblin") {
    // 哥布林：人形尖耳
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 2, y + p * 3 + bounce, p * 4, p * 4);
    ctx.fillRect(x + p * 3, y + p * 1 + bounce, p * 2, p * 3);
    // 尖耳
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 2, y + p * 1 + bounce, p, p * 2);
    ctx.fillRect(x + p * 5, y + p * 1 + bounce, p, p * 2);
    // 眼睛
    ctx.fillStyle = "#f00";
    ctx.fillRect(x + p * 3, y + p * 3 + bounce, p, p);
    ctx.fillRect(x + p * 5, y + p * 3 + bounce, p, p);
    // 腿
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 2, y + p * 7 + bounce, p * 2, p);
    ctx.fillRect(x + p * 4, y + p * 7 + bounce, p * 2, p);
  } else if (type === "dark_bear") {
    // 暗熊：大型四足
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 0, y + p * 3 + bounce, p * 8, p * 4);
    ctx.fillRect(x + p * 0, y + p * 2 + bounce, p * 3, p * 2);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 0, y + p * 2 + bounce, p * 3, p * 2);
    // 腿
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 1, y + p * 7 + bounce, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 7 + bounce, p * 2, p);
    // 眼睛
    ctx.fillStyle = "#f00";
    ctx.fillRect(x + p * 1, y + p * 2 + bounce, p * 0.5, p * 0.5);
  } else {
    // 通用形状
    ctx.fillStyle = color;
    ctx.fillRect(x + p * 2, y + p * 3 + bounce, p * 4, p * 4);
    ctx.fillStyle = accent;
    ctx.fillRect(x + p * 3, y + p * 1 + bounce, p * 2, p * 3);
  }

  ctx.globalAlpha = 1.0;

  // 名字标签
  if (!monster.inCombat) {
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    ctx.font = "10px monospace";
    const nameWidth = ctx.measureText(config.name).width + 10;
    ctx.fillRect(x + s / 2 - nameWidth / 2, y - 14, nameWidth, 14);
    ctx.fillStyle = "#ff8888";
    ctx.textAlign = "center";
    ctx.fillText(config.name, x + s / 2, y - 4);
  }

  // 精英标记
  if (config.type === "elite") {
    ctx.fillStyle = "#ff0";
    ctx.font = "bold 10px monospace";
    ctx.textAlign = "center";
    ctx.fillText("★", x + s / 2, y - 18);
  }
}

// 绘制战斗面板中的怪物精灵（放大版）
function drawMonsterSprite(monsterId) {
  const canvas = document.getElementById("monster-sprite-canvas");
  if (!canvas) return;
  const mCtx = canvas.getContext("2d");
  mCtx.clearRect(0, 0, 96, 96);

  const config = monstersConfig[monsterId];
  if (!config) return;

  const s = 96;
  const p = s / 8;
  const color = config.sprite_color;
  const accent = config.sprite_accent;

  // 阴影
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
  } else {
    mCtx.fillStyle = color;
    mCtx.fillRect(p * 2, p * 3, p * 4, p * 4);
    mCtx.fillStyle = accent;
    mCtx.fillRect(p * 3, p * 1, p * 2, p * 3);
  }
}

// 检查玩家是否碰到怪物
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

// 获取最近的可交互怪物
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

// 发起战斗
async function initiateCombat(monsterInstanceId) {
  if (combatOpen || dialogueOpen || inventoryOpen || shopOpen || playerInfoOpen || npcInteractOpen || gameMenuOpen) return;

  await savePlayerPosition();

  try {
    const resp = await fetch("/api/combat/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        monster_instance_id: monsterInstanceId,
        map_id: currentMap.id,
      }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      showInteractMessage(data.detail || "无法开始战斗");
      return;
    }

    combatSessionId = data.session_id;
    // 将嵌套结构扁平化，与 action 响应保持一致
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
    combatOpen = true;
    combatMonsterInstanceId = monsterInstanceId;

    const monster = mapMonsters.find(m => m.instance_id === monsterInstanceId);
    if (monster) monster.inCombat = true;

    document.getElementById("combat-panel").classList.add("active");
    renderCombat();
    drawMonsterSprite(data.monster.id);
  } catch (e) {
    console.error("战斗请求失败:", e);
  }
}

// 渲染战斗界面
function renderCombat() {
  if (!combatState) return;

  // 回合信息
  document.getElementById("combat-turn-info").textContent = `第 ${combatState.turn_count || 1} 回合`;

  // 怪物信息
  document.getElementById("combat-monster-name").textContent = combatState.monster_name || combatState.monster?.name || "";
  const monsterHpPct = (combatState.monster_hp / combatState.monster_max_hp) * 100;
  document.getElementById("combat-monster-hp-bar").style.width = monsterHpPct + "%";
  document.getElementById("combat-monster-hp-text").textContent = `${combatState.monster_hp}/${combatState.monster_max_hp}`;

  // 玩家信息
  const playerHpPct = (combatState.player_hp / combatState.player_max_hp) * 100;
  document.getElementById("combat-player-hp-bar").style.width = playerHpPct + "%";
  document.getElementById("combat-player-hp-text").textContent = `${combatState.player_hp}/${combatState.player_max_hp}`;

  const playerMpPct = ((combatState.player_mp || 0) / (combatState.player_max_mp || 1)) * 100;
  document.getElementById("combat-player-mp-bar").style.width = playerMpPct + "%";
  document.getElementById("combat-player-mp-text").textContent = `${combatState.player_mp || 0}/${combatState.player_max_mp || 0}`;

  // 状态效果
  renderEffects("combat-player-effects", combatState.player_effects || []);
  renderEffects("combat-monster-effects", combatState.monster_effects || []);

  // 按钮状态
  const isPlayerTurn = combatState.phase === "player_turn";
  document.getElementById("btn-combat-attack").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-defend").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-skill").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-item").disabled = !isPlayerTurn;
  document.getElementById("btn-combat-flee").disabled = !isPlayerTurn;
}

// 渲染状态效果
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

// 追加战斗日志
function appendCombatLog(logEntries) {
  const logDiv = document.getElementById("combat-log");
  if (!logDiv) return;

  for (const entry of logEntries) {
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
    }

    div.textContent = entry.text || "";
    logDiv.appendChild(div);
  }

  logDiv.scrollTop = logDiv.scrollHeight;
}

// 执行战斗动作
async function combatAction(action, itemId) {
  if (combatAnimating || !combatOpen) return;
  if (combatState.phase !== "player_turn") return;

  combatAnimating = true;
  disableCombatButtons();

  if (combatItemSelectOpen) {
    closeCombatItemSelect();
  }

  try {
    const body = { session_id: combatSessionId, action: action };
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

    // 攻击动画
    if (action === "attack") {
      await playCombatAnimation("player");
    }

    combatState = { ...combatState, ...data };
    renderCombat();
    appendCombatLog(data.log || []);

    // 怪物攻击动画
    const hasMonsterAttack = (data.log || []).some(l =>
      l.type === "monster_attack" || l.type === "monster_special"
    );
    if (hasMonsterAttack) {
      await playCombatAnimation("monster");
    }

    // 检查战斗结束
    if (data.phase === "victory") {
      await showCombatResult(data, true);
    } else if (data.phase === "defeat") {
      await showCombatResult(data, false);
    }

    // 同步玩家信息
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

// 战斗动画
async function playCombatAnimation(who) {
  const panel = document.getElementById("combat-panel");
  if (!panel) return;

  if (who === "player") {
    const monsterArea = document.getElementById("combat-monster-area");
    monsterArea.classList.add("combat-shake");
    monsterArea.classList.add("combat-flash");
    await sleep(300);
    monsterArea.classList.remove("combat-shake");
    monsterArea.classList.remove("combat-flash");
  } else {
    const playerArea = document.getElementById("combat-player-area");
    playerArea.classList.add("combat-shake");
    panel.classList.add("combat-hit-flash");
    await sleep(300);
    playerArea.classList.remove("combat-shake");
    panel.classList.remove("combat-hit-flash");
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 显示战斗结果
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

// 结束战斗
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

  // 移除怪物
  if (combatMonsterInstanceId) {
    const monster = mapMonsters.find(m => m.instance_id === combatMonsterInstanceId);
    if (monster) {
      monster.alive = false;
      monster.inCombat = false;
    }
  }

  // 关闭战斗面板
  document.getElementById("combat-panel").classList.remove("active");
  combatOpen = false;
  combatSessionId = null;
  combatState = null;
  combatItemSelectOpen = false;
  combatMonsterInstanceId = null;

  // 清空战斗日志
  const logDiv = document.getElementById("combat-log");
  if (logDiv) logDiv.innerHTML = "";

  // 同步玩家信息
  if (typeof fetchPlayerInfo === "function") {
    await fetchPlayerInfo();
  }
  if (typeof updatePlayerHUD === "function") {
    updatePlayerHUD();
  }
}

// 物品选择
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
      div.className = "combat-skill-row";
      div.innerHTML = `
        <span class="combat-skill-name">${skill.name}${cdText}</span>
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

// 按钮控制
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

// 键盘快捷键
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
  }
});
