// 游戏主循环

let canvas, ctx;
let lastTime = 0;
let gameStarted = false;
let gameMenuOpen = false;
let positionSaveTimer = null;
// let helpVisible = false; // 帮助提示显示状态

function initCanvas() {
  canvas = document.getElementById("game-canvas");
  ctx = canvas.getContext("2d");
  resizeCanvas();
  ctx.imageSmoothingEnabled = false;
  
  // 窗口大小改变时更新画布
  window.addEventListener('resize', resizeCanvas);
}

function resizeCanvas() {
  if (!canvas) return;
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  camera.viewportWidth = canvas.width;
  camera.viewportHeight = canvas.height;
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
  updateCamera();
  checkPortalAutoTransfer();
  updateMonsters(dt);
  recordExploredTile();
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.save();
  ctx.translate(-camera.x, -camera.y);

  drawMap(ctx);
  drawObjects(ctx);
  drawEnvironmentParticles(ctx);

  // 收集所有可绘制对象（NPC + 怪物 + 玩家），按 Y 坐标排序实现遮挡
  const drawables = [];

  for (const npc of npcs) {
    drawables.push({ type: "npc", y: npc.y, data: npc });
  }
  for (const m of mapMonsters) {
    if (m.alive) {
      drawables.push({ type: "monster", y: m.y, data: m });
    }
  }
  drawables.push({ type: "player", y: player.y, data: player });

  drawables.sort((a, b) => a.y - b.y);

  for (const obj of drawables) {
    if (obj.type === "npc") {
      drawNPC(ctx, obj.data);
    } else if (obj.type === "monster") {
      drawMapMonster(ctx, obj.data);
    } else {
      drawPlayer(ctx);
    }
  }

  ctx.restore();

  renderMinimap();
  updateHudMapName();
  drawGatherHint();
}

function updateHudMapName() {
  const el = document.getElementById("hud-map-name");
  if (el && currentMap) {
    el.textContent = currentMap.name;
  }
}

function drawGatherHint() {
  if (!currentMap || !mapObjects) return;

  const playerTileX = Math.floor((player.x + PLAYER_SIZE / 2) / TILE_SIZE);
  const playerTileY = Math.floor((player.y + PLAYER_SIZE / 2) / TILE_SIZE);

  for (const obj of mapObjects) {
    if (obj.type !== "gather") continue;
    
    const dx = Math.abs(obj.x - playerTileX);
    const dy = Math.abs(obj.y - playerTileY);
    
    if (dx <= 1 && dy <= 1) {
      const itemId = obj.properties?.item_id || "物品";
      const itemName = getItemName(itemId);
      
      const hintEl = document.getElementById("gather-hint");
      if (!hintEl) {
        const newEl = document.createElement("div");
        newEl.id = "gather-hint";
        newEl.style.cssText = `
          position: absolute;
          bottom: 80px;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(0, 0, 0, 0.8);
          color: #f0c060;
          padding: 8px 16px;
          border-radius: 4px;
          font-size: 14px;
          pointer-events: none;
          z-index: 100;
        `;
        document.getElementById("game-container").appendChild(newEl);
      }
      
      document.getElementById("gather-hint").textContent = `按 E 采集 ${itemName}`;
      return;
    }
  }
  
  const hintEl = document.getElementById("gather-hint");
  if (hintEl) {
    hintEl.remove();
  }
}

function getItemName(itemId) {
  const itemNames = {
    "herb": "草药",
    "mushroom": "蘑菇",
    "iron_ore": "铁矿石",
    "beast_bone": "兽骨"
  };
  return itemNames[itemId] || itemId;
}

function drawHUD(ctx) {
  // 绘制帮助提示（居中显示）
  if (helpVisible) {
    const helpText1 = "WASD/方向键 移动  |  E 与NPC交互  |  I 背包  |  P 角色信息  |  O 菜单";
    const helpText2 = "靠近NPC按E开始冒险吧";

    ctx.font = "bold 13px monospace";
    const width1 = ctx.measureText(helpText1).width;
    const width2 = ctx.measureText(helpText2).width;
    const maxWidth = Math.max(width1, width2) + 40;
    const boxHeight = 60;

    // 居中位置
    const boxX = (canvas.width - maxWidth) / 2;
    const boxY = (canvas.height - boxHeight) / 2;

    // 背景
    ctx.fillStyle = "rgba(0, 0, 0, 0.85)";
    ctx.strokeStyle = "#f0c060";
    ctx.lineWidth = 2;
    ctx.fillRect(boxX, boxY, maxWidth, boxHeight);
    ctx.strokeRect(boxX, boxY, maxWidth, boxHeight);

    // 文字
    ctx.fillStyle = "#f0c060";
    ctx.textAlign = "center";
    ctx.fillText(helpText1, canvas.width / 2, boxY + 25);

    ctx.fillStyle = "#fff";
    ctx.font = "12px monospace";
    ctx.fillText(helpText2, canvas.width / 2, boxY + 45);
  }
}

// 检测传送门自动触发
let portalCooldown = 0;
function checkPortalAutoTransfer() {
  if (portalCooldown > 0) {
    portalCooldown--;
    return;
  }

  const portal = checkPortalCollision();
  if (portal) {
    const props = portal.properties;
    if (props?.target_map) {
      portalCooldown = 60; // 冷却 60 帧
      transferToMap(props.target_map, props.target_x, props.target_y);
    }
  }
}

// 地图切换
async function transferToMap(targetMap, targetX, targetY) {
  try {
    const resp = await fetch("/api/map/transfer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_map: targetMap,
        target_x: targetX,
        target_y: targetY,
      }),
    });
    const data = await resp.json();
    if (resp.ok && data.success) {
      // 更新地图
      currentMap = data.map_data;
      mapObjects = currentMap.objects || [];
      // 更新玩家位置
      setPlayerPosition(targetX, targetY);
      // 重新加载 NPC
      await fetchAllNpcs();
      // 重新加载怪物
      loadMapMonsters();
      // 同步玩家信息
      Object.assign(playerInfo, data.player_info);
      updatePlayerHUD();
      // 更新摄像机
      updateCamera();
    }
  } catch (e) {
    console.error("地图切换失败:", e);
  }
}

// 开始游戏（由开始界面调用）
async function startGame() {
  initCanvas();
  await initMapSystem();
  initWorldMap();
  gameStarted = true;

  // 先加载玩家信息（含位置），再加载地图和 NPC
  await fetchPlayerInfo();

  // 加载怪物配置
  await loadMonstersConfig();

  // 加载当前地图
  const mapId = playerInfo.current_map || "village";
  await loadMap(mapId);

  await fetchAllNpcs();
  loadMapMonsters();
  fetchInventory();
  await fetchAllQuests();
  updateQuestTracker();
  startExploreCheck();

  // 立即更新一次摄像机，确保初始位置正确
  updateCamera();

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
    if (talentPanelOpen) closeTalentPanel();
    if (npcInteractOpen) closeNpcInteract();
    if (combatOpen) endCombat();

    document.getElementById("game-container").style.display = "none";
    document.getElementById("start-screen").classList.remove("hidden");
    // 重新初始化开始界面
    initStartScreen();
  });
}

// O 键切换游戏菜单
document.addEventListener("keydown", (e) => {
  if ((e.key === "o" || e.key === "O") && gameStarted && !combatOpen) {
    toggleGameMenu();
  }
});

// M 键切换大地图
document.addEventListener("keydown", (e) => {
  if ((e.key === "m" || e.key === "M") && gameStarted) {
    console.log("M键按下，gameStarted:", gameStarted);
    toggleWorldMap();
  }
});

// ESC 键关闭大地图
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && worldMapOpen) {
    closeWorldMap();
  }
});

// H 键切换帮助提示显示/隐藏
// document.addEventListener("keydown", (e) => {
//   if ((e.key === "h" || e.key === "H") && gameStarted) {
//     helpVisible = !helpVisible;
//   }
// });
