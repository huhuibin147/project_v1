# NPC 系统设计文档

## 概述

NPC 系统包含 LLM 驱动的智能对话、商店交易、特殊服务、好感度系统和日程系统。NPC 由大语言模型驱动，拥有独立性格和情绪，能自然地与玩家交互。

## 系统架构

```
┌──────────────────────────────────────────────────────┐
│                      NPC 系统                        │
├────────────┬────────────┬────────────┬───────────────┤
│  对话系统   │  交易系统   │  服务系统   │  日程系统     │
│  LLM 驱动   │  商店面板   │  治疗/学习  │  位置切换     │
│  意图识别   │  对话交易   │  好感度     │  行为变化     │
│  性格情绪   │  库存管理   │  任务发布   │  交互控制     │
├────────────┴────────────┴────────────┴───────────────┤
│  config/npcs.json  backend/npc_agent.py              │
│  backend/llm_client.py  tools/npc_generator.py       │
└──────────────────────────────────────────────────────┘
```

---

# 第一部分：NPC 对话系统

## LLM 驱动对话

NPC 由大语言模型驱动，每次对话构建包含以下上下文的 Prompt：

```
System: 角色设定 + 性格参数 + 当前情绪/好感度 + 商店库存 + 玩家背包 + 对话历史（最近10轮）
User: 玩家输入
→ LLM 返回结构化 JSON
```

**LLM 输出格式**：
```json
{
  "reply": "NPC 对话（1-3句）",
  "intent": "chat|quest|trade|unknown",
  "mood": "当前情绪",
  "affinity_change": -10到+10,
  "trade_action": null | {"action": "buy|sell", "item_id": "...", "quantity": N}
}
```

## 性格系统

每个 NPC 有 4 个性格参数（0-1），影响 LLM 输出风格：

| 参数 | 说明 |
|------|------|
| friendliness | 友善度 |
| courage | 勇气 |
| greed | 贪婪度 |
| humor | 幽默感 |

## 好感度与情绪

- 好感度范围 0-100，初始值由 NPC 配置定义
- 玩家言行（夸赞、侮辱、帮助）影响好感度变化
- 情绪随对话动态变化（平静/高兴/担忧/生气）
- 好感度影响 NPC 态度和交易行为

## 意图识别

| 意图 | 触发条件 | 行为 |
|------|----------|------|
| chat | 日常对话 | NPC 自由回复 |
| quest | 询问任务 | NPC 描述任务 |
| trade | 明确说"买"/"卖" | 自动执行交易 |
| unknown | 无法识别 | NPC 礼貌回应 |

---

# 第二部分：NPC 交易与服务

## 交易系统

**两种交易路径**：
1. **对话驱动**：玩家在对话中表达交易意图，LLM 识别后自动执行
2. **商店面板**：按 E 打开 NPC 交互选项，选择"商店"直接交易

**交易校验**：
- 购买：金币充足 + NPC 库存足够 + 物品可买
- 出售：玩家持有物品 + 物品可卖 + NPC 金币充足
- NPC 收购的物品存入独立的收购仓库，不混入商店库存

## NPC 服务

### 治疗服务（祭司阿雅）

| 服务 | 效果 | 费用 |
|------|------|------|
| 恢复生命 | 将 HP 恢复至最大值 | 20 金币 |
| 恢复魔法 | 将 MP 恢复至最大值 | 15 金币 |
| 解除异常 | 清除所有负面状态效果 | 30 金币 |

### 技能学习（导师艾尔文）

- 学费：技能书原价 × 1.5 倍
- 限制：职业要求和等级要求与使用技能书相同
- 流程：打开技能学习面板 → 查看可学技能列表 → 支付学费学习

## 当前 NPC

| NPC | 身份 | 位置 | 商品类型 | 特殊服务 |
|-----|------|------|----------|----------|
| 铁匠老王 | 武器商人 | 村庄铁匠铺 | 武器、盾牌、防具、药水、工具 | — |
| 杂货婆刘婶 | 日用品商人 | 村庄杂货铺 | 食物、布料、绷带、法师技能书 | — |
| 祭司阿雅 | 治疗师 | 村庄神殿 | 药水、绷带、解毒药 | 恢复生命/魔法/解除异常 |
| 导师艾尔文 | 技能导师 | 村庄训练场 | 全职业技能书 | 直接学习技能 |
| 采药人老林 | 药草商人 | 森林深处 | 药水、饰品、草药、盗贼技能书 | — |

## NPC 交互面板

不同 NPC 的交互选项不同：

| NPC 类型 | 选项 |
|----------|------|
| 铁匠/商人/采药人 | 1-对话，2-任务，3-商店 |
| 祭司 | 1-对话，2-任务，3-治疗服务，4-商店 |
| 导师 | 1-对话，2-任务，3-学习技能，4-商店 |

---

# 第三部分：NPC 日程系统（规划）

## 设计目标

NPC 按时段切换位置和行为，增强世界真实感。

## 日程数据结构

```json
{
  "npc_id": "blacksmith",
  "schedule": [
    {"time_range": [6, 18], "location": "blacksmith_shop", "behavior": "work", "interactable": true},
    {"time_range": [18, 22], "location": "tavern", "behavior": "rest", "interactable": true},
    {"time_range": [22, 6], "location": "blacksmith_house", "behavior": "sleep", "interactable": false}
  ]
}
```

## 日程规则

- NPC 在指定时段出现在指定位置
- 非交互时段显示"已休息"提示
- 日程切换时 NPC 平滑移动到新位置（可选，或直接切换）

---

# 第四部分：NPC 生成工具

`tools/npc_generator.py` — 用于快速创建和管理游戏 NPC 配置。

## 功能

1. 从模板创建 NPC（商人、铁匠、治疗师、技能导师等）
2. 预设 NPC 快速创建
3. 商店库存分配
4. 批量生成
5. 数据验证
6. 预览

## 使用方法

```bash
cd tools
python npc_generator.py templates          # 查看可用模板
python npc_generator.py presets            # 查看可用预设
python npc_generator.py preset baker       # 从预设创建
python npc_generator.py shop blacksmith    # 更新商店库存
python npc_generator.py validate           # 验证数据
python npc_generator.py apply              # 应用到 npcs.json
```

---

# API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/npc/chat` | POST | 与 NPC 对话 |
| `/api/npc/trade` | POST | 与 NPC 交易 |
| `/api/shop?npc_id=xxx` | GET | NPC 商店库存 |
| `/api/npc/service/heal` | POST | 治疗服务 |
| `/api/npc/service/skills` | GET | 获取可学技能列表 |
| `/api/npc/service/learn_skill` | POST | 学习技能 |

## 文件清单

| 文件 | 说明 |
|------|------|
| `config/npcs.json` | NPC 定义 |
| `backend/npc_agent.py` | NPC Agent |
| `backend/llm_client.py` | LLM 调用 |
| `frontend/js/dialogue.js` | 对话系统 |
| `tools/npc_generator.py` | NPC 生成工具 |
