"""Combat session management module with multi-enemy support."""

import copy
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


BOSS_IMMUNITY = {
    "boss": {"stun", "freeze"},
    "elite_boss": {"stun", "freeze", "poison"},
}


def is_immune_to_effect(monster_config: dict, effect_type: str) -> bool:
    monster_type = monster_config.get("type", "normal")
    if monster_type != "boss":
        return False
    tags = set(monster_config.get("tags", []))
    immune_set = set(BOSS_IMMUNITY.get("boss", set()))
    if "elite" in tags:
        immune_set = immune_set | BOSS_IMMUNITY.get("elite_boss", set())
    return effect_type in immune_set


class MonsterInstance:
    def __init__(self, index: int, monster_id: str, config: dict):
        self.index = index
        self.monster_id = monster_id
        self.config = copy.deepcopy(config)
        self.hp = config["stats"]["hp"]
        self.max_hp = config["stats"]["hp"]
        self.base_attack = config["stats"]["attack"]
        self.base_defense = config["stats"]["defense"]
        self.base_speed = config["stats"]["speed"]
        self.defending = False
        self.effects: list[StatusEffect] = []
        self.current_phase: int = 0
        self.phase_changed: bool = False

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def is_boss(self) -> bool:
        return self.config.get("type") == "boss"

    @property
    def hp_ratio(self) -> float:
        return self.hp / self.max_hp if self.max_hp > 0 else 0.0

    @property
    def attack(self) -> int:
        return self.config["stats"]["attack"]

    @property
    def defense(self) -> int:
        return self.config["stats"]["defense"]

    @property
    def speed(self) -> int:
        return self.config["stats"]["speed"]

    def get_phase_name(self) -> str:
        phases = self.config.get("phases", [])
        if phases and 0 <= self.current_phase < len(phases):
            return phases[self.current_phase]["name"]
        return ""

    def get_current_special(self) -> dict | None:
        if self.is_boss:
            phases = self.config.get("phases", [])
            if phases and 0 <= self.current_phase < len(phases):
                phase_special = phases[self.current_phase].get("special")
                if phase_special is not None:
                    return phase_special
        return self.config.get("ai", {}).get("special")

    def to_dict(self, next_action: str = "") -> dict:
        return {
            "index": self.index,
            "monster_id": self.monster_id,
            "name": self.config["name"],
            "hp": self.hp,
            "max_hp": self.max_hp,
            "alive": self.alive,
            "defending": self.defending,
            "effects": [e.to_dict() for e in self.effects],
            "is_boss": self.is_boss,
            "current_phase": self.current_phase,
            "phase_name": self.get_phase_name(),
            "sprite_color": self.config.get("sprite_color", "#888"),
            "sprite_accent": self.config.get("sprite_accent", "#555"),
            "level": self.config.get("level", 1),
            "monster_type": self.config.get("type", "normal"),
            "element": self.config.get("element", "none"),
            "next_action": next_action,
        }


class CombatSession:
    def __init__(self, session_id: str, monster_configs: list[dict],
                 player_snapshot: dict):
        self.session_id = session_id

        self.monsters: list[MonsterInstance] = []
        for idx, mc in enumerate(monster_configs):
            mid = mc.get("id", f"monster_{idx}")
            self.monsters.append(MonsterInstance(idx, mid, mc))

        self.target_index: int = 0

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
        self.player_element: str = player_snapshot.get("element", "none")

        self.phase = CombatPhase.PLAYER_TURN
        self.turn_count = 0
        self.log: list[dict] = []
        self.created_at = time.time()
        self.drops: list[dict] = []
        self.exp_reward = 0
        self.gold_reward = 0

    @property
    def monster_id(self) -> str:
        if self.monsters:
            return self.monsters[0].monster_id
        return ""

    @property
    def monster_config(self) -> dict:
        if self.monsters:
            return self.monsters[0].config
        return {}

    @property
    def monster_hp(self) -> int:
        if self.monsters:
            return self.monsters[0].hp
        return 0

    @property
    def monster_max_hp(self) -> int:
        if self.monsters[0:]:
            return self.monsters[0].max_hp
        return 0

    @property
    def monster_defending(self) -> bool:
        if self.monsters:
            return self.monsters[0].defending
        return False

    @monster_defending.setter
    def monster_defending(self, value: bool):
        if self.monsters:
            self.monsters[0].defending = value

    @property
    def monster_effects(self) -> list[StatusEffect]:
        if self.monsters:
            return self.monsters[0].effects
        return []

    @monster_effects.setter
    def monster_effects(self, value: list[StatusEffect]):
        if self.monsters:
            self.monsters[0].effects = value

    def get_target(self) -> MonsterInstance | None:
        if 0 <= self.target_index < len(self.monsters):
            m = self.monsters[self.target_index]
            if m.alive:
                return m
        for m in self.monsters:
            if m.alive:
                self.target_index = m.index
                return m
        return None

    def alive_monsters(self) -> list[MonsterInstance]:
        return [m for m in self.monsters if m.alive]

    def all_monsters_dead(self) -> bool:
        return all(not m.alive for m in self.monsters)


_combat_sessions: dict[str, CombatSession] = {}
SESSION_TIMEOUT = 600


def create_combat_session(monster_configs: list[dict],
                          player_snapshot: dict) -> CombatSession:
    session_id = str(uuid.uuid4())
    session = CombatSession(session_id, monster_configs, player_snapshot)
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
