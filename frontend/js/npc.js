// NPC 渲染与交互

const npcState = {
  name: "...",
  greeting: "",
  x: 4 * TILE_SIZE,
  y: 4 * TILE_SIZE,
  width: TILE_SIZE,
  height: TILE_SIZE,
  mood: "平静",
  affinity: 50,
  interactRange: 2,
  showPrompt: false,
};

function isPlayerNearNPC() {
  const dx = Math.abs(player.x - npcState.x);
  const dy = Math.abs(player.y - npcState.y);
  return dx <= npcState.interactRange * TILE_SIZE &&
         dy <= npcState.interactRange * TILE_SIZE;
}

function drawNPC(ctx) {
  const x = Math.round(npcState.x);
  const y = Math.round(npcState.y);
  const s = TILE_SIZE;
  const p = s / 8;
  const time = Date.now() / 1000;
  const breathe = Math.sin(time * 2) * 1;

  // 阴影
  ctx.fillStyle = "rgba(0,0,0,0.2)";
  ctx.fillRect(x + p * 2, y + s - p * 2, p * 4, p * 1);

  // 身体（围裙）
  ctx.fillStyle = "#8b4513";
  ctx.fillRect(x + p * 2, y + p * 3 + breathe, p * 4, p * 4);
  // 围裙高光
  ctx.fillStyle = "#a0522d";
  ctx.fillRect(x + p * 3, y + p * 4 + breathe, p * 2, p * 3);

  // 头部
  ctx.fillStyle = "#d4a574";
  ctx.fillRect(x + p * 2, y + p * 1 + breathe, p * 4, p * 3);

  // 头发/胡子
  ctx.fillStyle = "#4a3728";
  ctx.fillRect(x + p * 2, y + p * 0 + breathe, p * 4, p * 2);
  // 胡子
  ctx.fillRect(x + p * 3, y + p * 3 + breathe, p * 2, p * 1);

  // 眼睛 - 根据朝向
  ctx.fillStyle = "#333";
  ctx.fillRect(x + p * 3, y + p * 2 + breathe, p, p);
  ctx.fillRect(x + p * 5, y + p * 2 + breathe, p, p);

  // 锤子（右手）
  ctx.fillStyle = "#666";
  ctx.fillRect(x + p * 6, y + p * 3 + breathe, p, p * 3);
  ctx.fillStyle = "#8b6b4a";
  ctx.fillRect(x + p * 6, y + p * 2 + breathe, p * 2, p * 2);

  // 名字标签
  ctx.fillStyle = "rgba(0,0,0,0.6)";
  const nameWidth = ctx.measureText(npcState.name).width + 10;
  ctx.fillRect(x + s / 2 - nameWidth / 2, y - 14, nameWidth, 14);
  ctx.fillStyle = "#fff";
  ctx.font = "10px monospace";
  ctx.textAlign = "center";
  ctx.fillText(npcState.name, x + s / 2, y - 4);

  // 交互提示
  if (isPlayerNearNPC() && !dialogueOpen) {
    npcState.showPrompt = true;
    const prompt = "按 E 对话";
    const pw = ctx.measureText(prompt).width + 10;
    ctx.fillStyle = "rgba(255,200,0,0.9)";
    ctx.fillRect(x + s / 2 - pw / 2, y - 28, pw, 14);
    ctx.fillStyle = "#333";
    ctx.font = "bold 10px monospace";
    ctx.fillText(prompt, x + s / 2, y - 18);
  } else {
    npcState.showPrompt = false;
  }
}

// E 键交互
document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() === "e" && isPlayerNearNPC() && !dialogueOpen) {
    openDialogue();
  }
});

// 获取 NPC 配置（启动时调用一次）
async function fetchNPCConfig() {
  try {
    const resp = await fetch("/api/npc/config");
    const data = await resp.json();
    npcState.name = data.name;
    npcState.greeting = data.greeting;
    // 更新对话面板标题
    document.getElementById("dialogue-title").textContent = data.name;
  } catch (e) {
    console.error("获取 NPC 配置失败:", e);
  }
}

// 获取 NPC 状态
async function fetchNPCStatus() {
  try {
    const resp = await fetch("/api/npc/status");
    const data = await resp.json();
    npcState.mood = data.mood;
    npcState.affinity = data.affinity;
  } catch (e) {
    console.error("获取 NPC 状态失败:", e);
  }
}
