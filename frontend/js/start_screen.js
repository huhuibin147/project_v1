// 开始界面逻辑

let selectedClassId = "warrior";
let selectedSlot = 1;
let availableClasses = {};
let saveSlotData = [];

// 职业显示配置
const classDisplay = {
  warrior: { icon: "剑", color: "#ff6b6b" },
  rogue: { icon: "匕", color: "#ffd76b" },
  mage: { icon: "魔", color: "#6bafff" },
};

// 页面加载时初始化开始界面
async function initStartScreen() {
  try {
    const res = await fetch("/api/saves");
    if (!res.ok) throw new Error("获取存档失败");
    const data = await res.json();
    const saves = data.saves;
    const lastSlot = data.last_slot;
    saveSlotData = saves;

    // 显示"继续冒险"按钮
    const btn = document.getElementById("btn-continue");
    
    // 优先使用最后加载的存档槽，如果没有则使用最后一个存在的存档
    let continueSlot = null;
    if (lastSlot) {
      // 检查最后加载的存档是否存在
      const lastSave = saves.find(s => s.slot === lastSlot && s.exists);
      if (lastSave) {
        continueSlot = lastSave;
      }
    }
    
    // 如果最后加载的存档不存在，使用最后一个存在的存档
    if (!continueSlot) {
      const existingSaves = saves.filter(s => s.exists);
      if (existingSaves.length > 0) {
        continueSlot = existingSaves[existingSaves.length - 1];
      }
    }
    
    if (continueSlot) {
      btn.style.display = "block";
      btn.onclick = () => loadGame(continueSlot.slot);
    } else {
      btn.style.display = "none";
    }
  } catch (e) {
    console.error("初始化开始界面失败:", e);
    document.getElementById("btn-continue").style.display = "none";
  }
}

function hideStartScreen() {
  document.getElementById("start-screen").classList.add("hidden");
  document.getElementById("game-container").style.display = "block";
  closeSavePanel();
  // 清空前端对话记录，加载存档时会从后端重新获取
  for (const key in dialogueHistory) {
    delete dialogueHistory[key];
  }
}

function closeSavePanel() {
  document.getElementById("new-game-panel").classList.remove("active");
  document.getElementById("load-panel").classList.remove("active");
  // 重新显示主菜单
  document.getElementById("start-menu").style.display = "block";
}

// ===== 新建游戏 =====

async function showNewGamePanel() {
  // 隐藏主菜单，显示新建面板
  document.getElementById("start-menu").style.display = "none";

  // 加载职业数据
  if (!Object.keys(availableClasses).length) {
    try {
      const res = await fetch("/api/player/classes");
      if (!res.ok) throw new Error("获取职业失败");
      availableClasses = await res.json();
    } catch (e) {
      console.error("加载职业数据失败:", e);
      alert("加载职业数据失败，请重试");
      document.getElementById("start-menu").style.display = "block";
      return;
    }
  }

  // 加载存档信息以选择槽位
  try {
    const res = await fetch("/api/saves");
    if (!res.ok) throw new Error("获取存档失败");
    const data = await res.json();
    saveSlotData = data.saves;
  } catch (e) {
    console.error("加载存档信息失败:", e);
    alert("加载存档信息失败，请重试");
    document.getElementById("start-menu").style.display = "block";
    return;
  }

  // 重置选择状态
  selectedClassId = "warrior";
  const emptySlot = saveSlotData.find((s) => !s.exists);
  selectedSlot = emptySlot ? emptySlot.slot : 1;
  document.getElementById("new-name").value = "冒险者";

  renderClassCards();
  renderSlotSelect();

  document.getElementById("new-game-panel").classList.add("active");
}

function renderClassCards() {
  const container = document.getElementById("class-cards");
  container.innerHTML = "";

  for (const [id, cls] of Object.entries(availableClasses)) {
    const display = classDisplay[id] || { icon: "?", color: "#aaa" };
    const card = document.createElement("div");
    card.className = `class-card${id === selectedClassId ? " selected" : ""}`;
    card.onclick = () => selectClass(id);
    card.innerHTML = `
      <div class="class-icon" style="color:${display.color}">${display.icon}</div>
      <div class="class-name">${cls.name}</div>
      <div class="class-desc">${cls.description}</div>
      <div class="class-stats">
        <div class="class-stat-row"><span>生命</span><span class="class-stat-val">${cls.base_hp}</span></div>
        <div class="class-stat-row"><span>攻击</span><span class="class-stat-val">${cls.base_attack}</span></div>
        <div class="class-stat-row"><span>防御</span><span class="class-stat-val">${cls.base_defense}</span></div>
        <div class="class-stat-row"><span>速度</span><span class="class-stat-val">${cls.base_speed}</span></div>
      </div>
    `;
    container.appendChild(card);
  }
}

function selectClass(classId) {
  selectedClassId = classId;
  renderClassCards();
}

function renderSlotSelect() {
  const container = document.getElementById("new-slot-select");
  container.innerHTML = "";

  for (const save of saveSlotData) {
    const option = document.createElement("div");
    option.className = `slot-option${save.slot === selectedSlot ? " selected" : ""}${save.exists ? " has-save" : ""}`;
    option.onclick = () => selectSlot(save.slot);
    option.innerHTML = `
      <div class="slot-label">存档 ${save.slot}</div>
      <div class="slot-info">${save.exists ? `Lv.${save.level} ${save.name}` : "空"}</div>
    `;
    container.appendChild(option);
  }
}

function selectSlot(slot) {
  selectedSlot = slot;
  renderSlotSelect();
}

async function confirmNewGame() {
  const name = document.getElementById("new-name").value.trim();
  if (!name) {
    alert("请输入冒险者名称");
    return;
  }

  // 如果选中的槽位有存档，确认覆盖
  const existingSave = saveSlotData.find(
    (s) => s.slot === selectedSlot && s.exists
  );
  if (existingSave) {
    if (
      !confirm(
        `存档 ${selectedSlot} 已有数据（Lv.${existingSave.level} ${existingSave.name}），确定要覆盖吗？`
      )
    ) {
      return;
    }
  }

  try {
    const res = await fetch("/api/saves/new", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name,
        class_id: selectedClassId,
        slot: selectedSlot,
      }),
    });
    const data = await res.json();
    if (res.ok && data.success) {
      hideStartScreen();
      await startGame();
    } else {
      alert("创建失败：" + (data.detail || "未知错误"));
    }
  } catch (e) {
    alert("创建失败：" + e.message);
  }
}

// ===== 读取存档 =====

async function showLoadPanel() {
  // 隐藏主菜单，显示读档面板
  document.getElementById("start-menu").style.display = "none";

  try {
    const res = await fetch("/api/saves");
    if (!res.ok) throw new Error("获取存档失败");
    const data = await res.json();
    saveSlotData = data.saves;
  } catch (e) {
    console.error("加载存档信息失败:", e);
    alert("加载存档信息失败，请重试");
    document.getElementById("start-menu").style.display = "block";
    return;
  }

  renderLoadSlots();
  document.getElementById("load-panel").classList.add("active");
}

function renderLoadSlots() {
  const container = document.getElementById("load-slots");
  container.innerHTML = "";

  for (const save of saveSlotData) {
    const card = document.createElement("div");
    card.className = `save-slot-card${save.exists ? "" : " empty"}`;

    if (save.exists) {
      card.innerHTML = `
        <div class="save-slot-num">${save.slot}</div>
        <div class="save-slot-info">
          <div class="save-slot-name">${save.name}</div>
          <div class="save-slot-detail">Lv.${save.level} ${getClassName(save.class_id)}</div>
          <div class="save-slot-time">${save.save_time || ""}</div>
        </div>
        <button class="btn-delete-save" onclick="event.stopPropagation(); deleteSave(${save.slot})">删除</button>
      `;
      card.onclick = () => loadGame(save.slot);
    } else {
      card.innerHTML = `
        <div class="save-slot-num">${save.slot}</div>
        <div class="save-slot-info">
          <div class="save-slot-empty">空存档</div>
        </div>
      `;
    }

    container.appendChild(card);
  }
}

function getClassName(classId) {
  const names = { warrior: "战士", rogue: "盗贼", mage: "法师" };
  return names[classId] || classId;
}

async function loadGame(slot) {
  try {
    const res = await fetch("/api/saves/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slot: slot }),
    });
    const data = await res.json();
    if (res.ok && data.success) {
      hideStartScreen();
      await startGame();
    } else {
      alert("读取存档失败：" + (data.detail || "未知错误"));
    }
  } catch (e) {
    alert("读取存档失败：" + e.message);
  }
}

async function deleteSave(slot) {
  if (!confirm(`确定要删除存档 ${slot} 吗？此操作不可撤销。`)) {
    return;
  }

  try {
    const res = await fetch(`/api/saves/${slot}`, { method: "DELETE" });
    const data = await res.json();
    if (res.ok && data.success) {
      // 刷新存档列表
      const savesRes = await fetch("/api/saves");
      const savesData = await savesRes.json();
      saveSlotData = savesData.saves;
      renderLoadSlots();
    } else {
      alert("删除失败：" + (data.detail || "未知错误"));
    }
  } catch (e) {
    alert("删除失败：" + e.message);
  }
}
