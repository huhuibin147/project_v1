// 游戏主循环 - 使用管理器模块

// ===== 辅助函数 =====

function updateHudMapName() {
  const el = document.getElementById("hud-map-name");
  if (el && typeof currentMap !== 'undefined' && currentMap) {
    el.textContent = currentMap.name;
  }
}

function drawGatherHint() {
  if (typeof currentMap === 'undefined' || !currentMap || typeof mapObjects === 'undefined' || !mapObjects) return;

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
  if (typeof helpVisible === 'undefined' || !helpVisible) return;
  
  const canvas = GameManager.getCanvas();
  if (!canvas) return;

  const helpText1 = "WASD/方向键 移动  |  E 与NPC交互  |  I 背包  |  P 角色信息  |  O 菜单";
  const helpText2 = "靠近NPC按E开始冒险吧";

  ctx.font = "bold 13px monospace";
  const width1 = ctx.measureText(helpText1).width;
  const width2 = ctx.measureText(helpText2).width;
  const maxWidth = Math.max(width1, width2) + 40;
  const boxHeight = 60;

  const boxX = (canvas.width - maxWidth) / 2;
  const boxY = (canvas.height - boxHeight) / 2;

  ctx.fillStyle = "rgba(0, 0, 0, 0.85)";
  ctx.strokeStyle = "#f0c060";
  ctx.lineWidth = 2;
  ctx.fillRect(boxX, boxY, maxWidth, boxHeight);
  ctx.strokeRect(boxX, boxY, maxWidth, boxHeight);

  ctx.fillStyle = "#f0c060";
  ctx.textAlign = "center";
  ctx.fillText(helpText1, canvas.width / 2, boxY + 25);

  ctx.fillStyle = "#fff";
  ctx.font = "12px monospace";
  ctx.fillText(helpText2, canvas.width / 2, boxY + 45);
}

let portalCooldown = 0;
function checkPortalAutoTransfer() {
  if (portalCooldown > 0) {
    portalCooldown--;
    return;
  }

  if (typeof checkPortalCollision !== 'function') return;
  
  const portal = checkPortalCollision();
  if (portal) {
    const props = portal.properties;
    if (props?.target_map) {
      portalCooldown = 60;
      transferToMap(props.target_map, props.target_x, props.target_y);
    }
  }
}

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
      currentMap = data.map_data;
      mapObjects = currentMap.objects || [];
      if (typeof setPlayerPosition === 'function') setPlayerPosition(targetX, targetY);
      if (typeof fetchAllNpcs === 'function') await fetchAllNpcs();
      if (typeof loadMapMonsters === 'function') loadMapMonsters();
      if (typeof playerInfo !== 'undefined') Object.assign(playerInfo, data.player_info);
      if (typeof updatePlayerHUD === 'function') updatePlayerHUD();
      if (typeof updateCamera === 'function') updateCamera();
    }
  } catch (e) {
    console.error("地图切换失败:", e);
  }
}

// 开始游戏（由开始界面调用）
async function startGame() {
  await GameManager.start();
}

// 页面加载时初始化开始界面，启动游戏循环
initStartScreen();
GameManager.init();

// ===== 游戏菜单 =====

function toggleGameMenu() {
  GameManager.toggleGameMenu();
}

function openGameMenu() {
  GameManager.openGameMenu();
}

function closeGameMenu() {
  GameManager.closeGameMenu();
}

function saveGame() {
  GameManager.saveGame();
}

function returnToMainMenu() {
  GameManager.returnToMainMenu();
}
