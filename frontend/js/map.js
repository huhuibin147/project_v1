// 地图系统 - 数据驱动 + 摄像机 + 交互物件

const TILE_SIZE = 32;

// 当前地图数据
let currentMap = null;
let tileConfig = null;
let mapObjects = [];

// 摄像机系统
const camera = {
  x: 0,
  y: 0,
  viewportWidth: 0,
  viewportHeight: 0,
};

// 粒子系统
const particleSystem = {
  particles: [],
  emit(type, x, y, count = 1) {
    for (let i = 0; i < count; i++) {
      this.particles.push(createParticle(type, x, y));
    }
  },
  update(dt) {
    this.particles = this.particles.filter(p => {
      p.life -= dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      if (p.gravity) p.vy += p.gravity * dt;
      if (p.fade) p.alpha = Math.max(0, p.life / p.maxLife);
      return p.life > 0;
    });
  },
  render(ctx) {
    for (const p of this.particles) {
      ctx.globalAlpha = p.alpha || 1;
      ctx.fillStyle = p.color;
      if (p.shape === "circle") {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      } else {
        ctx.fillRect(p.x - p.size / 2, p.y - p.size / 2, p.size, p.size);
      }
    }
    ctx.globalAlpha = 1;
  }
};

function createParticle(type, x, y) {
  const base = { x, y, life: 1, maxLife: 1, alpha: 1, size: 2, shape: "rect", gravity: 0, fade: true };
  switch (type) {
    case "leaf":
      return { ...base, vx: (Math.random() - 0.5) * 20, vy: 10 + Math.random() * 20, life: 2 + Math.random(), maxLife: 3, color: ["#4a8c3f", "#6abf5a", "#8ee07a"][Math.floor(Math.random() * 3)], size: 2 + Math.random() * 2 };
    case "snow":
      return { ...base, vx: (Math.random() - 0.5) * 10, vy: 15 + Math.random() * 15, life: 3 + Math.random() * 2, maxLife: 5, color: "#fff", size: 1 + Math.random() * 2, gravity: 5 };
    case "sparkle":
      return { ...base, vx: (Math.random() - 0.5) * 30, vy: (Math.random() - 0.5) * 30, life: 0.5 + Math.random() * 0.5, maxLife: 1, color: ["#ffd700", "#fff", "#6bafff"][Math.floor(Math.random() * 3)], size: 1 + Math.random() * 2, fade: true };
    case "dust":
      return { ...base, vx: (Math.random() - 0.5) * 15, vy: -5 - Math.random() * 10, life: 0.3 + Math.random() * 0.3, maxLife: 0.6, color: "#c4a66a", size: 1 + Math.random(), fade: true };
    case "water_splash":
      return { ...base, vx: (Math.random() - 0.5) * 25, vy: -20 - Math.random() * 15, life: 0.4 + Math.random() * 0.3, maxLife: 0.7, color: "#7ab8f0", size: 1 + Math.random() * 2, gravity: 40, fade: true };
    default:
      return { ...base, vx: 0, vy: 0, life: 1, color: "#fff" };
  }
}

// 瓦片渲染器注册表
const tileRenderers = {};

// 注册瓦片渲染器
function registerTileRenderer(name, renderer) {
  tileRenderers[name] = renderer;
}

// 加载瓦片配置
async function loadTileConfig() {
  try {
    const resp = await fetch("/api/map/tiles");
    if (!resp.ok) throw new Error("加载瓦片配置失败");
    tileConfig = await resp.json();
  } catch (e) {
    console.error("加载瓦片配置失败:", e);
    // 使用默认配置
    tileConfig = {};
  }
}

// 加载地图数据
async function loadMap(mapId) {
  try {
    const resp = await fetch(`/api/map/${mapId}`);
    if (!resp.ok) throw new Error(`加载地图 ${mapId} 失败`);
    currentMap = await resp.json();
    mapObjects = currentMap.objects || [];
    return currentMap;
  } catch (e) {
    console.error("加载地图失败:", e);
    return null;
  }
}

// 更新摄像机
function updateCamera() {
  if (!currentMap) return;

  const mapPixelWidth = currentMap.width * TILE_SIZE;
  const mapPixelHeight = currentMap.height * TILE_SIZE;

  // 目标：玩家居中
  let targetX = player.x + PLAYER_SIZE / 2 - camera.viewportWidth / 2;
  let targetY = player.y + PLAYER_SIZE / 2 - camera.viewportHeight / 2;

  // 边界钳制
  if (mapPixelWidth > camera.viewportWidth) {
    // 地图比视口宽，限制在地图范围内
    targetX = Math.max(0, Math.min(targetX, mapPixelWidth - camera.viewportWidth));
  } else {
    // 地图比视口窄，居中显示
    targetX = (mapPixelWidth - camera.viewportWidth) / 2;
  }

  if (mapPixelHeight > camera.viewportHeight) {
    // 地图比视口高，限制在地图范围内
    targetY = Math.max(0, Math.min(targetY, mapPixelHeight - camera.viewportHeight));
  } else {
    // 地图比视口矮，居中显示
    targetY = (mapPixelHeight - camera.viewportHeight) / 2;
  }

  camera.x = targetX;
  camera.y = targetY;
}

// 绘制地图（带视口裁剪）
function drawMap(ctx) {
  if (!currentMap || !tileConfig) return;

  const ground = currentMap.layers?.ground;
  if (!ground) return;

  // 计算可见区域的瓦片范围（考虑摄像机偏移）
  const startCol = Math.max(0, Math.floor(camera.x / TILE_SIZE));
  const endCol = Math.min(currentMap.width, Math.ceil((camera.x + camera.viewportWidth) / TILE_SIZE) + 1);
  const startRow = Math.max(0, Math.floor(camera.y / TILE_SIZE));
  const endRow = Math.min(currentMap.height, Math.ceil((camera.y + camera.viewportHeight) / TILE_SIZE) + 1);

  for (let row = startRow; row < endRow; row++) {
    for (let col = startCol; col < endCol; col++) {
      const tileId = ground[row]?.[col];
      if (tileId === undefined) continue;

      const tileInfo = tileConfig[String(tileId)];
      if (!tileInfo) continue;

      // 使用世界坐标（translate会处理偏移）
      const x = col * TILE_SIZE;
      const y = row * TILE_SIZE;

      // 基础色
      ctx.fillStyle = tileInfo.color || "#000";
      ctx.fillRect(x, y, TILE_SIZE, TILE_SIZE);

      // 像素细节
      const detailName = tileInfo.detail;
      if (detailName && tileRenderers[detailName]) {
        tileRenderers[detailName](ctx, x, y);
      }

      // 阴影效果（树木、建筑等）
      if (!tileInfo.walkable) {
        ctx.fillStyle = "rgba(0, 0, 0, 0.15)";
        ctx.fillRect(x + 2, y + 2, TILE_SIZE, TILE_SIZE);
      }
    }
  }
}

// 绘制环境粒子效果
function drawEnvironmentParticles(ctx) {
  if (!currentMap) return;

  const time = Date.now() / 1000;
  const mapId = currentMap.id;

  // 根据地图类型生成环境粒子
  if (mapId === "forest" && Math.random() < 0.1) {
    const px = camera.x + Math.random() * camera.viewportWidth;
    const py = camera.y - 10;
    particleSystem.emit("leaf", px, py, 1);
  }

  if (mapId === "village" && Math.random() < 0.05) {
    const px = camera.x + Math.random() * camera.viewportWidth;
    const py = camera.y - 10;
    particleSystem.emit("leaf", px, py, 1);
  }

  particleSystem.update(0.016);
  particleSystem.render(ctx);
}

// 绘制交互物件
function drawObjects(ctx) {
  if (!currentMap) return;

  for (const obj of mapObjects) {
    const x = obj.x * TILE_SIZE;
    const y = obj.y * TILE_SIZE;

    if (obj.type === "chest") {
      drawChest(ctx, x, y, obj.state?.opened);
    } else if (obj.type === "portal") {
      drawPortal(ctx, x, y, obj);
    } else if (obj.type === "gather") {
      drawGatherPoint(ctx, x, y, obj);
    } else if (obj.type === "decoration") {
      drawDecoration(ctx, x, y, obj.properties?.sprite);
    }
  }
}

// 宝箱绘制
function drawChest(ctx, x, y, opened) {
  const p = TILE_SIZE / 8;
  if (opened) {
    // 打开的宝箱
    ctx.fillStyle = "#8b6914";
    ctx.fillRect(x + p, y + p * 4, p * 6, p * 3);
    ctx.fillStyle = "#a67c00";
    ctx.fillRect(x + p, y + p * 2, p * 6, p * 2);
    ctx.fillStyle = "#666";
    ctx.fillRect(x + p * 3, y + p * 3, p * 2, p);
  } else {
    // 关闭的宝箱
    ctx.fillStyle = "#8b6914";
    ctx.fillRect(x + p, y + p * 3, p * 6, p * 4);
    ctx.fillStyle = "#a67c00";
    ctx.fillRect(x + p, y + p * 2, p * 6, p * 2);
    ctx.fillStyle = "#ffd700";
    ctx.fillRect(x + p * 3, y + p * 4, p * 2, p * 2);
  }
}

// 传送门绘制
function drawPortal(ctx, x, y, obj) {
  const p = TILE_SIZE / 8;
  const time = Date.now() / 1000;
  const alpha = 0.6 + Math.sin(time * 3) * 0.4;

  // 外圈光晕
  ctx.fillStyle = `rgba(170, 68, 255, ${alpha * 0.3})`;
  ctx.beginPath();
  ctx.arc(x + TILE_SIZE / 2, y + TILE_SIZE / 2, TILE_SIZE / 2 + 4, 0, Math.PI * 2);
  ctx.fill();

  // 传送门主体
  ctx.fillStyle = `rgba(100, 200, 255, ${alpha})`;
  ctx.fillRect(x + p, y + p, p * 6, p * 6);
  ctx.fillStyle = `rgba(150, 230, 255, ${alpha * 0.8})`;
  ctx.fillRect(x + p * 2, y + p * 2, p * 4, p * 4);
  ctx.fillStyle = `rgba(200, 240, 255, ${alpha * 0.6})`;
  ctx.fillRect(x + p * 3, y + p * 3, p * 2, p * 2);

  // 中心亮点
  ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.9})`;
  ctx.beginPath();
  ctx.arc(x + TILE_SIZE / 2, y + TILE_SIZE / 2, 2, 0, Math.PI * 2);
  ctx.fill();

  // 目标名称标签
  if (obj?.properties?.target_map) {
    const mapNames = {
      "village": "青石村",
      "forest": "幽暗森林",
      "dark_cave": "黑暗洞穴",
      "desert_oasis": "沙漠绿洲",
      "royal_city": "王城"
    };
    const name = mapNames[obj.properties.target_map] || obj.properties.target_map;
    
    ctx.save();
    ctx.font = "bold 11px 'Microsoft YaHei', sans-serif";
    ctx.textAlign = "center";
    
    // 标签背景
    const textWidth = ctx.measureText(name).width;
    const labelX = x + TILE_SIZE / 2;
    const labelY = y - 8;
    ctx.fillStyle = "rgba(0, 0, 0, 0.75)";
    ctx.fillRect(labelX - textWidth / 2 - 4, labelY - 10, textWidth + 8, 14);
    ctx.strokeStyle = "rgba(170, 68, 255, 0.6)";
    ctx.lineWidth = 1;
    ctx.strokeRect(labelX - textWidth / 2 - 4, labelY - 10, textWidth + 8, 14);
    
    // 标签文字
    ctx.fillStyle = "#cc88ff";
    ctx.fillText(name, labelX, labelY);
    ctx.restore();
  }
}

// 采集点绘制
function drawGatherPoint(ctx, x, y, obj) {
  const p = TILE_SIZE / 8;
  const itemId = obj?.properties?.item_id;
  const lastGathered = obj?.state?.lastGathered;
  const respawnTime = (obj?.properties?.respawn_time || 60) * 1000;
  const now = Date.now();
  
  // 检查是否在冷却中
  const isOnCooldown = lastGathered && (now - lastGathered) < respawnTime;
  
  if (isOnCooldown) {
    // 冷却中的采集点 - 灰色
    ctx.fillStyle = "#666";
    ctx.fillRect(x + p * 2, y + p * 4, p * 4, p * 3);
    ctx.fillStyle = "#888";
    ctx.fillRect(x + p * 3, y + p * 2, p * 2, p * 3);
    return;
  }
  
  // 根据物品类型显示不同颜色
  if (itemId === "herb") {
    // 草药 - 绿色
    ctx.fillStyle = "#4a8c3f";
    ctx.fillRect(x + p * 2, y + p * 4, p * 4, p * 3);
    ctx.fillStyle = "#6abf5a";
    ctx.fillRect(x + p * 3, y + p * 2, p * 2, p * 3);
    ctx.fillStyle = "#8ee07a";
    ctx.fillRect(x + p * 3, y + p * 2, p, p);
  } else if (itemId === "mushroom") {
    // 蘑菇 - 棕色
    ctx.fillStyle = "#8b6914";
    ctx.fillRect(x + p * 2, y + p * 4, p * 4, p * 3);
    ctx.fillStyle = "#a67c00";
    ctx.fillRect(x + p * 3, y + p * 2, p * 2, p * 3);
    ctx.fillStyle = "#c9a000";
    ctx.fillRect(x + p * 3, y + p * 2, p, p);
  } else if (itemId === "iron_ore") {
    // 铁矿石 - 灰色
    ctx.fillStyle = "#666";
    ctx.fillRect(x + p * 2, y + p * 4, p * 4, p * 3);
    ctx.fillStyle = "#888";
    ctx.fillRect(x + p * 3, y + p * 2, p * 2, p * 3);
    ctx.fillStyle = "#aaa";
    ctx.fillRect(x + p * 3, y + p * 2, p, p);
  } else if (itemId === "beast_bone") {
    // 兽骨 - 白色
    ctx.fillStyle = "#ccc";
    ctx.fillRect(x + p * 2, y + p * 4, p * 4, p * 3);
    ctx.fillStyle = "#eee";
    ctx.fillRect(x + p * 3, y + p * 2, p * 2, p * 3);
    ctx.fillStyle = "#fff";
    ctx.fillRect(x + p * 3, y + p * 2, p, p);
  } else {
    // 默认颜色
    ctx.fillStyle = "#4a8c3f";
    ctx.fillRect(x + p * 2, y + p * 4, p * 4, p * 3);
    ctx.fillStyle = "#6abf5a";
    ctx.fillRect(x + p * 3, y + p * 2, p * 2, p * 3);
    ctx.fillStyle = "#8ee07a";
    ctx.fillRect(x + p * 3, y + p * 2, p, p);
  }
  
  // 添加闪烁效果表示可采集
  const blink = Math.sin(Date.now() / 300) > 0;
  if (blink) {
    ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
    ctx.fillRect(x + p * 3, y + p * 2, p * 2, p * 3);
  }
}

// 装饰物绘制
function drawDecoration(ctx, x, y, sprite) {
  const p = TILE_SIZE / 8;
  if (sprite === "sign") {
    // 告示牌
    ctx.fillStyle = "#8b6914";
    ctx.fillRect(x + p * 3, y + p * 4, p * 2, p * 4);
    ctx.fillStyle = "#a67c00";
    ctx.fillRect(x + p * 1, y + p * 1, p * 6, p * 4);
    ctx.fillStyle = "#333";
    ctx.fillRect(x + p * 2, y + p * 2, p * 4, p);
    ctx.fillRect(x + p * 2, y + p * 4, p * 3, p);
  }
}

// 碰撞检测
function isWalkable(col, row) {
  if (!currentMap) return false;
  if (col < 0 || col >= currentMap.width || row < 0 || row >= currentMap.height) return false;

  const ground = currentMap.layers?.ground;
  if (!ground) return false;

  const tileId = ground[row]?.[col];
  if (tileId === undefined) return false;

  const tileInfo = tileConfig?.[String(tileId)];
  if (!tileInfo) return false;

  return tileInfo.walkable !== false;
}

// 检测玩家所在位置的传送门
function checkPortalCollision() {
  if (!currentMap) return null;

  const playerTileX = Math.floor((player.x + PLAYER_SIZE / 2) / TILE_SIZE);
  const playerTileY = Math.floor((player.y + PLAYER_SIZE / 2) / TILE_SIZE);

  for (const obj of mapObjects) {
    if (obj.type === "portal" && obj.x === playerTileX && obj.y === playerTileY) {
      return obj;
    }
  }
  return null;
}

// 获取玩家附近的可交互物件
function getNearbyInteractableObject() {
  if (!currentMap) return null;

  const playerTileX = Math.floor((player.x + PLAYER_SIZE / 2) / TILE_SIZE);
  const playerTileY = Math.floor((player.y + PLAYER_SIZE / 2) / TILE_SIZE);

  for (const obj of mapObjects) {
    if (obj.type === "portal") continue; // 传送门自动触发，不参与 E 键交互
    const dx = Math.abs(obj.x - playerTileX);
    const dy = Math.abs(obj.y - playerTileY);
    if (dx <= 1 && dy <= 1) {
      return obj;
    }
  }
  return null;
}

// 初始化瓦片渲染器
function initTileRenderers() {
  const p = TILE_SIZE / 8;

  registerTileRenderer("grass", (ctx, x, y) => {
    ctx.fillStyle = "#3d7a33";
    const seed = (x * 7 + y * 13) % 100;
    if (seed < 30) ctx.fillRect(x + p * 2, y + p * 3, p, p);
    if (seed < 50) ctx.fillRect(x + p * 5, y + p * 6, p, p);
    if (seed < 70) ctx.fillRect(x + p * 1, y + p * 6, p, p);
  });

  registerTileRenderer("dirt_road", (ctx, x, y) => {
    ctx.fillStyle = "#b89a5a";
    ctx.fillRect(x + p * 1, y + p * 3, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 5, p * 2, p);
  });

  registerTileRenderer("brick_wall", (ctx, x, y) => {
    ctx.fillStyle = "#7a5c3a";
    ctx.fillRect(x, y + p * 3, TILE_SIZE, p);
    ctx.fillRect(x, y + p * 7, TILE_SIZE, p);
    ctx.fillRect(x + p * 4, y, p, p * 3);
    ctx.fillRect(x + p * 4, y + p * 4, p, p * 3);
  });

  registerTileRenderer("roof", (ctx, x, y) => {
    ctx.fillStyle = "#8b4513";
    for (let i = 0; i < 4; i++) {
      ctx.fillRect(x + i * p * 2, y + (i % 2) * p * 2, p * 2, p * 2);
    }
  });

  registerTileRenderer("tree", (ctx, x, y) => {
    ctx.fillStyle = "#1a3d0f";
    ctx.fillRect(x + p * 2, y, p * 4, p * 3);
    ctx.fillRect(x + p * 1, y + p * 1, p * 6, p * 2);
    ctx.fillStyle = "#5a3a1a";
    ctx.fillRect(x + p * 3, y + p * 3, p * 2, p * 3);
    ctx.fillStyle = "#3a7a2a";
    ctx.fillRect(x + p * 3, y + p * 1, p * 2, p);
  });

  registerTileRenderer("water", (ctx, x, y) => {
    ctx.fillStyle = "#5a9ae8";
    ctx.fillRect(x + p * 1, y + p * 2, p * 3, p);
    ctx.fillRect(x + p * 4, y + p * 5, p * 3, p);
  });

  registerTileRenderer("wood_floor", (ctx, x, y) => {
    // 无额外细节
  });

  registerTileRenderer("fence", (ctx, x, y) => {
    ctx.fillStyle = "#7a6b4e";
    ctx.fillRect(x + p * 1, y + p * 1, p * 2, p * 6);
    ctx.fillRect(x + p * 5, y + p * 1, p * 2, p * 6);
    ctx.fillRect(x + p * 0, y + p * 2, TILE_SIZE, p);
    ctx.fillRect(x + p * 0, y + p * 5, TILE_SIZE, p);
  });

  registerTileRenderer("stone", (ctx, x, y) => {
    ctx.fillStyle = "#666";
    ctx.fillRect(x + p * 2, y + p * 2, p * 4, p * 4);
    ctx.fillStyle = "#aaa";
    ctx.fillRect(x + p * 3, y + p * 2, p * 2, p);
  });

  registerTileRenderer("wood_floor2", (ctx, x, y) => {
    ctx.fillStyle = "#7a6a4a";
    ctx.fillRect(x + p * 0, y + p * 3, TILE_SIZE, p);
    ctx.fillRect(x + p * 0, y + p * 7, TILE_SIZE, p);
  });

  registerTileRenderer("stone_road", (ctx, x, y) => {
    ctx.fillStyle = "#8a8a7a";
    ctx.fillRect(x + p * 0, y + p * 4, TILE_SIZE, p);
    ctx.fillRect(x + p * 4, y + p * 0, p, TILE_SIZE);
  });

  registerTileRenderer("sand", (ctx, x, y) => {
    ctx.fillStyle = "#c4a85a";
    const seed = (x * 11 + y * 7) % 100;
    if (seed < 20) ctx.fillRect(x + p * 2, y + p * 5, p, p);
    if (seed < 40) ctx.fillRect(x + p * 6, y + p * 2, p, p);
  });

  registerTileRenderer("snow", (ctx, x, y) => {
    ctx.fillStyle = "#fff";
    const seed = (x * 13 + y * 11) % 100;
    if (seed < 30) ctx.fillRect(x + p * 3, y + p * 4, p, p);
    if (seed < 50) ctx.fillRect(x + p * 6, y + p * 1, p, p);
  });

  registerTileRenderer("cave_wall", (ctx, x, y) => {
    ctx.fillStyle = "#4a4a4a";
    ctx.fillRect(x + p * 1, y + p * 2, p * 3, p * 2);
    ctx.fillRect(x + p * 5, y + p * 5, p * 2, p * 2);
  });

  registerTileRenderer("cave_floor", (ctx, x, y) => {
    ctx.fillStyle = "#5a5a4a";
    const seed = (x * 9 + y * 13) % 100;
    if (seed < 15) ctx.fillRect(x + p * 3, y + p * 3, p, p);
  });

  registerTileRenderer("flowers", (ctx, x, y) => {
    ctx.fillStyle = "#3d7a33";
    const seed = (x * 7 + y * 13) % 100;
    if (seed < 30) ctx.fillRect(x + p * 2, y + p * 3, p, p);
    const flowerColors = ["#ff6b8a", "#ffd76b", "#6bafff", "#ff9a6b"];
    const fi = (x * 3 + y * 7) % flowerColors.length;
    ctx.fillStyle = flowerColors[fi];
    ctx.fillRect(x + p * 3, y + p * 2, p, p);
    ctx.fillRect(x + p * 6, y + p * 5, p, p);
  });

  registerTileRenderer("river", (ctx, x, y) => {
    const time = Date.now() / 1000;
    const offset = Math.sin(time * 2 + x * 0.1) * 2;
    ctx.fillStyle = "#5a9ae8";
    ctx.fillRect(x + p * 1 + offset, y + p * 2, p * 3, p);
    ctx.fillRect(x + p * 4 - offset, y + p * 5, p * 3, p);
    ctx.fillStyle = "#7ab8f0";
    ctx.fillRect(x + p * 2 + offset, y + p * 3, p * 2, p);
  });

  registerTileRenderer("bridge", (ctx, x, y) => {
    ctx.fillStyle = "#7a6a4a";
    ctx.fillRect(x + p * 0, y + p * 0, TILE_SIZE, p);
    ctx.fillRect(x + p * 0, y + p * 7, TILE_SIZE, p);
    ctx.fillStyle = "#6a5a3a";
    ctx.fillRect(x + p * 1, y + p * 1, p * 2, p * 6);
    ctx.fillRect(x + p * 5, y + p * 1, p * 2, p * 6);
  });

  registerTileRenderer("bush", (ctx, x, y) => {
    ctx.fillStyle = "#2a5a1a";
    ctx.fillRect(x + p * 1, y + p * 3, p * 6, p * 4);
    ctx.fillStyle = "#3a7a2a";
    ctx.fillRect(x + p * 2, y + p * 2, p * 4, p * 2);
    ctx.fillStyle = "#4a8a3a";
    ctx.fillRect(x + p * 3, y + p * 1, p * 2, p);
  });

  registerTileRenderer("dead_tree", (ctx, x, y) => {
    ctx.fillStyle = "#4a3a2a";
    ctx.fillRect(x + p * 3, y + p * 2, p * 2, p * 5);
    ctx.fillRect(x + p * 1, y + p * 3, p * 2, p);
    ctx.fillRect(x + p * 5, y + p * 2, p * 2, p);
    ctx.fillRect(x + p * 2, y + p * 1, p, p);
  });

  registerTileRenderer("flower_patch", (ctx, x, y) => {
    ctx.fillStyle = "#3d7a33";
    const seed = (x * 7 + y * 13) % 100;
    if (seed < 40) ctx.fillRect(x + p * 2, y + p * 3, p, p);
    const time = Date.now() / 1000;
    const bloom = 0.5 + Math.sin(time * 2 + x + y) * 0.5;
    ctx.fillStyle = `rgba(255, 107, 138, ${bloom})`;
    ctx.fillRect(x + p * 3, y + p * 2, p, p);
    ctx.fillStyle = `rgba(255, 215, 107, ${bloom})`;
    ctx.fillRect(x + p * 5, y + p * 4, p, p);
  });

  registerTileRenderer("deep_grass", (ctx, x, y) => {
    ctx.fillStyle = "#2a6a23";
    const seed = (x * 7 + y * 13) % 100;
    if (seed < 40) ctx.fillRect(x + p * 2, y + p * 3, p, p * 2);
    if (seed < 60) ctx.fillRect(x + p * 5, y + p * 5, p, p * 2);
    if (seed < 80) ctx.fillRect(x + p * 1, y + p * 6, p, p);
  });

  registerTileRenderer("stone_tile", (ctx, x, y) => {
    ctx.fillStyle = "#7a7a6a";
    ctx.fillRect(x + p * 0, y + p * 0, p * 4, p * 4);
    ctx.fillRect(x + p * 4, y + p * 4, p * 4, p * 4);
    ctx.fillStyle = "#9a9a8a";
    ctx.fillRect(x + p * 1, y + p * 1, p * 2, p * 2);
    ctx.fillRect(x + p * 5, y + p * 5, p * 2, p * 2);
  });

  registerTileRenderer("lava", (ctx, x, y) => {
    const time = Date.now() / 1000;
    const glow = 0.5 + Math.sin(time * 3 + x * 0.2) * 0.3;
    ctx.fillStyle = `rgba(255, 100, 0, ${glow})`;
    ctx.fillRect(x + p * 1, y + p * 2, p * 3, p * 2);
    ctx.fillRect(x + p * 4, y + p * 5, p * 3, p * 2);
    ctx.fillStyle = `rgba(255, 200, 0, ${glow * 0.7})`;
    ctx.fillRect(x + p * 2, y + p * 3, p * 2, p);
  });

  registerTileRenderer("ice", (ctx, x, y) => {
    const time = Date.now() / 1000;
    const shimmer = 0.3 + Math.sin(time * 2 + x * 0.3 + y * 0.3) * 0.2;
    ctx.fillStyle = `rgba(255, 255, 255, ${shimmer})`;
    ctx.fillRect(x + p * 1, y + p * 2, p * 3, p);
    ctx.fillRect(x + p * 4, y + p * 5, p * 3, p);
    ctx.fillStyle = "#a0c8e0";
    ctx.fillRect(x + p * 2, y + p * 3, p * 2, p);
  });
}

// 初始化地图系统
async function initMapSystem() {
  initTileRenderers();
  await loadTileConfig();
  initMinimap();
}

// ===== 实时小地图 =====

const MINIMAP_W = 160;
const MINIMAP_H = 120;
let minimapCanvas, minimapCtx;
let minimapTileCache = null;

function initMinimap() {
  minimapCanvas = document.getElementById("minimap-canvas");
  minimapCtx = minimapCanvas.getContext("2d");
  minimapCtx.imageSmoothingEnabled = false;
}

function renderMinimap() {
  if (!currentMap || !tileConfig || !minimapCtx) return;

  const ground = currentMap.layers?.ground;
  if (!ground) return;

  const mapW = currentMap.width;
  const mapH = currentMap.height;

  if (!minimapTileCache || minimapTileCache.mapId !== currentMap.id) {
    minimapTileCache = { mapId: currentMap.id, data: null };
    const imgData = minimapCtx.createImageData(MINIMAP_W, MINIMAP_H);
    const scaleX = mapW / MINIMAP_W;
    const scaleY = mapH / MINIMAP_H;

    for (let my = 0; my < MINIMAP_H; my++) {
      for (let mx = 0; mx < MINIMAP_W; mx++) {
        const tileCol = Math.floor(mx * scaleX);
        const tileRow = Math.floor(my * scaleY);
        const tileId = ground[tileRow]?.[tileCol];
        const tileInfo = tileConfig?.[String(tileId)];
        const color = tileInfo?.color || "#000";
        const idx = (my * MINIMAP_W + mx) * 4;
        const r = parseInt(color.slice(1, 3), 16);
        const g = parseInt(color.slice(3, 5), 16);
        const b = parseInt(color.slice(5, 7), 16);
        imgData.data[idx] = r;
        imgData.data[idx + 1] = g;
        imgData.data[idx + 2] = b;
        imgData.data[idx + 3] = 255;
      }
    }
    minimapTileCache.data = imgData;
  }

  minimapCtx.putImageData(minimapTileCache.data, 0, 0);

  const scaleX = MINIMAP_W / mapW;
  const scaleY = MINIMAP_H / mapH;

  const portals = mapObjects.filter(o => o.type === "portal");
  for (const p of portals) {
    minimapCtx.fillStyle = "#aa44ff";
    minimapCtx.fillRect(Math.floor(p.x * scaleX), Math.floor(p.y * scaleY), 2, 2);
  }

  if (typeof npcs !== "undefined") {
    for (const n of npcs) {
      minimapCtx.fillStyle = "#44cc44";
      minimapCtx.fillRect(Math.floor(n.x * scaleX), Math.floor(n.y * scaleY), 2, 2);
    }
  }

  if (typeof mapMonsters !== "undefined") {
    for (const m of mapMonsters) {
      if (m.alive) {
        minimapCtx.fillStyle = "#ff4444";
        minimapCtx.fillRect(Math.floor(m.x * scaleX), Math.floor(m.y * scaleY), 2, 2);
      }
    }
  }

  const playerTileX = Math.floor((player.x + PLAYER_SIZE / 2) / TILE_SIZE);
  const playerTileY = Math.floor((player.y + PLAYER_SIZE / 2) / TILE_SIZE);
  const px = Math.floor(playerTileX * scaleX);
  const py = Math.floor(playerTileY * scaleY);

  const blink = Math.sin(Date.now() / 200) > 0;
  if (blink) {
    minimapCtx.fillStyle = "rgba(68, 136, 255, 0.3)";
    minimapCtx.beginPath();
    minimapCtx.arc(px + 1, py + 1, 4, 0, Math.PI * 2);
    minimapCtx.fill();
  }
  minimapCtx.fillStyle = "#4488ff";
  minimapCtx.fillRect(px, py, 3, 3);

  const mapName = currentMap.name || "";
  minimapCtx.fillStyle = "rgba(0,0,0,0.6)";
  minimapCtx.fillRect(0, 0, MINIMAP_W, 14);
  minimapCtx.fillStyle = "#f0c060";
  minimapCtx.font = "bold 10px monospace";
  minimapCtx.textAlign = "center";
  minimapCtx.fillText(mapName, MINIMAP_W / 2, 11);
}

// ===== 大地图 (M 键) =====

let worldMapOpen = false;
let worldMapCanvas, worldMapCtx;
let exploredTiles = new Set();

function initWorldMap() {
  worldMapCanvas = document.getElementById("worldmap-canvas");
  worldMapCtx = worldMapCanvas.getContext("2d");
  worldMapCtx.imageSmoothingEnabled = false;
}

function toggleWorldMap() {
  console.log("切换大地图，当前状态:", worldMapOpen, "游戏状态:", gameStarted);
  if (worldMapOpen) {
    closeWorldMap();
  } else {
    openWorldMap();
  }
}

function openWorldMap() {
  if (!currentMap) {
    console.log("无法打开大地图：当前地图未加载");
    return;
  }
  if (dialogueOpen || inventoryOpen || shopOpen || playerInfoOpen || npcInteractOpen || gameMenuOpen || combatOpen || questOpen || healPanelOpen || skillLearnPanelOpen || talentPanelOpen) {
    console.log("无法打开大地图：有其他面板打开");
    return;
  }
  worldMapOpen = true;
  const panel = document.getElementById("worldmap-panel");
  panel.classList.add("active");
  renderWorldMap();
}

function closeWorldMap() {
  worldMapOpen = false;
  document.getElementById("worldmap-panel").classList.remove("active");
}

function renderWorldMap() {
  if (!currentMap || !tileConfig || !worldMapCtx) return;

  const ground = currentMap.layers?.ground;
  if (!ground) return;

  const mapW = currentMap.width;
  const mapH = currentMap.height;
  const canvasW = worldMapCanvas.width;
  const canvasH = worldMapCanvas.height;

  worldMapCtx.fillStyle = "#111";
  worldMapCtx.fillRect(0, 0, canvasW, canvasH);

  const scaleX = canvasW / mapW;
  const scaleY = canvasH / mapH;

  for (let my = 0; my < canvasH; my++) {
    for (let mx = 0; mx < canvasW; mx++) {
      const tileCol = Math.floor(mx / scaleX);
      const tileRow = Math.floor(my / scaleY);
      const tileId = ground[tileRow]?.[tileCol];
      const tileInfo = tileConfig?.[String(tileId)];
      let color = tileInfo?.color || "#000";

      const tileKey = `${tileCol},${tileRow}`;
      if (!exploredTiles.has(tileKey)) {
        const r = parseInt(color.slice(1, 3), 16);
        const g = parseInt(color.slice(3, 5), 16);
        const b = parseInt(color.slice(5, 7), 16);
        color = `rgb(${Math.floor(r * 0.3)},${Math.floor(g * 0.3)},${Math.floor(b * 0.3)})`;
      }

      worldMapCtx.fillStyle = color;
      worldMapCtx.fillRect(mx, my, 1, 1);
    }
  }

  const portals = mapObjects.filter(o => o.type === "portal");
  for (const p of portals) {
    const px = Math.floor(p.x * scaleX);
    const py = Math.floor(p.y * scaleY);
    worldMapCtx.fillStyle = "#aa44ff";
    worldMapCtx.beginPath();
    worldMapCtx.arc(px, py, 4, 0, Math.PI * 2);
    worldMapCtx.fill();
    worldMapCtx.strokeStyle = "#cc88ff";
    worldMapCtx.lineWidth = 1;
    worldMapCtx.stroke();

    if (p.properties?.target_map) {
      worldMapCtx.fillStyle = "rgba(170, 68, 255, 0.5)";
      worldMapCtx.font = "9px monospace";
      worldMapCtx.textAlign = "center";
      worldMapCtx.fillText(p.properties.target_map, px, py - 6);
    }
  }

  if (typeof npcs !== "undefined") {
    for (const n of npcs) {
      worldMapCtx.fillStyle = "#44cc44";
      worldMapCtx.beginPath();
      worldMapCtx.arc(Math.floor(n.x * scaleX), Math.floor(n.y * scaleY), 3, 0, Math.PI * 2);
      worldMapCtx.fill();
    }
  }

  if (typeof mapMonsters !== "undefined") {
    for (const m of mapMonsters) {
      if (m.alive) {
        worldMapCtx.fillStyle = "#ff4444";
        worldMapCtx.beginPath();
        worldMapCtx.arc(Math.floor(m.x * scaleX), Math.floor(m.y * scaleY), 2, 0, Math.PI * 2);
        worldMapCtx.fill();
      }
    }
  }

  const playerTileX = Math.floor((player.x + PLAYER_SIZE / 2) / TILE_SIZE);
  const playerTileY = Math.floor((player.y + PLAYER_SIZE / 2) / TILE_SIZE);
  const px = Math.floor(playerTileX * scaleX);
  const py = Math.floor(playerTileY * scaleY);

  const pulse = 3 + Math.sin(Date.now() / 300) * 2;
  worldMapCtx.fillStyle = "rgba(68, 136, 255, 0.3)";
  worldMapCtx.beginPath();
  worldMapCtx.arc(px, py, pulse + 3, 0, Math.PI * 2);
  worldMapCtx.fill();

  worldMapCtx.fillStyle = "#4488ff";
  worldMapCtx.beginPath();
  worldMapCtx.moveTo(px, py - pulse);
  worldMapCtx.lineTo(px - pulse * 0.7, py + pulse * 0.5);
  worldMapCtx.lineTo(px + pulse * 0.7, py + pulse * 0.5);
  worldMapCtx.closePath();
  worldMapCtx.fill();

  worldMapCtx.strokeStyle = "#fff";
  worldMapCtx.lineWidth = 1;
  worldMapCtx.stroke();

  document.getElementById("worldmap-title").textContent = currentMap.name + " - 世界地图";
  document.getElementById("worldmap-coords").textContent = `坐标: (${playerTileX}, ${playerTileY})`;
}

function recordExploredTile() {
  if (!currentMap) return;
  const tileX = Math.floor((player.x + PLAYER_SIZE / 2) / TILE_SIZE);
  const tileY = Math.floor((player.y + PLAYER_SIZE / 2) / TILE_SIZE);
  const key = `${tileX},${tileY}`;
  if (!exploredTiles.has(key)) {
    exploredTiles.add(key);
  }
  for (let dy = -1; dy <= 1; dy++) {
    for (let dx = -1; dx <= 1; dx++) {
      exploredTiles.add(`${tileX + dx},${tileY + dy}`);
    }
  }
}
