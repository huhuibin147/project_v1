// 对话 UI 与 API 调用

let dialogueOpen = false;

const dialogueUI = {
  messages: [],       // { role: "player"|"npc", text: "" }
  inputText: "",
  loading: false,
};

function openDialogue() {
  dialogueOpen = true;
  dialogueUI.inputText = "";
  document.getElementById("dialogue-panel").classList.add("active");
  document.getElementById("dialogue-input").focus();

  // 如果是第一次打开，显示 NPC 的开场白（从配置加载）
  if (dialogueUI.messages.length === 0 && npcState.greeting) {
    addNPCMessage(npcState.greeting);
  }

  renderDialogue();
}

function closeDialogue() {
  dialogueOpen = false;
  document.getElementById("dialogue-panel").classList.remove("active");
}

function addNPCMessage(text) {
  dialogueUI.messages.push({ role: "npc", text });
  renderDialogue();
}

function addPlayerMessage(text) {
  dialogueUI.messages.push({ role: "player", text });
  renderDialogue();
}

function renderDialogue() {
  const container = document.getElementById("dialogue-messages");
  container.innerHTML = "";

  // 只显示最近的消息
  const recent = dialogueUI.messages.slice(-10);
  for (const msg of recent) {
    const div = document.createElement("div");
    div.className = `dialogue-msg ${msg.role}`;
    const label = msg.role === "npc" ? npcState.name : "你";
    const color = msg.role === "npc" ? "#f0c060" : "#60a0f0";
    div.innerHTML = `<span style="color:${color};font-weight:bold">${label}：</span>${escapeHTML(msg.text)}`;
    container.appendChild(div);
  }

  container.scrollTop = container.scrollHeight;

  // 更新状态显示
  document.getElementById("npc-mood").textContent = npcState.mood;
  document.getElementById("npc-affinity").textContent = npcState.affinity;
}

function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function sendMessage() {
  const input = document.getElementById("dialogue-input");
  const text = input.value.trim();
  if (!text || dialogueUI.loading) return;

  input.value = "";
  addPlayerMessage(text);

  dialogueUI.loading = true;
  const loadingEl = document.getElementById("dialogue-loading");
  loadingEl.textContent = `${npcState.name}正在思考...`;
  loadingEl.style.display = "block";

  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await resp.json();

    addNPCMessage(data.reply);
    npcState.mood = data.mood;
    npcState.affinity = data.affinity;

    // 更新金币和背包
    if (data.player_gold !== undefined) {
      inventoryState.gold = data.player_gold;
      updateGoldDisplay();
    }
    if (data.player_inventory) {
      inventoryState.items = data.player_inventory;
    }

    // 根据意图添加视觉反馈
    showIntentBadge(data.intent);

    // 如果是交易意图，显示打开商店按钮
    if (data.intent === "trade") {
      showShopButton();
    }
  } catch (e) {
    addNPCMessage(`（${npcState.name}挠了挠头）俺刚才走神了，你说啥来着？`);
    console.error("对话请求失败:", e);
  } finally {
    dialogueUI.loading = false;
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

function showShopButton() {
  const container = document.getElementById("dialogue-messages");
  const div = document.createElement("div");
  div.className = "dialogue-msg system";
  div.innerHTML = '<button class="btn-open-shop" onclick="openShopFromDialogue()">打开商店</button>';
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function openShopFromDialogue() {
  closeDialogue();
  openShop();
}

// ESC 关闭对话
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && dialogueOpen) {
    closeDialogue();
  }
});
