"""Combat engine compatibility layer - re-exports all original interfaces."""

from .session import CombatSession, CombatPhase, StatusEffect, MonsterInstance, create_combat_session, get_session, remove_session, cleanup_expired_sessions, is_immune_to_effect
from .damage import calc_damage, calc_flee_chance, calc_drops
from .effects import process_effects, add_effect, find_effect, has_effect, is_blocked_by_effect, is_silenced
from .monster_ai import decide_action, execute_action, check_boss_phase
from .skills import execute_skill
from .turn import resolve_turn

__all__ = [
    "CombatSession",
    "CombatPhase",
    "StatusEffect",
    "MonsterInstance",
    "create_combat_session",
    "get_session",
    "remove_session",
    "cleanup_expired_sessions",
    "is_immune_to_effect",
    "calc_damage",
    "calc_flee_chance",
    "calc_drops",
    "process_effects",
    "add_effect",
    "find_effect",
    "has_effect",
    "is_blocked_by_effect",
    "is_silenced",
    "decide_action",
    "execute_action",
    "check_boss_phase",
    "execute_skill",
    "resolve_turn",
]
