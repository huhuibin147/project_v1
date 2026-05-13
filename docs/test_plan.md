# 自动化测试方案

> **实现状态**：前端 JS 测试（层级5）已全部实现，共 8 个测试套件 142 个测试用例，全部通过。后端测试（层级1-4）待实现。

## 1. 系统架构概览

```
project_v1/
├── backend/           # 后端（Python/FastAPI）
│   ├── main.py        # FastAPI 主服务，API 路由
│   ├── combat_engine.py  # 战斗引擎
│   ├── item_system.py # 物品/背包/商店系统
│   ├── skill_system.py # 技能系统
│   ├── talent_system.py # 天赋系统
│   ├── quest_manager.py # 任务系统
│   ├── player_profile.py # 玩家存档
│   ├── npc_agent.py   # NPC AI 对话
│   ├── llm_client.py  # LLM API 调用
│   └── config.py      # 配置加载
├── frontend/          # 前端（HTML5 Canvas + JS）
│   ├── js/
│   │   ├── game.js    # 游戏主循环
│   │   ├── map.js     # 地图渲染/摄像机/粒子
│   │   ├── player.js  # 玩家控制/移动
│   │   ├── combat.js  # 战斗 UI
│   │   ├── npc.js     # NPC 交互
│   │   ├── dialogue.js # 对话 UI
│   │   ├── inventory.js # 背包/商店 UI
│   │   ├── quest.js   # 任务 UI
│   │   ├── talent.js  # 天赋 UI
│   │   ├── player_info.js # 角色信息
│   │   ├── help.js    # 帮助
│   │   └── start_screen.js # 开始画面
│   └── index.html
├── config/            # 配置数据（JSON）
│   ├── items.json     # 物品
│   ├── monsters.json  # 怪物
│   ├── npcs.json      # NPC
│   ├── skills.json    # 技能
│   ├── talents.json   # 天赋
│   ├── quests.json    # 任务
│   ├── tiles.json     # 瓦片
│   ├── player_default.json # 玩家默认
│   └── maps/          # 地图文件
└── tools/             # 工具脚本
    ├── validate_maps.py  # 地图校验
    ├── validate_all.py   # 全局配置校验
    └── map_generator.py  # 地图生成器
```

## 2. 测试分层

### 层级1：配置数据测试（纯数据校验，无需启动服务）
- 所有 JSON 配置文件格式正确、可解析
- 配置数据内部一致性（ID 匹配、必填字段、数值范围）
- 配置数据交叉引用（物品引用、怪物掉落、NPC 商品、任务目标）

### 层级2：后端逻辑测试（Python 单元测试，无需 LLM）
- 战斗引擎：伤害计算、状态效果、胜负判定
- 物品系统：背包操作、买卖逻辑、装备穿戴
- 技能系统：技能学习条件、技能效果
- 天赋系统：天赋解锁条件、前置依赖
- 任务系统：任务接受、进度更新、完成判定
- 玩家存档：创建、保存、加载、属性计算

### 层级3：地图系统测试（Python，无需启动服务）
- 地图数据完整性（尺寸、瓦片、出生点）
- 地图可达性（从出生点出发的 BFS）
- 封闭区域检测（四面封闭的不可达区域）
- 传送门校验（位置可行走、不重叠、距离足够、连通性）
- 物件位置校验（NPC/宝箱/采集点在可行走格子上）

### 层级4：API 集成测试（需启动 FastAPI 服务）
- 玩家 API：创建角色、获取状态、保存/加载
- 战斗 API：开始战斗、执行动作、结束战斗
- NPC API：对话、商店、任务
- 物品 API：背包操作、装备管理
- 地图 API：加载地图、传送

### 层级5：前端 JS 测试（Jest + jsdom）

#### 5.1 技术选型
- **测试框架**：Jest（最流行的 JS 测试框架）
- **DOM 模拟**：jsdom（Jest 内置）
- **Canvas 模拟**：jest-canvas-mock
- **Fetch 模拟**：jest-fetch-mock 或手动 mock
- **运行环境**：Node.js

#### 5.2 文件结构
```
frontend/
├── js/                          # 源代码
│   ├── managers/
│   │   ├── GameManager.js
│   │   ├── InputManager.js
│   │   ├── LoadingManager.js
│   │   └── RenderManager.js
│   ├── player.js
│   ├── map.js
│   ├── combat.js
│   ├── inventory.js
│   ├── quest.js
│   ├── talent.js
│   ├── ...
│   └── game.js
├── __tests__/                   # 测试文件
│   ├── setup.js                 # 全局测试配置
│   ├── player.test.js           # 玩家移动/位置测试
│   ├── map.test.js              # 地图碰撞/传送门测试
│   ├── combat.test.js           # 战斗状态管理测试
│   ├── inventory.test.js        # 背包逻辑测试
│   ├── quest.test.js            # 任务状态管理测试
│   ├── talent.test.js           # 天赋数据测试
│   ├── GameManager.test.js      # 游戏管理器测试
│   └── game.test.js             # 游戏主逻辑测试
├── package.json                 # Node.js 依赖配置
└── jest.config.js               # Jest 配置
```

#### 5.3 测试用例设计

##### 5.3.1 玩家模块 (player.test.js) ✅ 已实现 (31 用例)

| 编号 | 测试项 | 预期结果 | 状态 |
|------|--------|----------|------|
| PLY-01 | getPlayerSpeed 返回恒定速度 | 返回 BASE_PLAYER_SPEED (6) | ✅ |
| PLY-02 | setPlayerPosition 设置瓦片坐标 | player.x/y = tileX/Y * TILE_SIZE | ✅ |
| PLY-03 | getPlayerTilePosition 返回瓦片坐标 | 正确计算中心点瓦片坐标 | ✅ |
| PLY-04 | 按键 W 触发向上移动 | player.direction = "up", dy < 0 | ✅ |
| PLY-05 | 按键 S 触发向下移动 | player.direction = "down", dy > 0 | ✅ |
| PLY-06 | 按键 A 触发向左移动 | player.direction = "left", dx < 0 | ✅ |
| PLY-07 | 按键 D 触发向右移动 | player.direction = "right", dx > 0 | ✅ |
| PLY-08 | 无按键时 player.moving = false | moving 为 false | ✅ |
| PLY-09 | 有按键时 player.moving = true | moving 为 true | ✅ |
| PLY-10 | 面板打开时 updatePlayer 不移动 | 任何面板打开时直接 return | ✅ |
| PLY-11 | 碰撞检测阻止走入不可行走瓦片 | player 位置不变 | ✅ |
| PLY-12 | 可行走瓦片允许移动 | player 位置更新 | ✅ |

##### 5.3.2 地图模块 (map.test.js) ✅ 已实现 (22 用例)

| 编号 | 测试项 | 预期结果 | 状态 |
|------|--------|----------|------|
| MAP-01 | isWalkable 边界外返回 false | col/row 超出范围返回 false | ✅ |
| MAP-02 | isWalkable 可行走瓦片返回 true | walkable=true 的瓦片 | ✅ |
| MAP-03 | isWalkable 不可行走瓦片返回 false | walkable=false 的瓦片 | ✅ |
| MAP-04 | isWalkable 无地图数据返回 false | currentMap 为 null | ✅ |
| MAP-05 | checkPortalCollision 玩家在传送门上 | 返回传送门对象 | ✅ |
| MAP-06 | checkPortalCollision 玩家不在传送门上 | 返回 null | ✅ |
| MAP-07 | getNearbyInteractableObject 1格内 | 返回物件对象 | ✅ |
| MAP-08 | getNearbyInteractableObject 超出范围 | 返回 null | ✅ |
| MAP-09 | getNearbyInteractableObject 排除传送门 | 传送门不参与 E 键交互 | ✅ |
| MAP-10 | TILE_SIZE 常量值 | 等于 32 | ✅ |

##### 5.3.3 战斗模块 (combat.test.js) ✅ 已实现 (23 用例)

| 编号 | 测试项 | 预期结果 | 状态 |
|------|--------|----------|------|
| CBT-01 | combatOpen 初始为 false | 战斗未开启 | ✅ |
| CBT-02 | checkMonsterCollision 无怪物返回 null | mapMonsters 为空 | ✅ |
| CBT-03 | checkMonsterCollision 战斗开启时返回 null | combatOpen=true | ✅ |
| CBT-04 | checkMonsterCollision 1格内检测到怪物 | 返回怪物对象 | ✅ |
| CBT-05 | checkMonsterCollision 超出范围返回 null | 距离 > 1 | ✅ |
| CBT-06 | getNearestMonster 返回最近怪物 | 2格内最近怪物 | ✅ |
| CBT-07 | getNearestMonster 战斗开启时返回 null | combatOpen=true | ✅ |
| CBT-08 | updateMonsters 巡逻移动 | 怪物向巡逻点移动 | ✅ |
| CBT-09 | updateMonsters 到达巡逻点切换目标 | patrolIndex 递增 | ✅ |
| CBT-10 | updateMonsters 死亡/战斗中不移动 | 位置不变 | ✅ |

##### 5.3.4 背包模块 (inventory.test.js) ✅ 已实现 (19 用例)

| 编号 | 测试项 | 预期结果 | 状态 |
|------|--------|----------|------|
| INV-01 | formatItemStats 空 stats 返回空字符串 | 返回 "" | ✅ |
| INV-02 | formatItemStats 正常格式化 | 返回 "攻+10 防+5" | ✅ |
| INV-03 | RARITY_DEF 包含5个稀有度 | common/uncommon/rare/epic/legendary | ✅ |
| INV-04 | STAT_LABELS_INV 包含5个属性标签 | attack/defense/speed/max_hp/max_mp | ✅ |
| INV-05 | TIER_NAMES 包含3个等级段 | tier1/tier2/tier3 | ✅ |
| INV-06 | ITEMS_PER_PAGE 常量值 | 等于 8 | ✅ |
| INV-07 | inventoryOpen 初始为 false | 背包未开启 | ✅ |
| INV-08 | shopOpen 初始为 false | 商店未开启 | ✅ |

##### 5.3.5 任务模块 (quest.test.js) ✅ 已实现 (20 用例)

| 编号 | 测试项 | 预期结果 | 状态 |
|------|--------|----------|------|
| QST-01 | questOpen 初始为 false | 任务面板未开启 | ✅ |
| QST-02 | questManagerOpen 初始为 false | 任务管理未开启 | ✅ |
| QST-03 | currentQuestTab 初始为 'active' | 默认显示进行中 | ✅ |
| QST-04 | getNpcNameById 已知 NPC 返回名称 | 返回正确名称 | ✅ |
| QST-05 | getNpcNameById 未知 NPC 返回 ID | 返回原始 npcId | ✅ |
| QST-06 | switchQuestTab 切换标签 | currentQuestTab 更新 | ✅ |

##### 5.3.6 天赋模块 (talent.test.js) ✅ 已实现 (7 用例)

| 编号 | 测试项 | 预期结果 | 状态 |
|------|--------|----------|------|
| TAL-01 | TREE_NAMES 包含6个天赋树 | berserk/guard/assassin/trick/element/holy | ✅ |
| TAL-02 | TREE_COLORS 包含6个颜色 | 每个天赋树有对应颜色 | ✅ |
| TAL-03 | talentPanelOpen 初始为 false | 天赋面板未开启 | ✅ |

##### 5.3.7 GameManager 模块 (GameManager.test.js) ✅ 已实现 (15 用例)

| 编号 | 测试项 | 预期结果 | 状态 |
|------|--------|----------|------|
| GM-01 | isStarted 初始返回 false | 游戏未开始 | ✅ |
| GM-02 | isMenuOpen 初始返回 false | 菜单未打开 | ✅ |
| GM-03 | openGameMenu 后 isMenuOpen 返回 true | 菜单打开 | ✅ |
| GM-04 | closeGameMenu 后 isMenuOpen 返回 false | 菜单关闭 | ✅ |
| GM-05 | toggleGameMenu 切换状态 | 开关交替 | ✅ |
| GM-06 | stopGame 后 isStarted 返回 false | 游戏停止 | ✅ |
| GM-07 | getCanvas 返回 canvas 元素 | 非 null | ✅ |

#### 5.4 运行方式
```bash
# 安装依赖
cd frontend && npm install

# 运行所有测试
npm test

# 运行单个测试文件
npx jest player.test.js

# 运行并生成覆盖率报告
npm test -- --coverage

# 监听模式（开发时使用）
npm test -- --watch
```

#### 5.5 测试策略说明

1. **纯逻辑函数优先**：优先测试不依赖 DOM/Canvas/fetch 的纯函数
2. **状态管理测试**：测试全局状态变量的初始值和状态转换
3. **常量验证**：验证配置常量的正确性
4. **DOM 模拟测试**：使用 jsdom 模拟 DOM 环境测试 UI 交互
5. **Canvas Mock**：使用 jest-canvas-mock 避免 Canvas API 报错
6. **Fetch Mock**：手动 mock fetch 避免真实网络请求
7. **不测试渲染**：Canvas 绘制函数（drawPlayer/drawMap 等）不做像素级测试
8. **不测试动画**：动画帧和粒子系统不做测试

#### 5.6 实现细节

**脚本加载方案**：由于源代码使用 IIFE 模式和 `const`/`let` 声明，测试中通过 `loadScript` 函数加载源文件：
- 使用 Node.js `fs.readFileSync` 读取源文件
- 移除 `"use strict"` 指令
- 将 `const`/`let` 替换为 `var` 以暴露变量到全局作用域
- 使用间接 `eval`（`(0, eval)(code)`）在全局作用域执行代码

**环境模拟**：
- `setup.js` 中预设 `TILE_SIZE`、`PLAYER_SIZE` 等全局常量
- 模拟 `requestAnimationFrame`、`fetch`、`console` 等浏览器 API
- 预置完整的 DOM 结构（canvas、面板、按钮等元素）

**测试隔离**：
- 每个 `beforeEach` 中重置全局状态变量
- 使用 `Object.keys(keys).forEach(k => delete keys[k])` 清理按键状态
- 独立设置 `currentMap`、`tileConfig`、`mapObjects` 等地图数据

## 3. 测试用例设计

### 3.1 配置数据测试用例

| 编号 | 测试项 | 预期结果 |
|------|--------|----------|
| CFG-01 | items.json 可解析 | 无异常 |
| CFG-02 | 每个物品有 id/name/type | 无缺失 |
| CFG-03 | 物品 buy_price >= 0 | 无负值 |
| CFG-04 | monsters.json 可解析 | 无异常 |
| CFG-05 | 每个怪物有 stats(hp/attack/defense/speed) > 0 | 无缺失或非正值 |
| CFG-06 | 怪物掉落物品引用存在 | 无悬空引用 |
| CFG-07 | npcs.json 可解析 | 无异常 |
| CFG-08 | NPC 商品物品引用存在 | 无悬空引用 |
| CFG-09 | skills.json 可解析 | 无异常 |
| CFG-10 | 技能职业需求在有效范围内 | warrior/mage/rogue/priest |
| CFG-11 | talents.json 可解析 | 无异常 |
| CFG-12 | 天赋前置依赖存在 | 无悬空引用 |
| CFG-13 | quests.json 可解析 | 无异常 |
| CFG-14 | 任务目标引用存在 | 怪物/物品/地图存在 |
| CFG-15 | 所有 JSON 文件 UTF-8 编码 | 无乱码 |

### 3.2 后端逻辑测试用例

| 编号 | 测试项 | 预期结果 |
|------|--------|----------|
| BKE-01 | 战斗：普通攻击伤害 > 0 | damage > 0 |
| BKE-02 | 战斗：防御减少伤害 | 防御后伤害 < 普通伤害 |
| BKE-03 | 战斗：HP 降为0时判定失败 | phase = DEFEAT |
| BKE-04 | 战斗：怪物 HP 降为0时判定胜利 | phase = VICTORY |
| BKE-05 | 战斗：状态效果（中毒）每回合扣血 | poison_tick > 0 |
| BKE-06 | 战斗：使用治疗药水恢复 HP | hp_after > hp_before |
| BKE-07 | 物品：添加物品到背包 | 数量正确 |
| BKE-08 | 物品：移除背包物品 | 数量减少 |
| BKE-09 | 物品：购买物品扣金币 | gold 减少 |
| BKE-10 | 物品：出售物品加金币 | gold 增加 |
| BKE-11 | 物品：金币不足无法购买 | 购买失败 |
| BKE-12 | 物品：装备穿戴属性加成 | attack/defense 增加 |
| BKE-13 | 技能：满足条件可学习 | can_learn = True |
| BKE-14 | 技能：等级不足不可学习 | can_learn = False |
| BKE-15 | 技能：职业不符不可学习 | can_learn = False |
| BKE-16 | 天赋：等级不足不可解锁 | 5级以下无法解锁 |
| BKE-17 | 天赋：前置天赋未学不可解锁 | 无法跳级 |
| BKE-18 | 玩家：创建默认角色 | 属性为默认值 |
| BKE-19 | 玩家：升级经验计算 | exp_to_next 递增 |
| BKE-20 | 玩家：存档保存和加载一致 | save == load |

### 3.3 地图系统测试用例

| 编号 | 测试项 | 预期结果 |
|------|--------|----------|
| MAP-01 | 地图 JSON 可解析 | 无异常 |
| MAP-02 | 地图尺寸与声明一致 | width/height 匹配 |
| MAP-03 | 玩家出生点在可行走格子上 | walkable = True |
| MAP-04 | 所有 NPC 在可行走格子上 | walkable = True |
| MAP-05 | 所有传送门在可行走格子上 | walkable = True |
| MAP-06 | 所有采集点在可行走格子上 | walkable = True |
| MAP-07 | 无四面封闭区域 | 无不可达可行走区域 |
| MAP-08 | 传送门不重叠 | 同一位置最多1个传送门 |
| MAP-09 | 传送门之间距离 >= 5 | 曼哈顿距离 >= 5 |
| MAP-10 | 地图连通性：所有地图互相可达 | BFS 全连通 |
| MAP-11 | 传送门目标地图存在 | target_map 存在 |
| MAP-12 | 传送门目标位置可行走 | target 位置 walkable |

### 3.4 API 集成测试用例

| 编号 | 测试项 | 预期结果 |
|------|--------|----------|
| API-01 | GET /api/player 返回玩家数据 | 200 + 有效 JSON |
| API-02 | POST /api/player/position 更新位置 | 200 |
| API-03 | POST /api/combat/start 开始战斗 | 200 + session_id |
| API-04 | POST /api/combat/action 攻击 | 200 + 伤害数据 |
| API-05 | GET /api/npc/list 返回 NPC 列表 | 200 + 数组 |
| API-06 | GET /api/quests 返回任务列表 | 200 + 数组 |
| API-07 | GET /api/maps/{id} 返回地图数据 | 200 + 有效 JSON |
| API-08 | GET /api/items 返回物品列表 | 200 + 数组 |
| API-09 | GET /api/skills 返回技能列表 | 200 + 数组 |
| API-10 | GET /api/talents 返回天赋列表 | 200 + 数组 |

## 4. 测试实现方案

### 4.1 技术选型
- **Python 测试框架**：unittest（标准库，无需额外安装）
- **HTTP 测试**：FastAPI TestClient（无需真正启动服务）
- **JS 测试**：暂不实现（前端逻辑依赖 DOM，需要额外搭建环境）

### 4.2 文件结构
```
tests/
├── __init__.py
├── run_tests.py           # 测试入口（一键运行所有测试）
├── test_config_data.py    # 层级1：配置数据测试
├── test_backend_logic.py  # 层级2：后端逻辑测试
├── test_map_system.py     # 层级3：地图系统测试
└── test_api_integration.py # 层级4：API 集成测试
```

### 4.3 运行方式
```bash
# 运行所有测试
python tests/run_tests.py

# 运行单个测试模块
python tests/run_tests.py config
python tests/run_tests.py backend
python tests/run_tests.py map
python tests/run_tests.py api

# 运行单个测试用例
python tests/run_tests.py config CFG-01
python tests/run_tests.py backend BKE-01
```

### 4.4 输出格式
```
============================================================
自动化测试报告
============================================================

[配置数据测试] 15/15 通过 ✓
  CFG-01: items.json 可解析 .................... PASS
  CFG-02: 物品必填字段 ......................... PASS
  ...

[后端逻辑测试] 18/20 通过 ⚠
  BKE-01: 普通攻击伤害 ......................... PASS
  ...
  BKE-19: 存档一致性 ......................... FAIL
    原因: 保存后加载的 gold 不一致

[地图系统测试] 12/12 通过 ✓
  MAP-01: 地图可解析 ........................... PASS
  ...

[API 集成测试] 10/10 通过 ✓
  API-01: 获取玩家数据 ......................... PASS
  ...

============================================================
总计: 55/57 通过 (96.5%)
失败: 2
============================================================
```

## 5. 注意事项

1. **LLM 相关测试不纳入**：npc_agent.py 依赖外部 LLM API，不做自动化测试
2. **前端 JS 测试已实现**：使用 Jest + jsdom，覆盖玩家移动、地图碰撞、战斗状态、背包逻辑、任务管理、天赋数据、GameManager 等模块
3. **API 测试使用 TestClient**：不需要真正启动 HTTP 服务
4. **测试数据隔离**：测试使用临时目录，不修改真实存档
5. **配置数据测试复用**：复用 validate_all.py 的逻辑
6. **地图测试复用**：复用 validate_maps.py 的逻辑
