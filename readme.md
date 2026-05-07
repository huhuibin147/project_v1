# LLM NPC 像素风 RPG

一个基于大语言模型的像素风 RPG 游戏。玩家在村庄中探索，与 AI 驱动的 NPC 自由对话、交易物品。NPC 具备独立人格、记忆系统和情感变化。

## 核心特性

- **LLM 驱动对话**：NPC 由大语言模型驱动，支持自由对话，而非预设脚本
- **多 NPC 系统**：每个 NPC 有独立人格、记忆、商店，各自独立运行
- **角色人格系统**：每个 NPC 有独立的性格、说话风格、背景故事
- **多轮记忆**：NPC 记住与玩家的历史对话，实现连贯交互
- **意图识别**：自动识别玩家意图（闲聊/任务/交易）
- **好感度 & 情绪**：NPC 态度随玩家言行动态变化
- **物品交易系统**：金币、背包、商店，每个 NPC 卖不同的商品
- **玩家档案**：职业选择、等级经验、属性成长、HP/EXP 条
- **像素风渲染**：Canvas 逐像素绘制，无外部资源依赖

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置 LLM

首次运行自动生成配置文件：

```bash
python main.py
```

按提示编辑 `config.json`，填入 API 信息：

```json
{
  "api_key": "你的 API Key",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini"
}
```

支持任何 OpenAI 兼容接口（DeepSeek、通义千问、Ollama 等）。

### 3. 启动游戏

```bash
python main.py
```

浏览器打开 `http://localhost:8000`。

## 操作指南

| 按键 | 功能 |
|------|------|
| WASD / 方向键 | 移动角色 |
| E | 与 NPC 对话（需靠近） |
| I | 打开背包（内含商店入口） |
| P | 打开角色信息 |
| ESC | 关闭当前面板 |

## 项目结构

```
project_v1/
├── config.json.example         # LLM 配置模板
├── config.json                 # LLM 实际配置（不提交）
├── config/
│   ├── npcs.json               # NPC 定义（属性、性格、商店）
│   ├── items.json              # 物品定义（名称、类型、价格）
│   └── player_default.json     # 玩家默认属性和职业配置
├── backend/
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置加载
│   ├── llm_client.py           # LLM 调用封装
│   ├── npc_agent.py            # NPC Agent 核心逻辑
│   ├── item_system.py          # 物品系统
│   ├── player_profile.py       # 玩家档案系统
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── css/style.css
    └── js/
        ├── map.js              # 瓦片地图
        ├── player.js           # 玩家控制
        ├── npc.js              # NPC 渲染与交互
        ├── dialogue.js         # 对话系统
        ├── inventory.js        # 物品系统 UI
        ├── player_info.js      # 玩家信息面板
        └── game.js             # 游戏主循环
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML5 Canvas + 原生 JavaScript |
| 后端 | Python FastAPI |
| LLM | OpenAI 兼容协议 |

## 文档

- [Phase 1 实现文档](phase1_npc_game.md) — 使用方法、架构设计、API 接口
- [物品系统设计](item_system.md) — 物品/背包/交易系统设计
- [LLM NPC Agent 设计](llm_npc_agent.md) — NPC Agent 完整设计方案
- [AI Agent 游戏思路](ai_agent_game_ideas.md) — AI Agent 游戏方向项目思路

## 当前 NPC

| NPC | 身份 | 位置 | 商品 |
|-----|------|------|------|
| 铁匠老王 | 武器商人 | 铁匠铺 | 武器、防具、工具、药水 |
| 刘婶 | 日用品商人 | 杂货铺 | 食物、布料、绷带、蜡烛 |

## 扩展方向

- 更多 NPC（酒馆老板、村长、猎人）
- 任务系统（NPC 下发任务，完成后解锁新对话）
- 装备系统（物品可装备，影响角色属性）
- 传闻系统（NPC 间信息传递）
- 日程系统（NPC 按时间切换行为）
