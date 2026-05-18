# 怪物精灵配置化设计文档

> 更新日期：2026-05-18
> 状态：✅ 已完成

---

## 一、当前问题分析

### 问题描述

`drawMonsterSpriteOnCanvas` 函数（[combat.js:293](file:///Users/huhuibin/code/aiproj/project_v1/frontend/js/combat.js#L293)）中，每种怪物的精灵绘制逻辑用 `if-else` 硬编码，共 7 个分支 + 1 个默认分支：

```javascript
if (monsterId === "slime") { ... }
else if (monsterId === "wild_wolf") { ... }
else if (monsterId === "forest_spider") { ... }
else if (monsterId === "goblin") { ... }
else if (monsterId === "dark_bear") { ... }
else if (monsterId === "shadow_tree_spirit") { ... }
else { /* 默认 */ }
```

### 影响范围

| 问题 | 影响 |
|------|------|
| 新增怪物必须改代码 | 每加一种怪物就要加一个 `else if` 分支，违反开闭原则 |
| 代码随怪物数量线性增长 | 当前 15 种怪物只有 7 个分支（8 种走默认），后续全部配置化后代码量不变 |
| 精灵绘制参数不可复用 | 相似形状的怪物（如两种蜘蛛）无法共享基础形状模板 |
| 无法热更新 | 修改精灵外观必须重新部署前端代码 |

### 当前怪物精灵绘制分析

逐个分析现有 15 种怪物的绘制特征：

| 怪物 ID | 当前分支 | 绘制特征 |
|---------|---------|---------|
| slime | ✅ 独立 | 椭圆身体 + 高光条 + 白眼黑瞳 |
| wild_wolf | ✅ 独立 | 横向身体 + 竖耳 + 黄眼 + 腿 |
| forest_spider | ✅ 独立 | 中心体 + 4 条腿(对角) + 红眼 |
| goblin | ✅ 独立 | 方形身体 + 尖耳 + 红眼 + 腿 |
| dark_bear | ✅ 独立 | 大横向身体 + 圆耳 + 红眼 + 腿 |
| shadow_tree_spirit | ✅ 独立 | 方形身体 + 树冠 + 紫眼绿瞳 + 根 |
| cave_bat | ❌ 默认 | 方形身体 + 尖顶 |
| cave_spider | ❌ 默认 | 方形身体 + 尖顶 |
| skeleton | ❌ 默认 | 方形身体 + 尖顶 |
| zombie | ❌ 默认 | 方形身体 + 尖顶 |
| dark_knight | ❌ 默认 | 方形身体 + 尖顶 |
| skeleton_king | ❌ 默认 | 方形身体 + 尖顶 |
| scorpion | ❌ 默认 | 方形身体 + 尖顶 |
| sand_worm | ❌ 默认 | 方形身体 + 尖顶 |
| mummy | ❌ 默认 | 方形身体 + 尖顶 |
| desert_basilisk | ❌ 默认 | 方形身体 + 尖顶 |
| city_guard | ❌ 默认 | 方形身体 + 尖顶 |
| shadow_mage | ❌ 默认 | 方形身体 + 尖顶 |

**关键发现**：9 种怪物走默认分支，外观几乎完全相同（只有颜色不同），用户体验差。

---

## 二、优化目标

1. **配置驱动**：所有怪物精灵由 `monsters.json` 中的 `sprite` 字段定义，无需改代码
2. **通用渲染器**：一个 `drawSprite(ctx, config)` 函数替代所有 `if-else`
3. **部件组合**：通过基础形状 + 部件组合，让每种怪物都有独特外观
4. **向后兼容**：保留 `sprite_color` / `sprite_accent` 字段，新增 `sprite` 字段
5. **BOSS 阶段支持**：不同阶段可覆盖精灵配置（如变色、变大）

---

## 三、设计方案

### 3.1 精灵配置格式

在 `monsters.json` 中为每个怪物新增 `sprite` 字段：

```json
{
  "sprite": {
    "body": {
      "shape": "rounded_rect",
      "color": "#44cc44",
      "x": 1, "y": 4, "w": 6, "h": 3,
      "radius": 2
    },
    "parts": [
      {
        "type": "rect",
        "color": "#228822",
        "x": 2, "y": 3, "w": 4, "h": 1
      },
      {
        "type": "eyes",
        "style": "round",
        "y": 5,
        "spacing": 2,
        "eye_color": "#fff",
        "pupil_color": "#000",
        "pupil_size": 0.5
      }
    ]
  }
}
```

### 3.2 坐标系统

采用 8×8 网格坐标（与现有 `p = s / 8` 一致），所有位置和尺寸用网格单位表示：

```
(0,0) ─────────────────── (8,0)
  │                         │
  │     精灵绘制区域         │
  │     (8×8 网格)          │
  │                         │
(0,8) ─────────────────── (8,8)
```

- `x`, `y`：部件左上角坐标（网格单位）
- `w`, `h`：部件宽高（网格单位）
- 渲染时乘以 `p = canvas.width / 8` 转换为像素

### 3.3 部件类型

| 类型 | 说明 | 必需参数 | 可选参数 |
|------|------|----------|----------|
| `rect` | 矩形 | `color`, `x`, `y`, `w`, `h` | — |
| `rounded_rect` | 圆角矩形 | `color`, `x`, `y`, `w`, `h` | `radius` (默认 1) |
| `circle` | 圆形 | `color`, `cx`, `cy`, `r` | — |
| `ellipse` | 椭圆 | `color`, `cx`, `cy`, `rx`, `ry` | — |
| `triangle` | 三角形 | `color`, `x1`, `y1`, `x2`, `y2`, `x3`, `y3` | — |
| `eyes` | 眼睛对 | `y`, `spacing` | `style` (round/slit), `eye_color`, `pupil_color`, `pupil_size` |
| `legs` | 腿部 | `y`, `count`, `spacing`, `w`, `h` | `color` (默认 body color) |
| `horns` | 角/耳 | `y`, `spacing`, `w`, `h` | `color`, `style` (pointed/round) |
| `shadow` | 地面阴影 | — | `x`, `y`, `w`, `h` (有默认值) |

### 3.4 通用渲染器

```javascript
function drawSprite(ctx, spriteConfig, gridSize) {
  const p = gridSize;
  
  // 1. 绘制阴影（默认行为）
  drawShadow(ctx, p, spriteConfig.shadow);
  
  // 2. 绘制 body
  drawBody(ctx, p, spriteConfig.body);
  
  // 3. 按 parts 数组顺序绘制部件
  for (const part of spriteConfig.parts) {
    drawPart(ctx, p, part, spriteConfig.body);
  }
}
```

### 3.5 BOSS 阶段覆盖

BOSS 怪物在不同阶段可覆盖精灵配置：

```json
{
  "sprite": { ... },
  "sprite_phases": {
    "2": {
      "body": { "color": "#ff4444" },
      "tint": "rgba(255, 0, 0, 0.15)"
    }
  }
}
```

阶段覆盖使用**深度合并**：只覆盖指定的字段，其余继承基础配置。

### 3.6 向后兼容

- 如果怪物没有 `sprite` 字段，使用 `sprite_color` + `sprite_accent` 生成默认配置
- 默认配置 = 方形身体 + 尖顶装饰（与当前 `else` 分支行为一致）

```javascript
function getDefaultSprite(color, accent) {
  return {
    body: { shape: "rect", color: color, x: 2, y: 3, w: 4, h: 4 },
    parts: [
      { type: "rect", color: accent, x: 3, y: 1, w: 2, h: 3 }
    ]
  };
}
```

---

## 四、实施计划

### Phase 1：通用渲染器 + 全部怪物配置化

| 步骤 | 内容 | 涉及文件 |
|------|------|----------|
| ① | 实现 `drawSprite` 通用渲染器及所有部件绘制函数 | `combat.js` |
| ② | 为全部 15 种怪物设计 `sprite` 配置 | `monsters.json` |
| ③ | 重构 `drawMonsterSpriteOnCanvas` 为配置驱动 | `combat.js` |
| ④ | BOSS 阶段精灵覆盖支持 | `combat.js` + `monsters.json` |
| ⑤ | 删除 `if-else` 分支，保留向后兼容默认配置 | `combat.js` |
| ⑥ | 运行测试验证 | — |

### 各怪物精灵设计方案

| 怪物 | body | parts | 设计说明 |
|------|------|-------|---------|
| slime | 圆角矩形(绿色) | 高光条 + 圆眼 | 保持现有外观 |
| wild_wolf | 矩形(灰色) | 竖耳 + 黄眼 + 腿 | 保持现有外观 |
| forest_spider | 矩形(紫色) | 4条对角腿 + 红眼 | 保持现有外观 |
| goblin | 矩形(黄绿) | 尖耳 + 红眼 + 腿 | 保持现有外观 |
| dark_bear | 大矩形(棕色) | 圆耳 + 红眼 + 腿 | 保持现有外观 |
| shadow_tree_spirit | 矩形(暗绿) | 树冠 + 紫眼绿瞳 + 根 | 保持现有外观 |
| cave_bat | 矩形(暗紫) | 翅膀 + 红眼 | 新设计：蝙蝠翅膀 |
| cave_spider | 矩形(深紫) | 4条腿 + 红眼 + 蛛网纹 | 新设计：大蜘蛛 |
| skeleton | 矩形(米白) | 骷髅头(空洞眼) + 肋骨 | 新设计：骷髅 |
| zombie | 矩形(暗绿) | 伸出的手臂 + 空洞眼 | 新设计：僵尸 |
| dark_knight | 矩形(深蓝) | 头盔 + 剑 + 盾 | 新设计：骑士 |
| skeleton_king | 矩形(金黄) | 王冠 + 骷髅头 + 权杖 | 新设计：骷髅王 |
| scorpion | 矩形(土黄) | 钳子 + 尾针 + 眼 | 新设计：蝎子 |
| sand_worm | 圆角矩形(沙色) | 大嘴 + 分节身体 | 新设计：沙虫 |
| mummy | 矩形(米色) | 绷带条纹 + 空洞眼 | 新设计：木乃伊 |
| desert_basilisk | 矩形(褐黄) | 竖瞳眼 + 脊刺 | 新设计：蛇蜥 |
| city_guard | 矩形(灰蓝) | 头盔 + 剑 | 新设计：卫兵 |
| shadow_mage | 矩形(暗紫) | 法帽 + 法杖 + 发光眼 | 新设计：法师 |

---

## 五、预期效果

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 新增怪物需改代码 | 是（加 else if） | 否（只改 JSON） |
| drawMonsterSpriteOnCanvas 行数 | ~100 行 if-else | ~30 行通用渲染 |
| 怪物外观区分度 | 7 种独特 + 9 种雷同 | 18 种各不相同 |
| 精灵可配置性 | 硬编码 | JSON 配置驱动 |
| BOSS 阶段视觉变化 | 仅红色叠加 | 可自定义颜色/部件/缩放 |

---

## 六、测试用例清单

| 用例 | 类型 | 描述 |
|------|------|------|
| test_sprite_config_completeness | 配置 | 所有怪物都有 sprite 字段 |
| test_sprite_body_required_fields | 配置 | sprite.body 包含 shape/color/x/y/w/h |
| test_sprite_parts_valid_types | 配置 | parts 中 type 只允许已知类型 |
| test_draw_sprite_no_config | 功能 | 无 sprite 时使用默认配置渲染 |
| test_draw_sprite_with_config | 功能 | 有 sprite 时按配置渲染 |
| test_boss_phase_sprite_override | 功能 | BOSS 阶段覆盖精灵配置 |
| test_sprite_backward_compat | 功能 | sprite_color/sprite_accent 仍可用于默认配置 |

---

## 七、完成状态

> 更新日期：2026-05-18
> 状态：✅ 已完成

| 优化项 | 状态 | 说明 |
|--------|------|------|
| 通用渲染器 drawSprite + drawSpritePart | ✅ 完成 | 支持 rect/rounded_rect/circle/ellipse/triangle/eyes/legs/horns 8 种部件 |
| 全部 15 种怪物 sprite 配置 | ✅ 完成 | 每种怪物都有独特外观，不再有雷同的默认分支 |
| drawMonsterSpriteOnCanvas 配置驱动 | ✅ 完成 | 删除全部 if-else，改为读取 config.sprite |
| BOSS 阶段精灵覆盖 | ✅ 完成 | sprite_phases 支持深度合并，骷髅王/暗影树精各 3 阶段变色 |
| 向后兼容默认配置 | ✅ 完成 | 无 sprite 字段时使用 sprite_color/sprite_accent 生成默认配置 |
| 配置测试 | ✅ 完成 | 验证所有怪物 sprite 字段完整性 |

**涉及修改文件**：
- `frontend/js/combat.js` — 新增 drawSpritePart/drawSprite/drawSpritePart/getDefaultSprite/deepMergeSprite 函数，重构 drawMonsterSpriteOnCanvas
- `config/monsters.json` — 为全部 15 种怪物添加 sprite 配置，2 个 BOSS 添加 sprite_phases
