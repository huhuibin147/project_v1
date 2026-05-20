let talentPanelOpen = false;
let talentData = null;

const TREE_NAMES = {
  berserk: "狂战",
  guard: "守护",
  assassin: "刺杀",
  trick: "诡术",
  element: "元素",
  holy: "神圣",
};

const TREE_COLORS = {
  berserk: "#e74c3c",
  guard: "#3498db",
  assassin: "#e67e22",
  trick: "#9b59b6",
  element: "#e74c3c",
  holy: "#f1c40f",
};

async function fetchTalentData() {
  try {
    const resp = await fetch("/api/talents");
    const data = await resp.json();
    talentData = data;
    return data;
  } catch (e) {
    console.error("获取天赋数据失败:", e);
    return null;
  }
}

async function openTalentPanel() {
  if (talentPanelOpen) {
    closeTalentPanel();
    return;
  }
  if (dialogueOpen || shopOpen || GameManager.isMenuOpen() || combatOpen || npcInteractOpen || healPanelOpen || skillLearnPanelOpen || skillMenuOpen || (typeof forgePanelOpen !== 'undefined' && forgePanelOpen)) return;
  if (playerInfoOpen) closePlayerInfo();
  if (inventoryOpen) closeInventory();
  if (helpOpen) closeHelp();
  if (questManagerOpen) closeQuestManager();
  if (skillMenuOpen) closeSkillMenu();
  if (typeof worldMapOpen !== 'undefined' && worldMapOpen) closeWorldMap();
  const data = await fetchTalentData();
  if (!data) return;
  renderTalentPanel(data);
  document.getElementById("talent-panel").style.display = "flex";
  talentPanelOpen = true;
}

function closeTalentPanel() {
  document.getElementById("talent-panel").style.display = "none";
  talentPanelOpen = false;
  hideTalentMessage();
}

function renderTalentPanel(data) {
  document.getElementById("talent-available").textContent = data.available_points;
  document.getElementById("talent-total").textContent = data.total_points;

  const container = document.getElementById("talent-trees");
  container.innerHTML = "";

  const trees = data.trees || {};
  for (const [treeName, talents] of Object.entries(trees)) {
    const treeDiv = document.createElement("div");
    treeDiv.className = "talent-tree";

    const treeLabel = TREE_NAMES[treeName] || treeName;
    const treeColor = TREE_COLORS[treeName] || "#ffffff";

    const header = document.createElement("div");
    header.className = "talent-tree-header";
    header.style.borderLeftColor = treeColor;
    header.innerHTML = `<span class="talent-tree-name" style="color:${treeColor}">${treeLabel}</span>`;
    treeDiv.appendChild(header);

    const nodesDiv = document.createElement("div");
    nodesDiv.className = "talent-tree-nodes";

    for (const talent of talents) {
      const node = createTalentNode(talent, treeColor);
      nodesDiv.appendChild(node);
    }

    treeDiv.appendChild(nodesDiv);
    container.appendChild(treeDiv);
  }
}

function createTalentNode(talent, treeColor) {
  const node = document.createElement("div");
  node.className = "talent-node";
  if (talent.learned) {
    node.classList.add("talent-learned");
  } else if (talent.can_learn) {
    node.classList.add("talent-available");
  } else {
    node.classList.add("talent-locked");
  }

  const nameDiv = document.createElement("div");
  nameDiv.className = "talent-node-name";
  nameDiv.style.color = talent.learned ? treeColor : "";
  nameDiv.textContent = talent.name;

  const tierDiv = document.createElement("div");
  tierDiv.className = "talent-node-tier";
  tierDiv.textContent = `Tier ${talent.tier}`;

  const descDiv = document.createElement("div");
  descDiv.className = "talent-node-desc";
  descDiv.textContent = talent.description;

  node.appendChild(nameDiv);
  node.appendChild(tierDiv);
  node.appendChild(descDiv);

  if (talent.learned) {
    const badge = document.createElement("span");
    badge.className = "talent-badge learned";
    badge.textContent = "已学";
    node.appendChild(badge);
  } else if (talent.can_learn) {
    const btn = document.createElement("button");
    btn.className = "talent-learn-btn";
    btn.textContent = "学习";
    btn.onclick = () => learnTalent(talent.talent_id);
    node.appendChild(btn);
  } else if (talent.reason) {
    const lockReason = document.createElement("div");
    lockReason.className = "talent-lock-reason";
    lockReason.textContent = talent.reason;
    node.appendChild(lockReason);
  }

  return node;
}

async function learnTalent(talentId) {
  try {
    const resp = await fetch("/api/talents/learn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ talent_id: talentId }),
    });
    const data = await resp.json();
    if (data.success) {
      showTalentMessage(data.message, true);
      talentData = data.talent_info;
      renderTalentPanel(data.talent_info);
      if (typeof updatePlayerHUD === "function") {
        updatePlayerHUD();
      }
    } else {
      showTalentMessage(data.message, false);
    }
  } catch (e) {
    console.error("学习天赋失败:", e);
    showTalentMessage("网络错误", false);
  }
}

async function resetTalents() {
  if (!confirm("确定要重置所有天赋吗？将花费金币。")) return;
  try {
    const resp = await fetch("/api/talents/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await resp.json();
    if (data.success) {
      showTalentMessage(data.message, true);
      talentData = data.talent_info;
      renderTalentPanel(data.talent_info);
      if (typeof updatePlayerHUD === "function") {
        updatePlayerHUD();
      }
    } else {
      showTalentMessage(data.message, false);
    }
  } catch (e) {
    console.error("重置天赋失败:", e);
    showTalentMessage("网络错误", false);
  }
}

function showTalentMessage(msg, isSuccess) {
  const el = document.getElementById("talent-message");
  el.textContent = msg;
  el.style.display = "block";
  el.className = "trade-message " + (isSuccess ? "success" : "error");
  setTimeout(() => { el.style.display = "none"; }, 3000);
}

function hideTalentMessage() {
  document.getElementById("talent-message").style.display = "none";
}

document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() === "t" && !dialogueOpen && !GameManager.isMenuOpen() && !shopOpen && !inventoryOpen && !playerInfoOpen && !combatOpen && !helpOpen && !questManagerOpen && !npcInteractOpen && !healPanelOpen && !skillLearnPanelOpen && !skillMenuOpen) {
    if (talentPanelOpen) {
      closeTalentPanel();
    } else {
      openTalentPanel();
    }
  }
  if (e.key === "Escape" && talentPanelOpen) {
    closeTalentPanel();
  }
});
