"""Combat session management module."""

import time
import uuid
from enum import Enum


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
        self.equipment_affixes: list[dict] = player_snapshot.get("equipment_affixes", [])

        self.phase = CombatPhase.PLAYER_TURN
        self.turn_count = 0
        self.log: list[dict] = []
        self.created_at = time.time()
        self.drops: list[dict] = []
        self.exp_reward = 0
        self.gold_reward = 0


_combat_sessions: dict[str, CombatSession] = {}
SESSION_TIMEOUT = 600


def create_combat_session(monster_id: str, monster_config: dict,
                          player_snapshot: dict) -> CombatSession:
    session_id = str(uuid.uuid4())
    session = CombatSession(session_id, monster_id, monster_config, player_snapshot)
    _combat_sessions[session_id] = session
    return session


def get_session(session_id: str) -> CombatSession | None:
    return _combat_sessions.get(session_id)


def remove_session(session_id: str) -> None:
    _combat_sessions.pop(session_id, None)


def cleanup_expired_sessions() -> None:
    now = time.time()
    expired = [sid for sid, s in _combat_sessions.items()
               if now - s.created_at > SESSION_TIMEOUT]
    for sid in expired:
        del _combat_sessions[sid]
