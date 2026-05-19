# 地图系统优化设计文档

## 一、现状分析

### 1.1 前端硬编码问题

| 问题 | 位置 | 优先级 | 说明 |
|------|------|--------|------|
| 传送门目标名称硬编码 | `map.js:342` | 🔥 P0 | `mapNames` 字典写死 5 个地图名，新增地图必须改代码 |
| 环境粒子硬编码 | `map.js:256-264` | 🔥 P0 | `if (mapId === "forest")` / `if (mapId === "village")` 硬编码粒子类型 |
| 采集点绘制硬编码 | `map.js:395-445` | 🔥 P0 | `if (itemId === "herb")` / `if (itemId === "mushroom")` 等 4 种物品 if-else |
| 瓦片渲染器硬编码 | `map.js:497-680` | 🔴 P1 | 24 种瓦片渲染器全部硬编码注册，新增瓦片必须改代码 |
| 装饰物绘制硬编码 | `map.js:460-473` | 🔴 P1 | `drawDecoration` 只支持 `sign` 一种装饰 |
| 宝箱绘制硬编码 | `map.js:295-314` | 🟡 P2 | 只有一种宝箱外观，无外观变体 |

### 1.2 地图配置缺失

| 问题 | 优先级 | 说明 |
|------|--------|------|
| 无地图元数据 | 🔥 P0 | 地图 JSON 缺少 `environment`、`level_range`、`region` 等元数据 |
| 无地图列表 API | 🔥 P0 | 前端无法动态获取所有可用地图，只能硬编码 |
| 无环境配置 | 🔴 P1 | 地图无天气/粒子/氛围配置，全靠前端 if-else |
| 采集点无外观配置 | 🔴 P1 | 采集点颜色全靠 `itemId` if-else 判断 |
| 怪物组配置不一致 | 🟡 P2 | 仅 `forest.json` 有 `monster_groups`，其他地图用 `monsters` 数组 |

### 1.3 探索系统不完善

| 问题 | 优先级 | 说明 |
|------|--------|------|
| 探索记录纯前端 | 🔴 P1 | `exploredTiles` 只存在内存，刷新丢失，不同步到后端 |
| 无地图列表 API | 🔥 P0 | 前端无法获取所有地图概览信息 |

---

## 二、优化目标

1. **配置驱动**：地图元数据、环境粒子、采集点外观、瓦片细节全部由配置驱动，新增地图/瓦片/采集物零代码改动
2. **API 完善**：新增地图列表 API，前端动态获取地图概览
3. **探索持久化**：探索记录同步到后端存档
4. **怪物组统一**：所有地图统一使用 `monster_groups` 配置

---

## 三、设计方案

### 3.1 地图元数据配置化

**设计思路**：在每个地图 JSON 中新增 `metadata` 字段，包含环境、等级、区域等信息，前端根据元数据驱动渲染。

**metadata 结构**：

```json
{
  "id": "forest",
  "name": "幽暗森林",
  "metadata": {
    "level_range": [2, 5],
    "region": "forest",
    "environment": {
      "particles": [
        { "type": "leaf", "rate": 0.1 }
      ],
      "ambient_color": null,
      "danger_zone": false
    },
    "map_names": {
      "village": "青石村",
      "dark_cave": "黑暗洞穴"
    }
  }
}
```

**metadata 字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `level_range` | [min, max] | 推荐等级范围 |
| `region` | string | 区域类型标识（forest/cave/desert/city/village） |
| `environment.particles` | array | 环境粒子配置，`type` 为粒子类型，`rate` 为每帧生成概率 |
| `environment.ambient_color` | string/null | 全局色调滤镜（如洞穴用暗色） |
| `environment.danger_zone` | boolean | 是否危险区域（影响背景音乐等） |
| `map_names` | object | 本地图传送门目标的中文名映射 |

### 3.2 采集点外观配置化

**设计思路**：在 `tiles.json` 中新增 `gather_appearances` 字段，定义每种采集物品的渲染颜色，前端根据配置渲染。

**gather_appearances 结构**：

```json
{
  "gather_appearances": {
    "herb": { "base": "#4a8c3f", "mid": "#6abf5a", "top": "#8ee07a" },
    "mushroom": { "base": "#8b6914", "mid": "#a67c00", "top": "#c9a000" },
    "iron_ore": { "base": "#666", "mid": "#888", "top": "#aaa" },
    "beast_bone": { "base": "#ccc", "mid": "#eee", "top": "#fff" }
  }
}
```

**前端渲染**：`drawGatherPoint` 根据 `itemId` 从 `tileConfig.gather_appearances[itemId]` 读取颜色，无需 if-else。

### 3.3 瓦片细节配置化

**设计思路**：将 `initTileRenderers()` 中硬编码的 24 种瓦片渲染逻辑，改为由 `tiles.json` 中的 `detail_config` 驱动。

**detail_config 结构**：

```json
{
  "0": {
    "name": "草地",
    "color": "#4a8c3f",
    "walkable": true,
    "detail": "grass",
    "detail_config": {
      "type": "scatter",
      "color": "#3d7a33",
      "spots": [
        { "x": 2, "y": 3, "prob": 0.3 },
        { "x": 5, "y": 6, "prob": 0.5 },
        { "x": 1, "y": 6, "prob": 0.7 }
      ]
    }
  }
}
```

**detail_config 类型**：

| type | 说明 | 参数 |
|------|------|------|
| scatter | 随机散布像素点 | color, spots[{x, y, prob}] |
| lines | 水平/垂直线条 | color, lines[{x, y, w, h}] |
| rect | 矩形填充 | color, rects[{x, y, w, h}] |
| animated | 动画效果 | color, anim_type, params |
| none | 无额外细节 | — |

**通用渲染器**：

```javascript
function renderTileDetail(ctx, x, y, config) {
  const p = TILE_SIZE / 8;
  if (!config) return;
  switch (config.type) {
    case "scatter":
      ctx.fillStyle = config.color;
      const seed = (x * 7 + y * 13) % 100;
      for (const spot of config.spots) {
        if (seed < spot.prob * 100) ctx.fillRect(x + spot.x * p, y + spot.y * p, p, p);
      }
      break;
    case "lines":
      ctx.fillStyle = config.color;
      for (const line of config.lines) {
        ctx.fillRect(x + line.x * p, y + line.y * p, line.w * p, line.h * p);
      }
      break;
    case "rect":
      ctx.fillStyle = config.color;
      for (const rect of config.rects) {
        ctx.fillRect(x + rect.x * p, y + rect.y * p, rect.w * p, rect.h * p);
      }
      break;
    case "animated":
      renderAnimatedDetail(ctx, x, y, config);
      break;
  }
}
```

**向后兼容**：保留 `tileRenderers` 注册表作为 fallback，有 `detail_config` 时用配置驱动，否则用注册的渲染器。

### 3.4 地图列表 API

**新增 API**：`GET /api/maps`

返回所有地图的概览信息（不含瓦片数据，避免传输大量数据）：

```json
[
  {
    "id": "village",
    "name": "青石村",
    "width": 50,
    "height": 40,
    "level_range": [1, 1],
    "region": "village",
    "environment": { "particles": [], "danger_zone": false }
  },
  {
    "id": "forest",
    "name": "幽暗森林",
    "width": 60,
    "height": 50,
    "level_range": [2, 5],
    "region": "forest",
    "environment": { "particles": [{"type": "leaf", "rate": 0.1}], "danger_zone": true }
  }
]
```

### 3.5 探索记录持久化

**设计思路**：前端定期将 `exploredTiles` 上报到后端，存入 `player_profile`。

**后端变更**：
- `player_profile` 新增 `explored_tiles` 字段：`{ "village": ["25,21", "26,21", ...], "forest": [...] }`
- 新增 API：`POST /api/map/explored` — 上报探索瓦片
- `GET /api/map/{map_id}` 返回时附带 `explored_tiles`

**前端变更**：
- `loadMap()` 后从 API 响应恢复 `exploredTiles`
- `recordExploredTile()` 定期批量上报（每 30 秒或切换地图时）

### 3.6 怪物组配置统一

**设计思路**：所有地图统一使用 `monster_groups` 格式，废弃 `monsters` 数组。

**迁移**：将 `monsters` 数组转为 `monster_groups` 格式：

```json
"monster_groups": [
  {
    "group_id": "cave_bat_1",
    "x": 10,
    "y": 15,
    "monsters": [{ "monster_id": "cave_bat", "count": 1 }]
  }
]
```

---

## 四、实施计划

### Phase 1: 地图元数据 + 列表 API

**修改文件**：
1. `config/maps/*.json` — 5 个地图添加 `metadata` 字段
2. `backend/routes/map.py` — 新增 `GET /api/maps` 接口
3. `frontend/js/map.js` — 用 `metadata` 替代硬编码的 `mapNames` 和环境粒子

**步骤**：
1. 为 5 个地图 JSON 添加 `metadata` 字段
2. 实现 `GET /api/maps` API
3. 重构 `drawPortal` 使用 `metadata.map_names`
4. 重构 `drawEnvironmentParticles` 使用 `metadata.environment.particles`

### Phase 2: 采集点 + 瓦片细节配置化

**修改文件**：
1. `config/tiles.json` — 添加 `gather_appearances` 和 `detail_config`
2. `frontend/js/map.js` — 重构 `drawGatherPoint` 和瓦片渲染

**步骤**：
1. 在 `tiles.json` 添加 `gather_appearances`
2. 重构 `drawGatherPoint` 使用配置驱动
3. 在 `tiles.json` 为每种瓦片添加 `detail_config`
4. 实现 `renderTileDetail` 通用渲染器
5. 保留 `tileRenderers` 作为动画瓦片的 fallback

### Phase 3: 探索记录持久化

**修改文件**：
1. `backend/routes/map.py` — 新增探索上报 API
2. `backend/player_profile.py` — 新增 `explored_tiles` 字段
3. `frontend/js/map.js` — 探索记录同步

**步骤**：
1. `player_profile` 添加 `explored_tiles` 字段
2. 新增 `POST /api/map/explored` API
3. `GET /api/map/{map_id}` 返回 `explored_tiles`
4. 前端 `loadMap` 恢复探索记录
5. 前端定期上报新增探索瓦片

### Phase 4: 怪物组配置统一

**修改文件**：
1. `config/maps/*.json` — 4 个地图的 `monsters` 转为 `monster_groups`

**步骤**：
1. 编写迁移脚本将 `monsters` → `monster_groups`
2. 更新前端怪物加载逻辑（如需）
3. 验证所有地图怪物正常刷新

---

## 五、测试用例

| 用例 | 类型 | 描述 |
|------|------|------|
| test_map_metadata_exists | 配置 | 每个地图都有 metadata 字段 |
| test_map_metadata_level_range | 配置 | level_range 格式为 [min, max] |
| test_map_metadata_environment | 配置 | environment.particles 格式正确 |
| test_maps_api | API | GET /api/maps 返回所有地图概览 |
| test_gather_appearances_config | 配置 | tiles.json 有 gather_appearances |
| test_tile_detail_config | 配置 | 每种瓦片有 detail_config |
| test_explored_tiles_persist | 集成 | 探索记录刷新后不丢失 |
| test_monster_groups_unified | 配置 | 所有地图使用 monster_groups |

---

## ✅ 实施状态

| Phase | 状态 | 完成日期 |
|-------|------|----------|
| Phase 1: 地图元数据 + 列表 API | ✅ 已完成 | 2026-05-19 |
| Phase 2: 采集点 + 瓦片细节配置化 | ✅ 已完成 | 2026-05-19 |
| Phase 3: 探索记录持久化 | ✅ 已完成 | 2026-05-19 |
| Phase 4: 怪物组配置统一 | ✅ 已完成 | 2026-05-19 |
