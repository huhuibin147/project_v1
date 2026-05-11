"""Talent system: talent definitions, learning, and effect application."""

import json
from pathlib import Path

_TALENTS_FILE = Path(__file__).parent.parent / "config" / "talents.json"
_TALENTS_DB: dict = {}

TALENT_UNLOCK_LEVEL = 5
TALENT_POINT_INTERVAL = 3


def _load_talents():
    global _TALENTS_DB
    if _TALENTS_DB:
        return
    if not _TALENTS_FILE.exists():
        return
    with open(_TALENTS_FILE, "r", encoding="utf-8") as f:
        _TALENTS_DB = json.load(f)


def get_talent_config(talent_id: str) -> dict | None:
    _load_talents()
    return _TALENTS_DB.get(talent_id)


def get_class_talents(class_id: str) -> dict:
    _load_talents()
    result = {}
    for tid, cfg in _TALENTS_DB.items():
        if cfg.get("class") == class_id:
            result[tid] = cfg
    return result


def get_talent_trees(class_id: str) -> dict:
    _load_talents()
    trees = {}
    for tid, cfg in _TALENTS_DB.items():
        if cfg.get("class") != class_id:
            continue
        tree_name = cfg.get("tree", "default")
        if tree_name not in trees:
            trees[tree_name] = []
        trees[tree_name].append(cfg)
    for tree_name in trees:
        trees[tree_name].sort(key=lambda t: t.get("tier", 0))
    return trees


def calc_talent_points(level: int) -> int:
    if level < TALENT_UNLOCK_LEVEL:
        return 0
    return (level - TALENT_UNLOCK_LEVEL) // TALENT_POINT_INTERVAL + 1


def can_learn_talent(talent_id: str, class_id: str, level: int,
                     learned_talents: list[str]) -> tuple[bool, str]:
    _load_talents()
    cfg = _TALENTS_DB.get(talent_id)
    if not cfg:
        return False, "天赋不存在"
    if cfg.get("class") != class_id:
        return False, "职业不匹配"
    if level < TALENT_UNLOCK_LEVEL:
        return False, f"需要等级 {TALENT_UNLOCK_LEVEL} 解锁天赋系统"
    for prereq in cfg.get("prerequisites", []):
        if prereq not in learned_talents:
            prereq_cfg = _TALENTS_DB.get(prereq)
            prereq_name = prereq_cfg.get("name", prereq) if prereq_cfg else prereq
            return False, f"需要先学习天赋：{prereq_name}"
    if talent_id in learned_talents:
        return False, "已经学习过该天赋"
    used_points = len(learned_talents)
    total_points = calc_talent_points(level)
    if used_points >= total_points:
        return False, "天赋点不足"
    return True, ""


def calc_talent_stat_boosts(class_id: str, learned_talents: list[str]) -> dict:
    _load_talents()
    boosts = {
        "attack": 0.0, "defense": 0.0, "speed": 0.0,
        "max_hp": 0.0, "max_mp": 0.0,
        "crit_chance": 0.0, "crit_damage": 0.0, "dodge_chance": 0.0,
    }
    for tid in learned_talents:
        cfg = _TALENTS_DB.get(tid)
        if not cfg:
            continue
        for eff in cfg.get("effects", []):
            if eff.get("type") == "stat_boost":
                stat = eff.get("stat")
                value = eff.get("value", 0)
                if stat in boosts:
                    boosts[stat] += value
    return boosts


def get_talent_passives(class_id: str, learned_talents: list[str]) -> dict:
    _load_talents()
    passives = {
        "on_kill": [],
        "on_attack": [],
        "on_combat_start": [],
        "on_dodge": [],
        "conditional": [],
        "skill_enhance": {},
        "defend_boost": 0.5,
        "last_stand": False,
        "mp_regen": 0.0,
        "element_combo": 0.0,
        "element_storm": None,
    }
    for tid in learned_talents:
        cfg = _TALENTS_DB.get(tid)
        if not cfg:
            continue
        for eff in cfg.get("effects", []):
            etype = eff.get("type")
            if etype == "on_kill":
                passives["on_kill"].append(eff)
            elif etype == "on_attack":
                passives["on_attack"].append(eff)
            elif etype == "on_combat_start":
                passives["on_combat_start"].append(eff)
            elif etype == "on_dodge":
                passives["on_dodge"].append(eff)
            elif etype == "conditional":
                passives["conditional"].append(eff)
            elif etype == "skill_enhance":
                skill_id = eff.get("skill_id")
                enhance = eff.get("enhance")
                if skill_id not in passives["skill_enhance"]:
                    passives["skill_enhance"][skill_id] = []
                passives["skill_enhance"][skill_id].append(eff)
            elif etype == "passive":
                action = eff.get("action")
                if action == "defend_boost":
                    passives["defend_boost"] = eff.get("value", 0.75)
                elif action == "last_stand":
                    passives["last_stand"] = True
                elif action == "mp_regen":
                    passives["mp_regen"] = eff.get("value", 0.0)
                elif action == "element_combo":
                    passives["element_combo"] = eff.get("value", 0.0)
                elif action == "element_storm":
                    passives["element_storm"] = eff
    return passives


def format_talent_for_frontend(talent_id: str, cfg: dict, learned: bool = False,
                                can_learn: bool = False, reason: str = "") -> dict:
    return {
        "talent_id": talent_id,
        "name": cfg.get("name", talent_id),
        "class": cfg.get("class", ""),
        "tree": cfg.get("tree", ""),
        "tier": cfg.get("tier", 0),
        "description": cfg.get("description", ""),
        "effects": cfg.get("effects", []),
        "prerequisites": cfg.get("prerequisites", []),
        "learned": learned,
        "can_learn": can_learn,
        "reason": reason,
    }


def get_reset_cost(level: int) -> int:
    return 100 + level * 50
