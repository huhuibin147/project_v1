// 游戏主循环

const canvas = document.getElementById("game-canvas");
const ctx = canvas.getContext("2d");

canvas.width = MAP_COLS * TILE_SIZE;   // 800
canvas.height = MAP_ROWS * TILE_SIZE;  // 576

// 关闭图像平滑，保持像素风
ctx.imageSmoothingEnabled = false;

let lastTime = 0;

function gameLoop(timestamp) {
  const dt = timestamp - lastTime;
  lastTime = timestamp;

  update(dt);
  render();

  requestAnimationFrame(gameLoop);
}

function update(dt) {
  updatePlayer();
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 绘制地图
  drawMap(ctx);

  // 绘制 NPC（在玩家之前或之后，根据 Y 坐标决定遮挡）
  if (npcState.y <= player.y) {
    drawNPC(ctx);
    drawPlayer(ctx);
  } else {
    drawPlayer(ctx);
    drawNPC(ctx);
  }

  // HUD 信息
  drawHUD(ctx);
}

function drawHUD(ctx) {
  // 左上角操作提示
  ctx.fillStyle = "rgba(0,0,0,0.6)";
  ctx.fillRect(8, 8, 180, 50);
  ctx.fillStyle = "#fff";
  ctx.font = "11px monospace";
  ctx.textAlign = "left";
  ctx.fillText("WASD/方向键 移动", 16, 22);
  ctx.fillText("E 与NPC对话  I 背包", 16, 38);
  ctx.fillText("ESC 关闭面板", 16, 52);
}

// 启动游戏
fetchNPCConfig();
fetchInventory();
requestAnimationFrame(gameLoop);
