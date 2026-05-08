# LLM NPC 像素风 RPG

一个基于大语言模型的像素风 RPG 游戏。玩家在村庄中探索，与 AI 驱动的 NPC 自由对话、交易物品。NPC 具备独立人格、记忆系统和情感变化。

## 核心特性

- **LLM 驱动对话**：NPC 由大语言模型驱动，支持自由对话，而非预设脚本
- **多 NPC 系统**：每个 NPC 有独立人格、记忆、商店，各自独立运行
- **角色人格系统**：每个 NPC 有独立的性格、说话风格、背景故事
- **多轮记忆**：NPC 记住与玩家的历史对话，实现连贯交互
- **意图识别**：自动识别玩家意图（闲聊/任务/交易）
- **好感度 & 情绪**：NPC 态度随玩家言行动态变化
- **物品交易系统**：全局金币与背包，每个 NPC 卖不同的商品
- **玩家档案**：职业选择、等级经验、属性成长、HP/EXP 条
- **开始界面**：游戏启动时显示开始界面，支持新建冒险、读取存档、继续游戏
- **多存档系统**：3 个存档槽，支持新建、读取、删除存档，存档满时可覆盖
- **玩家名字显示**：玩家角色头顶显示自定义名字
- **游戏菜单**：右上角菜单按钮，包含背包、角色信息、保存游戏、返回主菜单
- **像素风渲染**：Canvas 逐像素绘制，无外部资源依赖
- **地图系统**：数据驱动的瓦片地图，支持摄像机滚动、多区域切换、交互物件
- **交互物件**：宝箱、传送门、采集点、装饰物等可交互物件

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置 LLM

首次运行自动生成配置文件：

```bash
python3.11 main.py
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
python3.11 main.py
```

浏览器打开 `http://localhost:8000`。

按 `Ctrl + C` 停止服务。

## 操作指南

| 按键 | 功能 |
|------|------|
| WASD / 方向键 | 移动角色 |
| E | 与 NPC 交互（需靠近，弹出对话/商店选项） |
| 1/2 | NPC交互选项（1-对话，2-商店） |
| I | 打开背包 |
| P | 打开角色信息 |
| O | 切换游戏菜单（打开/关闭） |
| H | 显示/隐藏帮助提示 |
| 右上角菜单按钮 | 打开游戏菜单（背包、角色、保存、返回主菜单） |

## 项目结构

```
project_v1/
├── config.json.example         # LLM 配置模板
├── config.json                 # LLM 实际配置（不提交）
├── config/
│   ├── npcs.json               # NPC 定义（属性、性格、商店）
│   ├── items.json              # 物品定义（名称、类型、价格）
│   ├── player_default.json     # 玩家默认属性和职业配置
│   ├── tiles.json              # 瓦片类型定义
│   └── maps/                   # 地图数据
│       ├── village.json        #   村庄地图
│       └── forest.json         #   森林地图
├── data/
│   ├── save_1/                 # 存档槽 1
│   │   ├── player.json         #   玩家数据
│   │   └── {npc_id}.json       #   NPC 数据（对话历史、商店库存等）
│   ├── save_2/                 # 存档槽 2
│   └── save_3/                 # 存档槽 3
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
        ├── map.js              # 地图系统（瓦片、摄像机、物件）
        ├── player.js           # 玩家控制
        ├── npc.js              # NPC 渲染与交互
        ├── dialogue.js         # 对话系统
        ├── inventory.js        # 物品系统 UI
        ├── player_info.js      # 玩家信息面板
        ├── start_screen.js     # 开始界面逻辑
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
- [地图系统设计](map_system_design.md) — 地图系统设计方案

## 地图系统

当前支持的地图：

| 地图 | 名称 | 尺寸 | 说明 |
|------|------|------|------|
| village | 青石村 | 25x18 | 起始村庄，有铁匠铺和杂货铺 |
| forest | 森林 | 40x30 | 村庄北方的森林区域 |

交互物件类型：

| 类型 | 说明 | 交互方式 |
|------|------|----------|
| portal | 传送门 | 踩上去自动触发 |
| chest | 宝箱 | 按 E 打开 |
| gather | 采集点 | 按 E 采集 |
| decoration | 装饰物 | 按 E 查看 |

## 当前 NPC

| NPC | 身份 | 位置 | 商品 |
|-----|------|------|------|
| 铁匠老王 | 武器商人 | 铁匠铺 | 武器、防具、工具、药水 |
| 刘婶 | 日用品商人 | 杂货铺 | 食物、布料、绷带、蜡烛 |

## 更新日志

详见 [更新日志](changelog.md)

## 扩展方向

- 更多 NPC（酒馆老板、村长、猎人）
- 任务系统（NPC 下发任务，完成后解锁新对话）
- 装备系统（物品可装备，影响角色属性）
- 传闻系统（NPC 间信息传递）
- 日程系统（NPC 按时间切换行为）
