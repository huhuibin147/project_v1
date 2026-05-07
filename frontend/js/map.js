// 地图数据与渲染
// 瓦片类型：0=草地 1=泥土路 2=房屋墙 3=屋顶 4=树木 5=水面 6=铁匠铺地板 7=栅栏 8=石头 9=杂货铺地板

const TILE_SIZE = 32;
const MAP_COLS = 25;
const MAP_ROWS = 18;

// 地图数据 (25x18)
const mapData = [
  [4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4],
  [4,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,4],
  [4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4],
  [4,0,0,2,2,2,0,0,0,0,0,0,0,0,0,0,0,2,2,2,0,0,0,0,4],
  [4,0,0,2,6,2,0,0,0,1,1,1,1,1,0,0,0,2,9,2,0,0,0,0,4],
  [4,0,0,2,6,2,0,0,0,1,0,0,0,1,0,0,0,2,2,2,0,0,0,0,4],
  [4,0,0,2,2,2,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,4],
  [4,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,4,0,0,4],
  [4,0,0,0,1,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,4],
  [4,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4],
  [4,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,2,2,2,0,0,0,0,4],
  [4,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,2,3,2,0,0,0,0,4],
  [4,0,0,0,0,0,7,7,0,1,0,0,0,0,0,0,0,2,2,2,0,0,0,0,4],
  [4,0,0,0,0,0,7,7,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,4],
  [4,0,0,0,0,0,0,0,0,0,0,0,8,0,0,0,0,0,1,0,0,0,0,0,4],
  [4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,4],
  [4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4],
  [4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4],
];

// 碰撞数据：true 表示不可通行
const collisionMap = mapData.map(row =>
  row.map(tile => [2, 3, 4, 5, 7, 8].includes(tile))
);

const tileColors = {
  0: "#4a8c3f", // 草地
  1: "#c4a66a", // 泥土路
  2: "#8b6b4a", // 房屋墙
  3: "#a0522d", // 屋顶
  4: "#2d5a1e", // 树木
  5: "#3b7dd8", // 水面
  6: "#7a6b5a", // 铁匠铺地板
  7: "#9e8b6e", // 栅栏
  8: "#888888", // 石头
  9: "#8a7a5a", // 杂货铺地板
};

function drawMap(ctx) {
  for (let row = 0; row < MAP_ROWS; row++) {
    for (let col = 0; col < MAP_COLS; col++) {
      const tile = mapData[row][col];
      const x = col * TILE_SIZE;
      const y = row * TILE_SIZE;

      // 基础色
      ctx.fillStyle = tileColors[tile] || "#000";
      ctx.fillRect(x, y, TILE_SIZE, TILE_SIZE);

      // 像素细节
      drawTileDetail(ctx, tile, x, y);
    }
  }
}

function drawTileDetail(ctx, tile, x, y) {
  const s = TILE_SIZE;
  const p = s / 8; // 像素单元

  if (tile === 0) {
    // 草地 - 随机深色草点
    ctx.fillStyle = "#3d7a33";
    const seed = (x * 7 + y * 13) % 100;
    if (seed < 30) ctx.fillRect(x + p * 2, y + p * 3, p, p);
    if (seed < 50) ctx.fillRect(x + p * 5, y + p * 6, p, p);
    if (seed < 70) ctx.fillRect(x + p * 1, y + p * 6, p, p);
  } else if (tile === 1) {
    // 泥土路 - 车辙痕迹
    ctx.fillStyle = "#b89a5a";
    ctx.fillRect(x + p * 1, y + p * 3, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 5, p * 2, p);
  } else if (tile === 2) {
    // 房屋墙 - 砖块纹理
    ctx.fillStyle = "#7a5c3a";
    ctx.fillRect(x, y + p * 3, s, p);
    ctx.fillRect(x, y + p * 7, s, p);
    ctx.fillRect(x + p * 4, y, p, p * 3);
    ctx.fillRect(x + p * 4, y + p * 4, p, p * 3);
  } else if (tile === 3) {
    // 屋顶 - 瓦片纹理
    ctx.fillStyle = "#8b4513";
    for (let i = 0; i < 4; i++) {
      ctx.fillRect(x + i * p * 2, y + (i % 2) * p * 2, p * 2, p * 2);
    }
  } else if (tile === 4) {
    // 树木 - 树冠和树干
    ctx.fillStyle = "#1a3d0f";
    ctx.fillRect(x + p * 2, y, p * 4, p * 3);
    ctx.fillRect(x + p * 1, y + p * 1, p * 6, p * 2);
    ctx.fillStyle = "#5a3a1a";
    ctx.fillRect(x + p * 3, y + p * 3, p * 2, p * 3);
    // 高光
    ctx.fillStyle = "#3a7a2a";
    ctx.fillRect(x + p * 3, y + p * 1, p * 2, p);
  } else if (tile === 5) {
    // 水面 - 波纹
    ctx.fillStyle = "#5a9ae8";
    ctx.fillRect(x + p * 1, y + p * 2, p * 3, p);
    ctx.fillRect(x + p * 4, y + p * 5, p * 3, p);
  } else if (tile === 7) {
    // 栅栏
    ctx.fillStyle = "#7a6b4e";
    ctx.fillRect(x + p * 1, y + p * 1, p * 2, p * 6);
    ctx.fillRect(x + p * 5, y + p * 1, p * 2, p * 6);
    ctx.fillRect(x + p * 0, y + p * 2, s, p);
    ctx.fillRect(x + p * 0, y + p * 5, s, p);
  } else if (tile === 8) {
    // 石头
    ctx.fillStyle = "#666";
    ctx.fillRect(x + p * 2, y + p * 2, p * 4, p * 4);
    ctx.fillStyle = "#aaa";
    ctx.fillRect(x + p * 3, y + p * 2, p * 2, p);
  } else if (tile === 9) {
    // 杂货铺地板 - 木纹
    ctx.fillStyle = "#7a6a4a";
    ctx.fillRect(x + p * 0, y + p * 3, s, p);
    ctx.fillRect(x + p * 0, y + p * 7, s, p);
  }
}

function isWalkable(col, row) {
  if (col < 0 || col >= MAP_COLS || row < 0 || row >= MAP_ROWS) return false;
  return !collisionMap[row][col];
}
