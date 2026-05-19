# 地图生成器优化设计

> 创建日期：2026-05-18
> 优先级：P0 高
> 状态：开发中

---

## 一、当前问题分析

### 问题清单

| # | 问题 | 影响 | 优先级 |
|---|------|------|--------|
| 1 | TILES 字典与 tiles.json 不一致 | 生成器对瓦片属性判断完全错误，导致装饰物/道路/建筑放置逻辑异常 | P0 |
| 2 | 建筑与路径的放置顺序错误 | paths 在 buildings 之前绘制，建筑放置时覆盖道路，导致门口无路 | P0 |
| 3 | 道路宽度覆盖问题 | width=2 的横向道路覆盖两整行，可能覆盖旁边的建筑或地标 | P1 |
| 4 | 随机装饰物放置无逻辑 | 完全随机分布，没有考虑地形、路径、区域划分，视觉杂乱 | P1 |
| 5 | 模板设计简陋 | zones 只是矩形区域，landmarks 和 buildings 布局缺乏美学考量 | P2 |

### 详细分析

#### 问题1：TILES 字典与 tiles.json 不一致

**代码中 TILES 字典**（`map_generator.py`）：

| ID | 代码定义 | tiles.json 定义 | 差异 |
|----|----------|----------------|------|
| 0  | 草地 | 草地 | ✅ 一致 |
| 1  | 泥土路 | 泥土路 | ✅ 一致 |
| 2  | 水面 | **房屋墙** | ❌ 完全不同 |
| 3  | 木桥 | **屋顶** | ❌ 完全不同 |
| 4  | 墙/边界 | **树木** | ❌ 完全不同 |
| 5  | 树木 | **水面** | ❌ 完全不同 |
| 6  | 石头 | **木地板** | ❌ 完全不同 |
| 7  | 花朵 | **栅栏** | ❌ 完全不同 |
| 8  | 栅栏 | **石头** | ❌ 完全不同 |
| 9  | 森林地面 | **木地板2** | ❌ 完全不同 |
| 10 | 洞穴地面 | **石板路** | ❌ 完全不同 |
| 11 | **熔岩** | **沙地** | ❌ 完全不同 |
| 14 | 室内地板 | **岩地** | ❌ 完全不同 |

**根本原因**：TILES 字典是早期硬编码的，后来 tiles.json 做了重新设计，但生成器代码没有同步更新。

**影响**：
- `place_structure` 中建筑模板的瓦片 ID 是基于 TILES 字典定义的（如墙=4，室内地板=14），但 tiles.json 中 4=树木、14=岩地
- `add_random_trees` 放置的 tile_id=5 在 tiles.json 中是水面而非树木
- `_apply_zone_decoration` 中的 deco_map 也基于旧的 TILES 字典

#### 问题2：生成顺序错误

当前 `generate_from_template` 执行顺序：
```
zones → landmarks → paths → water → buildings → decorations
```

问题：paths（道路）在 buildings（建筑）之前绘制，建筑放置时会覆盖道路，导致建筑门口无路可走。

正确顺序应为：
```
zones → landmarks → buildings → paths → water → decorations
```

先放建筑，再画道路，道路遇到建筑时绕行或停止，确保门口有路。

#### 问题3：道路宽度覆盖

`_draw_path_segment` 中 width=2 的横向道路会覆盖 y 和 y+1 两整行，可能覆盖旁边的建筑或地标。

需要添加碰撞检测：道路只覆盖可行走的瓦片，遇到不可行走的瓦片（建筑墙、水面等）时跳过。

#### 问题4：随机装饰物放置无逻辑

`add_random_trees` 和 `_apply_zone_decoration` 完全随机放置，没有考虑：
- 与建筑/道路的距离
- 与其他装饰物的最小间距
- 区域内的密度控制

需要添加：
- 最小间距检查
- 避让建筑/道路区域
- 密度控制

#### 问题5：模板设计简陋

当前模板中 zones 只是简单的矩形区域，buildings 的 offset 是硬编码的，缺乏：
- 建筑之间的间距规划
- 道路与建筑的连接关系
- 区域内的景观设计

---

## 二、优化目标

| 目标 | 优先级 | 说明 |
|------|--------|------|
| 同步 TILES 字典与 tiles.json | P0 | 从 tiles.json 动态加载瓦片定义，消除不一致 |
| 修正生成顺序 | P0 | 先建筑后道路，确保门口有路 |
| 道路碰撞检测 | P1 | 道路遇到不可行走瓦片时跳过，不覆盖建筑 |
| 装饰物智能放置 | P1 | 最小间距、避让建筑、密度控制 |
| 更新建筑模板瓦片ID | P0 | 建筑模板使用 tiles.json 的瓦片ID |
| 更新 deco_map | P0 | 装饰物映射使用 tiles.json 的瓦片ID |

---

## 三、设计方案

### 3.1 从 tiles.json 动态加载瓦片定义

**当前**：TILES 字典硬编码在 `map_generator.py` 中，与 tiles.json 不一致。

**优化后**：启动时从 `config/tiles.json` 加载瓦片定义，替代硬编码的 TILES 字典。

```python
def load_tiles_config():
    """从 tiles.json 加载瓦片定义"""
    tiles_path = CONFIG_DIR / "tiles.json"
    if tiles_path.exists():
        with open(tiles_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tiles = {}
        for key, val in data.items():
            if key == "gather_appearances":
                continue
            tid = int(key)
            tiles[tid] = {
                "name": val["name"],
                "walkable": val.get("walkable", True),
            }
        return tiles
    return TILES  # fallback
```

### 3.2 修正生成顺序

**当前顺序**：zones → landmarks → paths → water → buildings → decorations

**优化后顺序**：zones → landmarks → buildings → paths → water → decorations

关键变化：buildings 移到 paths 之前，确保道路绘制时可以感知建筑位置。

### 3.3 道路碰撞检测

`_draw_path_segment` 添加碰撞检测：道路只覆盖可行走的瓦片。

```python
def _draw_path_segment(self, ground, start, end, width, tile):
    # ... 计算路径点 ...
    for each point (tx, ty):
        current = ground[ty][tx]
        if not self._is_walkable(current):
            continue  # 跳过不可行走的瓦片（建筑墙、水面等）
        ground[ty][tx] = tile
```

### 3.4 装饰物智能放置

`_apply_zone_decoration` 添加：
- 最小间距检查（装饰物之间至少 2 格）
- 避让建筑区域（不覆盖不可行走的瓦片）
- 避让道路区域（不覆盖道路瓦片）

```python
def _apply_zone_decoration(self, ground, zone, deco):
    # ... 现有逻辑 ...
    min_spacing = deco.get("min_spacing", 2)
    road_tiles = {1, 10, 22}  # 道路瓦片集合
    
    while placed < count and attempts < count * 10:
        x, y = random_position(zone)
        if ground[y][x] != gt:  # 只在地面瓦片上放置
            continue
        if ground[y][x] in road_tiles:  # 不覆盖道路
            continue
        if not self._check_spacing(ground, x, y, tile_id, min_spacing):  # 最小间距
            continue
        ground[y][x] = tile_id
        placed += 1
```

### 3.5 更新建筑模板瓦片ID

根据 tiles.json 重新定义建筑模板的瓦片ID：

| 旧ID | 旧含义 | 新ID | 新含义(tiles.json) |
|------|--------|------|-------------------|
| 4 | 墙/边界 | 2 | 房屋墙 |
| 14 | 室内地板 | 6 | 木地板 |
| 1 | 泥土路(门) | 1 | 泥土路(门) |
| 22 | 石板 | 22 | 石板 |
| 8 | 栅栏 | 7 | 栅栏 |
| 2 | 水面(井) | 5 | 水面(井) |
| 16 | 小河 | 16 | 小河 |
| 17 | 木桥 | 17 | 木桥 |
| 5 | 树木 | 4 | 树木 |
| 0 | 草地 | 0 | 草地 |
| 15 | 花丛草地 | 15 | 花丛草地 |
| 18 | 灌木丛 | 18 | 灌木丛 |
| 20 | 花朵 | 20 | 花朵 |

边界瓦片：旧 4(墙/边界) → 新 13(岩壁) 作为地图边界

### 3.6 更新 deco_map

根据 tiles.json 更新装饰物映射：

| deco_type | 旧 tile_id | 新 tile_id | tiles.json 名称 |
|-----------|-----------|-----------|----------------|
| farmland | 25 | 25 | 田地 |
| graves | 26 | 26 | 墓碑 |
| riverside_flowers | 20 | 20 | 花朵 |
| flowers | 15 | 15 | 花丛草地 |
| light_forest | 5→4 | 4 | 树木 |
| medium_forest | 5→4 | 4 | 树木 |
| dark_forest | 19 | 19 | 枯树 |
| ruins_vegetation | 8→8 | 8 | 石头 |
| stream_vegetation | 18 | 18 | 灌木丛 |
| cave_entrance_deco | 31 | 31 | 火把 |
| mine_deco | 8 | 8 | 石头 |
| spider_deco | 8 | 8 | 石头 |
| mushroom_deco | 20 | 20 | 花朵 |
| abyss_deco | 23 | 23 | 熔岩 |
| boss_deco | 31 | 31 | 火把 |
| barren_desert | 19 | 19 | 枯树 |
| dune_desert | 29 | 29 | 沙丘 |
| oasis_vegetation | 28 | 28 | 棕榈树 |
| quicksand_area | 30 | 30 | 流沙 |
| noble_garden | 20 | 20 | 花朵 |
| palace_deco | 22 | 22 | 石板 |
| avenue_deco | 20 | 20 | 花朵 |
| dark_alley_deco | 8 | 8 | 石头 |

---

## 四、实施计划

### Phase 1：修复核心问题（P0）

1. 从 tiles.json 动态加载瓦片定义，替代硬编码 TILES
2. 更新 STRUCTURES 中所有建筑模板的瓦片ID
3. 更新 deco_map 中的瓦片ID
4. 修正生成顺序：buildings 移到 paths 之前
5. 更新边界瓦片：4→13

### Phase 2：改进算法（P1）

1. 道路碰撞检测：不覆盖不可行走瓦片
2. 装饰物智能放置：最小间距、避让建筑/道路
3. 门口道路延伸：建筑放置后自动在门口延伸道路

### Phase 3：模板优化（P2）

1. 优化 village.json 模板布局
2. 优化其他模板布局

---

## 五、文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `tools/map_generator.py` | 动态加载 tiles.json、更新 TILES/STRUCTURES/deco_map、修正生成顺序、道路碰撞检测、装饰物智能放置 |
| `config/map_templates/*.json` | 更新模板中的瓦片ID（如果需要） |

---

## 六、测试用例

| 用例 | 描述 |
|------|------|
| TILES 加载 | 从 tiles.json 加载后，TILES[4].name == "树木" |
| 建筑模板瓦片ID | house_small 的墙使用 tile_id=2，地板使用 tile_id=6 |
| 生成顺序 | buildings 在 paths 之前放置 |
| 道路碰撞 | 道路不覆盖建筑墙壁（tile_id=2） |
| 门口有路 | 建筑放置后门口瓦片是可行走的 |
| 装饰物间距 | 装饰物之间至少 2 格间距 |
| 装饰物避让 | 装饰物不覆盖道路和建筑 |
| 边界瓦片 | 地图边界使用 tile_id=13（岩壁） |
| 生成后可达性 | 所有建筑门口可达 |

---

## 七、完成状态

> 更新日期：2026-05-19
> 状态：✅ 已完成（Phase1 + Phase2）

| 优化项 | 状态 | 说明 |
|--------|------|------|
| 动态加载 tiles.json | ✅ | load_tiles_config() 从 config/tiles.json 加载，fallback _TILES_FALLBACK |
| 更新建筑模板瓦片ID | ✅ | 墙4→2, 地板14→6, 栅栏8→7, 水2→5, 树5→4 |
| 更新 deco_map | ✅ | 树5→4, 洞穴10→14, 熔岩11→23 |
| 修正生成顺序 | ✅ | zones→landmarks→buildings→paths→water→decorations |
| 道路碰撞检测 | ✅ | _draw_path_segment 跳过不可行走瓦片，不覆盖建筑墙 |
| 装饰物智能放置 | ✅ | 最小间距(min_spacing)、避让道路、避让建筑 |
| 门口道路延伸 | ✅ | place_structure 门外延伸2格道路 |
| 模板优化 | ⏳ | Phase3 待开发 |
