# LLM NPC 像素风 RPG

一个基于大语言模型的像素风 RPG 游戏。玩家在村庄和森林中探索，与 AI 驱动的 NPC 自由对话、交易物品、战斗怪物。NPC 具备独立人格、记忆系统和情感变化。

## 核心特性

- **LLM 驱动对话**：NPC 由大语言模型驱动，支持自由对话，本地意图分类器降低 LLM 调用频率 50%+
- **多 NPC 系统**：每个 NPC 有独立人格、记忆、商店，各自独立运行
- **角色人格系统**：每个 NPC 有独立的性格、说话风格、背景故事
- **分层记忆系统**：短期记忆（最近 10 条对话）+ 长期记忆（关键事件记录，最多 50 条）
- **意图识别**：本地规则 + 关键词匹配，交易意图可完全本地处理，响应时间 <0.5 秒
- **好感度 & 情绪**：NPC 态度随玩家言行动态变化，好感度影响商店折扣（敌对 +20% → 亲密 -20%）和对话风格
- **物品交易系统**：全局金币与背包，每个 NPC 卖不同的商品，支持本地意图识别快速交易，物品效果配置化，分类系统（消耗品/食物/技能书/材料/装备/任务物品），智能堆叠逻辑
- **对话缓存**：常见问题回答缓存 1 小时，相同好感度等级下直接返回
- **玩家档案**：职业选择、等级经验、属性成长、HP/MP/EXP 条、存档备份与恢复、属性计算缓存
- **装备系统**：5个装备槽位，装备影响属性，稀有度和等级段系统
- **锻造系统**：25种锻造配方，消耗材料打造装备，支持稀有度抽取、失败返还和保底机制
- **词条系统**：5大类别30+词条，装备附带随机词条，战斗中触发各种特效（灼烧/雷击/吸血/反伤等），支持词条洗练和动态权重
- **模块化战斗引擎**：策略模式状态效果、事件驱动词条/天赋触发、属性克制系统（火>草>水>火）
- **回合制战斗**：地图怪物、回合制战斗、经验掉落、状态效果
- **多敌人战斗**：支持 1-3 个怪物同时战斗，目标选择系统（点击/TAB 切换）
- **BOSS 战系统**：多阶段转换、免疫机制、狂暴状态、阶段转换动画
- **群体技能**：AOE 技能支持，伤害递减机制
- **怪物组系统**：地图可配置怪物组（狼群、蜘蛛巢穴等）
- **战斗 UI 优化**：日志虚拟滚动、伤害数字弹出动画、状态效果脉冲动画、HP 条平滑过渡
- **背包系统优化**：搜索过滤、词条简要描述、拖拽装备到槽位、DocumentFragment 批量渲染
- **地图渲染优化**：离屏 Canvas 缓存地面层、地图切换自动重建缓存
- **角色动画增强**：攻击挥砍动画（4方向）、受击红色闪烁、武器轨迹与冲击波
- **摄像机平滑跟随**：线性插值平滑过渡，告别生硬跳转
- **对话系统优化**：气泡动画与打字机效果、LLM 等待 Loading 反馈与防重复发送、对话历史展开/收起
- **锻造系统优化**：锻造进度动画（进度条+火花粒子）、配方搜索（按名称/产出/材料模糊搜索）
- **技能系统**：消耗 MP 释放职业技能，通过技能书学习新技能
- **任务系统**：NPC 下发任务，进度追踪，完成奖励，任务链自动接续，跨时区每日重置
- **开始界面**：游戏启动时显示开始界面，支持新建冒险、读取存档、继续游戏
- **多存档系统**：3 个存档槽，支持新建、读取、删除存档，存档满时可覆盖
- **全屏渲染**：Canvas 自动填充整个浏览器窗口，支持响应式调整
- **像素风渲染**：Canvas 逐像素绘制，无外部资源依赖
- **地图系统**：数据驱动的瓦片地图，支持摄像机滚动、多区域切换、交互物件

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

### 4. 运行前端测试

```bash
cd frontend
npm install
npm test
```

测试覆盖玩家移动、地图碰撞、战斗状态、背包逻辑、任务管理、天赋数据、GameManager 等核心模块。详见[测试方案文档](docs/test_plan.md)。

## 操作指南

| 按键 | 功能 |
|------|------|
| WASD / 方向键 | 移动角色 |
| E | 与 NPC/物件/怪物交互（需靠近） |
| I | 打开背包 |
| P | 打开角色信息 |
| Q | 打开任务管理 |
| O | 切换游戏菜单 |
| H | 显示/隐藏帮助提示 |

### 战斗操作

| 按键 | 功能 |
|------|------|
| 1 | 攻击 |
| 2 | 防御（减少50%伤害） |
| 3 | 技能（打开技能选择面板） |
| 4 | 使用物品（打开物品选择面板） |
| 5 | 逃跑（基于速度的概率） |
| Tab | 切换攻击目标（多敌人时） |

## 项目结构

```
project_v1/
├── config.json.example         # LLM 配置模板
├── config.json                 # LLM 实际配置（不提交）
├── config/                     # 游戏数据配置（NPC、物品、怪物、技能、任务、地图、词条、锻造配方等）
├── data/                       # 存档数据
├── backend/                    # 后端服务（FastAPI）
│   ├── main.py                 # FastAPI 入口（路由注册 + 异常处理）
│   ├── routes/                 # 模块化路由
│   │   ├── context.py          # 共享应用上下文
│   │   ├── models.py           # Pydantic 请求/响应模型
│   │   ├── npc.py              # NPC 路由
│   │   ├── player.py           # 玩家路由
│   │   ├── map.py              # 地图路由
│   │   ├── combat.py           # 战斗路由
│   │   ├── forge.py            # 锻造/词条路由
│   │   └── quest.py            # 任务/天赋路由
│   └── combat/                 # 战斗引擎模块
│       ├── session.py          # 战斗会话管理
│       ├── damage.py           # 伤害计算（含属性克制）
│       ├── effects.py          # 状态效果系统（策略模式）
│       ├── events.py           # 事件驱动系统（词条/天赋触发）
│       ├── monster_ai.py       # 怪物 AI 决策
│       ├── skills.py           # 技能执行
│       ├── turn.py             # 回合解析核心
│       └── engine.py           # 对外统一接口
├── frontend/                   # 前端界面（HTML5 Canvas + JS）
│   ├── __tests__/              # 前端自动化测试
│   │   ├── setup.js              # 全局测试环境配置
│   │   ├── player.test.js        # 玩家移动/位置测试
│   │   ├── map.test.js           # 地图碰撞/传送门测试
│   │   ├── combat.test.js        # 战斗状态管理测试
│   │   ├── inventory.test.js     # 背包逻辑测试
│   │   ├── quest.test.js         # 任务状态管理测试
│   │   ├── talent.test.js        # 天赋数据测试
│   │   ├── GameManager.test.js   # 游戏管理器测试
│   │   └── game.test.js          # 游戏主逻辑测试
│   ├── package.json             # Node.js 依赖配置
│   ├── jest.config.js           # Jest 测试配置
│   └── js/
│       └── managers/           # 管理器模块
│           ├── GameManager.js    # 游戏核心管理器
│           ├── InputManager.js   # 输入管理器
│           ├── RenderManager.js  # 渲染管理器
│           └── LoadingManager.js # 加载管理器
├── docs/                       # 设计文档
│   ├── game_design.md          #   游戏设计与优化方向总览
└── tools/                      # 工具脚本（物品/NPC/怪物/任务生成器）
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML5 Canvas + 原生 JavaScript |
| 后端 | Python FastAPI |
| LLM | OpenAI 兼容协议 |

## 文档

详细系统设计请查看 [游戏设计文档](docs/game_design.md)，包含：

- 架构设计、玩家系统、技能系统
- NPC 系统、地图系统、战斗系统
- 物品与药水系统、装备系统
- 任务系统、扩展方向

其他专项文档：
- [自动化测试方案](docs/test_plan.md)
- [物品与装备系统](docs/items_equipment.md)
- [战斗系统设计](docs/combat_system.md)
- [锻造与词条系统](docs/forge_and_affix_system.md)
- [锻造与词条优化设计](docs/forge_affix_optimization.md)
- [战斗引擎重构设计](docs/combat_engine_refactor.md)
- [玩家档案优化设计](docs/player_profile_refactor.md)
- [NPC 对话优化设计](docs/npc_agent_optimization.md)
- [物品系统优化设计](docs/item_system_optimization.md)
- [任务系统优化设计](docs/quest_system_optimization.md)
- [前端游戏主循环优化设计](docs/frontend_gamejs_optimization.md)
- [多敌人与 BOSS 战设计](docs/multi_enemy_boss_design.md)
- [物品生成器](docs/item_generator.md)
- [地图生成器](docs/map_generator.md)
- [游戏设计与优化方向](docs/game_design.md)

## 更新日志

详见 [更新日志](changelog.md)
