# 自动化测试方案

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

### 层级5：前端 JS 测试（Node.js 环境）
- 玩家移动逻辑
- 地图瓦片碰撞检测
- 战斗 UI 状态管理
- 背包操作逻辑

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
2. **前端 JS 测试暂不实现**：需要 Node.js + jsdom 环境，复杂度高
3. **API 测试使用 TestClient**：不需要真正启动 HTTP 服务
4. **测试数据隔离**：测试使用临时目录，不修改真实存档
5. **配置数据测试复用**：复用 validate_all.py 的逻辑
6. **地图测试复用**：复用 validate_maps.py 的逻辑
