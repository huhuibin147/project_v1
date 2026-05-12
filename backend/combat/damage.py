"""Damage calculation module with elemental attribute system."""

import random
from enum import Enum


class Element(str, Enum):
    NONE = "none"
    FIRE = "fire"
    WATER = "water"
    GRASS = "grass"


ELEMENT_ADVANTAGE = {
    Element.FIRE: Element.GRASS,
    Element.WATER: Element.FIRE,
    Element.GRASS: Element.WATER,
}


def calc_element_multiplier(attacker_element: str, defender_element: str) -> float:
    try:
        atk_elem = Element(attacker_element)
    except ValueError:
        atk_elem = Element.NONE

    try:
        def_elem = Element(defender_element)
    except ValueError:
        def_elem = Element.NONE

    if atk_elem == Element.NONE or def_elem == Element.NONE:
        return 1.0

    if ELEMENT_ADVANTAGE.get(atk_elem) == def_elem:
        return 1.5

    if ELEMENT_ADVANTAGE.get(def_elem) == atk_elem:
        return 0.67

    return 1.0


def calc_crit_chance(attacker_speed: int, defender_speed: int) -> tuple[float, bool]:
    speed_diff = attacker_speed - defender_speed
    crit_chance = min(0.25, max(0.05, 0.05 + speed_diff * 0.005))
    is_crit = random.random() < crit_chance
    return crit_chance, is_crit


def calc_base_damage(attacker_attack: int, defender_defense: int) -> float:
    return attacker_attack * (100.0 / (100.0 + defender_defense))


def calc_damage(
    attacker_attack: int,
    defender_defense: int,
    attacker_speed: int,
    defender_speed: int,
    is_defending: bool,
    attacker_element: str = "none",
    defender_element: str = "none",
) -> dict:
    base = calc_base_damage(attacker_attack, defender_defense)

    variance = random.uniform(0.9, 1.1)
    damage = base * variance

    crit_chance, is_crit = calc_crit_chance(attacker_speed, defender_speed)
    if is_crit:
        damage *= 1.5

    element_multiplier = calc_element_multiplier(attacker_element, defender_element)
    damage *= element_multiplier

    if is_defending:
        damage *= 0.5

    damage = max(1, int(damage))

    return {
        "damage": damage,
        "is_crit": is_crit,
        "defended": is_defending,
        "crit_chance": crit_chance,
        "element_multiplier": element_multiplier,
    }


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


def apply_shield(shield_value: int, damage: int) -> tuple[int, int]:
    absorbed = min(shield_value, damage)
    remaining_damage = damage - absorbed
    remaining_shield = shield_value - absorbed
    return remaining_damage, absorbed


def apply_reflect(reflect_value: int, damage: int, is_percent: bool = True) -> int:
    if is_percent:
        reflect_pct = reflect_value / 100.0 if reflect_value > 1 else reflect_value
    else:
        reflect_pct = reflect_value
    return max(1, int(damage * reflect_pct))


def apply_lifesteal(lifesteal_value: int, damage: int, is_percent: bool = True) -> int:
    if is_percent:
        heal_pct = lifesteal_value / 100.0 if lifesteal_value > 1 else lifesteal_value
    else:
        heal_pct = lifesteal_value
    return max(1, int(damage * heal_pct))
