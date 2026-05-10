# 地图与美术系统设计文档

## 概述

本文档描述游戏地图系统、美术渲染系统、建筑类型系统的设计方案。目标是提升游戏视觉表现力，丰富地图内容，增强玩家沉浸感。

---

## 一、美术系统升级

### 1.1 瓦片系统升级

#### 当前问题
- 瓦片仅使用纯色填充 + 简单像素细节
- 缺少层次感和动画效果
- 瓦片类型有限，场景单调

#### 升级方案

**多层瓦片渲染：**
```
地面层（Ground） → 装饰层（Decoration） → 物件层（Object）
```

**瓦片类型扩展：**

| ID | 名称 | 颜色 | 可通行 | 细节类型 | 动画 |
|----|------|------|--------|----------|------|
| 0 | 草地 | #4a8c3f | 是 | grass | 微风摇摆 |
| 1 | 泥土路 | #c4a66a | 是 | dirt_road | — |
| 2 | 房屋墙 | #8b6b4a | 否 | brick_wall | — |
| 3 | 屋顶 | #a0522d | 否 | roof | — |
| 4 | 树木 | #2d5a1e | 否 | tree | 树叶摇曳 |
| 5 | 水面 | #3b7dd8 | 否 | water | 波纹动画 |
| 6 | 木地板 | #7a6b5a | 是 | wood_floor | — |
| 7 | 栅栏 | #9e8b6e | 否 | fence | — |
| 8 | 石头 | #888888 | 否 | stone | — |
| 9 | 木地板2 | #8a7a5a | 是 | wood_floor2 | — |
| 10 | 石板路 | #9a9a8a | 是 | stone_road | — |
| 11 | 沙地 | #d4b86a | 是 | sand | — |
| 12 | 雪地 | #e8e8f0 | 是 | snow | 飘雪 |
| 13 | 岩壁 | #5a5a5a | 否 | cave_wall | — |
| 14 | 岩地 | #6a6a5a | 是 | cave_floor | — |
| 15 | 花朵 | #4a8c3f | 是 | flowers | 花朵摇曳 |
| 16 | 小河 | #3b7dd8 | 否 | river | 水流动画 |
| 17 | 木桥 | #8a7a5a | 是 | bridge | — |
| 18 | 花丛 | #4a8c3f | 是 | flower_bush | — |
| 19 | 枯树 | #5a4a3a | 否 | dead_tree | — |
| 20 | 灌木 | #3a6a2a | 否 | bush | — |

**新增动画系统：**
- 水面波纹：使用正弦函数模拟波纹
- 树叶摇曳：随机偏移模拟风吹效果
- 飘雪效果：随机生成雪花粒子
- 花朵摇曳：轻微摆动

### 1.2 光影系统

**基础光照：**
- 全局环境光：轻微暖色调
- 阴影：建筑物、树木投射简单阴影
- 高光：水面、金属物件反射

**实现方案：**
```javascript
// 阴影层（半透明黑色覆盖）
function drawShadowLayer(ctx, x, y, height) {
  ctx.fillStyle = `rgba(0, 0, 0, ${0.1 * height})`;
  ctx.fillRect(x + 4, y + 4, TILE_SIZE, TILE_SIZE);
}

// 高光层
function drawHighlight(ctx, x, y, intensity) {
  ctx.fillStyle = `rgba(255, 255, 255, ${intensity * 0.1})`;
  ctx.fillRect(x, y, TILE_SIZE, TILE_SIZE);
}
```

### 1.3 粒子系统

**粒子类型：**

| 类型 | 触发条件 | 效果 |
|------|----------|------|
| 落叶 | 草地/森林区域 | 随机飘落 |
| 雪花 | 雪地场景 | 持续飘落 |
| 水花 | 水面/河流 | 波纹扩散 |
| 萤火虫 | 夜晚森林 | 随机闪烁 |
| 尘土 | 玩家移动 | 脚步扬起 |

**粒子系统架构：**
```javascript
class ParticleSystem {
  constructor() {
    this.particles = [];
  }
  
  emit(type, x, y, count = 1) {
    for (let i = 0; i < count; i++) {
      this.particles.push(createParticle(type, x, y));
    }
  }
  
  update(dt) {
    this.particles = this.particles.filter(p => {
      p.life -= dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      return p.life > 0;
    });
  }
  
  render(ctx) {
    for (const p of this.particles) {
      renderParticle(ctx, p);
    }
  }
}
```

### 1.4 天气系统

| 天气 | 效果 | 适用场景 |
|------|------|----------|
| 晴天 | 明亮色调，轻微光晕 | 所有场景 |
| 阴天 | 灰暗色调，无光晕 | 所有场景 |
| 雨天 | 雨滴粒子，水面涟漪 | 村庄、森林 |
| 雪天 | 雪花粒子，地面积雪 | 雪地场景 |

---

## 二、地图脚本系统升级

### 2.1 地图事件系统

**事件类型：**

| 事件类型 | 触发条件 | 效果 |
|----------|----------|------|
| onEnter | 玩家进入地图 | 播放入场动画/音乐 |
| onExit | 玩家离开地图 | 播放退场动画 |
| onZoneEnter | 玩家进入特定区域 | 触发对话/任务 |
| onTimeChange | 游戏时间变化 | 切换日夜 |
| onObjectInteract | 玩家交互物件 | 执行脚本 |

**事件配置格式：**
```json
{
  "events": [
    {
      "type": "onEnter",
      "actions": [
        {"type": "showText", "text": "你来到了青石村"},
        {"type": "playSound", "sound": "village_bgm"}
      ]
    },
    {
      "type": "onZoneEnter",
      "zone": {"x": 10, "y": 5, "width": 5, "height": 5},
      "actions": [
        {"type": "showText", "text": "这里是铁匠铺"}
      ]
    }
  ]
}
```

### 2.2 地图区域系统

**区域定义：**
```json
{
  "zones": [
    {
      "id": "blacksmith_area",
      "name": "铁匠铺区域",
      "bounds": {"x": 10, "y": 5, "width": 8, "height": 6},
      "properties": {
        "bgm": "blacksmith_bgm",
        "lighting": "warm",
        "npc_spawn": "blacksmith"
      }
    }
  ]
}
```

---

## 三、建筑类型系统升级

### 3.1 建筑类型定义

| 建筑类型 | 外观特征 | 功能 | 内部结构 |
|----------|----------|------|----------|
| 民居 | 木质结构，斜屋顶 | 玩家休息 | 床、桌子、椅子 |
| 铁匠铺 | 石质结构，烟囱 | 锻造/买卖武器 | 熔炉、铁砧、武器架 |
| 商店 | 木质结构，招牌 | 买卖物品 | 货架、柜台 |
| 神殿 | 石质结构，尖顶 | 治疗/净化 | 祭坛、圣水池 |
| 学院 | 石质结构，高塔 | 学习技能 | 书架、讲台 |
| 酒馆 | 木质结构，大招牌 | 休息/情报 | 吧台、桌椅 |
| 仓库 | 简易木质结构 | 存储物品 | 货架、箱子 |
| 传送阵 | 石质基座，魔法阵 | 地图传送 | 魔法阵图案 |

### 3.2 建筑结构配置

**建筑模板：**
```json
{
  "building_templates": {
    "house": {
      "wall_tile": 2,
      "roof_tile": 3,
      "floor_tile": 6,
      "door_tile": 1,
      "width": 6,
      "height": 5,
      "features": ["door", "window", "chimney"]
    },
    "blacksmith": {
      "wall_tile": 2,
      "roof_tile": 3,
      "floor_tile": 14,
      "door_tile": 1,
      "width": 8,
      "height": 6,
      "features": ["door", "chimney", "anvil", "furnace"]
    },
    "temple": {
      "wall_tile": 13,
      "roof_tile": 3,
      "floor_tile": 10,
      "door_tile": 1,
      "width": 7,
      "height": 7,
      "features": ["door", "spire", "altar"]
    }
  }
}
```

### 3.3 建筑生成器

**自动生成建筑：**
```javascript
function generateBuilding(map, x, y, template, rotation = 0) {
  const { wall_tile, roof_tile, floor_tile, door_tile, width, height } = template;
  
  // 生成墙壁
  for (let dy = 0; dy < height; dy++) {
    for (let dx = 0; dx < width; dx++) {
      if (dy === 0 || dy === height - 1 || dx === 0 || dx === width - 1) {
        map.layers.ground[y + dy][x + dx] = wall_tile;
      } else {
        map.layers.ground[y + dy][x + dx] = floor_tile;
      }
    }
  }
  
  // 生成门
  map.layers.ground[y + height - 1][x + Math.floor(width / 2)] = door_tile;
  
  // 生成屋顶（使用对象层）
  map.layers.roof = map.layers.roof || [];
  for (let dy = 0; dy < height; dy++) {
    for (let dx = 0; dx < width; dx++) {
      map.layers.roof[y + dy][x + dx] = roof_tile;
    }
  }
}
```

---

## 四、地图文档更新

### 4.1 地图列表

| 地图ID | 名称 | 尺寸 | 描述 | 解锁条件 |
|--------|------|------|------|----------|
| village | 青石村 | 50×40 | 玩家起始村庄 | 无 |
| forest | 迷雾森林 | 60×50 | 怪物出没的森林 | 通过村庄传送门 |
| cave | 暗影洞穴 | 40×35 | 阴暗的地下洞穴 | 完成森林任务 |
| town | 白石镇 | 70×60 | 繁华的城镇 | 达到等级5 |
| mountain | 雪峰山 | 50×45 | 终年积雪的高山 | 完成镇任务 |

### 4.2 地图数据结构

```json
{
  "id": "map_id",
  "name": "地图名称",
  "width": 50,
  "height": 40,
  "tile_size": 32,
  "layers": {
    "ground": [...],
    "decoration": [...],
    "roof": [...]
  },
  "monsters": [...],
  "objects": [...],
  "npcs": [...],
  "player_spawn": {"x": 25, "y": 20},
  "events": [...],
  "zones": [...],
  "weather": "sunny",
  "bgm": "village_bgm"
}
```

---

## 五、实现计划

### 阶段一：美术系统升级
1. 扩展瓦片类型（新增花朵、河流、木桥等）
2. 实现瓦片动画系统（水面、树叶、飘雪）
3. 实现基础光影系统
4. 实现粒子系统

### 阶段二：地图脚本优化
1. 实现地图事件系统
2. 实现地图区域系统
3. 优化地图加载流程

### 阶段三：建筑类型升级
1. 定义建筑模板系统
2. 实现建筑生成器
3. 新增多种建筑类型
4. 更新现有地图

### 阶段四：文档更新
1. 更新地图文档
2. 更新美术系统文档
3. 更新相关配置文档
