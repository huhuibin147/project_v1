import json
import random
from pathlib import Path
from dataclasses import dataclass

CONFIG_DIR = Path(__file__).parent.parent / "config"
RECIPES_FILE = CONFIG_DIR / "forge_recipes.json"
ITEMS_FILE = CONFIG_DIR / "items.json"

RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary"]


def load_recipes_config() -> dict:
    with open(RECIPES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


RECIPES_DB = load_recipes_config()


def reload_recipes():
    global RECIPES_DB
    RECIPES_DB = load_recipes_config()


def get_recipe(recipe_id: str) -> dict | None:
    return RECIPES_DB.get(recipe_id)


def get_all_recipes() -> list[dict]:
    return list(RECIPES_DB.values())


def get_recipes_by_category(category: str) -> list[dict]:
    return [r for r in RECIPES_DB.values() if r.get("category") == category]


def check_can_craft(recipe: dict, player_level: int, player_gold: int,
                    inventory_items: list) -> dict:
    missing_materials = []
    has_all_materials = True
    materials_info = []

    for mat in recipe.get("materials", []):
        mat_id = mat["item_id"]
        required = mat["quantity"]
        owned = 0
        for inv_item in inventory_items:
            if inv_item.get("item_id") == mat_id:
                owned = inv_item.get("quantity", 0)
                break

        with open(ITEMS_FILE, "r", encoding="utf-8") as f:
            items_db = json.load(f)
        mat_name = items_db.get(mat_id, {}).get("name", mat_id)

        materials_info.append({
            "item_id": mat_id,
            "name": mat_name,
            "quantity": required,
            "owned": owned,
        })

        if owned < required:
            has_all_materials = False
            missing_materials.append({
                "item_id": mat_id,
                "name": mat_name,
                "needed": required - owned,
            })

    level_ok = player_level >= recipe.get("level_requirement", 1)
    gold_ok = player_gold >= recipe.get("gold_cost", 0)
    missing_gold = max(0, recipe.get("gold_cost", 0) - player_gold)

    can_craft = has_all_materials and level_ok and gold_ok

    return {
        "can_craft": can_craft,
        "level_ok": level_ok,
        "gold_ok": gold_ok,
        "materials_ok": has_all_materials,
        "missing_materials": missing_materials,
        "missing_gold": missing_gold,
        "materials_info": materials_info,
    }


def format_recipe_for_frontend(recipe: dict, player_level: int,
                               player_gold: int,
                               inventory_items: list) -> dict:
    check = check_can_craft(recipe, player_level, player_gold, inventory_items)

    with open(ITEMS_FILE, "r", encoding="utf-8") as f:
        items_db = json.load(f)

    output_id = recipe["output"]["item_id"]
    output_info = items_db.get(output_id, {})

    return {
        "recipe_id": recipe["recipe_id"],
        "name": recipe["name"],
        "description": recipe.get("description", ""),
        "output": {
            "item_id": output_id,
            "name": output_info.get("name", output_id),
            "quantity": recipe["output"].get("quantity", 1),
            "equip_slot": output_info.get("equip_slot"),
            "stats": output_info.get("stats"),
            "rarity": output_info.get("rarity", "common"),
        },
        "materials": check["materials_info"],
        "gold_cost": recipe.get("gold_cost", 0),
        "level_requirement": recipe.get("level_requirement", 1),
        "success_rate": recipe.get("success_rate", 1.0),
        "fail_return_rate": recipe.get("fail_return_rate", 0.5),
        "can_craft": check["can_craft"],
        "level_ok": check["level_ok"],
        "gold_ok": check["gold_ok"],
        "materials_ok": check["materials_ok"],
        "missing_materials": check["missing_materials"],
        "missing_gold": check["missing_gold"],
        "category": recipe.get("category", "weapon"),
        "tier": recipe.get("tier", "basic"),
        "rarity_guarantee": recipe.get("rarity_guarantee", "common"),
    }


@dataclass
class ForgeResult:
    success: bool
    message: str
    forged: bool = False
    output_item_id: str = ""
    output_name: str = ""
    output_rarity: str = "common"
    output_affixes: list = None
    returned_materials: list = None
    player_inventory: list = None
    player_gold: int = 0

    def __post_init__(self):
        if self.output_affixes is None:
            self.output_affixes = []
        if self.returned_materials is None:
            self.returned_materials = []


def execute_forge(recipe_id: str, player_level: int, player_gold: int,
                  inventory_items: list) -> ForgeResult:
    recipe = RECIPES_DB.get(recipe_id)
    if not recipe:
        return ForgeResult(False, "配方不存在")

    check = check_can_craft(recipe, player_level, player_gold, inventory_items)
    if not check["level_ok"]:
        return ForgeResult(False, f"等级不足，需要 Lv.{recipe['level_requirement']}")
    if not check["gold_ok"]:
        return ForgeResult(False, f"金币不足，需要 {recipe['gold_cost']} 金币")
    if not check["materials_ok"]:
        names = ", ".join(m["name"] for m in check["missing_materials"])
        return ForgeResult(False, f"材料不足：{names}")

    with open(ITEMS_FILE, "r", encoding="utf-8") as f:
        items_db = json.load(f)

    output_id = recipe["output"]["item_id"]
    output_info = items_db.get(output_id, {})
    output_name = output_info.get("name", output_id)

    gold_cost = recipe.get("gold_cost", 0)
    new_gold = player_gold - gold_cost

    new_items = _deep_copy_inventory(inventory_items)

    for mat in recipe.get("materials", []):
        _remove_from_inventory(new_items, mat["item_id"], mat["quantity"])

    success_roll = random.random()
    success_rate = recipe.get("success_rate", 1.0)

    if success_roll < success_rate:
        final_rarity = _roll_rarity(recipe.get("rarity_guarantee", "common"))

        from affix_system import generate_affixes
        equip_slot = output_info.get("equip_slot", "")
        affixes = generate_affixes(equip_slot, final_rarity, player_level)

        _add_item_with_affixes(new_items, output_id, 1, affixes, final_rarity)

        rarity_names = {
            "common": "普通", "uncommon": "优秀", "rare": "稀有",
            "epic": "史诗", "legendary": "传说",
        }
        rarity_name = rarity_names.get(final_rarity, final_rarity)

        affix_text = ""
        if affixes:
            affix_names = "、".join(a["name"] for a in affixes)
            affix_text = f"，附带词条：{affix_names}"

        message = f"锻造成功！获得【{rarity_name}】{output_name}{affix_text}"

        return ForgeResult(
            success=True,
            message=message,
            forged=True,
            output_item_id=output_id,
            output_name=output_name,
            output_rarity=final_rarity,
            output_affixes=affixes,
            player_inventory=new_items,
            player_gold=new_gold,
        )
    else:
        fail_return_rate = recipe.get("fail_return_rate", 0.5)
        returned = []
        for mat in recipe.get("materials", []):
            return_qty = max(1, int(mat["quantity"] * fail_return_rate))
            if return_qty > 0:
                mat_name = items_db.get(mat["item_id"], {}).get("name", mat["item_id"])
                _add_to_inventory(new_items, mat["item_id"], return_qty)
                returned.append({
                    "item_id": mat["item_id"],
                    "name": mat_name,
                    "quantity": return_qty,
                })

        return_text = ""
        if returned:
            parts = [f"{r['name']}×{r['quantity']}" for r in returned]
            return_text = f"返还了：{', '.join(parts)}"

        message = f"锻造失败...{return_text}"

        return ForgeResult(
            success=True,
            message=message,
            forged=False,
            returned_materials=returned,
            player_inventory=new_items,
            player_gold=new_gold,
        )


def _roll_rarity(guarantee: str) -> str:
    guarantee_idx = RARITY_ORDER.index(guarantee) if guarantee in RARITY_ORDER else 0
    if random.random() < 0.2 and guarantee_idx < len(RARITY_ORDER) - 1:
        return RARITY_ORDER[guarantee_idx + 1]
    return guarantee


def _deep_copy_inventory(items: list) -> list:
    return [dict(item) for item in items]


def _remove_from_inventory(items: list, item_id: str, quantity: int) -> bool:
    for item in items:
        if item.get("item_id") == item_id:
            if item.get("quantity", 0) < quantity:
                return False
            item["quantity"] = item.get("quantity", 0) - quantity
            if item["quantity"] <= 0:
                items.remove(item)
            return True
    return False


def _add_to_inventory(items: list, item_id: str, quantity: int):
    for item in items:
        if item.get("item_id") == item_id:
            item["quantity"] = item.get("quantity", 0) + quantity
            return
    items.append({"item_id": item_id, "quantity": quantity})


def _add_item_with_affixes(items: list, item_id: str, quantity: int,
                           affixes: list, rarity: str):
    for item in items:
        if item.get("item_id") == item_id and not item.get("instance_affixes"):
            item["quantity"] = item.get("quantity", 0) + quantity
            if affixes:
                item["instance_affixes"] = affixes
                item["instance_rarity"] = rarity
            return
    new_item = {"item_id": item_id, "quantity": quantity}
    if affixes:
        new_item["instance_affixes"] = affixes
        new_item["instance_rarity"] = rarity
    items.append(new_item)
