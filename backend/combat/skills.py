"""Skill execution module."""

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import CombatSession, StatusEffect
    from .effects import add_effect, _recalculate_player_buffs, STAT_BUFF_MAP, EFFECT_NAMES
    from .damage import calc_damage


def execute_skill(session: "CombatSession", skill_id: str) -> dict:
    from skill_system import get_skill
    from .session import StatusEffect
    from .effects import add_effect, _recalculate_player_buffs, STAT_BUFF_MAP
    from .damage import calc_damage

    skill = get_skill(skill_id)
    if not skill:
        return {"type": "skill", "success": False, "text": "未知技能。"}
    if skill_id not in session.player_skills:
        return {"type": "skill", "success": False, "text": "你尚未学会该技能。"}
    if session.skill_cooldowns.get(skill_id, 0) > 0:
        return {"type": "skill", "success": False, "text": f"技能冷却中，剩余 {session.skill_cooldowns[skill_id]} 回合。"}
    if session.player_mp < skill["mp_cost"]:
        return {"type": "skill", "success": False, "text": "魔法值不足！"}

    session.player_mp -= skill["mp_cost"]
    if skill["cooldown"] > 0:
        session.skill_cooldowns[skill_id] = skill["cooldown"]

    skill_type = skill["type"]
    power = skill.get("power", 1.0)
    effects = skill.get("effects", [])
    monster_name = session.monster_config["name"]

    if session.talent_passives:
        skill_enhances = session.talent_passives.get("skill_enhance", {})
        if skill_id in skill_enhances:
            for enh in skill_enhances[skill_id]:
                if enh.get("enhance") == "power":
                    power += enh.get("value", 0)
                elif enh.get("enhance") == "mp_reduce":
                    session.player_mp += min(skill["mp_cost"], enh.get("value", 0))
                    session.player_mp = min(session.player_max_mp, session.player_mp)

    if session.talent_passives and session.talent_passives.get("element_combo", 0) > 0:
        if skill.get("damage_type") == "magic":
            power += session.talent_passives["element_combo"]

    if session.talent_passives and session.talent_passives.get("element_storm"):
        storm = session.talent_passives["element_storm"]
        if skill.get("damage_type") == "magic" and random.random() < storm.get("chance", 0.1):
            extra_dmg = max(1, int(session.player_attack * storm.get("value", 0.3)))
            session.monster_hp = max(0, session.monster_hp - extra_dmg)

    if skill_type == "damage":
        return _execute_damage_skill(session, skill, power, effects, monster_name)
    elif skill_type == "heal":
        return _execute_heal_skill(session, skill, power)
    elif skill_type == "buff":
        return _execute_buff_skill(session, skill, effects, skill_id)
    elif skill_type == "shield":
        return _execute_shield_skill(session, skill)

    return {"type": "skill", "success": False, "text": "未知技能类型。"}


def _execute_damage_skill(session, skill, power, effects, monster_name):
    from .session import StatusEffect
    from .effects import add_effect, STAT_BUFF_MAP
    from .damage import calc_damage

    damage_type = skill.get("damage_type", "physical")
    damage_type_names = {"physical": "物理", "magic": "魔法"}
    damage_type_cn = damage_type_names.get(damage_type, damage_type)
    effect_type_names = {
        "poison": "中毒", "burn": "灼烧", "freeze": "冻结", "stun": "眩晕",
        "silence": "沉默", "speed_down": "减速", "bleed": "流血",
        "shield": "护盾", "regen": "再生", "reflect": "反伤", "lifesteal": "吸血",
        "defense_down": "防御降低", "attack_down": "攻击降低",
        "evasion_up": "闪避提升", "attack_up": "攻击提升", "defense_up": "防御提升",
        "speed_up": "速度提升", "damage_reduction": "伤害减免",
    }

    base_atk = session.player_attack
    if damage_type == "magic":
        base_atk = session.player_attack + session.player_max_mp // 5

    defense_ignore = 0
    for eff in effects:
        if eff.get("type") == "defense_ignore":
            defense_ignore = eff.get("value", 0)
            break

    monster_defense = session.monster_config["stats"]["defense"]
    if defense_ignore > 0:
        monster_defense = int(monster_defense * (1 - defense_ignore / 100.0))

    result = calc_damage(
        int(base_atk * power),
        monster_defense,
        session.player_speed,
        session.monster_config["stats"]["speed"],
        session.monster_defending
    )
    session.monster_hp = max(0, session.monster_hp - result["damage"])

    entry = {"type": "skill", "skill_id": skill["skill_id"], "success": True,
             "damage": result["damage"], "crit": result["is_crit"],
             "text": f"使用 {skill['name']}！对{monster_name}造成 {result['damage']} 点{damage_type_cn}伤害。"}
    if defense_ignore > 0:
        entry["text"] += f" (无视 {defense_ignore}% 防御)"

    for eff in effects:
        if eff.get("type") in ("defense_ignore",):
            continue
        if random.random() < eff.get("chance", 1.0):
            new_eff = StatusEffect(eff["type"], eff["duration"], source=f"skill:{skill['skill_id']}")
            session.monster_effects = add_effect(session.monster_effects, new_eff)
            eff_name_cn = effect_type_names.get(eff["type"], eff["type"])
            entry["text"] += f" [{eff_name_cn}]"

    return entry


def _execute_heal_skill(session, skill, power):
    heal_amount = int(session.player_max_hp * power)
    session.player_hp = min(session.player_max_hp, session.player_hp + heal_amount)
    return {"type": "skill", "skill_id": skill["skill_id"], "success": True,
            "text": f"使用 {skill['name']}！恢复了 {heal_amount} 点生命。"}


def _execute_buff_skill(session, skill, effects, skill_id):
    from .session import StatusEffect
    from .effects import add_effect, _recalculate_player_buffs, STAT_BUFF_MAP

    for eff in effects:
        new_eff = StatusEffect(eff["type"], eff["duration"],
                               value=eff.get("value", 0), source=f"skill:{skill_id}")
        session.player_effects = add_effect(session.player_effects, new_eff)
        if eff["type"] in STAT_BUFF_MAP:
            _recalculate_player_buffs(session)
    return {"type": "skill", "skill_id": skill_id, "success": True,
            "text": f"使用 {skill['name']}！获得了增益效果。"}


def _execute_shield_skill(session, skill):
    shield_value = skill.get("shield_value", 0)
    session.player_shield += shield_value
    return {"type": "skill", "skill_id": skill["skill_id"], "success": True,
            "text": f"使用 {skill['name']}！获得了 {shield_value} 点护盾。"}
