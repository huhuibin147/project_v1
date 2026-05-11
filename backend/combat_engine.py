"""Combat engine: turn-based combat logic, session management, damage formulas."""

import random
import time
import uuid
from enum import Enum
from pathlib import Path

# Load items DB for name lookups
_ITEMS_FILE = Path(__file__).parent.parent / "config" / "items.json"
_ITEMS_DB = {}
if _ITEMS_FILE.exists():
    import json
    with open(_ITEMS_FILE, "r", encoding="utf-8") as f:
        _ITEMS_DB = json.load(f)


def _get_item_name(item_id: str) -> str:
    item = _ITEMS_DB.get(item_id)
    return item["name"] if item else item_id


class CombatPhase(str, Enum):
    PLAYER_TURN = "player_turn"
    VICTORY = "victory"
    DEFEAT = "defeat"


class StatusEffect:
    def __init__(self, effect_type: str, duration: int, value: int = 0,
                 stack: int = 1, source: str = ""):
        self.effect_type = effect_type
        self.duration = duration
        self.value = value
        self.stack = stack
        self.source = source

    def to_dict(self):
        return {
            "type": self.effect_type,
            "duration": self.duration,
            "value": self.value,
            "stack": self.stack,
            "source": self.source,
        }


class CombatSession:
    def __init__(self, session_id: str, monster_id: str, monster_config: dict,
                 player_snapshot: dict):
        self.session_id = session_id
        self.monster_id = monster_id
        self.monster_config = monster_config

        self.monster_hp = monster_config["stats"]["hp"]
        self.monster_max_hp = monster_config["stats"]["hp"]
        self.monster_defending = False
        self.monster_effects: list[StatusEffect] = []

        self.player_hp = player_snapshot["hp"]
        self.player_max_hp = player_snapshot["max_hp"]
        self.player_mp = player_snapshot.get("mp", 0)
        self.player_max_mp = player_snapshot.get("max_mp", 0)
        self.player_attack = player_snapshot["attack"]
        self.player_defense = player_snapshot["defense"]
        self.player_speed = player_snapshot["speed"]
        self.base_player_attack = player_snapshot["attack"]
        self.base_player_defense = player_snapshot["defense"]
        self.base_player_speed = player_snapshot["speed"]
        self.player_skills = player_snapshot.get("skills", [])
        self.player_defending = False
        self.player_effects: list[StatusEffect] = []
        self.player_shield: int = 0
        self.skill_cooldowns: dict[str, int] = {}
        self.talent_passives: dict = player_snapshot.get("talent_passives", {})

        self.phase = CombatPhase.PLAYER_TURN
        self.turn_count = 0
        self.log: list[dict] = []
        self.created_at = time.time()
        self.drops: list[dict] = []
        self.exp_reward = 0
        self.gold_reward = 0


# --- Item effects (shared with item_system) ---

from item_system import ITEM_EFFECTS


# --- Damage calculation ---

def calc_damage(attacker_attack: int, defender_defense: int,
                attacker_speed: int, defender_speed: int,
                is_defending: bool) -> dict:
    base = attacker_attack * (100.0 / (100.0 + defender_defense))
    variance = random.uniform(0.9, 1.1)
    damage = base * variance

    speed_diff = attacker_speed - defender_speed
    crit_chance = min(0.25, max(0.05, 0.05 + speed_diff * 0.005))
    is_crit = random.random() < crit_chance
    if is_crit:
        damage *= 1.5

    if is_defending:
        damage *= 0.5

    damage = max(1, int(damage))
    return {"damage": damage, "is_crit": is_crit, "defended": is_defending}


def calc_flee_chance(player_speed: int, monster_speed: int) -> float:
    speed_ratio = player_speed / max(1, monster_speed)
    chance = 0.3 + (speed_ratio - 1.0) * 0.3
    return max(0.1, min(0.9, chance))


def calc_drops(monster_config: dict) -> tuple[list[dict], int]:
    drops = []
    for drop in monster_config.get("drops", []):
        if random.random() < drop["chance"]:
            drops.append({"item_id": drop["item_id"], "quantity": 1})
    gold_range = monster_config.get("gold_reward", [0, 0])
    gold = random.randint(gold_range[0], gold_range[1])
    return drops, gold


# --- Status effect processing ---

STAT_BUFF_MAP = {
    "attack_up": ("attack", "base_player_attack"),
    "defense_up": ("defense", "base_player_defense"),
    "speed_up": ("speed", "base_player_speed"),
    "defense_down": ("defense", "base_player_defense"),
    "speed_down": ("speed", "base_player_speed"),
}

EFFECT_NAMES = {
    "poison": "中毒", "burn": "灼烧", "freeze": "冻结", "stun": "眩晕",
    "silence": "沉默", "speed_down": "减速", "bleed": "流血",
    "shield": "护盾", "regen": "再生", "reflect": "反伤", "lifesteal": "吸血",
    "attack_up": "攻击增强", "defense_up": "防御增强", "speed_up": "速度增强",
    "defense_down": "防御降低",
}

STACKABLE_EFFECTS = {"bleed"}
MAX_STACKS = {"bleed": 3}

MUTEX_PAIRS = [("burn", "freeze")]

def _find_effect(effects: list[StatusEffect], effect_type: str) -> StatusEffect | None:
    for e in effects:
        if e.effect_type == effect_type:
            return e
    return None

def _add_effect(effects: list[StatusEffect], new_eff: StatusEffect) -> list[StatusEffect]:
    for pair_a, pair_b in MUTEX_PAIRS:
        if new_eff.effect_type == pair_a:
            effects = [e for e in effects if e.effect_type != pair_b]
        elif new_eff.effect_type == pair_b:
            effects = [e for e in effects if e.effect_type != pair_a]
    existing = _find_effect(effects, new_eff.effect_type)
    if existing:
        if new_eff.effect_type in STACKABLE_EFFECTS:
            existing.stack = min(existing.stack + 1, MAX_STACKS.get(new_eff.effect_type, 1))
            existing.duration = max(existing.duration, new_eff.duration)
            existing.value = new_eff.value
        else:
            existing.duration = max(existing.duration, new_eff.duration)
            existing.value = new_eff.value
        return effects
    effects.append(new_eff)
    return effects

def _apply_buff(session: CombatSession, eff: StatusEffect) -> None:
    if eff.effect_type == "attack_up":
        session.player_attack = session.base_player_attack + eff.value
    elif eff.effect_type == "defense_up":
        session.player_defense = session.base_player_defense + eff.value
    elif eff.effect_type == "speed_up":
        session.player_speed = session.base_player_speed + eff.value
    elif eff.effect_type == "defense_down":
        session.player_defense = max(0, session.base_player_defense - eff.value)
    elif eff.effect_type == "speed_down":
        session.player_speed = max(1, int(session.base_player_speed * 0.7))

def _recalculate_player_buffs(session: CombatSession) -> None:
    session.player_attack = session.base_player_attack
    session.player_defense = session.base_player_defense
    session.player_speed = session.base_player_speed
    for eff in session.player_effects:
        if eff.effect_type in STAT_BUFF_MAP:
            _apply_buff(session, eff)

def _process_effects(session: CombatSession, is_player: bool) -> list[dict]:
    if is_player:
        effects = session.player_effects
        hp = session.player_hp
        max_hp = session.player_max_hp
    else:
        effects = session.monster_effects
        hp = session.monster_hp
        max_hp = session.monster_max_hp

    logs = []
    remaining = []
    expired_buffs = []
    for eff in effects:
        name = EFFECT_NAMES.get(eff.effect_type, eff.effect_type)

        if eff.effect_type == "poison":
            dmg = max(1, int(max_hp * 0.05))
            hp = max(0, hp - dmg)
            logs.append({"type": "effect", "text": f"中毒！受到 {dmg} 点伤害。"})
        elif eff.effect_type == "burn":
            dmg = max(1, int(max_hp * 0.03))
            hp = max(0, hp - dmg)
            logs.append({"type": "effect", "text": f"灼烧！受到 {dmg} 点伤害。"})
        elif eff.effect_type == "bleed":
            dmg = max(1, int(max_hp * 0.04 * eff.stack))
            hp = max(0, hp - dmg)
            stack_text = f"（{eff.stack} 层）" if eff.stack > 1 else ""
            logs.append({"type": "effect", "text": f"流血{stack_text}！受到 {dmg} 点伤害。"})
        elif eff.effect_type == "regen":
            heal = max(1, int(max_hp * 0.03))
            hp = min(max_hp, hp + heal)
            logs.append({"type": "effect", "text": f"再生！恢复了 {heal} 点生命。"})
        elif eff.effect_type == "stun":
            logs.append({"type": "effect", "text": f"{name}！无法行动！"})
        elif eff.effect_type == "silence":
            logs.append({"type": "effect", "text": f"{name}！无法使用技能！"})
        elif eff.effect_type == "speed_down":
            logs.append({"type": "effect", "text": f"{name}！速度降低！"})
        elif eff.effect_type == "freeze":
            logs.append({"type": "effect", "text": f"{name}！无法行动！"})

        eff.duration -= 1
        if eff.duration > 0:
            remaining.append(eff)
        else:
            if eff.effect_type in STAT_BUFF_MAP:
                expired_buffs.append(eff)
            logs.append({"type": "effect_end", "text": f"{name}效果消失了。"})

    if is_player:
        session.player_hp = hp
        session.player_effects = remaining
        if expired_buffs:
            _recalculate_player_buffs(session)
    else:
        session.monster_hp = hp
        session.monster_effects = remaining

    return logs


# --- Item use ---

def _use_item_in_combat(session: CombatSession, item_id: str) -> dict:
    effect = ITEM_EFFECTS.get(item_id)
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
        session.player_effects = _add_effect(session.player_effects, new_eff)
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
        session.player_effects = _add_effect(session.player_effects, new_eff)
        if eff_type in STAT_BUFF_MAP:
            _recalculate_player_buffs(session)
        eff_name = EFFECT_NAMES.get(eff_type, eff_type)
        return {"type": "use_item", "success": True, "item_id": item_id,
                "text": f"使用了{item_name}，获得了{eff_name}效果！"}

    return {"type": "use_item", "success": False, "text": "未知物品效果。"}


# --- Monster AI ---

def _decide_monster_action(session: CombatSession) -> str:
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


def _execute_monster_action(session: CombatSession, action: str) -> list[dict]:
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
        actual_dmg, shield_absorbed = _apply_shield(session, result["damage"], is_player=True)
        session.player_hp = max(0, session.player_hp - actual_dmg)
        reflect_dmg = _apply_reflect(session, actual_dmg, is_player=False)
        lifesteal_heal = _apply_lifesteal(session, actual_dmg, is_player=False)
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
                session.player_effects = _add_effect(session.player_effects, new_eff)
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
                actual_dmg, shield_absorbed = _apply_shield(session, result["damage"], is_player=True)
                session.player_hp = max(0, session.player_hp - actual_dmg)
                return [{"type": "monster_attack", "damage": actual_dmg,
                        "crit": result["is_crit"], "defended": result["defended"],
                        "text": f"{monster_name}攻击了你，造成 {actual_dmg} 点伤害。"}]
        else:
            return _execute_monster_action(session, "attack")

    return [{"type": "monster_idle", "text": f"{monster_name}在观望。"}]


# --- Build response state ---

def _build_state(session: CombatSession, log_entries: list[dict], fled: bool = False) -> dict:
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
    if session.phase == CombatPhase.VICTORY:
        state["exp_reward"] = session.exp_reward
        state["gold_reward"] = session.gold_reward
        state["drops"] = session.drops
        state["fled"] = fled
    return state


# --- Core turn resolution ---

def _has_effect(effects: list[StatusEffect], effect_type: str) -> bool:
    return any(e.effect_type == effect_type for e in effects)


def _apply_shield(session: CombatSession, damage: int, is_player: bool) -> int:
    absorbed = 0
    if is_player and session.player_shield > 0:
        absorbed = min(session.player_shield, damage)
        session.player_shield -= absorbed
        damage -= absorbed
    elif not is_player:
        shield_eff = _find_effect(session.monster_effects, "shield")
        if shield_eff and shield_eff.value > 0:
            absorbed = min(shield_eff.value, damage)
            shield_eff.value -= absorbed
            damage -= absorbed
            if shield_eff.value <= 0:
                session.monster_effects = [e for e in session.monster_effects if e.effect_type != "shield"]
    return damage, absorbed


def _apply_reflect(session: CombatSession, damage: int, is_player: bool) -> int:
    reflect_dmg = 0
    if is_player:
        reflect_eff = _find_effect(session.monster_effects, "reflect")
        if reflect_eff:
            reflect_pct = reflect_eff.value / 100.0 if reflect_eff.value > 1 else reflect_eff.value
            reflect_dmg = max(1, int(damage * reflect_pct))
            session.monster_hp = max(0, session.monster_hp - reflect_dmg)
    else:
        reflect_eff = _find_effect(session.player_effects, "reflect")
        if reflect_eff:
            reflect_pct = reflect_eff.value / 100.0 if reflect_eff.value > 1 else reflect_eff.value
            reflect_dmg = max(1, int(damage * reflect_pct))
            session.player_hp = max(0, session.player_hp - reflect_dmg)
    return reflect_dmg


def _apply_lifesteal(session: CombatSession, damage: int, is_player: bool) -> int:
    heal = 0
    if is_player:
        ls_eff = _find_effect(session.player_effects, "lifesteal")
        if ls_eff:
            ls_pct = ls_eff.value / 100.0 if ls_eff.value > 1 else ls_eff.value
            heal = max(1, int(damage * ls_pct))
            session.player_hp = min(session.player_max_hp, session.player_hp + heal)
    else:
        ls_eff = _find_effect(session.monster_effects, "lifesteal")
        if ls_eff:
            ls_pct = ls_eff.value / 100.0 if ls_eff.value > 1 else ls_eff.value
            heal = max(1, int(damage * ls_pct))
            session.monster_hp = min(session.monster_max_hp, session.monster_hp + heal)
    return heal


def _apply_talent_on_combat_start(session: CombatSession) -> list[dict]:
    logs = []
    passives = session.talent_passives
    for eff in passives.get("on_combat_start", []):
        if eff.get("action") == "apply_effect_to_monster":
            effect_type = eff.get("effect")
            duration = eff.get("duration", 1)
            chance = eff.get("chance", 1.0)
            if random.random() < chance:
                new_eff = StatusEffect(effect_type, duration, source="talent")
                session.monster_effects = _add_effect(session.monster_effects, new_eff)
                eff_name = EFFECT_NAMES.get(effect_type, effect_type)
                logs.append({"type": "talent", "text": f"天赋触发！怪物被{eff_name}！"})
    return logs


def _apply_talent_on_attack(session: CombatSession, damage: int) -> list[dict]:
    logs = []
    passives = session.talent_passives
    for eff in passives.get("on_attack", []):
        if eff.get("action") == "lifesteal":
            pct = eff.get("value", 0) / 100.0
            heal = max(1, int(damage * pct))
            session.player_hp = min(session.player_max_hp, session.player_hp + heal)
            logs.append({"type": "talent", "text": f"天赋吸血！恢复了 {heal} 点生命。"})
        elif eff.get("action") == "chance_bleed":
            chance = eff.get("chance", 0.2)
            if random.random() < chance:
                new_eff = StatusEffect("bleed", eff.get("duration", 3),
                                       source="talent", stack=1)
                session.monster_effects = _add_effect(session.monster_effects, new_eff)
                logs.append({"type": "talent", "text": "天赋触发！怪物开始流血！"})
        elif eff.get("action") == "chance_stun":
            chance = eff.get("chance", 0.15)
            if random.random() < chance:
                new_eff = StatusEffect("stun", eff.get("duration", 1),
                                       source="talent")
                session.monster_effects = _add_effect(session.monster_effects, new_eff)
                logs.append({"type": "talent", "text": "天赋触发！怪物被眩晕！"})
    return logs


def _apply_talent_on_kill(session: CombatSession) -> list[dict]:
    logs = []
    passives = session.talent_passives
    for eff in passives.get("on_kill", []):
        if eff.get("action") == "heal_pct":
            pct = eff.get("value", 0) / 100.0
            heal = max(1, int(session.player_max_hp * pct))
            session.player_hp = min(session.player_max_hp, session.player_hp + heal)
            logs.append({"type": "talent", "text": f"天赋触发！击杀恢复 {heal} 点生命。"})
        elif eff.get("action") == "attack_boost":
            pct = eff.get("value", 0) / 100.0
            boost = max(1, int(session.base_player_attack * pct))
            new_eff = StatusEffect("attack_up", eff.get("duration", 3),
                                   value=boost, source="talent")
            session.player_effects = _add_effect(session.player_effects, new_eff)
            _recalculate_player_buffs(session)
            logs.append({"type": "talent", "text": f"天赋触发！攻击力提升 {boost}！"})
    return logs


def _apply_talent_conditional(session: CombatSession) -> list[dict]:
    logs = []
    passives = session.talent_passives
    for eff in passives.get("conditional", []):
        condition = eff.get("condition")
        if condition == "hp_below" and session.player_hp < session.player_max_hp * eff.get("threshold", 0.3):
            pct = eff.get("value", 0) / 100.0
            boost = max(1, int(session.base_player_attack * pct))
            new_eff = StatusEffect("attack_up", 1, value=boost, source="talent")
            session.player_effects = _add_effect(session.player_effects, new_eff)
            _recalculate_player_buffs(session)
            logs.append({"type": "talent", "text": f"天赋触发！绝境之力，攻击力 +{boost}！"})
        elif condition == "mp_above" and session.player_mp > session.player_max_mp * eff.get("threshold", 0.5):
            pct = eff.get("value", 0) / 100.0
            boost = max(1, int(session.base_player_attack * pct))
            new_eff = StatusEffect("attack_up", 1, value=boost, source="talent")
            session.player_effects = _add_effect(session.player_effects, new_eff)
            _recalculate_player_buffs(session)
            logs.append({"type": "talent", "text": f"天赋触发！魔力涌动，攻击力 +{boost}！"})
    return logs


def resolve_turn(session: CombatSession, action: str,
                 action_data: dict = None) -> dict:
    session.turn_count += 1
    log_entries = []

    # Talent: combat start (first turn only)
    if session.turn_count == 1 and session.talent_passives:
        talent_start_logs = _apply_talent_on_combat_start(session)
        log_entries.extend(talent_start_logs)

    # Talent: conditional passives
    if session.talent_passives:
        talent_cond_logs = _apply_talent_conditional(session)
        log_entries.extend(talent_cond_logs)

    # Talent: MP regen
    if session.talent_passives and session.talent_passives.get("mp_regen", 0) > 0:
        mp_regen = max(1, int(session.player_max_mp * session.talent_passives["mp_regen"]))
        session.player_mp = min(session.player_max_mp, session.player_mp + mp_regen)

    # Process player effects at start of turn
    player_effects_log = _process_effects(session, is_player=True)
    log_entries.extend(player_effects_log)

    if session.player_hp <= 0:
        session.phase = CombatPhase.DEFEAT
        log_entries.append({"type": "defeat", "text": "你倒下了..."})
        return _build_state(session, log_entries)

    # Check stun/freeze on player
    is_stunned = _has_effect(session.player_effects, "stun") or _has_effect(session.player_effects, "freeze")
    is_silenced = _has_effect(session.player_effects, "silence")

    if is_stunned:
        action = "stunned"

    # Player action
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
        actual_dmg, shield_absorbed = _apply_shield(session, result["damage"], is_player=False)
        session.monster_hp = max(0, session.monster_hp - actual_dmg)
        reflect_dmg = _apply_reflect(session, actual_dmg, is_player=True)
        lifesteal_heal = _apply_lifesteal(session, actual_dmg, is_player=True)
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

        # Talent: on attack triggers
        if session.talent_passives:
            talent_atk_logs = _apply_talent_on_attack(session, actual_dmg)
            log_entries.extend(talent_atk_logs)

    elif action == "defend":
        # Talent: defend boost
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
        if is_silenced:
            log_entries.append({"type": "skill", "success": False, "text": "你被沉默，无法使用技能！"})
        else:
            skill_id = (action_data or {}).get("skill_id")
            skill_result = _execute_skill(session, skill_id)
            log_entries.append(skill_result)
            if not skill_result.get("success"):
                return _build_state(session, log_entries)

    # Check if monster died
    if session.monster_hp <= 0:
        session.phase = CombatPhase.VICTORY
        drops, gold = calc_drops(session.monster_config)
        session.drops = drops
        session.gold_reward = gold
        session.exp_reward = session.monster_config["exp_reward"]
        log_entries.append({"type": "victory",
                            "text": f"击败了{session.monster_config['name']}！"})
        # Talent: on kill triggers
        if session.talent_passives:
            talent_kill_logs = _apply_talent_on_kill(session)
            log_entries.extend(talent_kill_logs)
        # Talent: last stand
        if session.talent_passives and session.talent_passives.get("last_stand"):
            if session.player_hp <= 0:
                session.player_hp = 1
                log_entries.append({"type": "talent", "text": "天赋触发！不屈意志，HP 锁定为 1！"})
        return _build_state(session, log_entries)

    # Reset monster defending
    session.monster_defending = False

    # Process monster effects
    monster_effects_log = _process_effects(session, is_player=False)
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

    # Monster action
    monster_action = _decide_monster_action(session)
    monster_logs = _execute_monster_action(session, monster_action)
    log_entries.extend(monster_logs)

    if session.player_hp <= 0:
        session.phase = CombatPhase.DEFEAT
        log_entries.append({"type": "defeat", "text": "你倒下了..."})

    session.player_defending = False

    # Reduce skill cooldowns
    for sid in list(session.skill_cooldowns.keys()):
        session.skill_cooldowns[sid] -= 1
        if session.skill_cooldowns[sid] <= 0:
            del session.skill_cooldowns[sid]

    return _build_state(session, log_entries)


def _execute_skill(session: CombatSession, skill_id: str) -> dict:
    from skill_system import get_skill
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
    target = skill["target"]
    power = skill.get("power", 1.0)
    effects = skill.get("effects", [])
    monster_name = session.monster_config["name"]

    # Talent: skill enhance
    if session.talent_passives:
        skill_enhances = session.talent_passives.get("skill_enhance", {})
        if skill_id in skill_enhances:
            for enh in skill_enhances[skill_id]:
                if enh.get("enhance") == "power":
                    power += enh.get("value", 0)
                elif enh.get("enhance") == "mp_reduce":
                    session.player_mp += min(skill["mp_cost"], enh.get("value", 0))
                    session.player_mp = min(session.player_max_mp, session.player_mp)

    # Talent: element combo
    if session.talent_passives and session.talent_passives.get("element_combo", 0) > 0:
        if skill.get("damage_type") == "magic":
            power += session.talent_passives["element_combo"]

    # Talent: element storm
    if session.talent_passives and session.talent_passives.get("element_storm"):
        storm = session.talent_passives["element_storm"]
        if skill.get("damage_type") == "magic" and random.random() < storm.get("chance", 0.1):
            extra_dmg = max(1, int(session.player_attack * storm.get("value", 0.3)))
            session.monster_hp = max(0, session.monster_hp - extra_dmg)

    if skill_type == "damage":
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
        # Calculate defense ignore from skill effects
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
        entry = {"type": "skill", "skill_id": skill_id, "success": True,
                 "damage": result["damage"], "crit": result["is_crit"],
                 "text": f"使用 {skill['name']}！对{monster_name}造成 {result['damage']} 点{damage_type_cn}伤害。"}
        if defense_ignore > 0:
            entry["text"] += f" (无视 {defense_ignore}% 防御)"
        # Apply effects
        for eff in effects:
            if eff.get("type") in ("defense_ignore",):
                continue
            if random.random() < eff.get("chance", 1.0):
                new_eff = StatusEffect(eff["type"], eff["duration"], source=f"skill:{skill_id}")
                session.monster_effects = _add_effect(session.monster_effects, new_eff)
                eff_name_cn = effect_type_names.get(eff["type"], eff["type"])
                entry["text"] += f" [{eff_name_cn}]"
        return entry

    elif skill_type == "heal":
        for eff in effects:
            if eff["type"] == "heal":
                old_hp = session.player_hp
                session.player_hp = min(session.player_max_hp, session.player_hp + eff["value"])
                healed = session.player_hp - old_hp
                return {"type": "skill", "skill_id": skill_id, "success": True,
                        "text": f"使用 {skill['name']}！恢复了 {healed} 点生命值。"}
        return {"type": "skill", "skill_id": skill_id, "success": True,
                "text": f"使用 {skill['name']}！但没有任何效果。"}

    elif skill_type == "buff":
        buff_names = []
        buff_name_map = {
            "evasion_up": "闪避提升", "attack_up": "攻击提升", "defense_up": "防御提升",
            "speed_up": "速度提升", "damage_reduction": "伤害减免",
            "shield": "护盾", "regen": "再生", "reflect": "反伤", "lifesteal": "吸血",
        }
        for eff in effects:
            se = StatusEffect(eff["type"], eff["duration"], eff.get("value", 0),
                              source=f"skill:{skill_id}")
            session.player_effects = _add_effect(session.player_effects, se)
            if eff["type"] in STAT_BUFF_MAP:
                _apply_buff(session, se)
            buff_names.append(buff_name_map.get(eff["type"], eff["type"]))
        return {"type": "skill", "skill_id": skill_id, "success": True,
                "text": f"使用 {skill['name']}！获得了{'+'.join(buff_names)}效果。"}

    return {"type": "skill", "success": False, "text": "技能类型未实现。"}


# --- Session management ---

_combat_sessions: dict[str, CombatSession] = {}


def create_combat_session(monster_id: str, monster_config: dict,
                          player_snapshot: dict) -> CombatSession:
    cleanup_expired_sessions()
    session_id = str(uuid.uuid4())[:8]
    session = CombatSession(session_id, monster_id, monster_config, player_snapshot)
    _combat_sessions[session_id] = session
    return session


def get_session(session_id: str) -> CombatSession | None:
    return _combat_sessions.get(session_id)


def remove_session(session_id: str):
    _combat_sessions.pop(session_id, None)


def cleanup_expired_sessions(max_age_seconds: int = 600):
    now = time.time()
    expired = [sid for sid, s in _combat_sessions.items()
               if now - s.created_at > max_age_seconds]
    for sid in expired:
        del _combat_sessions[sid]
