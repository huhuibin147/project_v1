# Todo 记录区

> 随手记录：优化想法、Bug、待开发功能、设计灵感……
> **不需要分类，不需要排版，直接写。**
> AI 会定期整理到下方区域。
> 已完成项归档至 [changelog.md](changelog.md)

---

## 随手写（从这里开始）
---

## AI 整理区

> 以下内容将由 AI 根据上方记录自动更新，无需手动编辑。

### 待办

#### 优化

#### Bug 修复

#### 新功能

#### 设计 & 其他

---

### 已完成（近期，归档见 [changelog.md](changelog.md)）

#### Bug 修复
- 修复右上角任务不更新状态：endCombat() 未调用 updateQuestTracker()，已添加调用
- 修复 skillmaster NPC 配置缺失：village.json 中有重复的 skillmaster 和 skill_master 条目，已删除无效的 skillmaster 条目
- P键传送玩家：openPlayerInfo 中 fetchPlayerInfo 调用 setPlayerPosition 重置玩家位置，已移除该调用
- 技能菜单 updatePlayerInfo 未定义：升级技能时调用不存在的函数导致JS报错，已改为 Object.assign
- 技能菜单互斥逻辑矛盾：可自动关闭的面板同时出现在返回条件和关闭代码中，已修正
- 技能菜单 level_scaling 数据泄露：get_skill_at_level(level=1) 未移除内部字段，已修复
- 技能菜单 Tab 事件重复绑定：每次打开面板重新绑定 click 事件，已添加初始化标志
- 天赋面板互斥逻辑：同步修复与技能菜单相同的互斥问题

#### 新功能
- 任务交付奖励提示：完成任务时显示 toast 通知，展示获得的奖励内容
- 任务 NPC 对话限制：Q键任务面板中接取/交付任务需到对应NPC处，非NPC面板操作会提示
- 商店购买 toast 提示：购买成功/失败时弹出 toast 通知
- Toast 通知系统：新增全局 showToast() 函数，支持 success/reward/error/info 四种类型

#### 排查确认
- 史莱姆护盾结算逻辑：确认正常，turn.py 中 _apply_damage_to_monster 正确处理护盾吸收和消耗
- 战士吸血机制：确认战士无自带吸血，技能中也不含吸血效果

#### 文档整理
- 整合 docs 下同类文档：将优化文档合并到对应核心系统文档的"相关优化记录"章节
  - 战斗系统：combat_engine_refactor / combat_ui_redesign / multi_enemy_boss_design / elemental_system_design → combat_system.md
  - NPC 系统：npc_system_optimization / npc_agent_optimization → npc_system.md
  - 地图系统：map_redesign / map_system_optimization / map_generator_optimization / map_validation_guide → exploration_and_map_system.md
  - 锻造词条：forge_affix_optimization → forge_and_affix_system.md
  - 物品经济：item_system_optimization / item_shop_ui_optimization → items_and_economy_system.md
  - 技能天赋：skill_menu_and_upgrade → skill_and_talent_system.md
  - 任务剧情：quest_system_optimization → quest_and_story_system.md
  - 怪物系统：monster_skill_expansion / monster_sprite_config_design → monster_system.md（新建）
- 更新 readme.md 文档链接，移除已删除文档引用
- 更新 game_design.md 中失效的文档引用
