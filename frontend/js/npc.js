// 多 NPC 系统

// NPC 列表，启动时从接口加载
let npcs = [];
let activeNpcId = null; // 当前正在对话的 NPC
let interactNpcId = null; // 当前交互选项对应的 NPC
let npcInteractOpen = false;
let healPanelOpen = false;
let skillLearnPanelOpen = false;

// 注册面板
PanelManager.register('npcInteract',
  () => { npcInteractOpen = true; document.getElementById("npc-interact-panel").classList.add("active"); },
  () => { npcInteractOpen = false; interactNpcId = null; document.getElementById("npc-interact-panel").classList.remove("active"); }
);
PanelManager.register('heal',
  () => { healPanelOpen = true; document.getElementById("heal-panel").classList.add("active"); },
  () => { healPanelOpen = false; document.getElementById("heal-panel").classList.remove("active"); document.getElementById("heal-message").style.display = "none"; }
);
PanelManager.register('skillLearn',
  () => { skillLearnPanelOpen = true; document.getElementById("skill-learn-panel").classList.add("active"); },
  () => { skillLearnPanelOpen = false; document.getElementById("skill-learn-panel").classList.remove("active"); document.getElementById("skill-learn-message").style.display = "none"; }
);

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
        appearance: cfg.appearance || null,
        services: cfg.services || {},
        interaction_buttons: cfg.interaction_buttons || ["talk", "quest", "shop"],
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

const DEFAULT_NPC_APPEARANCE = {
  body: { color: "#6a4a8a", light: "#8a6aaa" },
  head: { color: "#d4a574" },
  hair: { color: "#3a2a2a", style: "default" },
  accessories: []
};

function drawNPCAccessory(ctx, acc, x, y, p, breathe) {
  const type = acc.type;
  if (type === "beard") {
    ctx.fillStyle = acc.color;
    ctx.fillRect(x + p * 3, y + p * 3 + breathe, p * 2, p * 1);
  } else if (type === "hood") {
    ctx.fillStyle = acc.color;
    ctx.fillRect(x + p * 1, y + p * 0 + breathe, p * 6, p * 2);
    if (acc.accent) {
      ctx.fillStyle = acc.accent;
      ctx.fillRect(x + p * 3, y + p * 4 + breathe, p * 2, p * 1);
      ctx.fillRect(x + p * 3, y + p * 5 + breathe, p * 2, p * 1);
    }
  } else if (type === "glasses") {
    ctx.fillStyle = acc.frame_color || "#333";
    ctx.fillRect(x + p * 2, y + p * 2 + breathe, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 2 + breathe, p * 2, p);
    ctx.fillStyle = "#aaa";
    ctx.fillRect(x + p * 4, y + p * 2 + breathe, p, p);
  } else if (type === "tool") {
    const pos = acc.position || "right";
    const toolType = acc.tool_type || "staff";
    if (pos === "right") {
      if (toolType === "hammer") {
        ctx.fillStyle = acc.color;
        ctx.fillRect(x + p * 6, y + p * 3 + breathe, p, p * 3);
        ctx.fillStyle = acc.accent;
        ctx.fillRect(x + p * 6, y + p * 2 + breathe, p * 2, p * 2);
      } else if (toolType === "staff") {
        ctx.fillStyle = acc.color;
        ctx.fillRect(x + p * 7, y + p * 2 + breathe, p, p * 5);
        ctx.fillStyle = acc.accent;
        ctx.fillRect(x + p * 6, y + p * 1 + breathe, p * 3, p);
      } else if (toolType === "book") {
        ctx.fillStyle = acc.color;
        ctx.fillRect(x + p * 7, y + p * 3 + breathe, p * 2, p * 3);
        ctx.fillStyle = acc.accent;
        ctx.fillRect(x + p * 7, y + p * 4 + breathe, p * 2, p);
      }
    }
  } else if (type === "hat") {
    ctx.fillStyle = acc.color;
    ctx.fillRect(x + p * 2, y + p * 0 + breathe, p * 4, p * 1);
  } else if (type === "apron") {
    ctx.fillStyle = acc.color;
    ctx.fillRect(x + p * 3, y + p * 5 + breathe, p * 2, p * 2);
  } else if (type === "cape") {
    ctx.fillStyle = acc.color;
    ctx.fillRect(x + p * 1, y + p * 5 + breathe, p * 6, p * 3);
  } else if (type === "scarf") {
    ctx.fillStyle = acc.color;
    ctx.fillRect(x + p * 2, y + p * 3 + breathe, p * 4, p * 1);
  }
}

function drawNPC(ctx, npc) {
  const x = Math.round(npc.x);
  const y = Math.round(npc.y);
  const s = TILE_SIZE;
  const p = s / 8;
  const time = Date.now() / 1000;
  const breathe = Math.sin(time * 2) * 1;

  const appearance = npc.appearance || DEFAULT_NPC_APPEARANCE;
  const bodyColor = appearance.body.color;
  const bodyLight = appearance.body.light;
  const skinColor = appearance.head.color;
  const hairColor = appearance.hair.color;

  ctx.fillStyle = "rgba(0,0,0,0.2)";
  ctx.fillRect(x + p * 2, y + s - p * 2, p * 4, p * 1);

  ctx.fillStyle = bodyColor;
  ctx.fillRect(x + p * 2, y + p * 3 + breathe, p * 4, p * 4);
  ctx.fillStyle = bodyLight;
  ctx.fillRect(x + p * 3, y + p * 4 + breathe, p * 2, p * 3);

  ctx.fillStyle = skinColor;
  ctx.fillRect(x + p * 2, y + p * 1 + breathe, p * 4, p * 3);

  ctx.fillStyle = hairColor;
  ctx.fillRect(x + p * 2, y + p * 0 + breathe, p * 4, p * 2);

  const accessories = appearance.accessories || [];
  for (const acc of accessories) {
    drawNPCAccessory(ctx, acc, x, y, p, breathe);
  }

  ctx.fillStyle = "#333";
  ctx.fillRect(x + p * 3, y + p * 2 + breathe, p, p);
  ctx.fillRect(x + p * 5, y + p * 2 + breathe, p, p);

  ctx.fillStyle = "rgba(0,0,0,0.6)";
  ctx.font = "10px monospace";
  const nameWidth = ctx.measureText(npc.name).width + 10;
  ctx.fillRect(x + s / 2 - nameWidth / 2, y - 14, nameWidth, 14);
  ctx.fillStyle = "#fff";
  ctx.textAlign = "center";
  ctx.fillText(npc.name, x + s / 2, y - 4);

  if (isPlayerNearNpc(npc) && !PanelManager.isAnyOpen() && !GameManager.isMenuOpen() && !PanelManager.isOpen('combat')) {
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



const INTERACTION_BUTTON_MAP = {
  talk: { label: "对话", handler: "interactTalk" },
  quest: { label: "任务", handler: "interactQuest" },
  shop: { label: "商店", handler: "interactShop" },
  forge: { label: "锻造", handler: "interactForge" },
  heal: { label: "治疗服务", handler: "interactHeal" },
  learn_skill: { label: "学习技能", handler: "interactLearnSkill" },
  rest: { label: "住宿休息", handler: "interactRest" },
  rumor: { label: "打听消息", handler: "interactRumor" },
  cave_guide: { label: "洞穴向导", handler: "interactCaveGuide" },
};

function openNpcInteract(npc) {
  interactNpcId = npc.npc_id;
  activeNpcId = npc.npc_id;
  document.getElementById("npc-interact-title").textContent = npc.name;
  const actionsDiv = document.getElementById("npc-interact-actions");
  const buttons = npc.interaction_buttons || ["talk", "quest", "shop"];
  let html = "";
  buttons.forEach((btnKey, idx) => {
    const btnDef = INTERACTION_BUTTON_MAP[btnKey];
    if (btnDef) {
      html += `<button class="btn-interact" onclick="${btnDef.handler}()">${btnDef.label} (${idx + 1})</button>`;
    }
  });
  actionsDiv.innerHTML = html;
  PanelManager.open('npcInteract');
}

function closeNpcInteract() {
  PanelManager.close('npcInteract');
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

function interactForge() {
  if (!interactNpcId) return;
  closeNpcInteract();
  openForgePanel(interactNpcId);
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
  document.getElementById("heal-title").textContent = "治疗服务";
  document.getElementById("player-gold-heal").textContent = inventoryState.gold || 0;
  renderHealServices(npcId);
  PanelManager.open('heal');
}

function closeHealPanel() {
  PanelManager.close('heal');
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
  document.getElementById("skill-learn-title").textContent = "技能学习";
  document.getElementById("player-gold-skill").textContent = inventoryState.gold || 0;
  fetchAvailableSkills(npcId);
  PanelManager.open('skillLearn');
}

function closeSkillLearnPanel() {
  PanelManager.close('skillLearn');
}

function interactRest() {
  if (!interactNpcId) return;
  const npcId = interactNpcId;
  closeNpcInteract();
  requestNpcService(npcId, "rest");
}

function interactRumor() {
  if (!interactNpcId) return;
  const npcId = interactNpcId;
  closeNpcInteract();
  requestNpcService(npcId, "rumor");
}

function interactCaveGuide() {
  if (!interactNpcId) return;
  const npcId = interactNpcId;
  closeNpcInteract();
  requestNpcService(npcId, "cave_guide");
}

async function requestNpcService(npcId, serviceType) {
  try {
    const resp = await fetch("/api/npc/service/generic", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ npc_id: npcId, service_type: serviceType }),
    });
    const data = await resp.json();
    if (data.success && data.dialogue) {
      activeNpcId = npcId;
      openDialogueWithMessage(npcId, data.dialogue);
    } else {
      const npc = npcs.find(n => n.npc_id === npcId);
      if (npc) {
        activeNpcId = npcId;
        openDialogue(npc);
      }
    }
  } catch (e) {
    console.error("requestNpcService error:", e);
    const npc = npcs.find(n => n.npc_id === npcId);
    if (npc) {
      activeNpcId = npcId;
      openDialogue(npc);
    }
  }
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
        const mapObj = mapObjects.find(o => o.id === obj.id);
        if (mapObj) mapObj.state = { opened: true };
      }
      // 采集点处理
      if (data.type === "gather") {
        obj.state = { lastGathered: Date.now() };
        const mapObj = mapObjects.find(o => o.id === obj.id);
        if (mapObj) mapObj.state = { lastGathered: Date.now() };
      }
      // 显示交互结果
      if (data.message) {
        showInteractMessage(data.message);
      }
      // 如果获得物品，刷新背包
      if (data.items) {
        fetchInventory();
      }
    } else {
      // 交互失败（如冷却中）
      if (data.message) {
        showInteractMessage(data.message);
      }
    }
  } catch (e) {
    console.error("物件交互失败:", e);
    showInteractMessage("交互失败，请稍后再试");
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
