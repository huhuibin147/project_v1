// 对话 UI 与 API 调用（支持多 NPC）

let dialogueOpen = false;
let typewriterTimer = null;
let typewriterNpcId = null;
let dialogueShowAll = false;

const dialogueHistory = {};

function getDialogueState(npcId) {
  if (!dialogueHistory[npcId]) {
    dialogueHistory[npcId] = { messages: [], loading: false };
  }
  return dialogueHistory[npcId];
}

async function openDialogue(npc) {
  if (combatOpen) return;
  dialogueOpen = true;
  dialogueShowAll = false;
  activeNpcId = npc.npc_id;
  const state = getDialogueState(npc.npc_id);

  document.getElementById("dialogue-panel").classList.add("active");
  document.getElementById("dialogue-title").textContent = npc.name;
  
  // 先清空输入框
  document.getElementById("dialogue-input").value = "";
  document.getElementById("dialogue-input").focus();

  // 如果前端没有对话记录，从后端加载
  if (state.messages.length === 0) {
    try {
      const resp = await fetch(`/api/npc/history?npc_id=${npc.npc_id}`);
      if (resp.ok) {
        const data = await resp.json();
        if (data.history && data.history.length > 0) {
          for (const h of data.history) {
            state.messages.push({
              role: h.role === "player" ? "player" : "npc",
              text: h.content,
            });
          }
        }
      }
    } catch (e) {
      console.error("加载对话历史失败:", e);
    }

    // 如果仍然没有记录，显示开场白
    if (state.messages.length === 0 && npc.greeting) {
      state.messages.push({ role: "npc", text: npc.greeting });
    }
  }

  // 同步 NPC 状态
  try {
    const statusResp = await fetch(`/api/npc/status?npc_id=${npc.npc_id}`);
    if (statusResp.ok) {
      const statusData = await statusResp.json();
      npc.mood = statusData.mood;
      npc.affinity = statusData.affinity;
    }
  } catch (e) {
    console.error("获取NPC状态失败:", e);
  }

  renderDialogue(npc.npc_id);
  
  setTimeout(() => {
    document.getElementById("dialogue-input").value = "";
  }, 0);
}

function openDialogueWithMessage(npcId, message) {
  const npc = npcs.find(n => n.npc_id === npcId);
  if (!npc) return;
  dialogueOpen = true;
  dialogueShowAll = false;
  activeNpcId = npcId;
  const state = getDialogueState(npcId);
  state.messages.push({ role: "npc", text: message });
  document.getElementById("dialogue-panel").classList.add("active");
  document.getElementById("dialogue-title").textContent = npc.name;
  document.getElementById("dialogue-input").value = "";
  document.getElementById("dialogue-input").focus();
  renderDialogue(npcId);
  setTimeout(() => {
    document.getElementById("dialogue-input").value = "";
  }, 0);
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
  startTypewriter(npcId, text);
}

function addPlayerMessage(npcId, text) {
  const state = getDialogueState(npcId);
  state.messages.push({ role: "player", text });
  renderDialogue(npcId);
}

function startTypewriter(npcId, fullText) {
  if (typewriterTimer) {
    clearInterval(typewriterTimer);
    finishTypewriter();
  }
  typewriterNpcId = npcId;
  const container = document.getElementById("dialogue-messages");
  const lastMsg = container.lastElementChild;
  if (!lastMsg || !lastMsg.classList.contains("npc")) {
    renderDialogue(npcId);
    return;
  }

  const textSpan = lastMsg.querySelector(".dialogue-text");
  if (!textSpan) {
    renderDialogue(npcId);
    return;
  }

  textSpan.textContent = "";
  lastMsg.classList.add("typewriter-active");
  let charIndex = 0;

  typewriterTimer = setInterval(() => {
    if (charIndex < fullText.length) {
      textSpan.textContent += fullText[charIndex];
      charIndex++;
      container.scrollTop = container.scrollHeight;
    } else {
      clearInterval(typewriterTimer);
      typewriterTimer = null;
      lastMsg.classList.remove("typewriter-active");
      lastMsg.classList.add("typewriter-done");
    }
  }, 30);
}

function finishTypewriter() {
  if (typewriterTimer) {
    clearInterval(typewriterTimer);
    typewriterTimer = null;
  }
  const container = document.getElementById("dialogue-messages");
  const activeMsg = container.querySelector(".typewriter-active");
  if (activeMsg) {
    const state = getDialogueState(typewriterNpcId);
    const lastMsg = state.messages[state.messages.length - 1];
    const textSpan = activeMsg.querySelector(".dialogue-text");
    if (textSpan && lastMsg) {
      textSpan.textContent = lastMsg.text;
    }
    activeMsg.classList.remove("typewriter-active");
    activeMsg.classList.add("typewriter-done");
  }
  typewriterNpcId = null;
}

function renderDialogue(npcId) {
  const container = document.getElementById("dialogue-messages");
  const state = getDialogueState(npcId);
  const npc = npcs.find(n => n.npc_id === npcId);
  container.innerHTML = "";

  const maxRecent = 10;
  const hasMore = state.messages.length > maxRecent;
  const recent = dialogueShowAll ? state.messages : state.messages.slice(-maxRecent);

  if (hasMore && !dialogueShowAll) {
    const moreDiv = document.createElement("div");
    moreDiv.className = "dialogue-history-toggle";
    moreDiv.innerHTML = `<button class="btn-history-toggle" onclick="toggleDialogueHistory()">查看更早的 ${state.messages.length - maxRecent} 条消息</button>`;
    container.appendChild(moreDiv);
  } else if (hasMore && dialogueShowAll) {
    const moreDiv = document.createElement("div");
    moreDiv.className = "dialogue-history-toggle";
    moreDiv.innerHTML = `<button class="btn-history-toggle" onclick="toggleDialogueHistory()">收起历史消息</button>`;
    container.appendChild(moreDiv);
  }

  for (const msg of recent) {
    const div = document.createElement("div");
    div.className = `dialogue-msg ${msg.role}`;
    const label = msg.role === "npc" ? (npc ? npc.name : "NPC") : "你";
    const color = msg.role === "npc" ? "#f0c060" : "#60a0f0";
    div.innerHTML = `<span class="dialogue-label" style="color:${color}">${label}：</span><span class="dialogue-text">${escapeHTML(msg.text)}</span>`;
    container.appendChild(div);
  }

  container.scrollTop = container.scrollHeight;

  if (npc) {
    document.getElementById("npc-mood").textContent = npc.mood;
    document.getElementById("npc-affinity").textContent = npc.affinity;
  }
}

function toggleDialogueHistory() {
  dialogueShowAll = !dialogueShowAll;
  if (activeNpcId) {
    renderDialogue(activeNpcId);
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
  const sendBtn = document.getElementById("dialogue-send");
  const text = input.value.trim();
  if (!text || state.loading) return;

  input.value = "";
  finishTypewriter();
  addPlayerMessage(activeNpcId, text);

  state.loading = true;
  input.disabled = true;
  sendBtn.disabled = true;
  sendBtn.classList.add("btn-loading");

  const loadingEl = document.getElementById("dialogue-loading");
  loadingEl.innerHTML = `<span class="loading-dots"></span>${npc ? npc.name : "NPC"}正在思考...`;
  loadingEl.style.display = "block";

  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, npc_id: activeNpcId }),
    });
    const data = await resp.json();

    addNPCMessage(activeNpcId, data.reply);

    if (npc) {
      npc.mood = data.mood;
      npc.affinity = data.affinity;
    }

    if (data.player_gold !== undefined) {
      inventoryState.gold = data.player_gold;
      updateGoldDisplay();
    }
    if (data.player_inventory) {
      inventoryState.items = data.player_inventory;
    }

    showIntentBadge(data.intent);

  } catch (e) {
    addNPCMessage(activeNpcId, `（${npc ? npc.name : "NPC"}挠了挠头）俺刚才走神了，你说啥来着？`);
    console.error("对话请求失败:", e);
  } finally {
    state.loading = false;
    input.disabled = false;
    sendBtn.disabled = false;
    sendBtn.classList.remove("btn-loading");
    document.getElementById("dialogue-loading").style.display = "none";
    input.focus();
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
