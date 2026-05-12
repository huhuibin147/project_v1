"""Monster AI decision and execution module."""

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import CombatSession, StatusEffect
    from .effects import StatusEffect, add_effect, _recalculate_player_buffs, EFFECT_NAMES, STAT_BUFF_MAP
    from .damage import calc_damage, apply_shield


def decide_action(session: "CombatSession") -> str:
    ai = session.monster_config.get("ai", {})
    behavior = ai.get("behavior", "aggressive")
    attack_w = ai.get("attack_weight", 70)
    defend_w = ai.get("defend_weight", 20)
    special_w = ai.get("special_weight", 10)

    if behavior == "cautious":
        hp_ratio = session.monster_hp / session.monster_max_hp
        if hp_ratio < 0.3:
            defend_w += 30
            attack_w = max(10, attack_w - 20)

    special = ai.get("special")
    if special is None:
        attack_w += special_w
        special_w = 0

    total = attack_w + defend_w + special_w
    roll = random.randint(1, total)

    if roll <= attack_w:
        return "attack"
    elif roll <= attack_w + defend_w:
        return "defend"
    else:
        return "special"


def execute_action(session: "CombatSession", action: str) -> list[dict]:
    from .session import StatusEffect
    from .effects import add_effect, _recalculate_player_buffs, EFFECT_NAMES, STAT_BUFF_MAP
    from .damage import calc_damage, apply_shield, apply_reflect, apply_lifesteal

    monster_name = session.monster_config["name"]
    logs = []

    if action == "attack":
        result = calc_damage(
            session.monster_config["stats"]["attack"],
            session.player_defense,
            session.monster_config["stats"]["speed"],
            session.player_speed,
            session.player_defending
        )
        raw_dmg = result["damage"]
        actual_dmg, shield_absorbed = apply_shield(session.player_shield, raw_dmg)
        session.player_shield -= shield_absorbed
        session.player_hp = max(0, session.player_hp - actual_dmg)
        reflect_dmg = apply_reflect(
            next((e.value for e in session.player_effects if e.effect_type == "reflect"), 0),
            actual_dmg
        )
        if reflect_dmg > 0:
            session.monster_hp = max(0, session.monster_hp - reflect_dmg)

        lifesteal_heal = apply_lifesteal(
            next((e.value for e in session.player_effects if e.effect_type == "lifesteal"), 0),
            actual_dmg
        )
        if lifesteal_heal > 0:
            session.player_hp = min(session.player_max_hp, session.player_hp + lifesteal_heal)

        entry = {"type": "monster_attack", "damage": actual_dmg,
                 "crit": result["is_crit"], "defended": result["defended"]}
        if shield_absorbed > 0:
            entry["shield_absorbed"] = shield_absorbed
        if result["is_crit"]:
            entry["text"] = f"暴击！{monster_name}对你造成 {actual_dmg} 点伤害！"
        else:
            entry["text"] = f"{monster_name}攻击了你，造成 {actual_dmg} 点伤害。"
        if shield_absorbed > 0:
            entry["text"] += f"（护盾吸收 {shield_absorbed}）"
        logs.append(entry)
        if reflect_dmg > 0:
            logs.append({"type": "reflect", "text": f"反伤！{monster_name}受到 {reflect_dmg} 点反弹伤害！"})
        if lifesteal_heal > 0:
            logs.append({"type": "lifesteal", "text": f"吸血！{monster_name}恢复了 {lifesteal_heal} 点生命。"})
        return logs

    elif action == "defend":
        session.monster_defending = True
        return [{"type": "monster_defend", "text": f"{monster_name}摆出了防御姿态。"}]

    elif action == "special":
        special = session.monster_config.get("ai", {}).get("special")
        if special and special.get("type") == "apply_effect":
            if random.random() < special.get("chance", 0.3):
                effect_type = special["effect"]
                duration = special.get("duration", 3)
                new_eff = StatusEffect(effect_type, duration, source="monster")
                session.player_effects = add_effect(session.player_effects, new_eff)
                if effect_type in STAT_BUFF_MAP:
                    _recalculate_player_buffs(session)
                return [{"type": "monster_special", "text": special.get("message", f"{monster_name}使用了特殊技能！")}]
            else:
                result = calc_damage(
                    session.monster_config["stats"]["attack"],
                    session.player_defense,
                    session.monster_config["stats"]["speed"],
                    session.player_speed,
                    session.player_defending
                )
                actual_dmg, shield_absorbed = apply_shield(session.player_shield, result["damage"])
                session.player_shield -= shield_absorbed
                session.player_hp = max(0, session.player_hp - actual_dmg)
                return [{"type": "monster_attack", "damage": actual_dmg,
                        "crit": result["is_crit"], "defended": result["defended"],
                        "text": f"{monster_name}攻击了你，造成 {actual_dmg} 点伤害。"}]
        else:
            return execute_action(session, "attack")

    return [{"type": "monster_idle", "text": f"{monster_name}在观望。"}]
