// 游戏主循环

let canvas, ctx;
let lastTime = 0;
let gameStarted = false;
let gameMenuOpen = false;
let positionSaveTimer = null;

function initCanvas() {
  canvas = document.getElementById("game-canvas");
  ctx = canvas.getContext("2d");
  canvas.width = MAP_COLS * TILE_SIZE;
  canvas.height = MAP_ROWS * TILE_SIZE;
  ctx.imageSmoothingEnabled = false;
}

function gameLoop(timestamp) {
  const dt = timestamp - lastTime;
  lastTime = timestamp;

  if (gameStarted) {
    update(dt);
    render();
  }

  requestAnimationFrame(gameLoop);
}

function update(dt) {
  updatePlayer();
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  drawMap(ctx);

  // 收集所有可绘制对象（NPC + 玩家），按 Y 坐标排序实现遮挡
  const drawables = [];

  for (const npc of npcs) {
    drawables.push({ type: "npc", y: npc.y, data: npc });
  }
  drawables.push({ type: "player", y: player.y, data: player });

  drawables.sort((a, b) => a.y - b.y);

  for (const obj of drawables) {
    if (obj.type === "npc") {
      drawNPC(ctx, obj.data);
    } else {
      drawPlayer(ctx);
    }
  }

  drawHUD(ctx);
}

function drawHUD(ctx) {
  const hudBarEl = document.getElementById("hud-bar");
  const hudBottom = hudBarEl ? hudBarEl.getBoundingClientRect().bottom - canvas.getBoundingClientRect().top : 0;
  const startY = Math.max(hudBottom + 6, 40);

  ctx.fillStyle = "rgba(0,0,0,0.6)";
  ctx.fillRect(8, startY, 220, 38);
  ctx.fillStyle = "#fff";
  ctx.font = "11px monospace";
  ctx.textAlign = "left";
  ctx.fillText("WASD/方向键 移动  E 对话", 16, startY + 14);
  ctx.fillText("靠近NPC按E开始冒险吧", 16, startY + 28);
}

// 开始游戏（由开始界面调用）
async function startGame() {
  initCanvas();
  gameStarted = true;

  // 先加载玩家信息（含位置），再加载 NPC
  await fetchPlayerInfo();
  await fetchAllNpcs();
  fetchInventory();

  // 启动定期保存位置的定时器（每5秒）
  if (positionSaveTimer) clearInterval(positionSaveTimer);
  positionSaveTimer = setInterval(() => {
    if (gameStarted) {
      savePlayerPosition();
    }
  }, 5000);
}

// 页面加载时初始化开始界面，启动游戏循环
initStartScreen();
requestAnimationFrame(gameLoop);

// ===== 游戏菜单 =====

function toggleGameMenu() {
  if (gameMenuOpen) {
    closeGameMenu();
  } else {
    openGameMenu();
  }
}

function openGameMenu() {
  gameMenuOpen = true;
  document.getElementById("game-menu-panel").classList.add("active");
}

function closeGameMenu() {
  gameMenuOpen = false;
  document.getElementById("game-menu-panel").classList.remove("active");
}

function saveGame() {
  closeGameMenu();
  savePlayerPosition().then(() => {
    alert("游戏已保存！");
  });
}

function returnToMainMenu() {
  closeGameMenu();
  if (!confirm("确定要返回主菜单吗？")) {
    return;
  }
  // 保存位置后返回主菜单
  savePlayerPosition().then(() => {
    gameStarted = false;
    if (positionSaveTimer) {
      clearInterval(positionSaveTimer);
      positionSaveTimer = null;
    }
    // 关闭所有面板
    if (dialogueOpen) closeDialogue();
    if (inventoryOpen) closeInventory();
    if (shopOpen) closeShop();
    if (playerInfoOpen) closePlayerInfo();
    if (npcInteractOpen) closeNpcInteract();

    document.getElementById("game-container").style.display = "none";
    document.getElementById("start-screen").classList.remove("hidden");
    // 重新初始化开始界面
    initStartScreen();
  });
}

// ESC 键切换游戏菜单
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && gameStarted) {
    toggleGameMenu();
  }
});
