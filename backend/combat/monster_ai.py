"""Monster AI decision and execution module with BOSS phase support."""

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import CombatSession, MonsterInstance, StatusEffect
    from .effects import StatusEffect, add_effect, _recalculate_player_buffs, EFFECT_NAMES, STAT_BUFF_MAP
    from .damage import calc_damage, apply_shield


def check_boss_phase(monster: "MonsterInstance") -> dict | None:
    if not monster.is_boss:
        return None
    phases = monster.config.get("phases", [])
    if not phases:
        return None

    triggered_phase = None
    for i, phase in enumerate(phases):
        if i <= monster.current_phase:
            continue
        if monster.hp_ratio <= phase["hp_threshold"]:
            monster.current_phase = i
            monster.phase_changed = True
            triggered_phase = phase
            stat_boost = phase.get("stat_boost", {})
            if "attack" in stat_boost:
                monster.config["stats"]["attack"] = int(
                    monster.base_attack * stat_boost["attack"]
                )
            if "defense" in stat_boost:
                monster.config["stats"]["defense"] = int(
                    monster.base_defense * stat_boost["defense"]
                )
            if "speed" in stat_boost:
                monster.config["stats"]["speed"] = int(
                    monster.base_speed * stat_boost["speed"]
                )

    return triggered_phase


def decide_action(session: "CombatSession", monster: "MonsterInstance" = None) -> str:
    if monster is None:
        monster = session.monsters[0] if session.monsters else None
        if monster is None:
            return "attack"

    ai = monster.config.get("ai", {})
    behavior = ai.get("behavior", "aggressive")

    if monster.is_boss:
        phases = monster.config.get("phases", [])
        if phases and 0 <= monster.current_phase < len(phases):
            phase_ai = phases[monster.current_phase].get("ai")
            if phase_ai:
                attack_w = int(phase_ai.get("attack", 0.5) * 100)
                defend_w = int(phase_ai.get("defend", 0.3) * 100)
                special_w = int(phase_ai.get("special", 0.2) * 100)

                special = monster.get_current_special()
                if special is None:
                    attack_w += special_w
                    special_w = 0

                total = attack_w + defend_w + special_w
                if total == 0:
                    return "attack"
                roll = random.randint(1, total)

                if roll <= attack_w:
                    return "attack"
                elif roll <= attack_w + defend_w:
                    return "defend"
                else:
                    return "special"

    attack_w = ai.get("attack_weight", 70)
    defend_w = ai.get("defend_weight", 20)
    special_w = ai.get("special_weight", 10)

    if behavior == "cautious":
        hp_ratio = monster.hp / monster.max_hp
        if hp_ratio < 0.3:
            defend_w += 30
            attack_w = max(10, attack_w - 20)

    special = monster.get_current_special() if monster.is_boss else ai.get("special")
    if special is None:
        attack_w += special_w
        special_w = 0

    total = attack_w + defend_w + special_w
    if total == 0:
        return "attack"
    roll = random.randint(1, total)

    if roll <= attack_w:
        return "attack"
    elif roll <= attack_w + defend_w:
        return "defend"
    else:
        return "special"


def execute_action(session: "CombatSession", action: str,
                   monster: "MonsterInstance" = None) -> list[dict]:
    from .session import StatusEffect, is_immune_to_effect
    from .effects import add_effect, _recalculate_player_buffs, EFFECT_NAMES, STAT_BUFF_MAP
    from .damage import calc_damage, apply_shield, apply_reflect, apply_lifesteal

    if monster is None:
        monster = session.monsters[0] if session.monsters else None
        if monster is None:
            return []

    monster_name = monster.config["name"]
    logs = []

    if action == "attack":
        result = calc_damage(
            monster.attack,
            session.player_defense,
            monster.speed,
            session.player_speed,
            session.player_defending,
            attacker_element=monster.config.get("element", "none"),
            defender_element=session.player_element,
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
            monster.hp = max(0, monster.hp - reflect_dmg)

        lifesteal_heal = apply_lifesteal(
            next((e.value for e in session.player_effects if e.effect_type == "lifesteal"), 0),
            actual_dmg
        )
        if lifesteal_heal > 0:
            session.player_hp = min(session.player_max_hp, session.player_hp + lifesteal_heal)

        entry = {"type": "monster_attack", "damage": actual_dmg,
                 "crit": result["is_crit"], "defended": result["defended"],
                 "monster_index": monster.index}
        if shield_absorbed > 0:
            entry["shield_absorbed"] = shield_absorbed
        if result["is_crit"]:
            entry["text"] = f"暴击！{monster_name}对你造成 {actual_dmg} 点伤害！"
        else:
            entry["text"] = f"{monster_name}攻击了你，造成 {actual_dmg} 点伤害。"
        if shield_absorbed > 0:
            entry["text"] += f"（护盾吸收 {shield_absorbed}）"
        if result.get("element_multiplier", 1.0) > 1.0:
            entry["text"] += " [属性克制！]"
            logs.append({"type": "element_advantage",
                         "text": f"{monster_name}属性克制你！伤害提升！",
                         "multiplier": result["element_multiplier"]})
        elif result.get("element_multiplier", 1.0) < 1.0:
            entry["text"] += " [属性被克制！]"
            logs.append({"type": "element_disadvantage",
                         "text": f"{monster_name}属性被你克制！伤害降低！",
                         "multiplier": result["element_multiplier"]})
        logs.append(entry)
        if reflect_dmg > 0:
            logs.append({"type": "reflect", "text": f"反伤！{monster_name}受到 {reflect_dmg} 点反弹伤害！"})
        if lifesteal_heal > 0:
            logs.append({"type": "lifesteal", "text": f"吸血！{monster_name}恢复了 {lifesteal_heal} 点生命。"})
        return logs

    elif action == "defend":
        monster.defending = True
        return [{"type": "monster_defend", "text": f"{monster_name}摆出了防御姿态。",
                 "monster_index": monster.index}]

    elif action == "special":
        special = monster.get_current_special() if monster.is_boss else monster.config.get("ai", {}).get("special")
        if not special:
            return execute_action(session, "attack", monster)

        special_type = special.get("type", "apply_effect")

        if special_type == "aoe_attack":
            dmg_mult = special.get("damage_multiplier", 0.8)
            raw_dmg = int(monster.attack * dmg_mult)
            actual_dmg, shield_absorbed = apply_shield(session.player_shield, raw_dmg)
            session.player_shield -= shield_absorbed
            session.player_hp = max(0, session.player_hp - actual_dmg)
            entry = {"type": "monster_special", "damage": actual_dmg,
                     "aoe": True, "monster_index": monster.index,
                     "text": special.get("message", f"{monster_name}发动了群体攻击！造成 {actual_dmg} 点伤害。")}
            if shield_absorbed > 0:
                entry["text"] += f"（护盾吸收 {shield_absorbed}）"

            effect_type = special.get("effect")
            if effect_type and random.random() < special.get("chance", 0.3):
                if not is_immune_to_effect(monster.config, effect_type):
                    duration = special.get("duration", 2)
                    value = special.get("value", 0)
                    new_eff = StatusEffect(effect_type, duration, value=value, source="monster")
                    session.player_effects = add_effect(session.player_effects, new_eff)
                    if effect_type in STAT_BUFF_MAP:
                        _recalculate_player_buffs(session)
                    eff_name = EFFECT_NAMES.get(effect_type, effect_type)
                    entry["text"] += f" 你被{eff_name}了！"
            logs.append(entry)
            return logs

        elif special_type == "self_heal":
            heal_pct = special.get("heal_percent", 0.15)
            heal_amount = int(monster.max_hp * heal_pct)
            monster.hp = min(monster.max_hp, monster.hp + heal_amount)
            return [{"type": "monster_special",
                     "text": special.get("message", f"{monster_name}恢复了 {heal_amount} 点生命！"),
                     "monster_index": monster.index, "heal": heal_amount}]

        elif special_type == "apply_effect":
            effect_type = special["effect"]
            if is_immune_to_effect(monster.config, effect_type):
                return execute_action(session, "attack", monster)

            if random.random() < special.get("chance", 0.3):
                duration = special.get("duration", 3)
                value = special.get("value", 0)
                new_eff = StatusEffect(effect_type, duration, value=value, source="monster")
                session.player_effects = add_effect(session.player_effects, new_eff)
                if effect_type in STAT_BUFF_MAP:
                    _recalculate_player_buffs(session)
                return [{"type": "monster_special", "text": special.get("message", f"{monster_name}使用了特殊技能！"),
                         "monster_index": monster.index}]
            else:
                result = calc_damage(
                    monster.attack,
                    session.player_defense,
                    monster.speed,
                    session.player_speed,
                    session.player_defending,
                    attacker_element=monster.config.get("element", "none"),
                    defender_element=session.player_element,
                )
                actual_dmg, shield_absorbed = apply_shield(session.player_shield, result["damage"])
                session.player_shield -= shield_absorbed
                session.player_hp = max(0, session.player_hp - actual_dmg)
                return [{"type": "monster_attack", "damage": actual_dmg,
                        "crit": result["is_crit"], "defended": result["defended"],
                        "monster_index": monster.index,
                        "text": f"{monster_name}攻击了你，造成 {actual_dmg} 点伤害。"}]
        else:
            return execute_action(session, "attack", monster)

    return [{"type": "monster_idle", "text": f"{monster_name}在观望。",
             "monster_index": monster.index}]
