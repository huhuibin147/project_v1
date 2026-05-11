#!/usr/bin/env python3
"""技能和天赋配置生成器 - 生成/验证/管理技能与天赋配置"""
import json
import random
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
SKILLS_FILE = CONFIG_DIR / "skills.json"
TALENTS_FILE = CONFIG_DIR / "talents.json"

CLASSES = ["warrior", "mage", "rogue", "priest"]

SKILL_TEMPLATES = {
    "warrior": {
        "damage": [
            {"name": "猛击", "power": 1.3, "mp_cost": 8, "cooldown": 0, "effects": []},
            {"name": "旋风斩", "power": 1.0, "mp_cost": 15, "cooldown": 2, "effects": [{"type": "aoe", "target": "all_enemies"}]},
            {"name": "碎甲击", "power": 1.2, "mp_cost": 12, "cooldown": 1, "effects": [{"type": "defense_down", "value": 20, "duration": 2}]},
            {"name": "致命一击", "power": 2.0, "mp_cost": 25, "cooldown": 4, "effects": [{"type": "crit_boost", "value": 30}]},
        ],
        "buff": [
            {"name": "战吼", "power": 0, "mp_cost": 10, "cooldown": 3, "effects": [{"type": "attack_up", "value": 20, "duration": 3}]},
            {"name": "铁壁", "power": 0, "mp_cost": 12, "cooldown": 4, "effects": [{"type": "defense_up", "value": 40, "duration": 2}]},
        ],
    },
    "mage": {
        "damage": [
            {"name": "火球术", "power": 1.5, "mp_cost": 12, "cooldown": 0, "effects": [{"type": "burn", "duration": 2, "chance": 0.3}]},
            {"name": "冰锥术", "power": 1.2, "mp_cost": 10, "cooldown": 0, "effects": [{"type": "freeze", "duration": 1, "chance": 0.2}]},
            {"name": "雷电术", "power": 1.8, "mp_cost": 20, "cooldown": 2, "effects": [{"type": "stun", "duration": 1, "chance": 0.25}]},
            {"name": "陨石术", "power": 2.5, "mp_cost": 35, "cooldown": 5, "effects": [{"type": "aoe", "target": "all_enemies"}, {"type": "burn", "duration": 3, "chance": 0.5}]},
        ],
        "buff": [
            {"name": "魔力护盾", "power": 0, "mp_cost": 15, "cooldown": 4, "effects": [{"type": "shield", "value": 50, "duration": 3}]},
            {"name": "智慧祝福", "power": 0, "mp_cost": 10, "cooldown": 5, "effects": [{"type": "magic_up", "value": 25, "duration": 3}]},
        ],
    },
    "rogue": {
        "damage": [
            {"name": "暗影突袭", "power": 1.6, "mp_cost": 10, "cooldown": 0, "effects": []},
            {"name": "毒刃", "power": 1.2, "mp_cost": 12, "cooldown": 1, "effects": [{"type": "poison", "duration": 3, "chance": 0.5}]},
            {"name": "连击", "power": 0.8, "mp_cost": 15, "cooldown": 2, "effects": [{"type": "multi_hit", "hits": 3}]},
            {"name": "暗杀", "power": 3.0, "mp_cost": 30, "cooldown": 6, "effects": [{"type": "crit_boost", "value": 50}]},
        ],
        "buff": [
            {"name": "隐身", "power": 0, "mp_cost": 15, "cooldown": 5, "effects": [{"type": "stealth", "duration": 2}]},
            {"name": "疾风步", "power": 0, "mp_cost": 8, "cooldown": 3, "effects": [{"type": "speed_up", "value": 30, "duration": 2}]},
        ],
    },
    "priest": {
        "damage": [
            {"name": "圣光术", "power": 1.3, "mp_cost": 10, "cooldown": 0, "effects": [{"type": "holy", "bonus_vs_undead": 1.5}]},
            {"name": "神圣之火", "power": 1.5, "mp_cost": 15, "cooldown": 1, "effects": [{"type": "burn", "duration": 2, "chance": 0.3}]},
        ],
        "buff": [
            {"name": "治疗术", "power": 0, "mp_cost": 12, "cooldown": 0, "effects": [{"type": "heal", "value": 40}]},
            {"name": "群体治疗", "power": 0, "mp_cost": 25, "cooldown": 3, "effects": [{"type": "heal", "value": 25, "target": "all_allies"}]},
            {"name": "庇护", "power": 0, "mp_cost": 18, "cooldown": 4, "effects": [{"type": "defense_up", "value": 30, "duration": 3, "target": "all_allies"}]},
        ],
    },
}

TALENT_TREES = {
    "warrior": {
        "berserk": {
            "name": "狂战",
            "talents": [
                {"name": "力量强化", "tier": 1, "effects": [{"type": "stat_boost", "stat": "attack", "value": 0.08, "is_percent": True}]},
                {"name": "嗜血本能", "tier": 2, "effects": [{"type": "on_kill", "action": "heal_percent", "value": 0.10}]},
                {"name": "狂暴之心", "tier": 3, "effects": [{"type": "conditional", "condition": "hp_below", "threshold": 0.30, "stat": "attack", "value": 0.25, "is_percent": True}]},
                {"name": "战意昂扬", "tier": 4, "effects": [{"type": "stat_boost", "stat": "crit_chance", "value": 0.10, "is_percent": False}]},
                {"name": "战神附体", "tier": 5, "effects": [{"type": "on_kill", "action": "buff", "stat": "attack", "value": 0.15, "duration": 3, "stackable": True}]},
            ],
        },
        "guard": {
            "name": "守护",
            "talents": [
                {"name": "铁壁", "tier": 1, "effects": [{"type": "stat_boost", "stat": "defense", "value": 0.10, "is_percent": True}]},
                {"name": "生命强化", "tier": 2, "effects": [{"type": "stat_boost", "stat": "max_hp", "value": 0.15, "is_percent": True}]},
                {"name": "嘲讽", "tier": 3, "effects": [{"type": "passive", "action": "taunt", "value": 0.20}]},
                {"name": "坚韧意志", "tier": 4, "effects": [{"type": "resist", "resist_type": "stun", "value": 0.30}]},
                {"name": "不屈战魂", "tier": 5, "effects": [{"type": "on_death", "action": "revive", "hp_percent": 0.30, "once_per_combat": True}]},
            ],
        },
    },
    "mage": {
        "elemental": {
            "name": "元素",
            "talents": [
                {"name": "元素亲和", "tier": 1, "effects": [{"type": "stat_boost", "stat": "magic", "value": 0.08, "is_percent": True}]},
                {"name": "灼烧强化", "tier": 2, "effects": [{"type": "effect_boost", "effect_type": "burn", "duration_bonus": 1}]},
                {"name": "元素共鸣", "tier": 3, "effects": [{"type": "conditional", "condition": "target_debuff", "stat": "magic", "value": 0.20, "is_percent": True}]},
                {"name": "法力涌动", "tier": 4, "effects": [{"type": "stat_boost", "stat": "max_mp", "value": 0.20, "is_percent": True}]},
                {"name": "元素风暴", "tier": 5, "effects": [{"type": "on_cast", "action": "chain", "chance": 0.15, "damage_percent": 0.50}]},
            ],
        },
        "arcane": {
            "name": "奥术",
            "talents": [
                {"name": "奥术专注", "tier": 1, "effects": [{"type": "stat_boost", "stat": "magic", "value": 0.10, "is_percent": True}]},
                {"name": "法力回流", "tier": 2, "effects": [{"type": "on_cast", "action": "mp_refund", "chance": 0.15}]},
                {"name": "奥术屏障", "tier": 3, "effects": [{"type": "passive", "action": "magic_shield", "value": 0.10}]},
                {"name": "时间扭曲", "tier": 4, "effects": [{"type": "cooldown_reduction", "value": 1}]},
                {"name": "奥术大师", "tier": 5, "effects": [{"type": "stat_boost", "stat": "magic", "value": 0.25, "is_percent": True}]},
            ],
        },
    },
    "rogue": {
        "assassination": {
            "name": "刺杀",
            "talents": [
                {"name": "精准打击", "tier": 1, "effects": [{"type": "stat_boost", "stat": "crit_chance", "value": 0.05, "is_percent": False}]},
                {"name": "致命毒药", "tier": 2, "effects": [{"type": "effect_boost", "effect_type": "poison", "damage_bonus": 0.20}]},
                {"name": "暗影之刃", "tier": 3, "effects": [{"type": "conditional", "condition": "stealthed", "stat": "attack", "value": 0.30, "is_percent": True}]},
                {"name": "割喉", "tier": 4, "effects": [{"type": "on_crit", "action": "extra_damage", "value": 0.25}]},
                {"name": "死亡印记", "tier": 5, "effects": [{"type": "active", "action": "mark", "duration": 3, "damage_bonus": 0.50}]},
            ],
        },
        "shadow": {
            "name": "暗影",
            "talents": [
                {"name": "潜行大师", "tier": 1, "effects": [{"type": "effect_boost", "effect_type": "stealth", "duration_bonus": 1}]},
                {"name": "闪避本能", "tier": 2, "effects": [{"type": "stat_boost", "stat": "dodge", "value": 0.08, "is_percent": False}]},
                {"name": "暗影步", "tier": 3, "effects": [{"type": "passive", "action": "shadow_step", "chance": 0.15}]},
                {"name": "毒雾", "tier": 4, "effects": [{"type": "on_stealth_end", "action": "aoe_poison", "duration": 2}]},
                {"name": "暗影之主", "tier": 5, "effects": [{"type": "conditional", "condition": "stealthed", "stat": "crit_chance", "value": 0.30, "is_percent": False}]},
            ],
        },
    },
    "priest": {
        "holy": {
            "name": "神圣",
            "talents": [
                {"name": "虔诚", "tier": 1, "effects": [{"type": "stat_boost", "stat": "heal_power", "value": 0.10, "is_percent": True}]},
                {"name": "圣光庇佑", "tier": 2, "effects": [{"type": "on_heal", "action": "shield", "value": 0.15}]},
                {"name": "神圣之怒", "tier": 3, "effects": [{"type": "conditional", "condition": "target_undead", "stat": "magic", "value": 0.30, "is_percent": True}]},
                {"name": "复活术", "tier": 4, "effects": [{"type": "active", "action": "revive", "hp_percent": 0.50}]},
                {"name": "圣者", "tier": 5, "effects": [{"type": "on_heal", "action": "cleanse", "chance": 0.30}]},
            ],
        },
        "shadow_priest": {
            "name": "暗影",
            "talents": [
                {"name": "暗影之触", "tier": 1, "effects": [{"type": "stat_boost", "stat": "magic", "value": 0.08, "is_percent": True}]},
                {"name": "吸血", "tier": 2, "effects": [{"type": "on_damage", "action": "lifesteal", "value": 0.10}]},
                {"name": "暗影折磨", "tier": 3, "effects": [{"type": "effect_boost", "effect_type": "fear", "duration_bonus": 1}]},
                {"name": "灵魂吞噬", "tier": 4, "effects": [{"type": "on_kill", "action": "mp_heal", "value": 0.20}]},
                {"name": "暗影形态", "tier": 5, "effects": [{"type": "active", "action": "shadow_form", "magic_boost": 0.30, "heal_reduction": 0.50}]},
            ],
        },
    },
}


class SkillTalentGenerator:
    def __init__(self):
        self.skills = self._load_json(SKILLS_FILE)
        self.talents = self._load_json(TALENTS_FILE)

    def _load_json(self, filepath):
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_skills(self):
        SKILLS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SKILLS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.skills, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(self.skills)} 个技能到 {SKILLS_FILE}")

    def _save_talents(self):
        TALENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TALENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.talents, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(self.talents)} 个天赋到 {TALENTS_FILE}")

    def generate_skill(self, skill_id, name, skill_type, class_name, level_req=1,
                       power=1.0, mp_cost=10, cooldown=0, effects=None, description=None):
        if class_name not in CLASSES:
            print(f"错误：未知职业 '{class_name}'，可用：{', '.join(CLASSES)}")
            return None
        damage_type = "physical" if class_name in ("warrior", "rogue") else "magic"
        target = "enemy" if skill_type == "damage" else "self"
        skill = {
            "skill_id": skill_id,
            "name": name,
            "description": description or f"{name} - {class_name}的{skill_type}技能",
            "mp_cost": mp_cost,
            "cooldown": cooldown,
            "type": skill_type,
            "target": target,
            "damage_type": damage_type,
            "power": power,
            "effects": effects or [],
            "class_requirement": [class_name],
            "level_requirement": level_req,
        }
        self.skills[skill_id] = skill
        print(f"已生成技能：{name} ({skill_id}) - {class_name} Lv.{level_req}")
        return skill

    def generate_class_skills(self, class_name):
        if class_name not in SKILL_TEMPLATES:
            print(f"错误：无模板 '{class_name}'")
            return []
        templates = SKILL_TEMPLATES[class_name]
        generated = []
        level_counter = 1
        for skill_type, skill_list in templates.items():
            for tmpl in skill_list:
                skill_id = f"{class_name}_{self._to_pinyin(tmpl['name'])}"
                if skill_id in self.skills:
                    continue
                skill = self.generate_skill(
                    skill_id=skill_id,
                    name=tmpl["name"],
                    skill_type=skill_type,
                    class_name=class_name,
                    level_req=level_counter,
                    power=tmpl["power"],
                    mp_cost=tmpl["mp_cost"],
                    cooldown=tmpl["cooldown"],
                    effects=tmpl.get("effects", []),
                )
                if skill:
                    generated.append(skill)
                level_counter += 1
        print(f"为 {class_name} 生成了 {len(generated)} 个技能")
        return generated

    def generate_all_skills(self):
        total = 0
        for class_name in CLASSES:
            generated = self.generate_class_skills(class_name)
            total += len(generated)
        self._save_skills()
        print(f"共生成 {total} 个新技能")
        return total

    def generate_talent(self, talent_id, name, class_name, tree, tier,
                        effects, prerequisites=None, description=None):
        if class_name not in CLASSES:
            print(f"错误：未知职业 '{class_name}'")
            return None
        talent = {
            "talent_id": talent_id,
            "name": name,
            "class": class_name,
            "tree": tree,
            "tier": tier,
            "description": description or name,
            "effects": effects,
            "prerequisites": prerequisites or [],
        }
        self.talents[talent_id] = talent
        print(f"已生成天赋：{name} ({talent_id}) - {class_name}/{tree} T{tier}")
        return talent

    def generate_class_talents(self, class_name):
        if class_name not in TALENT_TREES:
            print(f"错误：无天赋模板 '{class_name}'")
            return []
        generated = []
        for tree_key, tree_data in TALENT_TREES[class_name].items():
            prev_id = None
            for tmpl in tree_data["talents"]:
                talent_id = f"{class_name}_{tree_key}_{self._to_pinyin(tmpl['name'])}"
                if talent_id in self.talents:
                    prev_id = talent_id
                    continue
                prereqs = [prev_id] if prev_id and tmpl["tier"] > 1 else []
                talent = self.generate_talent(
                    talent_id=talent_id,
                    name=tmpl["name"],
                    class_name=class_name,
                    tree=tree_key,
                    tier=tmpl["tier"],
                    effects=tmpl["effects"],
                    prerequisites=prereqs,
                )
                if talent:
                    generated.append(talent)
                prev_id = talent_id
        print(f"为 {class_name} 生成了 {len(generated)} 个天赋")
        return generated

    def generate_all_talents(self):
        total = 0
        for class_name in CLASSES:
            generated = self.generate_class_talents(class_name)
            total += len(generated)
        self._save_talents()
        print(f"共生成 {total} 个新天赋")
        return total

    def validate_skills(self):
        issues = []
        for sid, skill in self.skills.items():
            if skill.get("skill_id") != sid:
                issues.append(f"{sid}: skill_id 不匹配")
            for field in ["name", "type", "mp_cost", "power", "class_requirement", "level_requirement"]:
                if field not in skill:
                    issues.append(f"{sid}: 缺少 '{field}'")
            if skill.get("mp_cost", 0) < 0:
                issues.append(f"{sid}: mp_cost 不能为负")
            if skill.get("power", 0) < 0:
                issues.append(f"{sid}: power 不能为负")
            if skill.get("cooldown", 0) < 0:
                issues.append(f"{sid}: cooldown 不能为负")
            for cls in skill.get("class_requirement", []):
                if cls not in CLASSES:
                    issues.append(f"{sid}: 未知职业 '{cls}'")
        if issues:
            print(f"技能验证发现 {len(issues)} 个问题：")
            for issue in issues:
                print(f"  ⚠ {issue}")
        else:
            print(f"技能验证通过！共 {len(self.skills)} 个技能")
        return len(issues)

    def validate_talents(self):
        issues = []
        for tid, talent in self.talents.items():
            if talent.get("talent_id") != tid:
                issues.append(f"{tid}: talent_id 不匹配")
            for field in ["name", "class", "tree", "tier", "effects"]:
                if field not in talent:
                    issues.append(f"{tid}: 缺少 '{field}'")
            if talent.get("class") not in CLASSES:
                issues.append(f"{tid}: 未知职业 '{talent.get('class')}'")
            if talent.get("tier", 0) < 1 or talent.get("tier", 0) > 5:
                issues.append(f"{tid}: tier 应在 1-5 范围内")
            for prereq in talent.get("prerequisites", []):
                if prereq not in self.talents:
                    issues.append(f"{tid}: 前置天赋 '{prereq}' 不存在")
            if not talent.get("effects"):
                issues.append(f"{tid}: effects 不能为空")
        if issues:
            print(f"天赋验证发现 {len(issues)} 个问题：")
            for issue in issues:
                print(f"  ⚠ {issue}")
        else:
            print(f"天赋验证通过！共 {len(self.talents)} 个天赋")
        return len(issues)

    def validate(self):
        skill_issues = self.validate_skills()
        talent_issues = self.validate_talents()
        total = skill_issues + talent_issues
        if total == 0:
            print("\n全部验证通过！")
        else:
            print(f"\n共发现 {total} 个问题")
        return total

    def list_skills(self, class_name=None):
        skills = self.skills
        if class_name:
            skills = {k: v for k, v in skills.items() if class_name in v.get("class_requirement", [])}
        print(f"\n共 {len(skills)} 个技能{'（' + class_name + '）' if class_name else ''}:\n")
        for sid, s in sorted(skills.items(), key=lambda x: x[1].get("level_requirement", 0)):
            classes = "/".join(s.get("class_requirement", []))
            print(f"  Lv.{s.get('level_requirement', 0):2d} [{s.get('type', '?'):6s}] {sid}: {s.get('name', '?')} ({classes})")

    def list_talents(self, class_name=None):
        talents = self.talents
        if class_name:
            talents = {k: v for k, v in talents.items() if v.get("class") == class_name}
        print(f"\n共 {len(talents)} 个天赋{'（' + class_name + '）' if class_name else ''}:\n")
        for tid, t in sorted(talents.items(), key=lambda x: (x[1].get("class", ""), x[1].get("tree", ""), x[1].get("tier", 0))):
            print(f"  T{t.get('tier', 0)} [{t.get('class', '?'):7s}/{t.get('tree', '?'):12s}] {tid}: {t.get('name', '?')}")

    def _to_pinyin(self, chinese_name):
        mapping = {
            "猛击": "mengji", "旋风斩": "xuanfengzhan", "碎甲击": "suijiaji", "致命一击": "zhimingyiji",
            "战吼": "zhanhou", "铁壁": "tiebi", "火球术": "huoqiushu", "冰锥术": "bingzhuishu",
            "雷电术": "leidianishu", "陨石术": "yunshishu", "魔力护盾": "molihudun", "智慧祝福": "zhihuizhufu",
            "暗影突袭": "anyingtuoxi", "毒刃": "dureng", "连击": "lianji", "暗杀": "ansha",
            "隐身": "yinshen", "疾风步": "jifengbu", "圣光术": "shengguangshu", "神圣之火": "shenshengzhihuo",
            "治疗术": "zhiliaoshu", "群体治疗": "quntizhiliao", "庇护": "bihu",
            "力量强化": "liliangqianghua", "嗜血本能": "shixuebenmeng", "狂暴之心": "kuangbaozhixin",
            "战意昂扬": "zhanyiangyang", "战神附体": "zhanshenfuti", "生命强化": "shengmingqianghua",
            "嘲讽": "chaofeng", "坚韧意志": "jianrenyizhi", "不屈战魂": "buquzhanhun",
            "元素亲和": "yuansuqinhe", "灼烧强化": "zhuoshaoqianghua", "元素共鸣": "yuansugongming",
            "法力涌动": "faliyongdong", "元素风暴": "yuansufengbao", "奥术专注": "aoshuzhuanzhu",
            "法力回流": "falihuiliu", "奥术屏障": "aoshupingzhang", "时间扭曲": "shijianniuqu",
            "奥术大师": "aoshudashi", "精准打击": "jingzhundaji", "致命毒药": "zhimingduyao",
            "暗影之刃": "anyingzhiren", "割喉": "gehou", "死亡印记": "siwangyinji",
            "潜行大师": "qianxingdashi", "闪避本能": "shanbibenmeng", "暗影步": "anyingbu",
            "毒雾": "duwu", "暗影之主": "anyingzhizhu", "虔诚": "qiancheng", "圣光庇佑": "shengguangbiyou",
            "神圣之怒": "shenshengzhinu", "复活术": "fuhuoshu", "圣者": "shengzhe",
            "暗影之触": "anyingzhichu", "吸血": "xixue", "暗影折磨": "anyingzhemo",
            "灵魂吞噬": "linghuntunshi", "暗影形态": "anyingxingtai",
        }
        return mapping.get(chinese_name, chinese_name)


if __name__ == "__main__":
    gen = SkillTalentGenerator()
    if len(sys.argv) < 2:
        print("用法: python skill_talent_generator.py <命令> [参数]")
        print("\n命令:")
        print("  generate-skills [class]   生成技能（可选指定职业）")
        print("  generate-talents [class]  生成天赋（可选指定职业）")
        print("  generate-all              生成所有技能和天赋")
        print("  validate                  验证所有配置")
        print("  list-skills [class]       列出技能")
        print("  list-talents [class]      列出天赋")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "generate-skills":
        cls = sys.argv[2] if len(sys.argv) > 2 else None
        if cls:
            gen.generate_class_skills(cls)
        else:
            gen.generate_all_skills()
        gen._save_skills()
    elif cmd == "generate-talents":
        cls = sys.argv[2] if len(sys.argv) > 2 else None
        if cls:
            gen.generate_class_talents(cls)
        else:
            gen.generate_all_talents()
        gen._save_talents()
    elif cmd == "generate-all":
        gen.generate_all_skills()
        gen.generate_all_talents()
    elif cmd == "validate":
        gen.validate()
    elif cmd == "list-skills":
        cls = sys.argv[2] if len(sys.argv) > 2 else None
        gen.list_skills(cls)
    elif cmd == "list-talents":
        cls = sys.argv[2] if len(sys.argv) > 2 else None
        gen.list_talents(cls)
    else:
        print(f"未知命令: {cmd}")
