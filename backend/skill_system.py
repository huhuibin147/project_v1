"""Skill system: skill definitions, learning, upgrade, and combat usage."""

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
    result = []
    for skill_id, skill in SKILLS_DB.items():
        req_classes = skill.get("class_requirement", [])
        req_level = skill.get("level_requirement", 1)
        if (not req_classes or class_id in req_classes) and level >= req_level:
            result.append({"skill_id": skill_id, **skill})
    return result


def can_learn_skill(skill_id: str, class_id: str, level: int, known_skills: list[str]) -> tuple[bool, str]:
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


def get_skill_at_level(skill_id: str, level: int = 1) -> dict | None:
    if level <= 1:
        base = SKILLS_DB.get(skill_id)
        if base:
            result = base.copy()
            result.pop("level_scaling", None)
            result["current_level"] = 1
            return result
        return None

    base = SKILLS_DB.get(skill_id)
    if not base:
        return None

    max_level = base.get("max_level", 1)
    if level > max_level:
        level = max_level

    result = base.copy()
    scaling = result.pop("level_scaling", {})

    for lvl in range(2, level + 1):
        lvl_data = scaling.get(str(lvl), {})
        for key, value in lvl_data.items():
            if key not in ("upgrade_cost", "description_change"):
                result[key] = value

    if level > 1:
        lvl_data = scaling.get(str(level), {})
        if "description_change" in lvl_data:
            result["description"] = lvl_data["description_change"]

    result["current_level"] = level
    return result


def can_upgrade_skill(skill_id: str, current_level: int, player_gold: int) -> tuple[bool, str, int]:
    skill = SKILLS_DB.get(skill_id)
    if not skill:
        return False, "技能不存在", 0
    max_level = skill.get("max_level", 1)
    if current_level >= max_level:
        return False, "已达最高等级", 0
    next_level = current_level + 1
    scaling = skill.get("level_scaling", {})
    next_data = scaling.get(str(next_level), {})
    cost = next_data.get("upgrade_cost", 0)
    if cost <= 0:
        return False, "无法升级", 0
    if player_gold < cost:
        return False, f"金币不足，需要 {cost} 金币", cost
    return True, "", cost


def get_player_skills_info(class_id: str, level: int, known_skills: list[str], skill_levels: dict) -> dict:
    learned = []
    available = []

    for skill_id, skill in SKILLS_DB.items():
        req_classes = skill.get("class_requirement", [])
        if req_classes and class_id not in req_classes:
            continue

        if skill_id in known_skills:
            slevel = skill_levels.get(skill_id, 1)
            info = get_skill_at_level(skill_id, slevel)
            if info:
                max_level = skill.get("max_level", 1)
                can_up = slevel < max_level
                next_data = skill.get("level_scaling", {}).get(str(slevel + 1), {})
                info["max_level"] = max_level
                info["can_upgrade"] = can_up
                info["upgrade_cost"] = next_data.get("upgrade_cost", 0) if can_up else 0
                info["next_level_preview"] = {}
                if can_up and next_data:
                    preview = {}
                    if "description_change" in next_data:
                        preview["description_change"] = next_data["description_change"]
                    if "power" in next_data:
                        preview["power"] = next_data["power"]
                    if "mp_cost" in next_data:
                        preview["mp_cost"] = next_data["mp_cost"]
                    if "cooldown" in next_data:
                        preview["cooldown"] = next_data["cooldown"]
                    if "effects" in next_data:
                        preview["effects"] = next_data["effects"]
                    info["next_level_preview"] = preview
                learned.append(info)
        else:
            req_level = skill.get("level_requirement", 1)
            can_learn = level >= req_level
            reason = "" if can_learn else f"需要等级 {req_level}"
            info = {
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
                "aoe": skill.get("aoe", False),
                "current_level": 0,
                "max_level": skill.get("max_level", 1),
                "can_learn": can_learn,
                "reason": reason,
                "level_requirement": req_level,
                "class_requirement": req_classes,
            }
            if skill.get("element"):
                info["element"] = skill["element"]
            available.append(info)

    return {
        "class_id": class_id,
        "level": level,
        "learned_skills": learned,
        "available_skills": available,
    }


def format_skill_for_frontend(skill_id: str, cooldown_remaining: int = 0, skill_level: int = 1) -> dict:
    skill_data = get_skill_at_level(skill_id, skill_level)
    if not skill_data:
        return None
    return {
        "skill_id": skill_id,
        "name": skill_data["name"],
        "description": skill_data["description"],
        "mp_cost": skill_data["mp_cost"],
        "cooldown": skill_data["cooldown"],
        "type": skill_data["type"],
        "target": skill_data["target"],
        "damage_type": skill_data.get("damage_type", "physical"),
        "power": skill_data.get("power", 1.0),
        "effects": skill_data.get("effects", []),
        "cooldown_remaining": cooldown_remaining,
        "aoe": skill_data.get("aoe", False),
        "current_level": skill_data.get("current_level", 1),
        "max_level": skill_data.get("max_level", 1),
    }
