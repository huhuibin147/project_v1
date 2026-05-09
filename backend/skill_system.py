"""Skill system: skill definitions, learning, and combat usage."""

import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"
SKILLS_FILE = CONFIG_DIR / "skills.json"


def load_skills_config() -> dict:
    with open(SKILLS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


SKILLS_DB = load_skills_config()


def get_skill(skill_id: str) -> dict | None:
    return SKILLS_DB.get(skill_id)


def get_class_skills(class_id: str, level: int = 99) -> list[dict]:
    """获取某职业在指定等级前可学习的所有技能。"""
    result = []
    for skill_id, skill in SKILLS_DB.items():
        req_classes = skill.get("class_requirement", [])
        req_level = skill.get("level_requirement", 1)
        if (not req_classes or class_id in req_classes) and level >= req_level:
            result.append({"skill_id": skill_id, **skill})
    return result


def can_learn_skill(skill_id: str, class_id: str, level: int, known_skills: list[str]) -> tuple[bool, str]:
    """检查是否可以学习技能，返回 (是否可学, 原因)。"""
    skill = SKILLS_DB.get(skill_id)
    if not skill:
        return False, "技能不存在"
    if skill_id in known_skills:
        return False, "已学会该技能"
    req_classes = skill.get("class_requirement", [])
    if req_classes and class_id not in req_classes:
        return False, f"该技能仅限 {'/'.join(req_classes)} 学习"
    req_level = skill.get("level_requirement", 1)
    if level < req_level:
        return False, f"需要等级 {req_level}"
    return True, ""


def format_skill_for_frontend(skill_id: str, cooldown_remaining: int = 0) -> dict:
    """格式化技能信息供前端显示。"""
    skill = SKILLS_DB.get(skill_id)
    if not skill:
        return None
    return {
        "skill_id": skill_id,
        "name": skill["name"],
        "description": skill["description"],
        "mp_cost": skill["mp_cost"],
        "cooldown": skill["cooldown"],
        "type": skill["type"],
        "target": skill["target"],
        "damage_type": skill.get("damage_type", "physical"),
        "power": skill.get("power", 1.0),
        "effects": skill.get("effects", []),
        "cooldown_remaining": cooldown_remaining,
    }
