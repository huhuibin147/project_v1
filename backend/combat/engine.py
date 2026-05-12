"""Combat engine compatibility layer - re-exports all original interfaces."""

from .session import CombatSession, CombatPhase, StatusEffect, create_combat_session, get_session, remove_session, cleanup_expired_sessions
from .damage import calc_damage, calc_flee_chance, calc_drops
from .effects import process_effects, add_effect, find_effect, has_effect, is_blocked_by_effect, is_silenced
from .monster_ai import decide_action, execute_action
from .skills import execute_skill
from .turn import resolve_turn

__all__ = [
    "CombatSession",
    "CombatPhase",
    "StatusEffect",
    "create_combat_session",
    "get_session",
    "remove_session",
    "cleanup_expired_sessions",
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
    "execute_skill",
    "resolve_turn",
]
