# 地图生成器使用指南

## 概述

地图生成器是一个功能完整的地图管理工具，用于创建、编辑、验证和预览游戏地图。

## 功能列表

1. **生成新地图** - 支持多种地图模板（村庄、森林、洞穴、城镇、沙漠）
2. **格式化地图** - 清理JSON格式，使ground数组紧凑排列
3. **扩展地图** - 扩大地图尺寸，保持原有内容居中
4. **修复地图** - 移除多层边界墙，确保地图可通行
5. **验证地图** - 检查地图有效性、可达性、对象位置等
6. **预览地图** - 在终端中以字符形式查看地图布局
7. **列出地图** - 显示所有地图的基本信息

## 快速开始

```bash
# 查看帮助
python tools/map_generator.py

# 列出所有地图
python tools/map_generator.py list

# 生成新地图
python tools/map_generator.py generate village my_village

# 预览地图
python tools/map_generator.py preview village

# 验证地图
python tools/map_generator.py validate village

# 修复地图边界问题
python tools/map_generator.py fix village

# 扩展地图尺寸
python tools/map_generator.py expand village 60 50
```

## 命令详解

### 1. generate - 生成新地图

根据模板生成新地图，自动添加建筑、道路和装饰物。

```bash
python tools/map_generator.py generate <type> <id> [width] [height] [name]
```

**参数：**
- `type`: 地图类型（见下表）
- `id`: 地图唯一标识符
- `width`: 地图宽度（可选）
- `height`: 地图高度（可选）
- `name`: 地图显示名称（可选）

**地图类型：**

| 类型 | 描述 | 默认尺寸 | 特点 |
|------|------|----------|------|
| village | 村庄 | 50×40 | 有房屋、铁匠铺、商店、道路 |
| forest | 森林 | 60×50 | 有大量树木、道路、池塘 |
| cave | 洞穴 | 40×30 | 有石头、熔岩危险区域 |
| town | 城镇 | 80×60 | 大型村庄，更多建筑和道路网格 |
| desert | 沙漠 | 50×50 | 有绿洲、水井、沙地 |

**示例：**
```bash
# 生成默认尺寸的村庄
python tools/map_generator.py generate village my_village

# 生成自定义尺寸的森林
python tools/map_generator.py generate forest dark_forest 80 60

# 生成带名称的城镇
python tools/map_generator.py generate town capital 100 80 "王都"
```

### 2. format - 格式化地图

格式化所有地图JSON文件，使ground数组每行一个紧凑格式。

```bash
python tools/map_generator.py format
```

**效果：**
- 移除多余空格
- ground数组每行一个数组
- 保持JSON有效性

### 3. expand - 扩展地图尺寸

扩展现有地图，保持原有内容居中放置。

```bash
python tools/map_generator.py expand <id> <width> <height>
```

**参数：**
- `id`: 地图标识符
- `width`: 新宽度
- `height`: 新高度

**示例：**
```bash
# 将village地图扩展到60×50
python tools/map_generator.py expand village 60 50
```

**处理内容：**
- 自动移除原地图边界
- 原内容居中放置
- 新区域填充地面瓦片
- 自动调整所有对象、NPC、传送门坐标
- 自动调整玩家出生点

### 4. fix - 修复地图边界

修复地图中的多层边界墙问题，确保只有外围边界墙。

```bash
python tools/map_generator.py fix <id>
python tools/map_generator.py fix all
```

**参数：**
- `id`: 地图标识符，或使用 `all` 修复所有地图

**示例：**
```bash
# 修复单个地图
python tools/map_generator.py fix village

# 修复所有地图
python tools/map_generator.py fix all
```

**修复内容：**
- 移除内部多余的边界墙
- 保留外围2格宽的边界墙
- 自动调整对象、NPC、传送门坐标
- 确保地图可通行

### 5. validate - 验证地图

验证地图的有效性，检查各种潜在问题。

```bash
python tools/map_generator.py validate <id>
```

**检查项目：**
- 地图尺寸与声明是否匹配
- 玩家出生点是否在有效位置
- 玩家出生点是否在可通行区域
- NPC位置是否在地图范围内
- 对象位置是否在地图范围内
- 可达区域比例（从出生点可达的区域占比）

**示例：**
```bash
python tools/map_generator.py validate village
```

**输出示例：**
```
地图 'village' 验证通过
统计: {'width': 50, 'height': 40, 'total_tiles': 2000, 'walkable_tiles': 1800, 'npcs': 2, 'objects': 1}
```

### 6. preview - 预览地图

在终端中以字符形式预览地图布局。

```bash
python tools/map_generator.py preview <id>
```

**示例：**
```bash
python tools/map_generator.py preview village
```

**输出示例：**
```
地图: 青石村 (50×40)

##############################################
##..........................................##
##...####.......####.......................##
##...#..#.......#..#.......................##
##...####.......####.......................##
##..........................................##
##......························............##
##......·..................·...............##
##......·..................·...............##
...

图例:
  . = 草地 (0)
  · = 泥土路 (1)
  ~ = 水面 (2)
  # = 墙/边界 (4)
  T = 树木 (5)
```

### 7. list - 列出所有地图

显示所有地图的基本信息。

```bash
python tools/map_generator.py list
```

**输出示例：**
```
共 2 个地图:

  village: 青石村 (50×40)
  forest: 幽暗森林 (60×50)
```

## 瓦片类型

| ID | 名称 | 符号 | 可通行 | 说明 |
|----|------|------|--------|------|
| 0 | 草地 | . | 是 | 基础地面 |
| 1 | 泥土路 | · | 是 | 道路 |
| 2 | 水面 | ~ | 否 | 需要桥梁通过 |
| 3 | 木桥 | = | 是 | 跨越水面 |
| 4 | 墙/边界 | # | 否 | 阻挡通行 |
| 5 | 树木 | T | 否 | 森林装饰 |
| 6 | 石头 | S | 否 | 障碍物 |
| 7 | 花朵 | * | 是 | 装饰物 |
| 8 | 栅栏 | + | 否 | 围栏 |
| 9 | 森林地面 | , | 是 | 森林基础地面 |
| 10 | 洞穴地面 | _ | 是 | 洞穴基础地面 |
| 11 | 熔岩 | ! | 否 | 危险区域 |
| 12 | 沙地 | s | 是 | 沙漠基础地面 |
| 13 | 雪地 | S | 是 | 雪地基础地面 |
| 14 | 室内地板 | F | 是 | 室内地面 |
| 15 | 花丛草地 | f | 是 | 带花朵的草地 |
| 16 | 小河 | r | 否 | 河流，动画效果 |
| 17 | 木桥 | B | 是 | 跨越河流 |
| 18 | 灌木丛 | b | 否 | 灌木装饰 |
| 19 | 枯树 | D | 否 | 枯树装饰 |
| 20 | 花朵 | F | 是 | 花朵区域 |
| 21 | 深草地 | g | 是 | 深色草地 |
| 22 | 石板 | P | 是 | 石板地面 |
| 23 | 熔岩 | L | 否 | 熔岩区域，动画效果 |
| 24 | 冰面 | I | 是 | 冰面，动画效果 |

## 结构类型

可放置在地图上的建筑和装饰物：

| 结构 | 尺寸 | 说明 |
|------|------|------|
| house_small | 5×5 | 小型房屋，有门 |
| house_medium | 7×6 | 中型房屋，有门 |
| blacksmith | 8×6 | 铁匠铺，有门 |
| shop | 7×5 | 商店，有门 |
| temple | 7×7 | 神殿，石板地面 |
| academy | 8×7 | 学院，石板地面 |
| tavern | 7×6 | 酒馆，有门 |
| well | 3×3 | 水井，中心有水 |
| tree_cluster | 3×3 | 树丛 |
| pond | 5×4 | 池塘 |
| river_h | 5×2 | 横向河流 |
| river_v | 2×5 | 纵向河流 |
| bridge_h | 5×1 | 横向桥 |
| bridge_v | 1×5 | 纵向桥 |
| fence_h | 5×1 | 横向栅栏 |
| fence_v | 1×5 | 纵向栅栏 |
| road_h | 5×1 | 横向道路 |
| road_v | 1×5 | 纵向道路 |
| bush_cluster | 3×3 | 灌木丛 |
| flower_garden | 3×3 | 花坛 |

## 工作流程示例

### 创建新地图

```bash
# 1. 生成地图
python tools/map_generator.py generate village new_village 60 50 "新村庄"

# 2. 预览地图
python tools/map_generator.py preview new_village

# 3. 验证地图
python tools/map_generator.py validate new_village

# 4. 如有问题，修复地图
python tools/map_generator.py fix new_village
```

### 维护现有地图

```bash
# 1. 列出所有地图
python tools/map_generator.py list

# 2. 验证所有地图
python tools/map_generator.py validate village
python tools/map_generator.py validate forest

# 3. 修复所有地图
python tools/map_generator.py fix all

# 4. 格式化所有地图
python tools/map_generator.py format
```

### 扩展地图

```bash
# 1. 预览当前地图
python tools/map_generator.py preview village

# 2. 扩展地图
python tools/map_generator.py expand village 80 60

# 3. 验证扩展后的地图
python tools/map_generator.py validate village

# 4. 预览扩展后的地图
python tools/map_generator.py preview village
```

## 注意事项

1. **地图ID唯一性**：每个地图的ID必须唯一，否则会覆盖现有地图
2. **边界墙**：地图生成时会自动添加2格宽的边界墙
3. **坐标调整**：扩展和修复地图时会自动调整所有坐标
4. **可达性**：验证地图时会检查从玩家出生点可达的区域比例
5. **备份建议**：修改地图前建议备份原文件

## 扩展开发

如需添加新的地图类型或结构，可修改 `map_generator.py` 中的配置：

### 添加新地图类型

在 `TEMPLATES` 字典中添加新类型：

```python
TEMPLATES["dungeon"] = {
    "description": "地牢地图",
    "default_size": (30, 30),
    "border_tile": 4,
    "ground_tile": 10,
    "structures": [],
    "roads": False,
    "decorations": [],
}
```

然后在 `generate_map` 方法中添加对应的生成逻辑。

### 添加新结构

在 `STRUCTURES` 字典中添加新结构：

```python
STRUCTURES["tower"] = {
    "name": "瞭望塔",
    "width": 3,
    "height": 5,
    "tiles": [
        [0, 4, 0],
        [0, 4, 0],
        [0, 4, 0],
        [0, 4, 0],
        [4, 1, 4],
    ],
    "door": (1, 4),
}
```

### 添加新瓦片类型

在 `TILES` 字典中添加新瓦片：

```python
TILES[15] = {
    "name": "传送门",
    "symbol": "O",
    "color": "\033[35m",
    "walkable": True
}
```

## 常见问题

**Q: 地图生成后玩家无法移动？**
A: 运行 `validate` 命令检查可达性，可能是出生点在不可通行区域或地图被封闭。

**Q: 如何修改现有地图？**
A: 可以直接编辑JSON文件，或使用 `fix` 和 `expand` 命令进行修改。

**Q: 地图太大预览显示不全？**
A: 预览功能会自动缩放，但建议地图尺寸不超过100×80。

**Q: 如何添加自定义装饰物？**
A: 编辑地图JSON文件的 `layers.ground` 数组，或扩展生成器添加新结构。
