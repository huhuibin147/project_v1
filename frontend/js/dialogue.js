// 对话 UI 与 API 调用（支持多 NPC）

let dialogueOpen = false;

// 每个 NPC 独立的对话记录
const dialogueHistory = {};  // { npcId: { messages: [], loading: false } }

function getDialogueState(npcId) {
  if (!dialogueHistory[npcId]) {
    dialogueHistory[npcId] = { messages: [], loading: false };
  }
  return dialogueHistory[npcId];
}

function openDialogue(npc) {
  dialogueOpen = true;
  activeNpcId = npc.npc_id;
  const state = getDialogueState(npc.npc_id);

  document.getElementById("dialogue-panel").classList.add("active");
  document.getElementById("dialogue-title").textContent = npc.name;
  document.getElementById("dialogue-input").focus();

  // 第一次打开，显示开场白
  if (state.messages.length === 0 && npc.greeting) {
    state.messages.push({ role: "npc", text: npc.greeting });
  }

  renderDialogue(npc.npc_id);
}

function closeDialogue() {
  dialogueOpen = false;
  document.getElementById("dialogue-panel").classList.remove("active");
}

function openShopFromDialogue() {
  if (!activeNpcId) {
    console.error("openShopFromDialogue: activeNpcId is null");
    return;
  }
  console.log("openShopFromDialogue: opening shop for", activeNpcId);
  closeDialogue();
  openShop(activeNpcId);
}

function addNPCMessage(npcId, text) {
  const state = getDialogueState(npcId);
  state.messages.push({ role: "npc", text });
  renderDialogue(npcId);
}

function addPlayerMessage(npcId, text) {
  const state = getDialogueState(npcId);
  state.messages.push({ role: "player", text });
  renderDialogue(npcId);
}

function renderDialogue(npcId) {
  const container = document.getElementById("dialogue-messages");
  const state = getDialogueState(npcId);
  const npc = npcs.find(n => n.npc_id === npcId);
  container.innerHTML = "";

  const recent = state.messages.slice(-10);
  for (const msg of recent) {
    const div = document.createElement("div");
    div.className = `dialogue-msg ${msg.role}`;
    const label = msg.role === "npc" ? (npc ? npc.name : "NPC") : "你";
    const color = msg.role === "npc" ? "#f0c060" : "#60a0f0";
    div.innerHTML = `<span style="color:${color};font-weight:bold">${label}：</span>${escapeHTML(msg.text)}`;
    container.appendChild(div);
  }

  container.scrollTop = container.scrollHeight;

  // 更新状态
  if (npc) {
    document.getElementById("npc-mood").textContent = npc.mood;
    document.getElementById("npc-affinity").textContent = npc.affinity;
  }
}

function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function sendMessage() {
  if (!activeNpcId) return;
  const state = getDialogueState(activeNpcId);
  const npc = npcs.find(n => n.npc_id === activeNpcId);

  const input = document.getElementById("dialogue-input");
  const text = input.value.trim();
  if (!text || state.loading) return;

  input.value = "";
  addPlayerMessage(activeNpcId, text);

  state.loading = true;
  const loadingEl = document.getElementById("dialogue-loading");
  loadingEl.textContent = `${npc ? npc.name : "NPC"}正在思考...`;
  loadingEl.style.display = "block";

  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, npc_id: activeNpcId }),
    });
    const data = await resp.json();

    addNPCMessage(activeNpcId, data.reply);

    // 更新 NPC 状态
    if (npc) {
      npc.mood = data.mood;
      npc.affinity = data.affinity;
    }

    // 更新金币和背包
    if (data.player_gold !== undefined) {
      inventoryState.gold = data.player_gold;
      updateGoldDisplay();
    }
    if (data.player_inventory) {
      inventoryState.items = data.player_inventory;
    }

    showIntentBadge(data.intent);

    // 交易意图已不自动弹出商店按钮，玩家可通过接近NPC的交互面板选择商店

  } catch (e) {
    addNPCMessage(activeNpcId, `（${npc ? npc.name : "NPC"}挠了挠头）俺刚才走神了，你说啥来着？`);
    console.error("对话请求失败:", e);
  } finally {
    state.loading = false;
    document.getElementById("dialogue-loading").style.display = "none";
  }
}

function showIntentBadge(intent) {
  const badge = document.getElementById("intent-badge");
  const labels = {
    chat: "闲聊",
    quest: "任务",
    trade: "交易",
    unknown: "未知",
  };
  const colors = {
    chat: "#4CAF50",
    quest: "#FF9800",
    trade: "#2196F3",
    unknown: "#999",
  };
  badge.textContent = labels[intent] || "未知";
  badge.style.backgroundColor = colors[intent] || "#999";
  badge.style.display = "inline-block";
  setTimeout(() => { badge.style.display = "none"; }, 2000);
}

// 事件绑定
document.getElementById("dialogue-send").addEventListener("click", sendMessage);
document.getElementById("dialogue-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && dialogueOpen) {
    closeDialogue();
  }
});
