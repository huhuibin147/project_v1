# 多敌人与 BOSS 战设计文档

> 生成日期：2026-05-13
> 目标：实现 Phase 1.3 — 多敌人战斗与 BOSS 阶段转换机制

---

## 一、功能概述

| 功能 | 说明 |
|------|------|
| 多敌人战斗 | CombatSession 支持 1-3 个怪物，玩家需选择攻击目标 |
| BOSS 阶段转换 | BOSS 怪物根据 HP 阈值切换 AI 行为和属性加成 |
| BOSS 免疫 | BOSS 免疫眩晕/冻结，精英 BOSS 额外免疫中毒 |
| AOE 技能 | 群体伤害技能，命中多目标时伤害递减 |
| 暗影树精 | 新 BOSS 怪物（Lv.8，3 阶段），配置于幽暗森林深处 |

---

## 二、数据结构设计

### 2.1 MonsterInstance — 战斗中的怪物实例

```python
class MonsterInstance:
    def __init__(self, index: int, monster_id: str, config: dict):
        self.index = index                    # 在列表中的索引（0-2）
        self.monster_id = monster_id
        self.config = config                  # 怪物配置（来自 monsters.json）
        self.hp = config["stats"]["hp"]
        self.max_hp = config["stats"]["hp"]
        self.defending = False
        self.effects: list[StatusEffect] = []
        self.current_phase: int = 0           # BOSS 当前阶段索引
        self.phase_changed: bool = False      # 本回合是否发生阶段转换

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def is_boss(self) -> bool:
        return self.config.get("type") == "boss"

    @property
    def hp_ratio(self) -> float:
        return self.hp / self.max_hp if self.max_hp > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "monster_id": self.monster_id,
            "name": self.config["name"],
            "hp": self.hp,
            "max_hp": self.max_hp,
            "alive": self.alive,
            "defending": self.defending,
            "effects": [e.to_dict() for e in self.effects],
            "is_boss": self.is_boss,
            "current_phase": self.current_phase,
            "phase_name": self._get_phase_name(),
            "sprite_color": self.config.get("sprite_color", "#888"),
            "sprite_accent": self.config.get("sprite_accent", "#555"),
        }

    def _get_phase_name(self) -> str:
        phases = self.config.get("phases", [])
        if phases and 0 <= self.current_phase < len(phases):
            return phases[self.current_phase]["name"]
        return ""
```

### 2.2 CombatSession 改造

```python
class CombatSession:
    def __init__(self, session_id, monster_configs: list[dict], player_snapshot):
        # --- 怪物列表（核心变更） ---
        self.monsters: list[MonsterInstance] = []
        for idx, mc in enumerate(monster_configs):
            mid = mc.get("id", f"monster_{idx}")
            self.monsters.append(MonsterInstance(idx, mid, mc))

        # --- 玩家属性（不变） ---
        self.player_hp = ...
        # ... 其余玩家属性不变

        # --- 目标选择 ---
        self.target_index: int = 0   # 当前选中的怪物索引

        # --- 其余字段不变 ---
        self.phase = CombatPhase.PLAYER_TURN
        self.turn_count = 0
        self.log = []
        ...
```

**关键变更：**
- 移除 `monster_id`, `monster_config`, `monster_hp`, `monster_max_hp`, `monster_defending`, `monster_effects` 单怪物字段
- 新增 `monsters: list[MonsterInstance]` 和 `target_index: int`
- 向后兼容：提供 `@property` 访问器以兼容旧代码路径

### 2.3 地图怪物组配置

```json
{
  "monsters": [
    {
      "monster_id": "wild_wolf",
      "x": 40,
      "y": 20,
      "patrol": [{"x": 40, "y": 20}, {"x": 42, "y": 20}]
    },
    {
      "monster_group": [
        {"monster_id": "wild_wolf", "x": 40, "y": 20},
        {"monster_id": "wild_wolf", "x": 41, "y": 21}
      ]
    }
  ]
}
```

**规则：**
- 单怪物仍用 `monster_id` + `x/y` 格式（向后兼容）
- 怪物组用 `monster_group` 数组，包含 2-3 个怪物
- 怪物组的 `instance_id` 格式：`group_{idx}`（整组共享一个 instance_id）
- 碰到组内任意怪物即触发整组战斗

### 2.4 BOSS 阶段配置

```json
{
  "shadow_tree_spirit": {
    "id": "shadow_tree_spirit",
    "name": "暗影树精",
    "type": "boss",
    "stats": { "hp": 400, "attack": 22, "defense": 10, "speed": 8 },
    "phases": [
      {
        "name": "沉睡",
        "hp_threshold": 1.0,
        "ai": {"attack": 0.4, "defend": 0.3, "special": 0.3},
        "special": {
          "type": "apply_effect",
          "effect": "poison",
          "chance": 0.4,
          "duration": 3,
          "message": "暗影树精释放毒雾！"
        }
      },
      {
        "name": "觉醒",
        "hp_threshold": 0.6,
        "ai": {"attack": 0.5, "defend": 0.15, "special": 0.35},
        "stat_boost": {"attack": 1.3},
        "special": {
          "type": "apply_effect",
          "effect": "burn",
          "chance": 0.35,
          "duration": 2,
          "value": 5,
          "message": "暗影树精点燃暗焰！"
        }
      },
      {
        "name": "狂暴",
        "hp_threshold": 0.25,
        "ai": {"attack": 0.65, "defend": 0.0, "special": 0.35},
        "stat_boost": {"attack": 1.6, "defense": 0.8},
        "special": {
          "type": "apply_effect",
          "effect": "stun",
          "chance": 0.25,
          "duration": 1,
          "message": "暗影树精发动暗影震击！"
        }
      }
    ]
  }
}
```

**阶段转换规则：**
1. 每回合开始时检查 BOSS HP 比例
2. 若 HP ≤ `hp_threshold` 且 `current_phase` < 阶段索引，则转换
3. 转换时：更新 `current_phase`，应用 `stat_boost`，记录日志
4. `stat_boost` 中的值是乘法系数（1.3 = 攻击力 × 1.3）
5. 阶段只升不降

---

## 三、战斗流程变更

### 3.1 多敌人回合流程

```
1. 处理玩家状态效果（中毒/灼烧等）
2. 检查玩家是否死亡
3. 玩家行动（攻击/防御/技能/物品/逃跑）
   - 攻击和单体技能 → 对 target_index 指定的怪物生效
   - AOE 技能 → 对所有存活怪物生效（伤害递减）
   - 防御/物品/逃跑 → 不需要选择目标
4. 检查所有怪物是否死亡 → 胜利
5. 处理每个存活怪物的状态效果
6. 再次检查怪物死亡（毒/灼烧可能致死）
7. 按速度排序，存活怪物依次行动
8. 检查玩家是否死亡 → 失败
9. 重置防御状态，减少冷却
```

### 3.2 目标选择

- 玩家攻击/单体技能需要指定目标
- API 请求新增 `target_index` 字段
- 前端点击怪物头像/血条切换目标
- 默认选中第一个存活怪物
- 当前目标死亡时自动切换到下一个存活怪物

### 3.3 AOE 技能

- 技能配置新增 `"aoe": true` 字段
- AOE 伤害递减规则：
  - 1 目标：100% 伤害
  - 2 目标：80% 伤害
  - 3 目标：65% 伤害
- AOE 技能的效果（中毒/灼烧等）独立判定每个目标

### 3.4 逃跑

- 多敌人战斗中逃跑概率取所有怪物中最高速度计算
- 逃跑成功则逃离整场战斗

### 3.5 胜利奖励

- 击败所有怪物后统一结算
- 经验值 = 所有怪物 exp_reward 之和
- 金币 = 所有怪物 gold_reward 之和
- 掉落 = 所有怪物 drops 合并

---

## 四、BOSS 阶段转换机制

### 4.1 转换检测

在 `monster_ai.py` 的 `decide_action()` 中，战斗决策前先检查阶段：

```python
def check_boss_phase(monster: MonsterInstance) -> dict | None:
    if not monster.is_boss:
        return None
    phases = monster.config.get("phases", [])
    if not phases:
        return None

    for i, phase in enumerate(phases):
        if i <= monster.current_phase:
            continue
        if monster.hp_ratio <= phase["hp_threshold"]:
            monster.current_phase = i
            monster.phase_changed = True
            # 应用属性加成
            stat_boost = phase.get("stat_boost", {})
            if "attack" in stat_boost:
                monster.config["stats"]["attack"] = int(
                    monster.config["stats"]["attack"] * stat_boost["attack"]
                )
            if "defense" in stat_boost:
                monster.config["stats"]["defense"] = int(
                    monster.config["stats"]["defense"] * stat_boost["defense"]
                )
            return phase
    return None
```

### 4.2 阶段 AI 覆盖

BOSS 阶段配置中的 `ai` 字段覆盖怪物默认 AI 权重：

```python
def decide_action(session, monster: MonsterInstance) -> str:
    ai = monster.config.get("ai", {})
    # BOSS 阶段覆盖
    if monster.is_boss:
        phases = monster.config.get("phases", [])
        if phases and 0 <= monster.current_phase < len(phases):
            phase_ai = phases[monster.current_phase].get("ai")
            if phase_ai:
                attack_w = int(phase_ai.get("attack", 0.5) * 100)
                defend_w = int(phase_ai.get("defend", 0.3) * 100)
                special_w = int(phase_ai.get("special", 0.2) * 100)
                # 使用阶段 AI 权重...
```

### 4.3 BOSS 阶段特殊技能

每个阶段可以有独立的 `special` 技能，覆盖默认的 `ai.special`：

```python
def get_boss_special(monster: MonsterInstance) -> dict | None:
    if not monster.is_boss:
        return monster.config.get("ai", {}).get("special")
    phases = monster.config.get("phases", [])
    if phases and 0 <= monster.current_phase < len(phases):
        return phases[monster.current_phase].get("special")
    return monster.config.get("ai", {}).get("special")
```

### 4.4 BOSS 免疫

```python
BOSS_IMMUNITY = {
    "boss": {"stun", "freeze"},           # BOSS 免疫眩晕和冻结
    "elite_boss": {"stun", "freeze", "poison"},  # 精英 BOSS 额外免疫中毒
}

def is_immune(monster: MonsterInstance, effect_type: str) -> bool:
    monster_type = monster.config.get("type", "normal")
    tags = monster.config.get("tags", [])
    immune_set = set()
    if monster_type == "boss":
        immune_set = BOSS_IMMUNITY.get("boss", set())
        if "elite" in tags:
            immune_set = immune_set | BOSS_IMMUNITY.get("elite_boss", set())
    return effect_type in immune_set
```

---

## 五、API 变更

### 5.1 POST /api/combat/start

**请求（新增 monster_group 支持）：**
```json
{
  "monster_instance_id": "group_3",
  "map_id": "forest"
}
```

**响应（多怪物）：**
```json
{
  "session_id": "abc123",
  "monsters": [
    {
      "index": 0,
      "monster_id": "wild_wolf",
      "name": "野狼",
      "hp": 45,
      "max_hp": 45,
      "alive": true,
      "sprite_color": "#888",
      "sprite_accent": "#555",
      "is_boss": false,
      "current_phase": 0,
      "phase_name": ""
    },
    {
      "index": 1,
      "monster_id": "wild_wolf",
      "name": "野狼",
      "hp": 45,
      "max_hp": 45,
      "alive": true,
      "sprite_color": "#888",
      "sprite_accent": "#555",
      "is_boss": false,
      "current_phase": 0,
      "phase_name": ""
    }
  ],
  "target_index": 0,
  "player": { ... },
  "phase": "player_turn",
  "log": []
}
```

### 5.2 POST /api/combat/action

**请求（新增 target_index）：**
```json
{
  "session_id": "abc123",
  "action": "attack",
  "target_index": 1,
  "item_id": null,
  "skill_id": null
}
```

**响应（多怪物状态）：**
```json
{
  "session_id": "abc123",
  "phase": "player_turn",
  "turn_count": 2,
  "monsters": [
    { "index": 0, "name": "野狼", "hp": 22, "max_hp": 45, "alive": true, ... },
    { "index": 1, "name": "野狼", "hp": 0, "max_hp": 45, "alive": false, ... }
  ],
  "target_index": 0,
  "player_hp": 100,
  "player_max_hp": 120,
  "log": [ ... ],
  "player_effects": [],
  "skills": [ ... ]
}
```

### 5.3 向后兼容

- 单怪物战斗仍使用 `monster_instance_id` 格式 `"{monster_id}_{idx}"`
- 响应中同时返回 `monsters` 列表和旧的 `monster_*` 字段（取第一个怪物）
- 前端优先使用 `monsters` 列表，旧字段仅作降级

---

## 六、前端变更

### 6.1 多怪物渲染

战斗面板怪物区域改为横向排列，最多 3 个怪物：

```html
<div id="combat-monster-area">
  <!-- 动态生成，每个怪物一个 combat-monster-slot -->
  <div class="combat-monster-slot selected" data-index="0" onclick="selectTarget(0)">
    <canvas class="monster-sprite-canvas" width="64" height="64"></canvas>
    <div class="combat-monster-name">野狼</div>
    <div class="combat-hp-bar-row">...</div>
    <div class="combat-monster-effects">...</div>
  </div>
  <!-- 更多怪物... -->
</div>
```

### 6.2 目标选择

- 点击怪物 slot 切换 `target_index`
- 选中状态：高亮边框 + "目标" 标签
- 死亡怪物：灰化 + 叠加 " defeated" 效果
- 自动选中：当前目标死亡时切换到下一个存活怪物

### 6.3 BOSS 阶段视觉

- 阶段转换时：全屏闪烁 + 阶段名称显示
- BOSS 血条下方显示阶段名称标签
- 狂暴阶段：怪物精灵添加红色滤镜

### 6.4 技能面板

- AOE 技能标注 "群体" 标签
- 使用 AOE 技能不需要选择目标

---

## 七、暗影树精配置

```json
{
  "shadow_tree_spirit": {
    "id": "shadow_tree_spirit",
    "name": "暗影树精",
    "description": "沉睡在幽暗森林深处的远古树精，被暗影侵蚀后化为恐怖的存在",
    "type": "boss",
    "sprite_color": "#2a4a2a",
    "sprite_accent": "#1a3a1a",
    "stats": {
      "hp": 400,
      "attack": 22,
      "defense": 10,
      "speed": 8
    },
    "exp_reward": 300,
    "gold_reward": [100, 200],
    "drops": [
      {"item_id": "ancient_shard", "chance": 0.7},
      {"item_id": "shadow_essence", "chance": 0.5},
      {"item_id": "herb", "chance": 0.4},
      {"item_id": "strength_elixir", "chance": 0.15},
      {"item_id": "nature_staff", "chance": 0.05}
    ],
    "ai": {
      "behavior": "defensive",
      "attack_weight": 40,
      "defend_weight": 30,
      "special_weight": 30,
      "special": {
        "type": "apply_effect",
        "effect": "poison",
        "chance": 0.4,
        "duration": 3,
        "value": 0,
        "message": "暗影树精释放毒雾！"
      }
    },
    "phases": [
      {
        "name": "沉睡",
        "hp_threshold": 1.0,
        "ai": {"attack": 0.4, "defend": 0.3, "special": 0.3},
        "special": {
          "type": "apply_effect",
          "effect": "poison",
          "chance": 0.4,
          "duration": 3,
          "message": "暗影树精释放毒雾！"
        }
      },
      {
        "name": "觉醒",
        "hp_threshold": 0.6,
        "ai": {"attack": 0.5, "defend": 0.15, "special": 0.35},
        "stat_boost": {"attack": 1.3},
        "special": {
          "type": "apply_effect",
          "effect": "burn",
          "chance": 0.35,
          "duration": 2,
          "value": 5,
          "message": "暗影树精点燃暗焰！"
        }
      },
      {
        "name": "狂暴",
        "hp_threshold": 0.25,
        "ai": {"attack": 0.65, "defend": 0.0, "special": 0.35},
        "stat_boost": {"attack": 1.6, "defense": 0.8},
        "special": {
          "type": "apply_effect",
          "effect": "stun",
          "chance": 0.25,
          "duration": 1,
          "message": "暗影树精发动暗影震击！"
        }
      }
    ],
    "level": 8,
    "tags": ["plant", "forest", "boss", "legendary"]
  }
}
```

---

## 八、文件变更清单

### 后端修改

| 文件 | 变更内容 | 状态 |
|------|----------|------|
| `backend/combat/session.py` | 新增 MonsterInstance 类，CombatSession 改为多怪物列表 | ✅ 已实现 |
| `backend/combat/monster_ai.py` | BOSS 阶段检测、阶段 AI 覆盖、BOSS 免疫 | ✅ 已实现 |
| `backend/combat/turn.py` | 多敌人回合流程、目标选择、AOE 伤害递减 | ✅ 已实现 |
| `backend/combat/skills.py` | AOE 技能支持 | ✅ 已实现 |
| `backend/combat/effects.py` | BOSS 免疫检查 | ✅ 已实现 |
| `backend/combat/engine.py` | 更新导出 | ✅ 已实现 |
| `backend/routes/combat.py` | 多怪物 API、怪物组启动战斗 | ✅ 已实现 |
| `backend/routes/models.py` | CombatActionRequest 新增 target_index | ✅ 已实现 |
| `backend/skill_system.py` | AOE 技能元数据支持 | ✅ 已实现 |

### 配置修改

| 文件 | 变更内容 | 状态 |
|------|----------|------|
| `config/monsters.json` | 新增暗影树精 | ✅ 已实现 |
| `config/maps/forest.json` | 新增暗影树精 BOSS 和怪物组 | ✅ 已实现 |
| `config/skills.json` | 现有技能添加 aoe 字段（可选） | ✅ 已实现 |

### 前端修改

| 文件 | 变更内容 | 状态 |
|------|----------|------|
| `frontend/js/combat.js` | 多怪物渲染、目标选择、BOSS 阶段视觉、Tab 切换目标 | ✅ 已实现 |
| `frontend/index.html` | 多怪物 UI 布局、目标提示 | ✅ 已实现 |
| `frontend/css/style.css` | 多怪物样式、BOSS 阶段样式、AOE 标签 | ✅ 已实现 |

---

## 九、测试要点

1. ✅ 单怪物战斗不受影响（向后兼容）
2. ✅ 2-3 怪物组战斗正常
3. ✅ BOSS 阶段转换在正确 HP 阈值触发
4. ✅ BOSS 免疫眩晕/冻结
5. ✅ AOE 技能伤害递减正确
6. ✅ 目标死亡后自动切换
7. ✅ 胜利奖励正确合并
8. ✅ 逃跑概率基于最快怪物计算
9. ✅ 前端正确渲染多怪物和目标选择
10. ✅ 105 个后端测试全部通过

---

## 十、实现状态

**状态：✅ 已完成**

**实现日期：** 2026-05-14

**测试状态：** 105 个测试全部通过

**核心功能：**
- 多敌人战斗（1-3 个怪物）
- BOSS 阶段转换（沉睡 → 觉醒 → 狂暴）
- BOSS 免疫机制
- AOE 群体技能
- 目标选择系统（点击/TAB 切换）
- 怪物组配置
- 前端多怪物渲染与动画
