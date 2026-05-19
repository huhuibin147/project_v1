# NPC 系统全面优化设计

## ✅ 实施状态：全部完成

| Phase | 状态 | 完成日期 |
|-------|------|----------|
| Phase 1: NPC 外观配置化 | ✅ 完成 | 2026-05-19 |
| Phase 2: 交互面板配置化 | ✅ 完成 | 2026-05-19 |
| Phase 3: 好感度影响任务奖励 | ✅ 完成 | 2026-05-19 |
| Phase 4: 记忆摘要生成 | ✅ 完成 | 2026-05-19 |

## 一、当前问题分析

### 1.1 前端外观渲染硬编码

`frontend/js/npc.js` 的 `drawNPC()` 函数使用 if-else 判断 NPC ID 来选择颜色和装饰：

```javascript
const isBlacksmith = npc.npc_id === "blacksmith";
const isPriest = npc.npc_id === "priest";
const isSkillMaster = npc.npc_id === "skill_master";
if (isBlacksmith) { ... }
else if (isPriest) { ... }
else if (isSkillMaster) { ... }
else { /* 默认紫色 */ }
```

**问题**：
- 9 个 NPC 中只有 3 个有专属外观，其余 6 个（merchant、herbalist、cave_explorer、desert_merchant、tavern_keeper、royal_blacksmith）全部显示默认紫色
- 新增 NPC 必须修改前端代码，无法通过配置扩展
- 与怪物外观配置化（已完成）的设计理念不一致

### 1.2 交互面板硬编码

`openNpcInteract()` 使用 if-else 判断 NPC ID 来决定交互按钮：

```javascript
if (npc.npc_id === "priest") {
  html += '商店(3) + 治疗服务(4)';
} else if (npc.npc_id === "skill_master") {
  html += '商店(3) + 学习技能(4)';
} else if (npc.npc_id === "blacksmith") {
  html += '商店(3) + 锻造(4)';
} else {
  html += '商店(3)';
}
```

**问题**：
- 新增 NPC 的交互选项需要改前端代码
- NPC 配置中已有 `services` 字段但前端未使用
- 无法动态扩展 NPC 的服务类型

### 1.3 好感度影响任务奖励未实现

`npc_agent_optimization.md` 标记为 ❌ 未实现。当前好感度仅影响商店折扣和对话风格。

### 1.4 记忆摘要未实现

`npc_agent_optimization.md` 标记为 ❌ 未实现。长期记忆最多 50 条但无自动压缩，注入 LLM 上下文时只取最近 10 条。

---

## 二、优化目标

| 优化项 | 优先级 | 目标 |
|--------|--------|------|
| NPC 外观配置化 | 🔥 P0 | 所有 NPC 通过配置驱动渲染，消除 drawNPC 中的 if-else |
| 交互面板配置化 | 🔥 P0 | 交互选项由 NPC 配置的 services 字段驱动，消除前端硬编码 |
| 好感度影响任务奖励 | ⚡ P1 | 高好感度获得更多金币/经验奖励 |
| 记忆摘要生成 | ⚡ P1 | 长期记忆超过阈值时自动压缩为摘要 |

---

## 三、设计方案

### 3.1 NPC 外观配置化

**设计思路**：在 `npcs.json` 中为每个 NPC 添加 `appearance` 配置，前端使用通用渲染器。

**appearance 配置结构**：

```json
{
  "appearance": {
    "body": { "color": "#8b4513", "light": "#a0522d" },
    "head": { "color": "#d4a574" },
    "hair": { "color": "#4a3728", "style": "default" },
    "accessories": [
      { "type": "beard", "color": "#4a3728" },
      { "type": "tool", "color": "#666", "accent": "#8b6b4a", "position": "right" }
    ]
  }
}
```

**配件类型**：

| type | 说明 | 参数 |
|------|------|------|
| beard | 胡须 | color |
| hood | 兜帽/头巾 | color, accent |
| glasses | 眼镜 | frame_color |
| tool | 手持工具（锤子/法杖/书本） | color, accent, position |
| hat | 帽子 | color |
| cape | 披风 | color |
| apron | 围裙 | color |
| scarf | 围巾 | color |

**通用渲染器**：

```javascript
function drawNPC(ctx, npc) {
  const appearance = npc.appearance || DEFAULT_NPC_APPEARANCE;
  // 1. 阴影
  // 2. 身体 (appearance.body)
  // 3. 头部 (appearance.head)
  // 4. 头发 (appearance.hair)
  // 5. 配件 (appearance.accessories)
  // 6. 眼睛
  // 7. 名字标签 + 交互提示
}
```

**向后兼容**：无 appearance 字段时使用默认配色。

### 3.2 交互面板配置化

**设计思路**：NPC 配置中已有 `services` 字段，前端根据该字段动态生成交互按钮。

**services 字段扩展**：

```json
{
  "services": {
    "heal": {
      "name": "恢复生命",
      "description": "恢复全部生命值",
      "cost": 20,
      "ui_label": "治疗服务",
      "ui_order": 4,
      "ui_handler": "interactHeal"
    },
    "learn_skill": {
      "name": "直接传授",
      "description": "无需技能书，直接学习职业技能",
      "cost_multiplier": 1.5,
      "ui_label": "学习技能",
      "ui_order": 4,
      "ui_handler": "interactLearnSkill"
    },
    "forge": {
      "name": "高级锻造",
      "description": "使用稀有材料锻造高级装备",
      "cost_multiplier": 0.8,
      "ui_label": "锻造",
      "ui_order": 4,
      "ui_handler": "interactForge"
    },
    "rest": {
      "name": "住宿休息",
      "description": "恢复全部HP和MP",
      "cost": 30,
      "ui_label": "住宿休息",
      "ui_order": 4,
      "ui_handler": "interactRest"
    },
    "cave_guide": {
      "name": "洞穴向导",
      "description": "提供洞穴地图信息",
      "cost": 50,
      "ui_label": "洞穴向导",
      "ui_order": 4,
      "ui_handler": "interactCaveGuide"
    },
    "rumor": {
      "name": "打听消息",
      "description": "花点钱打听最新消息",
      "cost": 20,
      "ui_label": "打听消息",
      "ui_order": 4,
      "ui_handler": "interactRumor"
    }
  }
}
```

**前端动态生成**：

```javascript
function openNpcInteract(npc) {
  // 从 NPC 配置获取 services
  const services = npcConfig.services || {};
  
  // 固定选项：对话(1) + 任务(2) + 商店(3)
  let html = '<button class="btn-interact" onclick="interactTalk()">对话 (1)</button>';
  html += '<button class="btn-interact" onclick="interactQuest()">任务 (2)</button>';
  html += '<button class="btn-interact" onclick="interactShop()">商店 (3)</button>';
  
  // 动态选项：从 services 生成
  let serviceIndex = 4;
  for (const [key, svc] of Object.entries(services)) {
    const handler = svc.ui_handler || `interactService`;
    html += `<button class="btn-interact" onclick="${handler}('${npc.npc_id}', '${key}')">${svc.ui_label || svc.name} (${serviceIndex})</button>`;
    serviceIndex++;
  }
  
  actionsDiv.innerHTML = html;
}
```

**需要修改的文件**：
- `config/npcs.json` — 为每个 service 添加 `ui_label`、`ui_order`、`ui_handler`
- `frontend/js/npc.js` — 重构 `openNpcInteract()` 为配置驱动
- `backend/routes/npc.py` — `/api/npcs` 接口返回 services 信息

### 3.3 好感度影响任务奖励

**设计思路**：任务完成时，根据发布 NPC 的好感度等级，给予额外的金币和经验奖励。

**奖励倍率**：

| 好感度等级 | 金币倍率 | 经验倍率 |
|-----------|---------|---------|
| 敌对 (0-20) | 0.8 | 0.9 |
| 冷淡 (21-40) | 0.9 | 0.95 |
| 中性 (41-60) | 1.0 | 1.0 |
| 友善 (61-80) | 1.1 | 1.1 |
| 亲密 (81-100) | 1.2 | 1.25 |

**实现方案**：

在 `npc_affinity.py` 中新增：

```python
def get_quest_reward_multiplier(self) -> dict:
    """获取任务奖励倍率"""
    for min_val, max_val, name, _, _ in self.AFFINITY_LEVELS:
        if min_val <= self.affinity <= max_val:
            if name == "敌对":
                return {"gold": 0.8, "exp": 0.9}
            elif name == "冷淡":
                return {"gold": 0.9, "exp": 0.95}
            elif name == "中性":
                return {"gold": 1.0, "exp": 1.0}
            elif name == "友善":
                return {"gold": 1.1, "exp": 1.1}
            elif name == "亲密":
                return {"gold": 1.2, "exp": 1.25}
    return {"gold": 1.0, "exp": 1.0}
```

在 `quest_manager.py` 的任务完成逻辑中，查询发布 NPC 的好感度，应用奖励倍率。

### 3.4 记忆摘要生成

**设计思路**：当长期记忆超过 30 条时，将低重要性（importance=1）的旧记忆压缩为摘要文本。

**摘要生成逻辑**：

```python
def generate_summary(self) -> str:
    """将旧记忆压缩为摘要"""
    if len(self.long_term_memory) < 30:
        return self.conversation_summary
    
    # 分离：保留高重要性记忆，压缩低重要性记忆
    high_importance = [e for e in self.long_term_memory if e["importance"] >= 3]
    low_importance = [e for e in self.long_term_memory if e["importance"] < 3]
    
    # 按类型分组压缩
    summary_parts = []
    trade_events = [e for e in low_importance if e["type"] == "trade_completed"]
    if trade_events:
        summary_parts.append(f"与玩家进行了 {len(trade_events)} 次交易")
    
    quest_events = [e for e in low_importance if e["type"] == "quest_topic"]
    if quest_events:
        summary_parts.append(f"讨论了 {len(quest_events)} 次任务话题")
    
    # 保留高重要性记忆 + 摘要
    self.long_term_memory = high_importance
    self.conversation_summary = "；".join(summary_parts) if summary_parts else self.conversation_summary
```

---

## 四、实施计划

### Phase 1: NPC 外观配置化

**修改文件**：
1. `config/npcs.json` — 为 9 个 NPC 添加 `appearance` 配置
2. `frontend/js/npc.js` — 重构 `drawNPC()` 为配置驱动渲染器

**步骤**：
1. 为每个 NPC 设计 appearance 配置（颜色、配件）
2. 实现通用渲染器 `drawNPC()` + `drawNPCAccessory()`
3. 替换原 `drawNPC()` 中的 if-else 逻辑
4. 保留向后兼容（无 appearance 时用默认配色）

### Phase 2: 交互面板配置化

**修改文件**：
1. `config/npcs.json` — 为每个 service 添加 `ui_label`、`ui_handler`
2. `frontend/js/npc.js` — 重构 `openNpcInteract()` 为配置驱动
3. `backend/routes/npc.py` — `/api/npcs` 返回 services 信息

**步骤**：
1. 在 NPC 配置中为 services 添加 UI 元数据
2. 修改 `/api/npcs` 接口返回 services
3. 前端 `initNpcs()` 保存 services 配置
4. 重构 `openNpcInteract()` 动态生成按钮
5. 实现各 service handler 的通用调用逻辑

### Phase 3: 好感度影响任务奖励

**修改文件**：
1. `backend/npc_affinity.py` — 新增 `get_quest_reward_multiplier()`
2. `backend/quest_manager.py` — 任务完成时应用好感度奖励倍率
3. `backend/routes/npc.py` — 任务完成 API 返回好感度奖励信息

### Phase 4: 记忆摘要生成

**修改文件**：
1. `backend/npc_memory.py` — 新增 `generate_summary()` 和自动触发逻辑
2. `backend/npc_agent.py` — 对话结束后检查是否需要生成摘要

---

## 五、预期效果

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| NPC 外观差异化 | 3/9 有专属外观 | 9/9 配置化外观 |
| 新增 NPC 工作量 | 需改前端代码 | 只需修改配置文件 |
| 交互选项扩展性 | 硬编码 if-else | 配置驱动，零前端改动 |
| 好感度影响范围 | 仅商店折扣 | 折扣 + 任务奖励 |
| 长期记忆效率 | 50 条无压缩 | 超阈值自动摘要 |

---

## 六、测试用例清单

| 用例 | 类型 | 描述 |
|------|------|------|
| test_npc_appearance_config_exists | 配置 | 每个 NPC 都有 appearance 配置 |
| test_npc_appearance_body_color | 配置 | appearance.body.color 格式正确 |
| test_npc_services_ui_fields | 配置 | 每个 service 有 ui_label 和 ui_handler |
| test_affinity_quest_reward_multiplier | 单元 | 各好感度等级的奖励倍率正确 |
| test_memory_summary_generation | 单元 | 超过 30 条记忆时生成摘要 |
| test_memory_summary_preserves_important | 单元 | 摘要保留高重要性记忆 |
| NPC 外观渲染 | 前端 | drawNPC 正确渲染配置化外观 |
| 交互面板动态生成 | 前端 | openNpcInteract 根据 services 生成按钮 |
