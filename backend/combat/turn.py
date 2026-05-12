"""Turn resolution module - coordinates combat flow."""

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import CombatSession, CombatPhase
    from .effects import process_effects, is_blocked_by_effect, is_silenced
    from .damage import calc_damage, calc_flee_chance, calc_drops, apply_shield, apply_reflect, apply_lifesteal
    from .monster_ai import decide_action, execute_action
    from .skills import execute_skill
    from .events import get_dispatcher, CombatEvent, register_talent_handlers, register_affix_handlers, clear_dispatcher


def _use_item_in_combat(session: "CombatSession", item_id: str) -> dict:
    from item_system import get_item_effect
    from pathlib import Path

    _ITEMS_FILE = Path(__file__).parent.parent.parent / "config" / "items.json"
    _ITEMS_DB = {}
    if _ITEMS_FILE.exists():
        import json
        with open(_ITEMS_FILE, "r", encoding="utf-8") as f:
            _ITEMS_DB = json.load(f)

    def _get_item_name(item_id: str) -> str:
        item = _ITEMS_DB.get(item_id)
        return item["name"] if item else item_id

    from .session import StatusEffect
    from .effects import add_effect, _recalculate_player_buffs, STAT_BUFF_MAP, EFFECT_NAMES

    effect = get_item_effect(item_id)
    if not effect:
        return {"type": "use_item", "success": False, "text": "该物品无法在战斗中使用。"}

    item_name = _get_item_name(item_id)

    if effect["type"] == "heal":
        old_hp = session.player_hp
        session.player_hp = min(session.player_max_hp, session.player_hp + effect["value"])
        healed = session.player_hp - old_hp
        return {"type": "use_item", "success": True, "item_id": item_id,
                "text": f"使用了{item_name}，恢复了 {healed} 点生命。"}

    elif effect["type"] == "restore_mp":
        old_mp = session.player_mp
        session.player_mp = min(session.player_max_mp, session.player_mp + effect["value"])
        restored = session.player_mp - old_mp
        return {"type": "use_item", "success": True, "item_id": item_id,
                "text": f"使用了{item_name}，恢复了 {restored} 点魔法值。"}

    elif effect["type"] == "cure":
        removed = [e for e in session.player_effects if e.effect_type == effect["effect"]]
        session.player_effects = [e for e in session.player_effects if e.effect_type != effect["effect"]]
        if removed:
            return {"type": "use_item", "success": True, "item_id": item_id,
                    "text": f"使用了{item_name}，解除了{effect['effect']}状态。"}
        return {"type": "use_item", "success": True, "item_id": item_id,
                "text": f"使用了{item_name}，但没有需要解除的状态。"}

    elif effect["type"] == "buff":
        buff_type = f"buff_{effect['stat']}"
        new_eff = StatusEffect(buff_type, effect["duration"], effect["value"],
                               source=f"item:{item_id}")
        session.player_effects = add_effect(session.player_effects, new_eff)
        if buff_type in STAT_BUFF_MAP:
            _recalculate_player_buffs(session)
        stat_names = {"attack": "攻击力", "speed": "速度", "defense": "防御力"}
        stat_name = stat_names.get(effect["stat"], effect["stat"])
        return {"type": "use_item", "success": True, "item_id": item_id,
                "text": f"使用了{item_name}，{stat_name}提升 {effect['value']} 持续 {effect['duration']} 回合！"}

    elif effect["type"] == "shield":
        session.player_shield += effect["value"]
        return {"type": "use_item", "success": True, "item_id": item_id,
                "text": f"使用了{item_name}，获得了 {effect['value']} 点护盾！"}

    elif effect["type"] == "apply_effect":
        eff_type = effect["effect"]
        new_eff = StatusEffect(eff_type, effect.get("duration", 3),
                               effect.get("value", 0), source=f"item:{item_id}")
        session.player_effects = add_effect(session.player_effects, new_eff)
        if eff_type in STAT_BUFF_MAP:
            _recalculate_player_buffs(session)
        eff_name = EFFECT_NAMES.get(eff_type, eff_type)
        return {"type": "use_item", "success": True, "item_id": item_id,
                "text": f"使用了{item_name}，获得了{eff_name}效果！"}

    return {"type": "use_item", "success": False, "text": "未知物品效果。"}


def _build_state(session: "CombatSession", log_entries: list[dict], fled: bool = False) -> dict:
    from skill_system import format_skill_for_frontend
    state = {
        "session_id": session.session_id,
        "phase": session.phase.value,
        "turn_count": session.turn_count,
        "player_hp": session.player_hp,
        "player_max_hp": session.player_max_hp,
        "player_mp": session.player_mp,
        "player_max_mp": session.player_max_mp,
        "monster_hp": session.monster_hp,
        "monster_max_hp": session.monster_max_hp,
        "monster_name": session.monster_config["name"],
        "log": log_entries,
        "player_effects": [e.to_dict() for e in session.player_effects],
        "player_shield": session.player_shield,
        "monster_effects": [e.to_dict() for e in session.monster_effects],
        "monster_defending": session.monster_defending,
        "skills": [format_skill_for_frontend(s, session.skill_cooldowns.get(s, 0)) for s in session.player_skills],
    }
    if session.phase.value == "victory":
        state["exp_reward"] = session.exp_reward
        state["gold_reward"] = session.gold_reward
        state["drops"] = session.drops
        state["fled"] = fled
    return state


def resolve_turn(session: "CombatSession", action: str,
                 action_data: dict = None) -> dict:
    from .session import CombatPhase
    from .effects import process_effects, is_blocked_by_effect, is_silenced
    from .damage import calc_damage, calc_flee_chance, calc_drops, apply_shield, apply_reflect, apply_lifesteal
    from .monster_ai import decide_action, execute_action
    from .skills import execute_skill
    from .events import get_dispatcher, CombatEvent, register_talent_handlers, register_affix_handlers, clear_dispatcher

    clear_dispatcher()
    register_talent_handlers(session)
    register_affix_handlers(session)

    session.turn_count += 1
    log_entries = []

    if session.turn_count == 1:
        start_logs = get_dispatcher().dispatch(CombatEvent.ON_COMBAT_START, session=session)
        log_entries.extend(start_logs)

    cond_logs = get_dispatcher().dispatch(CombatEvent.ON_CONDITIONAL, session=session)
    log_entries.extend(cond_logs)

    regen_logs = get_dispatcher().dispatch(CombatEvent.ON_PASSIVE_REGEN, session=session)
    log_entries.extend(regen_logs)

    if session.talent_passives and session.talent_passives.get("mp_regen", 0) > 0:
        mp_regen = max(1, int(session.player_max_mp * session.talent_passives["mp_regen"]))
        session.player_mp = min(session.player_max_mp, session.player_mp + mp_regen)

    player_effects_log = process_effects(session, is_player=True)
    log_entries.extend(player_effects_log)

    if session.player_hp <= 0:
        session.phase = CombatPhase.DEFEAT
        log_entries.append({"type": "defeat", "text": "你倒下了..."})
        return _build_state(session, log_entries)

    is_stunned = is_blocked_by_effect(session.player_effects)
    is_silenced_flag = is_silenced(session.player_effects)

    if is_stunned:
        action = "stunned"

    if action == "stunned":
        log_entries.append({"type": "player_stunned", "text": "你被控制，无法行动！"})

    elif action == "attack":
        result = calc_damage(
            session.player_attack,
            session.monster_config["stats"]["defense"],
            session.player_speed,
            session.monster_config["stats"]["speed"],
            session.monster_defending
        )
        actual_dmg, shield_absorbed = apply_shield(
            next((e.value for e in session.monster_effects if e.effect_type == "shield"), 0),
            result["damage"]
        )
        if shield_absorbed > 0:
            shield_eff = next((e for e in session.monster_effects if e.effect_type == "shield"), None)
            if shield_eff:
                shield_eff.value -= shield_absorbed
                if shield_eff.value <= 0:
                    session.monster_effects = [e for e in session.monster_effects if e.effect_type != "shield"]

        session.monster_hp = max(0, session.monster_hp - actual_dmg)
        reflect_dmg = apply_reflect(
            next((e.value for e in session.player_effects if e.effect_type == "reflect"), 0),
            actual_dmg
        )
        if reflect_dmg > 0:
            session.player_hp = max(0, session.player_hp - reflect_dmg)

        lifesteal_heal = apply_lifesteal(
            next((e.value for e in session.player_effects if e.effect_type == "lifesteal"), 0),
            actual_dmg
        )
        if lifesteal_heal > 0:
            session.player_hp = min(session.player_max_hp, session.player_hp + lifesteal_heal)

        monster_name = session.monster_config["name"]
        entry = {"type": "player_attack", "damage": actual_dmg,
                 "crit": result["is_crit"], "defended": result["defended"]}
        if shield_absorbed > 0:
            entry["shield_absorbed"] = shield_absorbed
        if result["is_crit"]:
            entry["text"] = f"暴击！你对{monster_name}造成 {actual_dmg} 点伤害！"
        else:
            entry["text"] = f"你对{monster_name}造成 {actual_dmg} 点伤害。"
        if shield_absorbed > 0:
            entry["text"] += f"（护盾吸收 {shield_absorbed}）"
        if reflect_dmg > 0:
            log_entries.append({"type": "reflect", "text": f"反伤！你受到 {reflect_dmg} 点反弹伤害。"})
        if lifesteal_heal > 0:
            log_entries.append({"type": "lifesteal", "text": f"吸血！恢复了 {lifesteal_heal} 点生命。"})
        log_entries.append(entry)

        atk_logs = get_dispatcher().dispatch(CombatEvent.ON_ATTACK, session=session, damage=actual_dmg)
        log_entries.extend(atk_logs)

    elif action == "defend":
        defend_reduction = 0.5
        if session.talent_passives and session.talent_passives.get("defend_boost", 0.5) > 0.5:
            defend_reduction = 1.0 - session.talent_passives["defend_boost"]
        session.player_defending = True
        reduction_pct = int((1 - defend_reduction) * 100)
        log_entries.append({"type": "player_defend", "text": f"你举起防御姿态，减少{reduction_pct}%伤害。"})

    elif action == "use_item":
        item_id = (action_data or {}).get("item_id")
        item_result = _use_item_in_combat(session, item_id)
        log_entries.append(item_result)
        if not item_result.get("success"):
            return _build_state(session, log_entries)

    elif action == "flee":
        if is_stunned:
            log_entries.append({"type": "player_stunned", "text": "你被控制，无法行动！"})
        else:
            chance = calc_flee_chance(session.player_speed, session.monster_config["stats"]["speed"])
            if random.random() < chance:
                session.phase = CombatPhase.VICTORY
                session.drops = []
                session.exp_reward = 0
                session.gold_reward = 0
                log_entries.append({"type": "flee", "fled": True,
                                    "text": f"逃跑成功！(概率 {int(chance * 100)}%)"})
                return _build_state(session, log_entries, fled=True)
            else:
                log_entries.append({"type": "flee", "fled": False,
                                    "text": f"逃跑失败！(概率 {int(chance * 100)}%)"})

    elif action == "skill":
        if is_silenced_flag:
            log_entries.append({"type": "skill", "success": False, "text": "你被沉默，无法使用技能！"})
        else:
            skill_id = (action_data or {}).get("skill_id")
            skill_result = execute_skill(session, skill_id)
            log_entries.append(skill_result)
            if not skill_result.get("success"):
                return _build_state(session, log_entries)

    if session.monster_hp <= 0:
        session.phase = CombatPhase.VICTORY
        drops, gold = calc_drops(session.monster_config)
        session.drops = drops
        session.gold_reward = gold
        session.exp_reward = session.monster_config["exp_reward"]
        log_entries.append({"type": "victory",
                            "text": f"击败了{session.monster_config['name']}！"})

        kill_logs_result = get_dispatcher().dispatch(CombatEvent.ON_KILL, session=session)
        for kill_log in kill_logs_result:
            if isinstance(kill_log, tuple):
                logs_part, gold_mult, exp_mult = kill_log
                log_entries.extend(logs_part)
                if gold_mult > 1.0:
                    session.gold_reward = int(session.gold_reward * gold_mult)
                if exp_mult > 1.0:
                    session.exp_reward = int(session.exp_reward * exp_mult)
            elif isinstance(kill_log, dict):
                log_entries.append(kill_log)

        if session.talent_passives and session.talent_passives.get("last_stand"):
            if session.player_hp <= 0:
                session.player_hp = 1
                log_entries.append({"type": "talent", "text": "天赋触发！不屈意志，HP 锁定为 1！"})
        return _build_state(session, log_entries)

    session.monster_defending = False

    monster_effects_log = process_effects(session, is_player=False)
    log_entries.extend(monster_effects_log)

    if session.monster_hp <= 0:
        session.phase = CombatPhase.VICTORY
        drops, gold = calc_drops(session.monster_config)
        session.drops = drops
        session.gold_reward = gold
        session.exp_reward = session.monster_config["exp_reward"]
        log_entries.append({"type": "victory",
                            "text": f"{session.monster_config['name']}倒下了！"})
        return _build_state(session, log_entries)

    monster_action = decide_action(session)
    monster_logs = execute_action(session, monster_action)
    log_entries.extend(monster_logs)

    if session.player_hp <= 0:
        session.phase = CombatPhase.DEFEAT
        log_entries.append({"type": "defeat", "text": "你倒下了..."})

    session.player_defending = False

    for sid in list(session.skill_cooldowns.keys()):
        session.skill_cooldowns[sid] -= 1
        if session.skill_cooldowns[sid] <= 0:
            del session.skill_cooldowns[sid]

    return _build_state(session, log_entries)
