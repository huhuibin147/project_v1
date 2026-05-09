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
    def __init__(self, effect_type: str, duration: int, value: int = 0):
        self.effect_type = effect_type
        self.duration = duration
        self.value = value

    def to_dict(self):
        return {"type": self.effect_type, "duration": self.duration, "value": self.value}


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
        self.player_skills = player_snapshot.get("skills", [])
        self.player_defending = False
        self.player_effects: list[StatusEffect] = []
        self.skill_cooldowns: dict[str, int] = {}

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
    for eff in effects:
        if eff.effect_type == "poison":
            dmg = max(1, int(max_hp * 0.05))
            hp = max(0, hp - dmg)
            logs.append({"type": "effect", "text": f"中毒！受到 {dmg} 点伤害。"})
        elif eff.effect_type == "burn":
            dmg = max(1, int(max_hp * 0.03))
            hp = max(0, hp - dmg)
            logs.append({"type": "effect", "text": f"灼烧！受到 {dmg} 点伤害。"})
        elif eff.effect_type == "stun":
            logs.append({"type": "effect", "text": "被眩晕，无法行动！"})

        eff.duration -= 1
        if eff.duration > 0:
            remaining.append(eff)
        else:
            logs.append({"type": "effect_end", "text": f"{eff.effect_type}效果消失了。"})

    if is_player:
        session.player_hp = hp
        session.player_effects = remaining
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
        session.player_effects.append(
            StatusEffect(f"buff_{effect['stat']}", effect["duration"], effect["value"])
        )
        stat_names = {"attack": "攻击力", "speed": "速度", "defense": "防御力"}
        stat_name = stat_names.get(effect["stat"], effect["stat"])
        return {"type": "use_item", "success": True, "item_id": item_id,
                "text": f"使用了{item_name}，{stat_name}提升 {effect['value']} 持续 {effect['duration']} 回合！"}

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


def _execute_monster_action(session: CombatSession, action: str) -> dict:
    monster_name = session.monster_config["name"]

    if action == "attack":
        result = calc_damage(
            session.monster_config["stats"]["attack"],
            session.player_defense,
            session.monster_config["stats"]["speed"],
            session.player_speed,
            session.player_defending
        )
        session.player_hp = max(0, session.player_hp - result["damage"])
        entry = {"type": "monster_attack", "damage": result["damage"],
                 "crit": result["is_crit"], "defended": result["defended"]}
        if result["is_crit"]:
            entry["text"] = f"暴击！{monster_name}对你造成 {result['damage']} 点伤害！"
        else:
            entry["text"] = f"{monster_name}攻击了你，造成 {result['damage']} 点伤害。"
        return entry

    elif action == "defend":
        session.monster_defending = True
        return {"type": "monster_defend", "text": f"{monster_name}摆出了防御姿态。"}

    elif action == "special":
        special = session.monster_config.get("ai", {}).get("special")
        if special and special.get("type") == "apply_effect":
            if random.random() < special.get("chance", 0.3):
                effect_type = special["effect"]
                duration = special.get("duration", 3)
                session.player_effects.append(StatusEffect(effect_type, duration))
                return {"type": "monster_special", "text": special.get("message", f"{monster_name}使用了特殊技能！")}
            else:
                result = calc_damage(
                    session.monster_config["stats"]["attack"],
                    session.player_defense,
                    session.monster_config["stats"]["speed"],
                    session.player_speed,
                    session.player_defending
                )
                session.player_hp = max(0, session.player_hp - result["damage"])
                return {"type": "monster_attack", "damage": result["damage"],
                        "crit": result["is_crit"], "defended": result["defended"],
                        "text": f"{monster_name}攻击了你，造成 {result['damage']} 点伤害。"}
        else:
            return _execute_monster_action(session, "attack")

    return {"type": "monster_idle", "text": f"{monster_name}在观望。"}


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

def resolve_turn(session: CombatSession, action: str,
                 action_data: dict = None) -> dict:
    session.turn_count += 1
    log_entries = []

    # Process player effects at start of turn
    player_effects_log = _process_effects(session, is_player=True)
    log_entries.extend(player_effects_log)

    if session.player_hp <= 0:
        session.phase = CombatPhase.DEFEAT
        log_entries.append({"type": "defeat", "text": "你倒下了..."})
        return _build_state(session, log_entries)

    # Player action
    if action == "attack":
        result = calc_damage(
            session.player_attack,
            session.monster_config["stats"]["defense"],
            session.player_speed,
            session.monster_config["stats"]["speed"],
            session.monster_defending
        )
        session.monster_hp = max(0, session.monster_hp - result["damage"])
        monster_name = session.monster_config["name"]
        entry = {"type": "player_attack", "damage": result["damage"],
                 "crit": result["is_crit"], "defended": result["defended"]}
        if result["is_crit"]:
            entry["text"] = f"暴击！你对{monster_name}造成 {result['damage']} 点伤害！"
        else:
            entry["text"] = f"你对{monster_name}造成 {result['damage']} 点伤害。"
        log_entries.append(entry)

    elif action == "defend":
        session.player_defending = True
        log_entries.append({"type": "player_defend", "text": "你举起防御姿态，减少50%伤害。"})

    elif action == "use_item":
        item_id = (action_data or {}).get("item_id")
        item_result = _use_item_in_combat(session, item_id)
        log_entries.append(item_result)
        if not item_result.get("success"):
            # 物品使用失败，不继续回合
            return _build_state(session, log_entries)

    elif action == "flee":
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
        skill_id = (action_data or {}).get("skill_id")
        skill_result = _execute_skill(session, skill_id)
        log_entries.append(skill_result)
        if not skill_result.get("success"):
            # 技能使用失败，不继续回合
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
    monster_log = _execute_monster_action(session, monster_action)
    log_entries.append(monster_log)

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

    if skill_type == "damage":
        damage_type = skill.get("damage_type", "physical")
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
                 "text": f"使用 {skill['name']}！对{monster_name}造成 {result['damage']} 点{damage_type}伤害。"}
        if defense_ignore > 0:
            entry["text"] += f" (无视 {defense_ignore}% 防御)"
        # Apply effects
        for eff in effects:
            if eff.get("type") in ("defense_ignore",):
                continue
            if random.random() < eff.get("chance", 1.0):
                session.monster_effects.append(StatusEffect(eff["type"], eff["duration"]))
                entry["text"] += f" [{eff['type']}]"
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
        for eff in effects:
            session.player_effects.append(StatusEffect(eff["type"], eff["duration"], eff.get("value", 0)))
        return {"type": "skill", "skill_id": skill_id, "success": True,
                "text": f"使用 {skill['name']}！获得了增益效果。"}

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
