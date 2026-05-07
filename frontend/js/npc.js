// 多 NPC 系统

// NPC 列表，启动时从接口加载
let npcs = [];
let activeNpcId = null; // 当前正在对话的 NPC
let interactNpcId = null; // 当前交互选项对应的 NPC
let npcInteractOpen = false;

// NPC 默认位置（在地图上的瓦片坐标）
const npcPositions = {
  blacksmith: { col: 4, row: 5 },
  merchant:   { col: 18, row: 5 },
};

function initNpcs(npcList) {
  npcs = npcList.map(cfg => ({
    npc_id: cfg.npc_id,
    name: cfg.name,
    role: cfg.role,
    greeting: cfg.greeting,
    x: (npcPositions[cfg.npc_id]?.col || 4) * TILE_SIZE,
    y: (npcPositions[cfg.npc_id]?.row || 5) * TILE_SIZE,
    mood: "平静",
    affinity: 50,
    interactRange: 2,
    showPrompt: false,
  }));
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
  const bodyColor = isBlacksmith ? "#8b4513" : "#6a4a8a";   // 铁匠棕色/商人紫色
  const bodyLight = isBlacksmith ? "#a0522d" : "#8a6aaa";
  const hairColor = isBlacksmith ? "#4a3728" : "#3a2a2a";
  const skinColor = "#d4a574";

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
  if (isPlayerNearNpc(npc) && !dialogueOpen && !inventoryOpen && !shopOpen && !npcInteractOpen) {
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

// E 键交互：找最近的 NPC，弹出选项面板
document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() === "e" && !dialogueOpen && !inventoryOpen && !shopOpen && !npcInteractOpen) {
    const nearest = getNearestNpc();
    if (nearest) {
      openNpcInteract(nearest);
    }
  }
});

function openNpcInteract(npc) {
  interactNpcId = npc.npc_id;
  activeNpcId = npc.npc_id;
  npcInteractOpen = true;
  document.getElementById("npc-interact-title").textContent = npc.name;
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
