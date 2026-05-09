# 怪物生成器

`tools/monster_generator.py` — 用于快速创建和管理游戏怪物配置。

## 功能概览

1. **从模板创建怪物**：普通、精英、BOSS、谨慎型、防御型
2. **预设怪物快速创建**：骷髅兵、僵尸、幽灵、黑暗骑士、远古巨龙等
3. **掉落物品分配**：根据怪物种族自动分配掉落
4. **批量生成**：一次性生成多个同类型怪物
5. **数据验证**：检查怪物配置完整性
6. **预览**：查看怪物属性分布和统计

## 使用方法

```bash
cd tools

# 查看可用模板
python monster_generator.py templates

# 查看可用预设
python monster_generator.py presets

# 快捷创建怪物
python monster_generator.py create-normal skeleton "骷髅兵" 2
python monster_generator.py create-elite dark_knight "黑暗骑士" 8
python monster_generator.py create-boss dragon "远古巨龙" 15

# 从预设创建
python monster_generator.py preset skeleton
python monster_generator.py preset dragon

# 分配掉落物品
python monster_generator.py drops skeleton material weapon
python monster_generator.py drops dragon material consumable

# 批量生成怪物
python monster_generator.py batch normal 5 "1-3" "森林"
python monster_generator.py batch elite 3 "5-8" "洞穴"

# 验证和预览
python monster_generator.py validate       # 验证所有怪物配置
python monster_generator.py list           # 列出所有怪物
python monster_generator.py preview        # 预览属性分布

# 应用到 monsters.json
python monster_generator.py apply
```

## 怪物模板

| 模板名 | 类型 | HP倍率 | ATK倍率 | DEF倍率 | SPD倍率 | 经验倍率 | AI行为 |
|--------|------|--------|---------|---------|---------|---------|--------|
| normal | 普通 | ×1.0 | ×1.0 | ×1.0 | ×1.0 | ×1.0 | 攻击型 |
| elite | 精英 | ×2.0 | ×1.5 | ×1.3 | ×1.2 | ×2.5 | 攻击型 |
| boss | BOSS | ×4.0 | ×2.0 | ×1.8 | ×1.0 | ×5.0 | 防御型 |
| cautious | 普通 | ×0.9 | ×0.9 | ×1.2 | ×1.1 | ×1.0 | 谨慎型 |
| defensive | 普通 | ×1.3 | ×0.8 | ×1.5 | ×0.7 | ×1.1 | 防御型 |

### 模板属性说明

- **普通怪物**：基础属性，适合普通战斗
- **精英怪物**：属性大幅提升，掉落更好，头顶显示 ★ 标记
- **BOSS**：极高属性，丰富掉落，特殊技能
- **谨慎型**：低血量时增加防御概率
- **防御型**：高防御低攻击，适合坦克型怪物

## 预设怪物

| 预设名 | 名称 | 类型 | 等级 | 种族 | 特殊技能 |
|--------|------|------|------|------|---------|
| skeleton | 骷髅兵 | 普通 | 2 | 亡灵 | 无 |
| zombie | 僵尸 | 普通 | 2 | 亡灵 | 无 |
| ghost | 幽灵 | 谨慎 | 4 | 亡灵 | 恐惧效果 |
| giant_spider | 巨型蜘蛛 | 普通 | 3 | 野兽 | 中毒效果 |
| orc | 兽人战士 | 普通 | 4 | 人形 | 无 |
| dark_knight | 黑暗骑士 | 精英 | 8 | 人形 | 流血效果 |
| vampire | 吸血鬼伯爵 | 精英 | 10 | 亡灵 | 生命吸取 |
| dragon | 远古巨龙 | BOSS | 15 | 龙 | 灼烧效果 |

### 特殊技能类型

| 类型 | 效果 | 示例 |
|------|------|------|
| apply_effect | 施加状态效果 | 中毒、灼烧、恐惧、流血 |
| life_drain | 吸取生命 | 吸血鬼恢复HP |

## 怪物数据结构

生成的怪物配置遵循以下结构：

```json
{
  "id": "monster_id",
  "name": "怪物名称",
  "description": "怪物描述",
  "type": "normal",
  "sprite_color": "#44cc44",
  "sprite_accent": "#228822",
  "stats": {
    "hp": 30,
    "attack": 8,
    "defense": 3,
    "speed": 5
  },
  "exp_reward": 15,
  "gold_reward": [5, 15],
  "drops": [
    {"item_id": "herb", "chance": 0.3},
    {"item_id": "mushroom", "chance": 0.2}
  ],
  "ai": {
    "behavior": "aggressive",
    "attack_weight": 80,
    "defend_weight": 15,
    "special_weight": 5,
    "special": {
      "type": "apply_effect",
      "effect": "poison",
      "chance": 0.3,
      "duration": 3,
      "value": 0,
      "message": "毒蛛喷出毒液！"
    }
  },
  "level": 1,
  "tags": ["slime", "forest", "common"]
}
```

## 掉落物品规则

| 种族 | 材料掉落 | 消耗品掉落 | 装备掉落 | 基础概率 |
|------|---------|-----------|---------|---------|
| undead | 兽骨、魔晶、布料 | 生命药水、净化药水 | 武器、饰品 | 40% |
| beast | 狼皮、兽骨、毒液囊 | 生命药水、解毒药 | 防具、饰品 | 50% |
| humanoid | 铁矿、布料、钢锭 | 生命药水、绷带、魔力药水 | 武器、防具、盾牌 | 35% |
| dragon | 龙鳞、魔晶、晶片 | 强效生命药水、力量药剂 | 武器、防具、饰品 | 70% |
| default | 草药、蘑菇、布料 | 生命药水、绷带 | 无 | 30% |

### 掉落概率调整

- **精英怪物**：装备掉落概率提升，可能掉落稀有装备
- **BOSS**：额外掉落史诗/传说装备，概率 10%
- **等级影响**：高等级怪物金币奖励随等级提升

## 批量生成示例

为森林地图生成一批怪物：

```bash
# 生成5只 Lv.1-3 的普通怪物
python monster_generator.py batch normal 5 "1-3" "森林"

# 生成3只 Lv.5-8 的精英怪物
python monster_generator.py batch elite 3 "5-8" "洞穴"

# 生成1只 Lv.10 的 BOSS
python monster_generator.py batch boss 1 "10" "遗迹"

# 应用所有生成的怪物
python monster_generator.py apply
```

## 扩展模板

如需添加新的怪物模板，编辑 `tools/monster_generator.py` 中的 `MONSTER_TEMPLATES` 字典：

```python
MONSTER_TEMPLATES["ranged"] = {
    "type": "normal",
    "hp_multiplier": 0.8,
    "attack_multiplier": 1.2,
    "defense_multiplier": 0.6,
    "speed_multiplier": 1.3,
    "exp_multiplier": 1.0,
    "gold_range": (5, 20),
    "drop_count": (1, 3),
    "ai_behavior": "aggressive",
    "attack_weight": 85,
    "defend_weight": 10,
    "special_weight": 5,
    "description_suffix": ""
}
```

## 验证检查项

`validate` 命令会检查以下内容：

- 必填字段完整性（id, name, description, type, stats 等）
- stats 四项属性（hp, attack, defense, speed）是否大于 0
- AI 配置格式（behavior, attack_weight, defend_weight, special_weight）
- 掉落物品格式（item_id, chance）
- 掉落概率是否在 0-1 范围内
