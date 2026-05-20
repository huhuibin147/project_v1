# 地图问题检查指南

本文档详细说明地图可能出现的各类问题、对应的检测工具及使用方法。

---

## 1. 问题分类总览

| 类别 | 典型表现 | 检测工具 |
|------|----------|----------|
| 位置不可行走 | NPC/传送门/怪物站在墙壁或水面上 | `validate_maps.py` |
| 传送门卡死 | 传送后玩家无法移动 | `validate_maps.py` |
| 传送门命名不规范 | 名称使用英文或格式不统一 | `fix_portals.py` |
| 传送门重叠 | 同一位置多个传送门 | `validate_maps.py` |
| 传送门双向缺失 | A→B有传送门但B→A没有 | `validate_all.py` |
| 封闭区域 | 小面积区域四面被墙包围，玩家无法进出 | `validate_maps.py`、`fix_maps.py` |
| 怪物消失 | 地图无怪物组配置 | `validate_maps.py` |
| 怪物不可达 | 怪物站在不可行走格子 | `validate_maps.py` |
| NPC缺失 | npcs.json中属于某地图的NPC未在该地图中放置 | `validate_maps.py` |
| 地图连通断裂 | 从某地图出发无法到达其他地图 | `validate_maps.py` |
| 路径绕路 | 到传送门的实际路径远超直线距离 | `validate_maps.py` |
| 配置完整性 | 地图缺少必要字段 | `validate_all.py` |
| 交叉引用 | 地图引用了不存在的NPC/怪物/物品 | `validate_all.py` |

---

## 2. 工具详解

### 2.1 validate_maps.py — 地图核心校验与自动修复

**路径**: `tools/validate_maps.py`

**检测项目（共9类）**:

| # | 检测项 | 说明 |
|---|--------|------|
| 1 | NPC/物件/传送门位置 | 检查是否放在不可行走的格子上 |
| 2 | 物件重叠 | 同一位置有多个物件（尤其传送门重叠） |
| 3 | 传送门间距 | 传送门之间曼哈顿距离 < 5 视为太近 |
| 4 | 玩家出生点 | 出生点是否在可行走格子上 |
| 5 | NPC缺失 | 交叉引用 npcs.json，检测属于该地图但未在地图中放置的NPC |
| 6 | 封闭区域 | BFS从出生点出发，找出不可达的可行走小区域（面积<100格） |
| 7 | 怪物组问题 | 地图无怪物组（village除外）、怪物站在不可行走格子 |
| 8 | 传送门落点 | 目标地图不存在、落点越界、落点不可行走 |
| 9 | 路径效率 | 从出生点到传送门的实际路径过长（>2.5倍曼哈顿距离） |
| 9+ | 地图连通性 | BFS检查所有地图之间是否可以互相到达 |

**使用方法**:

```bash
# 检查所有地图（检测+自动修复+连通性检查）
python3 tools/validate_maps.py
```

**输出示例**:

```
检查地图: royal_city.json
  发现 2 个问题:
    - [传送卡死] portal_village -> village(56,25) - 传送门落点 (56,25) 不可行走 (tile=13)
    - [封闭区域] enclosed_area_1 - 5个格子，包含 1 个物件

地图连通性:
  royal_city:
    -> desert_oasis via [portal_desert] at (95, 55)
    -> village via [portal_village] at (3, 35)

从每个地图出发的可达性:
  ✓ royal_city 可以到达所有地图 (5 个)
```

**自动修复逻辑**:
- 不可行走位置 → 移到最近可行走格子
- NPC缺失 → 在出生点附近可行走格子自动添加NPC引用
- 封闭区域 → 移出区域内物件，打通边界墙
- 传送门太近 → 移开第二个传送门
- 传送门落点不可行走 → 在目标地图找最近可行走格子
- 物件重叠 → 保留传送门，移走其他物件

**注意**: `validate_maps.py` 运行后会直接修改地图文件，建议先备份。

---

### 2.2 fix_portals.py — 传送门位置与命名修复

**路径**: `tools/fix_portals.py`

**功能**:
1. 确保传送门所在格子**及四周相邻格子**都是可行走的（防止传送后卡住）
2. 将传送门名称统一为中文格式 `"传送门（前往XXX）"`

**传送门名称来源**:
- 优先从目标地图的 `metadata.map_names` 字段获取中文名
- 回退到内置映射表（village→青石村、forest→幽暗森林等）

**地图发现**:
- 自动扫描 `config/maps/` 目录，无需硬编码地图列表

**使用方法**:

```bash
# 修复所有地图的传送门
python3 tools/fix_portals.py
```

**何时使用**:
- 新增或修改地图后，传送门位置可能不安全
- 传送门名称不符合 `"传送门（前往XXX）"` 规范

---

### 2.3 fix_maps.py — 地图封闭区域修复与数据恢复

**路径**: `tools/fix_maps.py`

**功能**:
1. 检测并打通封闭区域（将边界不可行走瓦片改为道路瓦片）
2. 从旧地图备份恢复交互数据（NPC、怪物组、物件等）

**使用方法**:

```bash
# 需要先将旧地图文件放到 /tmp/ 下：
#   /tmp/old_village.json
#   /tmp/old_forest.json
#   /tmp/old_dark_cave.json
#   /tmp/old_desert_oasis.json
#   /tmp/old_royal_city.json

python3 tools/fix_maps.py
```

**何时使用**:
- 地图生成或修改后出现大面积封闭
- 交互数据（NPC/怪物/物件）丢失需要恢复

---

### 2.4 validate_all.py — 全局配置验证

**路径**: `tools/validate_all.py`

**地图相关检测**:
- 地图缺少必要字段（name、width、height、layers、player_spawn）
- player_spawn坐标超出地图范围
- 传送门目标地图不存在
- 传送门落点坐标超出目标地图范围
- 地图引用的NPC在配置中不存在
- 地图引用的怪物组中的怪物ID不存在

**交叉引用检测**:
- 怪物掉落物品是否存在于物品配置
- NPC商店商品是否存在于物品配置
- NPC所在地图是否存在
- 任务探索/收集/击杀目标是否存在
- 传送门双向链接完整性（A→B有传送门时检查B→A）

**使用方法**:

```bash
# 全量验证（包括物品、怪物、NPC、技能、天赋、任务、锻造、词条、地图）
python3 tools/validate_all.py

# 只验证地图
python3 tools/validate_all.py maps

# 只验证交叉引用
python3 tools/validate_all.py cross

# 查看配置概览
python3 tools/validate_all.py summary
```

---

## 3. 标准检查流程

地图修改后，按以下顺序执行检查：

```
Step 1: validate_all.py maps     → 检查地图配置完整性
Step 2: validate_maps.py          → 检查地图位置、封闭、传送、连通性
Step 3: fix_portals.py            → 修复传送门安全和命名（如有需要）
Step 4: validate_maps.py          → 再次检查确认修复效果
```

### 3.1 快速一键检查

```bash
python3 tools/validate_all.py && python3 tools/validate_maps.py
```

### 3.2 只检查某张地图

`validate_maps.py` 当前不支持单地图参数，会检查所有地图。如需只看某张地图的结果，关注输出中对应的部分即可。

---

## 4. 常见问题诊断与解决

### 4.1 传送门卡死（玩家传送后无法移动）

**症状**: 传送到目标地图后，角色周围全是墙壁/水面，无法走动。

**原因**: 传送门落点坐标在目标地图的不可行走格子上。

**诊断**:
```bash
python3 tools/validate_maps.py
# 查找输出中的 [传送卡死] 行
```

**解决**:
1. 运行 `fix_portals.py` 自动调整传送门位置
2. 或手动修改地图JSON中的 `properties.target_x` / `properties.target_y`，确保落点在可行走格子及其周围也可行走

### 4.2 封闭区域（小区域被墙围死）

**症状**: 地图上某个小区域四面被墙/栅栏等包围，玩家无法进入或离开。

**原因**: 建筑物排列恰好形成封闭圈，或地图生成时边界处理不当。

**诊断**:
```bash
python3 tools/validate_maps.py
# 查找输出中的 [封闭区域] 行
```

**解决**:
1. 运行 `validate_maps.py` 会自动修复（打通边界墙）
2. 或运行 `fix_maps.py` 进行更彻底的修复
3. 手动编辑：将封闭圈边缘的一个不可行走瓦片改为道路(1)或草地(0)

### 4.3 怪物消失

**症状**: 地图上没有怪物出现。

**原因**: 地图JSON的 `monster_groups` 字段为空（village地图除外）。

**诊断**:
```bash
python3 tools/validate_maps.py
# 查找 [怪物消失] 行
```

**解决**:
1. 检查地图生成时是否遗漏了怪物组
2. 运行 `monster_generator.py` 重新生成怪物组
3. 手动在地图JSON中添加 `monster_groups` 配置

### 4.4 地图连通断裂

**症状**: 从某地图无法通过传送门到达其他地图。

**原因**: 传送门配置缺少必要的双向链接。

**诊断**:
```bash
python3 tools/validate_maps.py
# 查看"地图连通性"和"可达性"输出
```

**解决**: 确保每对地图之间至少有一个传送门双向指向对方。例如：
- 王城有 `portal_village` → 青石村，青石村也应该有 `portal_royal_city` → 王城

### 4.5 传送门名称不规范

**症状**: 传送门显示英文名称，或格式不统一。

**规范**: 传送门名称必须使用中文，格式为 `"传送门（前往XXX）"`。

**诊断**: 检查地图JSON中 `objects` 的 `properties.name` 字段。

**解决**:
```bash
python3 tools/fix_portals.py
```

### 4.6 NPC缺失

**症状**: 地图上应该出现的NPC没有显示（如青石村的铁匠、杂货婆等）。

**原因**: 地图JSON的 `npcs` 字段为空或缺少某些NPC引用，但 `npcs.json` 中配置了该NPC属于该地图。

**诊断**:
```bash
python3 tools/validate_maps.py
# 查找 [NPC缺失] 行
```

**解决**:
1. 运行 `validate_maps.py` 会自动在出生点附近放置缺失的NPC
2. 手动在地图JSON的 `npcs` 数组中添加NPC引用，格式为 `{"npc_id": "xxx", "x": 10, "y": 20}`

### 4.7 传送门双向缺失

**症状**: 从A地图可以传送到B地图，但从B地图无法返回A地图。

**原因**: A地图有指向B的传送门，但B地图没有指向A的传送门。

**诊断**:
```bash
python3 tools/validate_all.py cross
# 查找 "缺少双向链接" 警告
```

**解决**: 在缺少传送门的地图中添加对应的传送门。例如：
- 青石村缺少到王城的传送门 → 在 `village.json` 的 `objects` 中添加 `portal_royal_city`

---

## 5. 瓦片参考

检查地图问题时，需要了解哪些瓦片可行走。关键瓦片：

| ID | 名称 | 可行走 | 常见用途 |
|----|------|--------|----------|
| 0 | 草地 | ✓ | 主要地面 |
| 1 | 泥土路 | ✓ | 路径 |
| 6 | 木地板 | ✓ | 房屋内部 |
| 22 | 石板 | ✓ | 城区地面 |
| 2 | 房屋墙 | ✗ | 墙壁 |
| 4 | 树木 | ✗ | 森林障碍 |
| 5 | 水面 | ✗ | 水域 |
| 7 | 栅栏 | ✗ | 围栏 |
| 8 | 石头 | ✗ | 障碍 |
| 13 | 岩壁 | ✗ | 地图边界墙 |
| 33 | 城墙 | ✗ | 城区墙壁 |

完整瓦片定义见 `config/tiles.json`。

---

## 6. 相关文件

| 文件 | 说明 |
|------|------|
| `tools/validate_maps.py` | 地图核心校验与自动修复 |
| `tools/validate_all.py` | 全局配置验证（含地图交叉引用） |
| `tools/fix_portals.py` | 传送门位置安全与命名修复 |
| `tools/fix_maps.py` | 地图封闭修复与数据恢复 |
| `tools/map_generator.py` | 地图生成（支持fix命令） |
| `tools/refactor_maps.py` | 地图重构 |
| `config/maps/*.json` | 地图数据文件 |
| `config/tiles.json` | 瓦片定义 |
| `config/monsters.json` | 怪物定义 |
| `config/npcs.json` | NPC定义（含 map_id 字段用于交叉引用） |