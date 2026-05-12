import json
import random
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"
AFFIXES_FILE = CONFIG_DIR / "affixes.json"
ITEMS_FILE = CONFIG_DIR / "items.json"

RARITY_AFFIX_COUNT = {
    "common": 0,
    "uncommon": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
}

RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary"]

REROLL_COSTS = {
    "common": 50,
    "uncommon": 100,
    "rare": 200,
    "epic": 500,
    "legendary": 1000,
}


def load_affixes_config() -> dict:
    with open(AFFIXES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


AFFIXES_DB = load_affixes_config()


def reload_affixes():
    global AFFIXES_DB
    AFFIXES_DB = load_affixes_config()


def get_affix(affix_id: str) -> dict | None:
    return AFFIXES_DB.get(affix_id)


def generate_affixes(equip_slot: str, rarity: str, player_level: int, count: int = None) -> list[dict]:
    if count is None:
        count = RARITY_AFFIX_COUNT.get(rarity, 0)
    if count == 0:
        return []

    pool = []
    for affix_id, affix in AFFIXES_DB.items():
        if equip_slot not in affix.get("compatible_slots", []):
            continue
        lr = affix.get("level_range", {})
        if lr.get("min", 1) <= player_level <= lr.get("max", 99):
            weight = _get_dynamic_weight(affix, player_level)
            affix_copy = dict(affix)
            affix_copy["_dynamic_weight"] = weight
            pool.append(affix_copy)

    if not pool:
        return []

    selected = _weighted_sample_without_replacement(pool, count)
    return [_format_affix(a) for a in selected]


def _get_dynamic_weight(affix: dict, player_level: int) -> float:
    base_weight = affix.get("weight", 1)
    multipliers = affix.get("level_weight_multipliers", {})

    for range_str, multiplier in multipliers.items():
        if _level_in_range(player_level, range_str):
            return base_weight * multiplier

    return base_weight


def _level_in_range(level: int, range_str: str) -> bool:
    if "+" in range_str:
        min_level = int(range_str.replace("+", ""))
        return level >= min_level
    if "-" in range_str:
        parts = range_str.split("-")
        min_level = int(parts[0])
        max_level = int(parts[1])
        return min_level <= level <= max_level
    return False


def _weighted_sample_without_replacement(items: list[dict], count: int) -> list[dict]:
    count = min(count, len(items))
    result = []
    remaining = list(items)
    for _ in range(count):
        weights = [item.get("_dynamic_weight", item.get("weight", 1)) for item in remaining]
        total = sum(weights)
        if total <= 0:
            break
        r = random.uniform(0, total)
        cumulative = 0
        chosen_idx = 0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                chosen_idx = i
                break
        result.append(remaining.pop(chosen_idx))
    return result


def _format_affix(affix: dict) -> dict:
    return {
        "affix_id": affix["affix_id"],
        "name": affix["name"],
        "category": affix.get("category", "passive"),
        "description": affix.get("description", ""),
        "effects": affix.get("effects", []),
    }


def calc_affix_stat_bonus(affixes: list[dict], base_stats: dict) -> dict:
    bonus = {"attack": 0, "defense": 0, "speed": 0, "max_hp": 0, "max_mp": 0}
    for affix in affixes:
        for eff in affix.get("effects", []):
            if eff.get("type") == "stat_percent":
                stat = eff.get("stat")
                if stat in bonus and stat in base_stats:
                    bonus[stat] += int(base_stats[stat] * eff.get("value", 0))
            elif eff.get("type") == "stat_flat":
                stat = eff.get("stat")
                if stat in bonus:
                    bonus[stat] += eff.get("value", 0)
    return bonus


def get_item_affixes(item_id: str, inventory_items: list) -> list[dict]:
    for inv_item in inventory_items:
        if inv_item.get("item_id") == item_id:
            instance = inv_item.get("instance_affixes")
            if instance is not None:
                return instance
    with open(ITEMS_FILE, "r", encoding="utf-8") as f:
        items_db = json.load(f)
    item_info = items_db.get(item_id, {})
    return item_info.get("affixes", [])


def get_item_rarity(item_id: str, inventory_items: list) -> str:
    for inv_item in inventory_items:
        if inv_item.get("item_id") == item_id:
            instance = inv_item.get("instance_rarity")
            if instance:
                return instance
    with open(ITEMS_FILE, "r", encoding="utf-8") as f:
        items_db = json.load(f)
    item_info = items_db.get(item_id, {})
    return item_info.get("rarity", "common")


def get_all_equipment_affixes(equipment: dict, inventory_items: list) -> list[dict]:
    all_affixes = []
    for slot_name, item_id in equipment.items():
        if item_id:
            affixes = get_item_affixes(item_id, inventory_items)
            for affix in affixes:
                affix_copy = dict(affix)
                affix_copy["_slot"] = slot_name
                all_affixes.append(affix_copy)
    return all_affixes


def get_affix_categories() -> list[dict]:
    return [
        {"id": "passive", "name": "被动加成"},
        {"id": "on_attack", "name": "攻击触发"},
        {"id": "on_hit", "name": "受击触发"},
        {"id": "on_kill", "name": "击杀触发"},
        {"id": "conditional", "name": "条件触发"},
    ]


def reroll_single_affix(item_instance: dict, player_level: int) -> dict:
    current_affixes = item_instance.get("instance_affixes", [])
    if not current_affixes:
        return {"success": False, "message": "该装备没有可洗练的词条"}

    rarity = item_instance.get("instance_rarity", "common")
    cost = REROLL_COSTS.get(rarity, 100)

    replace_idx = random.randint(0, len(current_affixes) - 1)
    old_affix = current_affixes[replace_idx]

    equip_slot = item_instance.get("equip_slot", "")
    new_affixes = generate_affixes(equip_slot, rarity, player_level, count=1)

    if not new_affixes:
        return {"success": False, "message": "无法生成新词条"}

    current_affixes[replace_idx] = new_affixes[0]

    return {
        "success": True,
        "message": f"洗练成功！{old_affix['name']} → {new_affixes[0]['name']}",
        "old_affix": old_affix,
        "new_affix": new_affixes[0],
        "cost": cost,
        "affixes": current_affixes,
    }
