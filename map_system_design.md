# 地图系统设计方案

## 概述

地图系统是一个数据驱动的瓦片地图系统，支持多区域地图、摄像机滚动、交互物件等功能。

## 核心特性

- **数据驱动**：地图数据存放在 `config/maps/` 目录下的 JSON 文件中
- **摄像机系统**：支持大地图滚动显示，摄像机跟随玩家
- **多区域支持**：通过传送门连接不同的地图区域
- **交互物件**：宝箱、传送门、采集点、装饰物等
- **瓦片配置化**：瓦片类型定义在 `config/tiles.json` 中

## 文件结构

```
config/
├── tiles.json              # 瓦片类型定义
└── maps/
    ├── village.json        # 村庄地图
    └── forest.json         # 森林地图
```

## 地图数据格式

### 单张地图 JSON 结构

```json
{
  "id": "village",
  "name": "青石村",
  "width": 25,
  "height": 18,
  "tile_size": 32,
  "layers": {
    "ground": [
      [0, 0, 0, 1, 1, ...],
      ...
    ]
  },
  "objects": [
    {
      "id": "chest_01",
      "type": "chest",
      "x": 15, "y": 8,
      "properties": {
        "items": [{"item_id": "health_potion", "quantity": 3}],
        "opened": false
      }
    },
    {
      "id": "portal_to_forest",
      "type": "portal",
      "x": 0, "y": 15,
      "properties": {
        "target_map": "forest",
        "target_x": 39,
        "target_y": 15
      }
    }
  ],
  "npcs": [
    {
      "npc_id": "blacksmith",
      "x": 4,
      "y": 5
    }
  ],
  "player_spawn": {
    "x": 9,
    "y": 9
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 地图唯一标识 |
| `name` | string | 地图显示名称 |
| `width` / `height` | int | 地图尺寸（瓦片数） |
| `layers.ground` | 2D int[][] | 地面层瓦片 ID |
| `objects` | array | 交互物件列表 |
| `npcs` | array | NPC 出生点列表 |
| `player_spawn` | object | 玩家出生点 |

## 瓦片系统

### 瓦片定义（`config/tiles.json`）

```json
{
  "0":  {"name": "草地",   "color": "#4a8c3f", "walkable": true,  "detail": "grass"},
  "1":  {"name": "泥土路", "color": "#c4a66a", "walkable": true,  "detail": "dirt_road"},
  "2":  {"name": "房屋墙", "color": "#8b6b4a", "walkable": false, "detail": "brick_wall"},
  ...
}
```

### 瓦片渲染器

瓦片渲染器在 `map.js` 中注册，根据 `detail` 字段分发到具体的绘制逻辑。

## 交互物件系统

### 物件类型

| 类型 | 说明 | 交互方式 | 关键属性 |
|------|------|----------|----------|
| `portal` | 传送门/区域切换点 | 踩上去自动触发 | target_map, target_x, target_y |
| `chest` | 宝箱 | 按 E 打开 | items[], opened |
| `gather` | 采集点 | 按 E 采集 | item_id, respawn_time |
| `decoration` | 装饰物（告示牌等） | 按 E 查看 | sprite, interact_text |

## 摄像机系统

摄像机跟随玩家居中显示，支持大地图滚动。

### 核心逻辑

1. 计算玩家位置居中的摄像机坐标
2. 边界钳制，防止摄像机超出地图范围
3. 地图小于视口时居中显示
4. 渲染时应用摄像机偏移
5. 只渲染视口范围内的瓦片（视口裁剪优化）

## 地图切换流程

1. 玩家走到传送门位置
2. 前端检测到 player 所在格有 portal 类型物件
3. 调用 `POST /api/map/transfer` 接口
4. 后端保存玩家位置，返回目标地图数据
5. 前端切换地图，更新玩家位置，重新加载 NPC

## API 接口

### GET /api/map/tiles

获取瓦片类型定义。

### GET /api/map/{map_id}

获取地图数据（含物件状态）。

### POST /api/map/transfer

地图切换（传送门）。

**请求**：
```json
{"target_map": "forest", "target_x": 12, "target_y": 1}
```

### POST /api/map/object/interact

与地图物件交互。

**请求**：
```json
{"map_id": "village", "object_id": "chest_01", "action": "interact"}
```

## 存档数据

玩家存档中包含当前地图信息：

```json
{
  "current_map": "village",
  "player_x": 9,
  "player_y": 9,
  "map_states": {
    "village": {
      "objects": {
        "chest_01": {"opened": true}
      }
    }
  }
}
```

## 扩展方向

- **更多地图**：洞穴、城镇、地下城等
- **地图编辑器**：可视化编辑地图
- **动态地图**：根据时间或事件变化的地图
- **多层地图**：支持地面层和装饰层
- **地图特效**：天气、光照等视觉效果
