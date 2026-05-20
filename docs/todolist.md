# Todo 记录区

> 随手记录：优化想法、Bug、待开发功能、设计灵感……
> **不需要分类，不需要排版，直接写。**
> AI 会定期整理到下方区域。
> 已完成项归档至 [changelog.md](changelog.md)

---

## 随手写（从这里开始）
- 史莱姆的护盾有结算吗
- 右上角显示的任务，不会更新状态
- 任务交付没有奖励效果和提示
- 任务要去npc对话中接取和交付
- 商店购买的提示换成toast提示
- 战士自带吸血吗

---

## AI 整理区

> 以下内容将由 AI 根据上方记录自动更新，无需手动编辑。

### 待办

#### 优化

#### Bug 修复
- skillmaster NPC 配置缺失：village 地图引用了 'skillmaster' 但 npcs.json 中不存在该 NPC

#### 新功能

#### 设计 & 其他

---

### 已完成（近期，归档见 [changelog.md](changelog.md)）

#### Bug 修复
- P键传送玩家：openPlayerInfo 中 fetchPlayerInfo 调用 setPlayerPosition 重置玩家位置，已移除该调用
- 技能菜单 updatePlayerInfo 未定义：升级技能时调用不存在的函数导致JS报错，已改为 Object.assign
- 技能菜单互斥逻辑矛盾：可自动关闭的面板同时出现在返回条件和关闭代码中，已修正
- 技能菜单 level_scaling 数据泄露：get_skill_at_level(level=1) 未移除内部字段，已修复
- 技能菜单 Tab 事件重复绑定：每次打开面板重新绑定 click 事件，已添加初始化标志
- 天赋面板互斥逻辑：同步修复与技能菜单相同的互斥问题
