// 多 NPC 系统

// NPC 列表，启动时从接口加载
let npcs = [];
let activeNpcId = null; // 当前正在对话的 NPC
let interactNpcId = null; // 当前交互选项对应的 NPC
let npcInteractOpen = false;
let healPanelOpen = false;
let skillLearnPanelOpen = false;

function initNpcs(npcList) {
  // 从当前地图配置获取 NPC 位置
  const currentMapId = currentMap?.id || "";
  const mapNpcs = currentMap?.npcs || [];
  const npcPositionMap = {};
  for (const mn of mapNpcs) {
    npcPositionMap[mn.npc_id] = { x: mn.x, y: mn.y };
  }

  // 只渲染属于当前地图的 NPC
  npcs = npcList
    .filter(cfg => cfg.map_id === currentMapId)
    .map(cfg => {
      const pos = npcPositionMap[cfg.npc_id] || { x: 4, y: 5 };
      return {
        npc_id: cfg.npc_id,
        name: cfg.name,
        role: cfg.role,
        greeting: cfg.greeting,
        x: pos.x * TILE_SIZE,
        y: pos.y * TILE_SIZE,
        mood: "平静",
        affinity: 50,
        interactRange: 2,
        showPrompt: false,
      };
    });
}

function isPlayerNearNpc(npc) {
  const dx = Math.abs(player.x - npc.x);
  const dy = Math.abs(player.y - npc.y);
  return dx <= npc.interactRange * TILE_SIZE &&
         dy <= npc.interactRange * TILE_SIZE;
}

function getNearestNpc() {
  let nearest = null;
  let minDist = Infinity;
  for (const npc of npcs) {
    const dx = player.x - npc.x;
    const dy = player.y - npc.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < minDist && dist <= npc.interactRange * TILE_SIZE * 1.5) {
      minDist = dist;
      nearest = npc;
    }
  }
  return nearest;
}

function drawNPC(ctx, npc) {
  const x = Math.round(npc.x);
  const y = Math.round(npc.y);
  const s = TILE_SIZE;
  const p = s / 8;
  const time = Date.now() / 1000;
  const breathe = Math.sin(time * 2) * 1;

  // 根据 NPC 类型选择颜色
  const isBlacksmith = npc.npc_id === "blacksmith";
  const isPriest = npc.npc_id === "priest";
  const isSkillMaster = npc.npc_id === "skill_master";
  let bodyColor, bodyLight, hairColor, skinColor;
  if (isBlacksmith) {
    bodyColor = "#8b4513"; bodyLight = "#a0522d"; hairColor = "#4a3728"; skinColor = "#d4a574";
  } else if (isPriest) {
    bodyColor = "#f0e6d2"; bodyLight = "#fff8ee"; hairColor = "#e8c880"; skinColor = "#f5d5b8";
  } else if (isSkillMaster) {
    bodyColor = "#2e4053"; bodyLight = "#3d5a80"; hairColor = "#c0c0c0"; skinColor = "#e0c8a8";
  } else {
    bodyColor = "#6a4a8a"; bodyLight = "#8a6aaa"; hairColor = "#3a2a2a"; skinColor = "#d4a574";
  }

  // 阴影
  ctx.fillStyle = "rgba(0,0,0,0.2)";
  ctx.fillRect(x + p * 2, y + s - p * 2, p * 4, p * 1);

  // 身体
  ctx.fillStyle = bodyColor;
  ctx.fillRect(x + p * 2, y + p * 3 + breathe, p * 4, p * 4);
  ctx.fillStyle = bodyLight;
  ctx.fillRect(x + p * 3, y + p * 4 + breathe, p * 2, p * 3);

  // 头部
  ctx.fillStyle = skinColor;
  ctx.fillRect(x + p * 2, y + p * 1 + breathe, p * 4, p * 3);

  // 头发
  ctx.fillStyle = hairColor;
  ctx.fillRect(x + p * 2, y + p * 0 + breathe, p * 4, p * 2);

  if (isBlacksmith) {
    // 铁匠：胡子
    ctx.fillRect(x + p * 3, y + p * 3 + breathe, p * 2, p * 1);
    // 锤子
    ctx.fillStyle = "#666";
    ctx.fillRect(x + p * 6, y + p * 3 + breathe, p, p * 3);
    ctx.fillStyle = "#8b6b4a";
    ctx.fillRect(x + p * 6, y + p * 2 + breathe, p * 2, p * 2);
  } else if (isPriest) {
    // 祭司：白色头巾/兜帽
    ctx.fillStyle = "#fff";
    ctx.fillRect(x + p * 1, y + p * 0 + breathe, p * 6, p * 2);
    // 金色十字架装饰
    ctx.fillStyle = "#ffd700";
    ctx.fillRect(x + p * 3, y + p * 4 + breathe, p * 2, p * 1);
    ctx.fillRect(x + p * 3, y + p * 5 + breathe, p * 2, p * 1);
    // 法杖
    ctx.fillStyle = "#8b7355";
    ctx.fillRect(x + p * 7, y + p * 2 + breathe, p, p * 5);
    ctx.fillStyle = "#ffd700";
    ctx.fillRect(x + p * 6, y + p * 1 + breathe, p * 3, p);
  } else if (isSkillMaster) {
    // 导师：眼镜
    ctx.fillStyle = "#333";
    ctx.fillRect(x + p * 2, y + p * 2 + breathe, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 2 + breathe, p * 2, p);
    ctx.fillStyle = "#aaa";
    ctx.fillRect(x + p * 4, y + p * 2 + breathe, p, p);
    // 长袍
    ctx.fillStyle = "#1a2a3a";
    ctx.fillRect(x + p * 1, y + p * 5 + breathe, p * 6, p * 3);
    // 书本
    ctx.fillStyle = "#8b4513";
    ctx.fillRect(x + p * 7, y + p * 3 + breathe, p * 2, p * 3);
    ctx.fillStyle = "#f5f5dc";
    ctx.fillRect(x + p * 7, y + p * 4 + breathe, p * 2, p);
  } else {
    // 商人：围裙
    ctx.fillStyle = "#e8d8b0";
    ctx.fillRect(x + p * 3, y + p * 5 + breathe, p * 2, p * 2);
    // 头巾
    ctx.fillStyle = "#d4a060";
    ctx.fillRect(x + p * 2, y + p * 0 + breathe, p * 4, p * 1);
  }

  // 眼睛
  ctx.fillStyle = "#333";
  ctx.fillRect(x + p * 3, y + p * 2 + breathe, p, p);
  ctx.fillRect(x + p * 5, y + p * 2 + breathe, p, p);

  // 名字标签
  ctx.fillStyle = "rgba(0,0,0,0.6)";
  ctx.font = "10px monospace";
  const nameWidth = ctx.measureText(npc.name).width + 10;
  ctx.fillRect(x + s / 2 - nameWidth / 2, y - 14, nameWidth, 14);
  ctx.fillStyle = "#fff";
  ctx.textAlign = "center";
  ctx.fillText(npc.name, x + s / 2, y - 4);

  // 交互提示
  if (isPlayerNearNpc(npc) && !dialogueOpen && !inventoryOpen && !shopOpen && !npcInteractOpen && !gameMenuOpen && !combatOpen) {
    npc.showPrompt = true;
    const prompt = "按 E 交互";
    const pw = ctx.measureText(prompt).width + 10;
    ctx.fillStyle = "rgba(255,200,0,0.9)";
    ctx.fillRect(x + s / 2 - pw / 2, y - 28, pw, 14);
    ctx.fillStyle = "#333";
    ctx.font = "bold 10px monospace";
    ctx.fillText(prompt, x + s / 2, y - 18);
  } else {
    npc.showPrompt = false;
  }
}

function drawAllNpcs(ctx) {
  for (const npc of npcs) {
    drawNPC(ctx, npc);
  }
}

// E 键交互：找最近的 NPC 或物件或怪物
document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() === "e" && !dialogueOpen && !inventoryOpen && !shopOpen && !npcInteractOpen && !gameMenuOpen && !combatOpen) {
    // 优先检查怪物
    const nearMonster = typeof getNearestMonster === "function" ? getNearestMonster() : null;
    if (nearMonster) {
      initiateCombat(nearMonster.instance_id);
      return;
    }
    // 其次检查 NPC
    const nearest = getNearestNpc();
    if (nearest) {
      openNpcInteract(nearest);
      return;
    }
    // 最后检查地图物件
    const nearObj = getNearbyInteractableObject();
    if (nearObj) {
      interactWithObject(nearObj);
    }
  }
  
  // NPC交互选项快捷键：1-对话，2-任务，3-商店，4-治疗/技能
  if (npcInteractOpen) {
    if (e.key === "1") {
      interactTalk();
    } else if (e.key === "2") {
      interactQuest();
    } else if (e.key === "3") {
      interactShop();
    } else if (e.key === "4") {
      if (interactNpcId === "priest") {
        interactHeal();
      } else if (interactNpcId === "skill_master") {
        interactLearnSkill();
      }
    }
  }
});

function openNpcInteract(npc) {
  interactNpcId = npc.npc_id;
  activeNpcId = npc.npc_id;
  npcInteractOpen = true;
  document.getElementById("npc-interact-title").textContent = npc.name;
  // 根据NPC类型显示不同的交互按钮
  const actionsDiv = document.getElementById("npc-interact-actions");
  let html = '<button class="btn-interact" onclick="interactTalk()">对话 (1)</button>';
  html += '<button class="btn-interact" onclick="interactQuest()">任务 (2)</button>';
  if (npc.npc_id === "priest") {
    html += '<button class="btn-interact" onclick="interactShop()">商店 (3)</button>';
    html += '<button class="btn-interact" onclick="interactHeal()">治疗服务 (4)</button>';
  } else if (npc.npc_id === "skill_master") {
    html += '<button class="btn-interact" onclick="interactShop()">商店 (3)</button>';
    html += '<button class="btn-interact" onclick="interactLearnSkill()">学习技能 (4)</button>';
  } else {
    html += '<button class="btn-interact" onclick="interactShop()">商店 (3)</button>';
  }
  actionsDiv.innerHTML = html;
  document.getElementById("npc-interact-panel").classList.add("active");
}

function closeNpcInteract() {
  npcInteractOpen = false;
  interactNpcId = null;
  document.getElementById("npc-interact-panel").classList.remove("active");
}

function interactTalk() {
  if (!interactNpcId) return;
  const npc = npcs.find(n => n.npc_id === interactNpcId);
  if (npc) {
    closeNpcInteract();
    activeNpcId = npc.npc_id;
    openDialogue(npc);
  }
}

function interactShop() {
  if (!interactNpcId) return;
  closeNpcInteract();
  openShop(interactNpcId);
}

function interactQuest() {
  if (!interactNpcId) return;
  const npcId = interactNpcId;
  closeNpcInteract();
  openQuestPanel(npcId);
}

// ===== 治疗服务 =====

function interactHeal() {
  if (!interactNpcId) return;
  const npcId = interactNpcId;
  closeNpcInteract();
  openHealPanel(npcId);
}

function openHealPanel(npcId) {
  healPanelOpen = true;
  document.getElementById("heal-panel").classList.add("active");
  document.getElementById("heal-title").textContent = "治疗服务";
  document.getElementById("player-gold-heal").textContent = inventoryState.gold || 0;
  renderHealServices(npcId);
}

function closeHealPanel() {
  healPanelOpen = false;
  document.getElementById("heal-panel").classList.remove("active");
  document.getElementById("heal-message").style.display = "none";
}

function renderHealServices(npcId) {
  const servicesDiv = document.getElementById("heal-services");
  // 服务配置（与后端保持一致）
  const services = [
    { id: "heal", name: "恢复生命", desc: "恢复全部生命值", cost: 20 },
    { id: "restore_mp", name: "恢复魔法", desc: "恢复全部魔法值", cost: 15 },
    { id: "cure", name: "解除异常", desc: "解除所有负面状态效果", cost: 30 },
  ];
  let html = "";
  for (const svc of services) {
    html += `<div class="heal-service-item">
      <div class="heal-service-info">
        <div class="heal-service-name">${svc.name}</div>
        <div class="heal-service-desc">${svc.desc}</div>
        <div class="heal-service-cost">${svc.cost} 金币</div>
      </div>
      <button class="btn-buy" onclick="requestHealService('${npcId}', '${svc.id}')">使用</button>
    </div>`;
  }
  servicesDiv.innerHTML = html;
}

async function requestHealService(npcId, serviceType) {
  if (!npcId) {
    console.error("requestHealService called with invalid npcId:", npcId);
    const msgEl = document.getElementById("heal-message");
    if (msgEl) {
      msgEl.textContent = "错误：NPC信息无效，请重新打开治疗服务";
      msgEl.style.display = "block";
      msgEl.className = "trade-message error";
    }
    return;
  }
  try {
    const resp = await fetch("/api/npc/service/heal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ npc_id: npcId, service_type: serviceType }),
    });
    const data = await resp.json();
    const msgEl = document.getElementById("heal-message");
    msgEl.textContent = data.message;
    msgEl.style.display = "block";
    msgEl.className = data.success ? "trade-message success" : "trade-message error";
    if (data.success) {
      // 更新玩家信息
      if (data.player_info) {
        if (typeof updatePlayerHUD === "function") {
          if (typeof playerInfo !== "undefined") {
            Object.assign(playerInfo, data.player_info);
          }
          updatePlayerHUD();
        }
        if (data.player_info.gold !== undefined) {
          inventoryState.gold = data.player_info.gold;
          if (typeof updateGoldDisplay === "function") updateGoldDisplay();
        }
      }
      document.getElementById("player-gold-heal").textContent = inventoryState.gold || 0;
    }
  } catch (e) {
    console.error("治疗服务请求失败:", e);
  }
}

// ===== 技能学习 =====

function interactLearnSkill() {
  if (!interactNpcId) return;
  const npcId = interactNpcId;
  closeNpcInteract();
  openSkillLearnPanel(npcId);
}

function openSkillLearnPanel(npcId) {
  skillLearnPanelOpen = true;
  document.getElementById("skill-learn-panel").classList.add("active");
  document.getElementById("skill-learn-title").textContent = "技能学习";
  document.getElementById("player-gold-skill").textContent = inventoryState.gold || 0;
  fetchAvailableSkills(npcId);
}

function closeSkillLearnPanel() {
  skillLearnPanelOpen = false;
  document.getElementById("skill-learn-panel").classList.remove("active");
  document.getElementById("skill-learn-message").style.display = "none";
}

async function fetchAvailableSkills(npcId) {
  try {
    const resp = await fetch(`/api/npc/service/skills?npc_id=${npcId}`);
    const data = await resp.json();
    if (data.success) {
      renderSkillList(data.skills);
    } else {
      document.getElementById("skill-learn-list").innerHTML = `<div class="skill-learn-empty">${data.message}</div>`;
    }
  } catch (e) {
    console.error("获取技能列表失败:", e);
  }
}

function renderSkillList(skills) {
  const listDiv = document.getElementById("skill-learn-list");
  if (!skills || skills.length === 0) {
    listDiv.innerHTML = '<div class="skill-learn-empty">暂无可学习的技能</div>';
    return;
  }
  let html = "";
  for (const skill of skills) {
    const canLearn = skill.can_learn;
    const disabled = canLearn ? "" : "disabled";
    const btnText = canLearn ? "学习" : skill.reason;
    const classReq = skill.class_requirement?.length > 0
      ? `职业: ${skill.class_requirement.join(", ")}`
      : "全职业可用";
    html += `<div class="skill-learn-item ${canLearn ? "" : "disabled"}">
      <div class="skill-learn-info">
        <div class="skill-learn-name">${skill.name}</div>
        <div class="skill-learn-desc">${skill.description}</div>
        <div class="skill-learn-meta">
          <span>MP: ${skill.mp_cost}</span>
          <span>冷却: ${skill.cooldown}回合</span>
          <span>等级要求: Lv.${skill.level_requirement}</span>
          <span>${classReq}</span>
        </div>
        <div class="skill-learn-cost">学费: ${skill.cost} 金币</div>
      </div>
      <button class="btn-buy" ${disabled} onclick="requestLearnSkill('${skill.skill_id}', ${skill.cost})">${btnText}</button>
    </div>`;
  }
  listDiv.innerHTML = html;
}

async function requestLearnSkill(skillId, cost) {
  const npcId = interactNpcId || "skill_master";
  if (!npcId) {
    console.error("requestLearnSkill called with invalid npcId:", npcId);
    const msgEl = document.getElementById("skill-learn-message");
    if (msgEl) {
      msgEl.textContent = "错误：NPC信息无效，请重新打开技能学习";
      msgEl.style.display = "block";
      msgEl.className = "trade-message error";
    }
    return;
  }
  try {
    const resp = await fetch("/api/npc/service/learn_skill", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ npc_id: npcId, skill_id: skillId }),
    });
    const data = await resp.json();
    const msgEl = document.getElementById("skill-learn-message");
    msgEl.textContent = data.message;
    msgEl.style.display = "block";
    msgEl.className = data.success ? "trade-message success" : "trade-message error";
    if (data.success) {
      if (data.player_info) {
        if (typeof updatePlayerHUD === "function") {
          if (typeof playerInfo !== "undefined") {
            Object.assign(playerInfo, data.player_info);
          }
          updatePlayerHUD();
        }
        if (data.player_info.gold !== undefined) {
          inventoryState.gold = data.player_info.gold;
          if (typeof updateGoldDisplay === "function") updateGoldDisplay();
        }
      }
      if (data.skills) {
        player.skills = data.skills;
      }
      document.getElementById("player-gold-skill").textContent = inventoryState.gold || 0;
      // 刷新技能列表
      fetchAvailableSkills(npcId);
    }
  } catch (e) {
    console.error("学习技能请求失败:", e);
  }
}

// 启动时获取 NPC 列表
async function fetchAllNpcs() {
  try {
    const resp = await fetch("/api/npcs");
    const data = await resp.json();
    initNpcs(data);
    return data;
  } catch (e) {
    console.error("获取 NPC 列表失败:", e);
    return [];
  }
}

// 获取指定 NPC 的状态
async function fetchNPCStatus(npcId) {
  try {
    const resp = await fetch(`/api/npc/status?npc_id=${npcId}`);
    const data = await resp.json();
    const npc = npcs.find(n => n.npc_id === npcId);
    if (npc) {
      npc.mood = data.mood;
      npc.affinity = data.affinity;
    }
    return data;
  } catch (e) {
    console.error("获取 NPC 状态失败:", e);
  }
}

// 与地图物件交互
async function interactWithObject(obj) {
  if (!currentMap) return;

  try {
    const resp = await fetch("/api/map/object/interact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        map_id: currentMap.id,
        object_id: obj.id,
        action: "interact",
      }),
    });
    const data = await resp.json();
    if (resp.ok && data.success) {
      // 更新物件状态
      if (data.type === "chest") {
        obj.state = { opened: true };
        // 更新地图物件列表中的状态
        const mapObj = mapObjects.find(o => o.id === obj.id);
        if (mapObj) mapObj.state = { opened: true };
      }
      // 显示交互结果
      if (data.message) {
        showInteractMessage(data.message);
      }
      // 如果获得物品，刷新背包
      if (data.items) {
        fetchInventory();
      }
    }
  } catch (e) {
    console.error("物件交互失败:", e);
  }
}

// 显示交互消息
function showInteractMessage(message) {
  // 创建临时消息元素
  const msgEl = document.createElement("div");
  msgEl.className = "interact-message";
  msgEl.textContent = message;
  document.getElementById("game-container").appendChild(msgEl);

  // 2 秒后移除
  setTimeout(() => {
    msgEl.remove();
  }, 2000);
}
