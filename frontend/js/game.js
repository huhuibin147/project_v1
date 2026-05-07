// 游戏主循环

const canvas = document.getElementById("game-canvas");
const ctx = canvas.getContext("2d");

canvas.width = MAP_COLS * TILE_SIZE;
canvas.height = MAP_ROWS * TILE_SIZE;

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
  ctx.fillRect(8, startY, 200, 52);
  ctx.fillStyle = "#fff";
  ctx.font = "11px monospace";
  ctx.textAlign = "left";
  ctx.fillText("WASD/方向键 移动", 16, startY + 14);
  ctx.fillText("E 对话  I 背包  P 角色", 16, startY + 28);
  ctx.fillText("靠近NPC按E开始冒险吧", 16, startY + 42);
}

// 启动
fetchAllNpcs().then(() => {
  fetchInventory("blacksmith");
});
fetchPlayerInfo();
requestAnimationFrame(gameLoop);
