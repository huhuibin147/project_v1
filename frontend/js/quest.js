let questOpen = false;
let questNpcId = null;
let questListData = [];
let questManagerOpen = false;
let currentQuestTab = 'active';

async function fetchAllQuests() {
  try {
    const resp = await fetch("/api/quests");
    const data = await resp.json();
    questListData = data.quests || [];
    return questListData;
  } catch (e) {
    console.error("获取任务列表失败:", e);
    return [];
  }
}

async function fetchActiveQuests() {
  try {
    const resp = await fetch("/api/quests/active");
    const data = await resp.json();
    return data.quests || [];
  } catch (e) {
    console.error("获取进行中任务失败:", e);
    return [];
  }
}

async function fetchNpcQuests(npcId) {
  try {
    const resp = await fetch(`/api/quests/npc/${npcId}`);
    const data = await resp.json();
    return data.quests || [];
  } catch (e) {
    console.error("获取NPC任务失败:", e);
    return [];
  }
}

async function acceptQuest(questId) {
  try {
    const resp = await fetch("/api/quests/accept", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quest_id: questId }),
    });
    const data = await resp.json();
    if (data.success) {
      showQuestMessage(data.message, true);
      if (questNpcId) {
        const quests = await fetchNpcQuests(questNpcId);
        renderNpcQuests(quests);
      }
      await fetchAllQuests();
      updateQuestTracker();
      if (questManagerOpen) {
        renderQuestManagerTab(currentQuestTab);
      }
    } else {
      showQuestMessage(data.message, false);
    }
    return data;
  } catch (e) {
    showQuestMessage("接取任务失败", false);
    console.error("接取任务失败:", e);
  }
}

async function abandonQuest(questId) {
  try {
    const resp = await fetch("/api/quests/abandon", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quest_id: questId }),
    });
    const data = await resp.json();
    if (data.success) {
      showQuestMessage(data.message, true);
      closeQuestPanel();
      await fetchAllQuests();
      updateQuestTracker();
      if (questManagerOpen) {
        renderQuestManagerTab(currentQuestTab);
      }
    } else {
      showQuestMessage(data.message, false);
    }
    return data;
  } catch (e) {
    showQuestMessage("放弃任务失败", false);
  }
}

async function completeQuest(questId) {
  try {
    const resp = await fetch("/api/quests/complete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quest_id: questId }),
    });
    const data = await resp.json();
    if (data.success) {
      let msg = data.dialogue || data.message;
      showQuestMessage(msg, true);
      if (data.rewards) {
        const r = data.rewards;
        let rewardText = "奖励：";
        const parts = [];
        if (r.exp > 0) parts.push(`${r.exp}经验`);
        if (r.gold > 0) parts.push(`${r.gold}金币`);
        if (r.items && r.items.length > 0) {
          for (const it of r.items) {
            parts.push(`${it.name}×${it.quantity}`);
          }
        }
        if (r.affinity > 0) parts.push(`${r.affinity_npc || "NPC"}好感+${r.affinity}`);
        rewardText += parts.join("、");
        showQuestMessage(rewardText, true);
      }
      if (data.player_info) {
        Object.assign(playerInfo, data.player_info);
        updatePlayerHUD();
        if (data.player_info.gold !== undefined) {
          inventoryState.gold = data.player_info.gold;
          updateGoldDisplay();
        }
      }
      if (questNpcId) {
        const quests = await fetchNpcQuests(questNpcId);
        renderNpcQuests(quests);
      }
      await fetchAllQuests();
      updateQuestTracker();
    } else {
      showQuestMessage(data.message, false);
    }
    return data;
  } catch (e) {
    showQuestMessage("完成任务失败", false);
    console.error("完成任务失败:", e);
  }
}

function openQuestPanel(npcId) {
  questNpcId = npcId;
  questOpen = true;
  document.getElementById("quest-panel").classList.add("active");
  document.getElementById("quest-panel-title").textContent = getNpcNameById(npcId) + "的任务";
  fetchNpcQuests(npcId).then(quests => renderNpcQuests(quests));
}

function closeQuestPanel() {
  questOpen = false;
  questNpcId = null;
  document.getElementById("quest-panel").classList.remove("active");
}

function openQuestList() {
  questOpen = true;
  document.getElementById("quest-panel").classList.add("active");
  document.getElementById("quest-panel-title").textContent = "任务列表";
  fetchAllQuests().then(quests => renderAllQuests(quests));
}

function closeQuestList() {
  questOpen = false;
  document.getElementById("quest-panel").classList.remove("active");
}

function getNpcNameById(npcId) {
  const npc = npcs.find(n => n.npc_id === npcId);
  if (npc) return npc.name;
  const nameMap = {
    blacksmith: "铁匠老王",
    merchant: "杂货婆刘婶",
    herbalist: "采药人老林",
    priest: "祭司阿雅",
    skill_master: "导师艾尔文",
  };
  return nameMap[npcId] || npcId;
}

function renderNpcQuests(quests) {
  const container = document.getElementById("quest-list");
  container.innerHTML = "";

  if (!quests || quests.length === 0) {
    container.innerHTML = '<div class="quest-empty">暂无任务</div>';
    return;
  }

  for (const q of quests) {
    const div = document.createElement("div");
    div.className = `quest-item quest-status-${q.status}`;

    let statusLabel = "";
    let actionsHtml = "";
    if (q.status === "available") {
      statusLabel = '<span class="quest-status-badge badge-available">可接取</span>';
      actionsHtml = `<button class="btn-quest-action" onclick="acceptQuest('${q.id}')">接取</button>`;
    } else if (q.status === "active") {
      statusLabel = '<span class="quest-status-badge badge-active">进行中</span>';
      if (q.can_complete) {
        actionsHtml = `<button class="btn-quest-action btn-complete" onclick="completeQuest('${q.id}')">交付</button>`;
      }
      actionsHtml += ` <button class="btn-quest-action btn-abandon" onclick="abandonQuest('${q.id}')">放弃</button>`;
    } else if (q.status === "completed") {
      statusLabel = '<span class="quest-status-badge badge-completed">已完成</span>';
    } else {
      statusLabel = '<span class="quest-status-badge badge-locked">未解锁</span>';
    }

    let objectivesHtml = "";
    if (q.objectives && q.objectives.length > 0) {
      objectivesHtml = '<div class="quest-objectives">';
      for (const obj of q.objectives) {
        const completed = obj.completed;
        const icon = completed ? "✓" : "○";
        const progressText = obj.count > 1 ? ` ${obj.progress}/${obj.count}` : "";
        objectivesHtml += `<div class="quest-obj ${completed ? 'obj-done' : ''}">${icon} ${obj.description}${progressText}</div>`;
      }
      objectivesHtml += "</div>";
    }

    let rewardsHtml = "";
    if (q.rewards) {
      const parts = [];
      if (q.rewards.exp > 0) parts.push(`<span class="reward-exp">${q.rewards.exp}经验</span>`);
      if (q.rewards.gold > 0) parts.push(`<span class="reward-gold">${q.rewards.gold}金币</span>`);
      if (q.rewards.items && q.rewards.items.length > 0) {
        for (const it of q.rewards.items) {
          parts.push(`<span class="reward-item">${it.name || it.item_id}×${it.quantity}</span>`);
        }
      }
      if (q.rewards.affinity && q.rewards.affinity.value > 0) {
        parts.push(`<span class="reward-affinity">好感+${q.rewards.affinity.value}</span>`);
      }
      if (parts.length > 0) {
        rewardsHtml = `<div class="quest-rewards">奖励：${parts.join(" ")}</div>`;
      }
    }

    div.innerHTML = `
      <div class="quest-header">
        <span class="quest-name">${q.name}</span>
        ${statusLabel}
      </div>
      <div class="quest-desc">${q.description}</div>
      ${objectivesHtml}
      ${rewardsHtml}
      <div class="quest-actions">${actionsHtml}</div>
    `;
    container.appendChild(div);
  }
}

function renderAllQuests(quests) {
  const container = document.getElementById("quest-list");
  container.innerHTML = "";

  if (!quests || quests.length === 0) {
    container.innerHTML = '<div class="quest-empty">暂无任务</div>';
    return;
  }

  const active = quests.filter(q => q.status === "active");
  const available = quests.filter(q => q.status === "available");
  const completed = quests.filter(q => q.status === "completed");
  const locked = quests.filter(q => q.status === "locked");

  if (active.length > 0) {
    container.innerHTML += '<div class="quest-section-title">进行中</div>';
    for (const q of active) {
      container.innerHTML += buildQuestItemHtml(q);
    }
  }
  if (available.length > 0) {
    container.innerHTML += '<div class="quest-section-title">可接取</div>';
    for (const q of available) {
      container.innerHTML += buildQuestItemHtml(q);
    }
  }
  if (completed.length > 0) {
    container.innerHTML += '<div class="quest-section-title">已完成</div>';
    for (const q of completed) {
      container.innerHTML += buildQuestItemHtml(q);
    }
  }
  if (locked.length > 0) {
    container.innerHTML += '<div class="quest-section-title">未解锁</div>';
    for (const q of locked) {
      container.innerHTML += buildQuestItemHtml(q);
    }
  }

  if (container.innerHTML === "") {
    container.innerHTML = '<div class="quest-empty">暂无任务</div>';
  }
}

function buildQuestItemHtml(q) {
  let statusLabel = "";
  let actionsHtml = "";
  if (q.status === "available") {
    statusLabel = '<span class="quest-status-badge badge-available">可接取</span>';
    actionsHtml = `<button class="btn-quest-action" onclick="acceptQuest('${q.id}')">接取</button>`;
  } else if (q.status === "active") {
    statusLabel = '<span class="quest-status-badge badge-active">进行中</span>';
    if (q.can_complete) {
      actionsHtml = `<button class="btn-quest-action btn-complete" onclick="completeQuest('${q.id}')">交付</button>`;
    }
    actionsHtml += ` <button class="btn-quest-action btn-abandon" onclick="abandonQuest('${q.id}')">放弃</button>`;
  } else if (q.status === "completed") {
    statusLabel = '<span class="quest-status-badge badge-completed">已完成</span>';
  } else {
    statusLabel = '<span class="quest-status-badge badge-locked">未解锁</span>';
  }

  let objectivesHtml = "";
  if (q.objectives && q.objectives.length > 0) {
    objectivesHtml = '<div class="quest-objectives">';
    for (const obj of q.objectives) {
      const completed = obj.completed;
      const icon = completed ? "✓" : "○";
      const progressText = obj.count > 1 ? ` ${obj.progress}/${obj.count}` : "";
      objectivesHtml += `<div class="quest-obj ${completed ? 'obj-done' : ''}">${icon} ${obj.description}${progressText}</div>`;
    }
    objectivesHtml += "</div>";
  }

  let rewardsHtml = "";
  if (q.rewards) {
    const parts = [];
    if (q.rewards.exp > 0) parts.push(`<span class="reward-exp">${q.rewards.exp}经验</span>`);
    if (q.rewards.gold > 0) parts.push(`<span class="reward-gold">${q.rewards.gold}金币</span>`);
    if (q.rewards.items && q.rewards.items.length > 0) {
      for (const it of q.rewards.items) {
        parts.push(`<span class="reward-item">${it.name || it.item_id}×${it.quantity}</span>`);
      }
    }
    if (q.rewards.affinity && q.rewards.affinity.value > 0) {
      parts.push(`<span class="reward-affinity">好感+${q.rewards.affinity.value}</span>`);
    }
    if (parts.length > 0) {
      rewardsHtml = `<div class="quest-rewards">奖励：${parts.join(" ")}</div>`;
    }
  }

  const npcLabel = q.npc_name ? `<span class="quest-npc-label">来自：${q.npc_name}</span>` : "";

  return `<div class="quest-item quest-status-${q.status}">
    <div class="quest-header">
      <span class="quest-name">${q.name}</span>
      ${statusLabel}
      ${npcLabel}
    </div>
    <div class="quest-desc">${q.description}</div>
    ${objectivesHtml}
    ${rewardsHtml}
    <div class="quest-actions">${actionsHtml}</div>
  </div>`;
}

function showQuestMessage(text, success) {
  const el = document.getElementById("quest-message");
  if (!el) return;
  el.textContent = text;
  el.className = `quest-message ${success ? "success" : "error"}`;
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 3000);
}

async function updateQuestTracker() {
  const tracker = document.getElementById("quest-tracker");
  if (!tracker) return;

  const activeQuests = await fetchActiveQuests();
  if (!activeQuests || activeQuests.length === 0) {
    tracker.style.display = "none";
    return;
  }

  tracker.style.display = "block";
  let html = '<div class="tracker-title">当前任务</div>';
  for (const q of activeQuests.slice(0, 3)) {
    html += `<div class="tracker-quest">`;
    html += `<div class="tracker-quest-name">${q.name}</div>`;
    if (q.objectives) {
      for (const obj of q.objectives) {
        const icon = obj.completed ? "✓" : "○";
        const progressText = obj.count > 1 ? ` ${obj.progress}/${obj.count}` : "";
        html += `<div class="tracker-obj ${obj.completed ? 'obj-done' : ''}">${icon} ${obj.description}${progressText}</div>`;
      }
    }
    html += "</div>";
  }
  if (activeQuests.length > 3) {
    html += `<div class="tracker-more">还有 ${activeQuests.length - 3} 个任务...</div>`;
  }
  tracker.innerHTML = html;
}

let exploreCheckTimer = null;

function startExploreCheck() {
  if (exploreCheckTimer) return;
  exploreCheckTimer = setInterval(() => {
    if (!gameStarted || combatOpen || dialogueOpen) return;
    const tile = getPlayerTilePosition();
    if (tile && currentMap) {
      fetch("/api/quests/progress", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_type: "explore",
          data: { map_id: currentMap.id, x: tile.x, y: tile.y },
        }),
      }).then(resp => resp.json())
        .then(data => {
          if (data.updated && data.updated.length > 0) {
            updateQuestTracker();
            if (questManagerOpen) {
              renderQuestManagerTab(currentQuestTab);
            }
          }
        })
        .catch(() => {});
    }
  }, 5000);
}

function openQuestManager() {
  questManagerOpen = true;
  currentQuestTab = 'active';
  document.getElementById("quest-manager-panel").classList.add("active");
  updateQuestTabButtons();
  fetchAllQuests().then(() => {
    renderQuestManagerTab('active');
  });
}

function closeQuestManager() {
  questManagerOpen = false;
  document.getElementById("quest-manager-panel").classList.remove("active");
}

function switchQuestTab(tab) {
  currentQuestTab = tab;
  updateQuestTabButtons();
  renderQuestManagerTab(tab);
}

function updateQuestTabButtons() {
  document.querySelectorAll('.quest-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === currentQuestTab);
  });
}

function renderQuestManagerTab(tab) {
  const container = document.getElementById("quest-manager-content");
  if (!container) return;

  const filtered = questListData.filter(q => q.status === tab);

  if (!filtered || filtered.length === 0) {
    const emptyText = {
      active: "暂无进行中的任务，去和NPC对话看看有没有任务吧！",
      available: "暂无可接取的任务，提升等级或完成其他任务来解锁更多任务！",
      completed: "暂无已完成的任务，快去接取任务吧！",
    };
    container.innerHTML = `<div class="quest-manager-empty">${emptyText[tab] || "暂无任务"}</div>`;
    return;
  }

  let html = "";
  for (const q of filtered) {
    html += buildQuestManagerItemHtml(q);
  }
  container.innerHTML = html;
}

function buildQuestManagerItemHtml(q) {
  let statusClass = "";
  let actionsHtml = "";
  let progressHtml = "";

  if (q.status === "active") {
    statusClass = "quest-active";
    if (q.can_complete) {
      actionsHtml = `<button class="qm-btn qm-btn-complete" onclick="completeQuest('${q.id}')">交付任务</button>`;
    }
    actionsHtml += ` <button class="qm-btn qm-btn-abandon" onclick="abandonQuest('${q.id}')">放弃任务</button>`;

    if (q.objectives && q.objectives.length > 0) {
      const total = q.objectives.length;
      const completed = q.objectives.filter(o => o.completed).length;
      const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
      progressHtml = `<div class="qm-progress-bar"><div class="qm-progress-fill" style="width:${percent}%"></div></div>`;
    }
  } else if (q.status === "available") {
    statusClass = "quest-available";
    actionsHtml = `<button class="qm-btn qm-btn-accept" onclick="acceptQuest('${q.id}')">接取任务</button>`;
  } else if (q.status === "completed") {
    statusClass = "quest-completed";
  } else {
    statusClass = "quest-locked";
  }

  let objectivesHtml = "";
  if (q.objectives && q.objectives.length > 0) {
    objectivesHtml = '<div class="qm-objectives">';
    for (const obj of q.objectives) {
      const completed = obj.completed;
      const icon = completed ? "✓" : "○";
      const progressText = obj.count > 1 ? ` ${obj.progress}/${obj.count}` : "";
      objectivesHtml += `<div class="qm-obj ${completed ? 'obj-done' : ''}"><span class="qm-obj-icon">${icon}</span>${obj.description}${progressText}</div>`;
    }
    objectivesHtml += "</div>";
  }

  let rewardsHtml = "";
  if (q.rewards) {
    const parts = [];
    if (q.rewards.exp > 0) parts.push(`<span class="reward-exp">${q.rewards.exp}经验</span>`);
    if (q.rewards.gold > 0) parts.push(`<span class="reward-gold">${q.rewards.gold}金币</span>`);
    if (q.rewards.items && q.rewards.items.length > 0) {
      for (const it of q.rewards.items) {
        parts.push(`<span class="reward-item">${it.name || it.item_id}×${it.quantity}</span>`);
      }
    }
    if (q.rewards.affinity && q.rewards.affinity.value > 0) {
      parts.push(`<span class="reward-affinity">好感+${q.rewards.affinity.value}</span>`);
    }
    if (parts.length > 0) {
      rewardsHtml = `<div class="qm-rewards">奖励：${parts.join(" ")}</div>`;
    }
  }

  const npcLabel = q.npc_name ? `<span class="qm-npc">来自：${q.npc_name}</span>` : "";

  return `<div class="quest-manager-item ${statusClass}">
    <div class="qm-header">
      <span class="qm-name">${q.name}</span>
      ${npcLabel}
    </div>
    <div class="qm-desc">${q.description}</div>
    ${objectivesHtml}
    ${progressHtml}
    ${rewardsHtml}
    <div class="qm-actions">${actionsHtml}</div>
  </div>`;
}

document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() === "q" && gameStarted && !dialogueOpen && !gameMenuOpen && !combatOpen && !talentPanelOpen) {
    if (questManagerOpen) {
      closeQuestManager();
    } else {
      if (inventoryOpen) closeInventory();
      if (playerInfoOpen) closePlayerInfo();
      if (helpOpen) closeHelp();
      openQuestManager();
    }
  }
  if (e.key === "Escape" && questManagerOpen) {
    closeQuestManager();
  }
});
