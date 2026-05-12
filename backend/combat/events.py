"""Event-driven system for affix and talent triggers."""

import random
from enum import Enum
from typing import TYPE_CHECKING, Callable, Any

if TYPE_CHECKING:
    from .session import CombatSession, StatusEffect
    from .effects import EFFECT_NAMES, add_effect


class CombatEvent(str, Enum):
    ON_COMBAT_START = "on_combat_start"
    ON_TURN_START = "on_turn_start"
    ON_ATTACK = "on_attack"
    ON_HIT = "on_hit"
    ON_KILL = "on_kill"
    ON_CONDITIONAL = "on_conditional"
    ON_PASSIVE_REGEN = "on_passive_regen"


class EventDispatcher:
    def __init__(self):
        self._listeners: dict[CombatEvent, list[Callable]] = {}

    def register(self, event: CombatEvent, handler: Callable):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(handler)

    def dispatch(self, event: CombatEvent, **kwargs) -> list[dict]:
        logs = []
        for handler in self._listeners.get(event, []):
            result = handler(**kwargs)
            if result:
                if isinstance(result, list):
                    logs.extend(result)
                elif isinstance(result, dict):
                    logs.append(result)
        return logs


_global_dispatcher = EventDispatcher()


def get_dispatcher() -> EventDispatcher:
    return _global_dispatcher


def register_talent_handlers(session: "CombatSession"):
    from .session import StatusEffect
    from .effects import EFFECT_NAMES, add_effect, _recalculate_player_buffs

    passives = session.talent_passives
    if not passives:
        return

    def on_combat_start_handler(**kwargs):
        logs = []
        for eff in passives.get("on_combat_start", []):
            if eff.get("action") == "apply_effect_to_monster":
                effect_type = eff.get("effect")
                duration = eff.get("duration", 1)
                chance = eff.get("chance", 1.0)
                if random.random() < chance:
                    new_eff = StatusEffect(effect_type, duration, source="talent")
                    session.monster_effects = add_effect(session.monster_effects, new_eff)
                    eff_name = EFFECT_NAMES.get(effect_type, effect_type)
                    logs.append({"type": "talent", "text": f"天赋触发！怪物被{eff_name}！"})
        return logs

    def on_attack_handler(**kwargs):
        logs = []
        damage = kwargs.get("damage", 0)
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
                    session.monster_effects = add_effect(session.monster_effects, new_eff)
                    logs.append({"type": "talent", "text": "天赋触发！怪物开始流血！"})
            elif eff.get("action") == "chance_stun":
                chance = eff.get("chance", 0.15)
                if random.random() < chance:
                    new_eff = StatusEffect("stun", eff.get("duration", 1),
                                           source="talent")
                    session.monster_effects = add_effect(session.monster_effects, new_eff)
                    logs.append({"type": "talent", "text": "天赋触发！怪物被眩晕！"})
        return logs

    def on_kill_handler(**kwargs):
        logs = []
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
                session.player_effects = add_effect(session.player_effects, new_eff)
                _recalculate_player_buffs(session)
                logs.append({"type": "talent", "text": f"天赋触发！攻击力提升 {boost}！"})
        return logs

    def on_conditional_handler(**kwargs):
        logs = []
        for eff in passives.get("conditional", []):
            condition = eff.get("condition")
            if condition == "hp_below" and session.player_hp < session.player_max_hp * eff.get("threshold", 0.3):
                pct = eff.get("value", 0) / 100.0
                boost = max(1, int(session.base_player_attack * pct))
                new_eff = StatusEffect("attack_up", 1, value=boost, source="talent")
                session.player_effects = add_effect(session.player_effects, new_eff)
                _recalculate_player_buffs(session)
                logs.append({"type": "talent", "text": f"天赋触发！绝境之力，攻击力 +{boost}！"})
            elif condition == "mp_above" and session.player_mp > session.player_max_mp * eff.get("threshold", 0.5):
                pct = eff.get("value", 0) / 100.0
                boost = max(1, int(session.base_player_attack * pct))
                new_eff = StatusEffect("attack_up", 1, value=boost, source="talent")
                session.player_effects = add_effect(session.player_effects, new_eff)
                _recalculate_player_buffs(session)
                logs.append({"type": "talent", "text": f"天赋触发！魔力涌动，攻击力 +{boost}！"})
        return logs

    get_dispatcher().register(CombatEvent.ON_COMBAT_START, on_combat_start_handler)
    get_dispatcher().register(CombatEvent.ON_ATTACK, on_attack_handler)
    get_dispatcher().register(CombatEvent.ON_KILL, on_kill_handler)
    get_dispatcher().register(CombatEvent.ON_CONDITIONAL, on_conditional_handler)


def register_affix_handlers(session: "CombatSession"):
    from .session import StatusEffect
    from .effects import EFFECT_NAMES, add_effect, _recalculate_player_buffs

    def on_attack_handler(**kwargs):
        logs = []
        damage = kwargs.get("damage", 0)
        for affix in session.equipment_affixes:
            if affix.get("category") != "on_attack":
                continue
            for eff in affix.get("effects", []):
                if eff.get("type") == "on_hit":
                    trigger_chance = eff.get("trigger_chance", 0.1)
                    if random.random() < trigger_chance:
                        apply_effect = eff.get("apply_effect")
                        duration = eff.get("effect_duration", 3)
                        if apply_effect == "thunder_damage":
                            extra_dmg = max(1, int(damage * 0.5))
                            session.monster_hp = max(0, session.monster_hp - extra_dmg)
                            logs.append({"type": "affix", "text": f"词条【{affix['name']}】触发！雷击造成 {extra_dmg} 点额外伤害！"})
                        elif apply_effect in ("burn", "freeze", "stun", "poison", "bleed", "silence", "speed_down"):
                            new_eff = StatusEffect(apply_effect, duration, source=f"affix:{affix['affix_id']}")
                            session.monster_effects = add_effect(session.monster_effects, new_eff)
                            eff_name = EFFECT_NAMES.get(apply_effect, apply_effect)
                            logs.append({"type": "affix", "text": f"词条【{affix['name']}】触发！怪物被{eff_name}！"})
                elif eff.get("type") == "lifesteal":
                    trigger_chance = eff.get("trigger_chance", 0.1)
                    if random.random() < trigger_chance:
                        ls_pct = eff.get("value", 0.1)
                        heal = max(1, int(damage * ls_pct))
                        session.player_hp = min(session.player_max_hp, session.player_hp + heal)
                        logs.append({"type": "affix", "text": f"词条【{affix['name']}】触发！吸血恢复 {heal} 点生命。"})
        return logs

    def on_hit_handler(**kwargs):
        logs = []
        damage = kwargs.get("damage", 0)
        reduced_damage = damage
        for affix in session.equipment_affixes:
            if affix.get("category") != "on_hit":
                continue
            for eff in affix.get("effects", []):
                if eff.get("type") == "reflect":
                    trigger_chance = eff.get("trigger_chance", 1.0)
                    if random.random() < trigger_chance:
                        reflect_pct = eff.get("value", 0.15)
                        reflect_dmg = max(1, int(damage * reflect_pct))
                        session.monster_hp = max(0, session.monster_hp - reflect_dmg)
                        logs.append({"type": "affix", "text": f"词条【{affix['name']}】触发！反弹 {reflect_dmg} 点伤害！"})
                elif eff.get("type") == "damage_reduce":
                    trigger_chance = eff.get("trigger_chance", 0.1)
                    if random.random() < trigger_chance:
                        reduce_pct = eff.get("value", 0.5)
                        reduction = int(reduced_damage * reduce_pct)
                        reduced_damage = max(1, reduced_damage - reduction)
                        logs.append({"type": "affix", "text": f"词条【{affix['name']}】触发！减伤 {reduction} 点！"})
        return logs, reduced_damage

    def on_kill_handler(**kwargs):
        logs = []
        gold_mult = 1.0
        exp_mult = 1.0
        for affix in session.equipment_affixes:
            if affix.get("category") != "on_kill":
                continue
            for eff in affix.get("effects", []):
                if eff.get("type") == "gold_bonus":
                    gold_mult += eff.get("value", 0.15)
                    logs.append({"type": "affix", "text": f"词条【{affix['name']}】触发！金币获取 +{int(eff.get('value', 0.15) * 100)}%"})
                elif eff.get("type") == "exp_bonus":
                    exp_mult += eff.get("value", 0.10)
                    logs.append({"type": "affix", "text": f"词条【{affix['name']}】触发！经验获取 +{int(eff.get('value', 0.10) * 100)}%"})
        return logs, gold_mult, exp_mult

    def on_conditional_handler(**kwargs):
        logs = []
        for affix in session.equipment_affixes:
            if affix.get("category") != "conditional":
                continue
            for eff in affix.get("effects", []):
                if eff.get("type") == "conditional_stat":
                    condition = eff.get("condition")
                    if condition == "hp_below_30" and session.player_hp < session.player_max_hp * 0.3:
                        stat = eff.get("stat", "attack")
                        pct = eff.get("value", 0.2)
                        if stat == "attack":
                            boost = max(1, int(session.base_player_attack * pct))
                            new_eff = StatusEffect("attack_up", 1, value=boost, source=f"affix:{affix['affix_id']}")
                            session.player_effects = add_effect(session.player_effects, new_eff)
                            _recalculate_player_buffs(session)
                            logs.append({"type": "affix", "text": f"词条【{affix['name']}】触发！攻击力 +{boost}！"})
        return logs

    def on_passive_regen_handler(**kwargs):
        logs = []
        for affix in session.equipment_affixes:
            if affix.get("category") != "passive":
                continue
            for eff in affix.get("effects", []):
                if eff.get("type") == "stat_flat" and eff.get("stat") == "regen_percent":
                    pct = eff.get("value", 0.03)
                    heal = max(1, int(session.player_max_hp * pct))
                    session.player_hp = min(session.player_max_hp, session.player_hp + heal)
                    logs.append({"type": "affix", "text": f"词条【{affix['name']}】再生恢复 {heal} 点生命。"})
        return logs

    get_dispatcher().register(CombatEvent.ON_ATTACK, on_attack_handler)
    get_dispatcher().register(CombatEvent.ON_HIT, on_hit_handler)
    get_dispatcher().register(CombatEvent.ON_KILL, on_kill_handler)
    get_dispatcher().register(CombatEvent.ON_CONDITIONAL, on_conditional_handler)
    get_dispatcher().register(CombatEvent.ON_PASSIVE_REGEN, on_passive_regen_handler)


def clear_dispatcher():
    global _global_dispatcher
    _global_dispatcher = EventDispatcher()
