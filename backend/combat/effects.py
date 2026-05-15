"""Status effect system using strategy pattern with BOSS immunity support."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import CombatSession, StatusEffect, MonsterInstance


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
    "defense_down": "防御降低", "attack_down": "攻击降低",
    "evasion_up": "闪避提升", "damage_reduction": "伤害减免",
    "fear": "恐惧",
}

STACKABLE_EFFECTS = {"bleed"}
MAX_STACKS = {"bleed": 3}

MUTEX_PAIRS = [("burn", "freeze")]


class EffectHandler(ABC):
    @abstractmethod
    def tick(self, session: "CombatSession", target_is_player: bool, effect: "StatusEffect",
             monster: "MonsterInstance" = None) -> list[dict]:
        pass

    def on_expire(self, session: "CombatSession", target_is_player: bool, effect: "StatusEffect",
                  monster: "MonsterInstance" = None) -> list[dict]:
        return [{"type": "effect_end", "text": f"{EFFECT_NAMES.get(effect.effect_type, effect.effect_type)}效果消失了。"}]

    def on_add(self, session: "CombatSession", target_is_player: bool, effect: "StatusEffect",
               monster: "MonsterInstance" = None) -> list[dict]:
        return []


class DamageOverTimeHandler(EffectHandler):
    def __init__(self, effect_types: list[str], base_pct: float, stack_multiplier: float = 0.0):
        self.effect_types = effect_types
        self.base_pct = base_pct
        self.stack_multiplier = stack_multiplier

    def tick(self, session, target_is_player, effect, monster=None):
        if target_is_player:
            max_hp = session.player_max_hp
            dmg_pct = self.base_pct + (self.stack_multiplier * effect.stack if effect.stack > 0 else 0)
            dmg = max(1, int(max_hp * dmg_pct))
            session.player_hp = max(0, session.player_hp - dmg)
        else:
            if monster is None:
                return []
            max_hp = monster.max_hp
            dmg_pct = self.base_pct + (self.stack_multiplier * effect.stack if effect.stack > 0 else 0)
            dmg = max(1, int(max_hp * dmg_pct))
            monster.hp = max(0, monster.hp - dmg)

        name = EFFECT_NAMES.get(effect.effect_type, effect.effect_type)
        stack_text = f"（{effect.stack} 层）" if effect.stack > 1 else ""
        return [{"type": "effect", "text": f"{name}{stack_text}！受到 {dmg} 点伤害。"}]


class HealOverTimeHandler(EffectHandler):
    def __init__(self, heal_pct: float):
        self.heal_pct = heal_pct

    def tick(self, session, target_is_player, effect, monster=None):
        if target_is_player:
            max_hp = session.player_max_hp
            heal = max(1, int(max_hp * self.heal_pct))
            session.player_hp = min(session.player_max_hp, session.player_hp + heal)
        else:
            if monster is None:
                return []
            max_hp = monster.max_hp
            heal = max(1, int(max_hp * self.heal_pct))
            monster.hp = min(monster.max_hp, monster.hp + heal)

        name = EFFECT_NAMES.get(effect.effect_type, effect.effect_type)
        return [{"type": "effect", "text": f"{name}！恢复了 {heal} 点生命。"}]


class BlockActionHandler(EffectHandler):
    def __init__(self, message: str):
        self.message = message

    def tick(self, session, target_is_player, effect, monster=None):
        name = EFFECT_NAMES.get(effect.effect_type, effect.effect_type)
        return [{"type": "effect", "text": f"{name}！{self.message}"}]


class StatBuffHandler(EffectHandler):
    def tick(self, session, target_is_player, effect, monster=None):
        if not target_is_player:
            return []

        if effect.effect_type == "attack_up":
            session.player_attack = session.base_player_attack + effect.value
        elif effect.effect_type == "defense_up":
            session.player_defense = session.base_player_defense + effect.value
        elif effect.effect_type == "speed_up":
            session.player_speed = session.base_player_speed + effect.value
        elif effect.effect_type == "defense_down":
            session.player_defense = max(0, session.base_player_defense - effect.value)
        elif effect.effect_type == "attack_down":
            session.player_attack = max(1, session.base_player_attack - effect.value)
        elif effect.effect_type == "speed_down":
            session.player_speed = max(1, int(session.base_player_speed * 0.7))

        return []

    def on_expire(self, session, target_is_player, effect, monster=None):
        if target_is_player:
            _recalculate_player_buffs(session)
        return super().on_expire(session, target_is_player, effect, monster)


class PassiveEffectHandler(EffectHandler):
    def tick(self, session, target_is_player, effect, monster=None):
        return []


EFFECT_HANDLERS: dict[str, EffectHandler] = {
    "poison": DamageOverTimeHandler(["poison"], 0.05),
    "burn": DamageOverTimeHandler(["burn"], 0.03),
    "bleed": DamageOverTimeHandler(["bleed"], 0.04, 0.04),
    "regen": HealOverTimeHandler(0.03),
    "stun": BlockActionHandler("无法行动！"),
    "silence": BlockActionHandler("无法使用技能！"),
    "freeze": BlockActionHandler("无法行动！"),
    "fear": BlockActionHandler("因恐惧无法行动！"),
    "speed_down": StatBuffHandler(),
    "attack_up": StatBuffHandler(),
    "defense_up": StatBuffHandler(),
    "attack_down": StatBuffHandler(),
    "defense_down": StatBuffHandler(),
    "evasion_up": PassiveEffectHandler(),
    "damage_reduction": PassiveEffectHandler(),
    "shield": PassiveEffectHandler(),
    "reflect": PassiveEffectHandler(),
    "lifesteal": PassiveEffectHandler(),
}


def register_effect_handler(effect_type: str, handler: EffectHandler):
    EFFECT_HANDLERS[effect_type] = handler


def find_effect(effects: list["StatusEffect"], effect_type: str) -> "StatusEffect | None":
    for e in effects:
        if e.effect_type == effect_type:
            return e
    return None


def add_effect(effects: list["StatusEffect"], new_eff: "StatusEffect",
               monster_config: dict = None) -> list["StatusEffect"]:
    from .session import is_immune_to_effect

    if monster_config and is_immune_to_effect(monster_config, new_eff.effect_type):
        return effects

    for pair_a, pair_b in MUTEX_PAIRS:
        if new_eff.effect_type == pair_a:
            effects = [e for e in effects if e.effect_type != pair_b]
        elif new_eff.effect_type == pair_b:
            effects = [e for e in effects if e.effect_type != pair_a]

    existing = find_effect(effects, new_eff.effect_type)
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


def _recalculate_player_buffs(session: "CombatSession") -> None:
    session.player_attack = session.base_player_attack
    session.player_defense = session.base_player_defense
    session.player_speed = session.base_player_speed
    for eff in session.player_effects:
        if eff.effect_type in STAT_BUFF_MAP:
            handler = EFFECT_HANDLERS.get(eff.effect_type)
            if handler:
                handler.tick(session, target_is_player=True, effect=eff)


def process_effects(session: "CombatSession", is_player: bool,
                    monster: "MonsterInstance" = None) -> list[dict]:
    if is_player:
        effects = session.player_effects
    else:
        if monster is None:
            return []
        effects = monster.effects

    logs = []
    remaining = []
    expired_buffs = []

    for eff in effects:
        handler = EFFECT_HANDLERS.get(eff.effect_type)
        if handler:
            tick_logs = handler.tick(session, is_player, eff, monster)
            logs.extend(tick_logs)

        eff.duration -= 1
        if eff.duration > 0:
            remaining.append(eff)
        else:
            if eff.effect_type in STAT_BUFF_MAP:
                expired_buffs.append(eff)

            handler = EFFECT_HANDLERS.get(eff.effect_type)
            if handler:
                expire_logs = handler.on_expire(session, is_player, eff, monster)
                logs.extend(expire_logs)

    if is_player:
        session.player_effects = remaining
        if expired_buffs:
            _recalculate_player_buffs(session)
    else:
        if monster is not None:
            monster.effects = remaining

    return logs


def has_effect(effects: list["StatusEffect"], effect_type: str) -> bool:
    return any(e.effect_type == effect_type for e in effects)


def is_blocked_by_effect(effects: list["StatusEffect"]) -> bool:
    return has_effect(effects, "stun") or has_effect(effects, "freeze") or has_effect(effects, "fear")


def is_silenced(effects: list["StatusEffect"]) -> bool:
    return has_effect(effects, "silence")
