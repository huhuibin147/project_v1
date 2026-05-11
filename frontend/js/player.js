// 玩家角色控制

const PLAYER_SPEED = 3;
const PLAYER_SIZE = TILE_SIZE;

const player = {
  x: 25 * TILE_SIZE,   // 初始位置（路上）
  y: 20 * TILE_SIZE,
  width: PLAYER_SIZE,
  height: PLAYER_SIZE,
  direction: "down",   // up/down/left/right
  frame: 0,
  moving: false,
  color: "#4488ff",
  name: "冒险者",      // 玩家名字
};

// 设置玩家位置（瓦片坐标）
function setPlayerPosition(tileX, tileY) {
  player.x = tileX * TILE_SIZE;
  player.y = tileY * TILE_SIZE;
}

// 获取玩家位置（瓦片坐标）
function getPlayerTilePosition() {
  return {
    x: Math.floor((player.x + PLAYER_SIZE / 2) / TILE_SIZE),
    y: Math.floor((player.y + PLAYER_SIZE / 2) / TILE_SIZE)
  };
}

// 保存玩家位置到服务器
async function savePlayerPosition() {
  const pos = getPlayerTilePosition();
  try {
    await fetch("/api/player/position", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x: pos.x, y: pos.y }),
    });
  } catch (e) {
    console.error("保存位置失败:", e);
  }
}

const keys = {};

document.addEventListener("keydown", (e) => {
  keys[e.key.toLowerCase()] = true;
  // 方向键也处理
  if (["arrowup","arrowdown","arrowleft","arrowright"].includes(e.key.toLowerCase())) {
    keys[e.key.toLowerCase()] = true;
  }
});

document.addEventListener("keyup", (e) => {
  keys[e.key.toLowerCase()] = false;
  if (["arrowup","arrowdown","arrowleft","arrowright"].includes(e.key.toLowerCase())) {
    keys[e.key.toLowerCase()] = false;
  }
});

function updatePlayer() {
  if (dialogueOpen || inventoryOpen || shopOpen || playerInfoOpen || npcInteractOpen || gameMenuOpen || combatOpen || questOpen || healPanelOpen || skillLearnPanelOpen || talentPanelOpen) return;

  let dx = 0, dy = 0;

  if (keys["w"] || keys["arrowup"])    { dy = -PLAYER_SPEED; player.direction = "up"; }
  if (keys["s"] || keys["arrowdown"])  { dy = PLAYER_SPEED;  player.direction = "down"; }
  if (keys["a"] || keys["arrowleft"])  { dx = -PLAYER_SPEED; player.direction = "left"; }
  if (keys["d"] || keys["arrowright"]) { dx = PLAYER_SPEED;  player.direction = "right"; }

  if (dx !== 0 || dy !== 0) {
    player.moving = true;
    player.frame++;
  } else {
    player.moving = false;
  }

  // 碰撞检测：分别检测 X 和 Y 方向
  const newCol = Math.floor((player.x + dx + PLAYER_SIZE / 2) / TILE_SIZE);
  const newRow = Math.floor((player.y + PLAYER_SIZE / 2) / TILE_SIZE);
  if (isWalkable(newCol, newRow)) {
    player.x += dx;
  }

  const newCol2 = Math.floor((player.x + PLAYER_SIZE / 2) / TILE_SIZE);
  const newRow2 = Math.floor((player.y + dy + PLAYER_SIZE / 2) / TILE_SIZE);
  if (isWalkable(newCol2, newRow2)) {
    player.y += dy;
  }

  // 碰撞检测：碰到怪物触发战斗
  if (typeof checkMonsterCollision === "function") {
    const hitMonster = checkMonsterCollision();
    if (hitMonster) {
      initiateCombat(hitMonster.instance_id);
    }
  }
}

function drawPlayer(ctx) {
  const x = Math.round(player.x);
  const y = Math.round(player.y);
  const s = TILE_SIZE;
  const p = s / 8;
  const bounce = player.moving ? Math.sin(player.frame * 0.3) * 2 : 0;

  // 阴影
  ctx.fillStyle = "rgba(0,0,0,0.2)";
  ctx.fillRect(x + p * 2, y + s - p * 2, p * 4, p * 1);

  // 身体
  ctx.fillStyle = player.color;
  ctx.fillRect(x + p * 2, y + p * 3 + bounce, p * 4, p * 4);

  // 头部
  ctx.fillStyle = "#ffd4a0";
  ctx.fillRect(x + p * 2, y + p * 1 + bounce, p * 4, p * 3);

  // 头发
  ctx.fillStyle = "#5a3a1a";
  ctx.fillRect(x + p * 2, y + p * 0 + bounce, p * 4, p * 2);

  // 眼睛
  ctx.fillStyle = "#333";
  if (player.direction === "down") {
    ctx.fillRect(x + p * 3, y + p * 2 + bounce, p, p);
    ctx.fillRect(x + p * 5, y + p * 2 + bounce, p, p);
  } else if (player.direction === "left") {
    ctx.fillRect(x + p * 2, y + p * 2 + bounce, p, p);
  } else if (player.direction === "right") {
    ctx.fillRect(x + p * 5, y + p * 2 + bounce, p, p);
  } else {
    // up - 看不到脸
  }

  // 腿
  ctx.fillStyle = "#3a5a8a";
  if (player.moving) {
    const legOffset = Math.sin(player.frame * 0.3) > 0 ? p : -p;
    ctx.fillRect(x + p * 2, y + p * 7 + bounce, p * 2, p * 1);
    ctx.fillRect(x + p * 4, y + p * 7 + bounce + legOffset, p * 2, p * 1);
  } else {
    ctx.fillRect(x + p * 2, y + p * 7 + bounce, p * 2, p * 1);
    ctx.fillRect(x + p * 4, y + p * 7 + bounce, p * 2, p * 1);
  }

  // 名字标签
  ctx.fillStyle = "rgba(0,0,0,0.6)";
  ctx.font = "10px monospace";
  const nameWidth = ctx.measureText(player.name).width + 10;
  ctx.fillRect(x + s / 2 - nameWidth / 2, y - 14, nameWidth, 14);
  ctx.fillStyle = "#6bafff";
  ctx.textAlign = "center";
  ctx.fillText(player.name, x + s / 2, y - 4);
}
