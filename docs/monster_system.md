# 怪物系统设计文档

> 整合自怪物技能扩展和精灵配置化设计文档
> 状态：✅ 已完成

---

## 一、怪物技能系统

### 技能类型

怪物支持 8 种技能类型：

| 类型 | 说明 | 关键参数 |
|------|------|----------|
| `apply_effect` | 施加状态效果 | effect, chance, duration, value |
| `aoe_attack` | 群体攻击 | damage_multiplier |
| `self_heal` | 自我治疗 | heal_pct |
| `summon` | 召唤小怪 | summon_ids, summon_count |
| `shield` | 获得护盾 | shield_value/shield_pct, duration |
| `elemental_attack` | 属性攻击 | element, damage_multiplier, effect |
| `buff_self` | 自我增益 | buffs (attack_up/defense_up/speed_up) |
| `drain` | 吸血攻击 | damage_multiplier, heal_pct |

### 召唤系统

- 战斗中怪物总数上限 3 只（含 BOSS），超出则召唤失败改为普攻
- 召唤出的怪物 HP 为原配置的 50%
- BOSS 专属技能，普通怪物不使用

### 怪物 Buff 效果

`effects.py` 中 `StatBuffHandler` 扩展支持怪物 buff，buff 过期后属性恢复基础值。

### 前端意图图标

后端 `next_action` 扩展为包含技能类型的对象 `{"action": "special", "special_type": "summon"}`，前端根据 `special_type` 显示对应图标。

---

## 二、怪物精灵配置化

### 配置格式

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
      { "type": "rect", "color": "#228822", "x": 2, "y": 3, "w": 4, "h": 1 },
      { "type": "eyes", "style": "round", "y": 5, "spacing": 2, "eye_color": "#fff", "pupil_color": "#000" }
    ]
  }
}
```

### 部件类型

| 类型 | 说明 | 必需参数 |
|------|------|----------|
| `rect` | 矩形 | color, x, y, w, h |
| `rounded_rect` | 圆角矩形 | color, x, y, w, h, radius |
| `circle` | 圆形 | color, cx, cy, r |
| `ellipse` | 椭圆 | color, cx, cy, rx, ry |
| `triangle` | 三角形 | color, x1, y1, x2, y2, x3, y3 |
| `eyes` | 眼睛对 | y, spacing |
| `legs` | 腿部 | y, count, spacing, w, h |
| `horns` | 角/耳 | y, spacing, w, h |

### 通用渲染器

`drawSprite(ctx, spriteConfig, gridSize)` 替代所有 if-else 分支，按 body → parts 顺序渲染。

### BOSS 阶段精灵覆盖

`sprite_phases` 支持深度合并，不同阶段可覆盖颜色/部件/缩放。

### 向后兼容

无 `sprite` 字段时使用 `sprite_color` + `sprite_accent` 生成默认配置。

---

## 三、完成状态

| 优化项 | 状态 | 说明 |
|--------|------|------|
| 5 种新技能类型 | ✅ | summon/shield/elemental_attack/buff_self/drain |
| 怪物配置差异化 | ✅ | 15 种怪物全部配置独特技能 |
| 前端意图图标 | ✅ | combat.js INTENT_ICONS + SPECIAL_TYPE_ICONS |
| 通用渲染器 | ✅ | drawSprite + drawSpritePart，8 种部件类型 |
| 全部怪物 sprite 配置 | ✅ | 18 种怪物各有独特外观 |
| BOSS 阶段精灵覆盖 | ✅ | sprite_phases 深度合并 |
| 向后兼容 | ✅ | 无 sprite 时用 sprite_color/sprite_accent |
