"""Forge and affix related routes."""

from fastapi import APIRouter

from routes.context import player_profile
from routes.models import ForgeCraftRequest, ForgeRerollRequest

router = APIRouter(prefix="/api", tags=["forge"])


@router.get("/forge/recipes")
async def get_forge_recipes(npc_id: str = "blacksmith"):
    from forge_system import get_all_recipes, format_recipe_for_frontend
    all_recipes = get_all_recipes()
    formatted = []
    for recipe in all_recipes:
        formatted.append(
            format_recipe_for_frontend(
                recipe, player_profile.level, player_profile.gold, player_profile.inventory
            )
        )
    return {
        "recipes": formatted,
        "player_level": player_profile.level,
        "player_gold": player_profile.gold,
    }


@router.post("/forge/craft")
async def forge_craft(req: ForgeCraftRequest):
    from forge_system import execute_forge
    result = execute_forge(
        req.recipe_id, player_profile.level, player_profile.gold, player_profile.inventory,
        player_profile.forge_streaks
    )
    if result.player_inventory is not None:
        player_profile.inventory = result.player_inventory
    player_profile.gold = result.player_gold
    if result.forge_streaks is not None:
        player_profile.forge_streaks = result.forge_streaks
    player_profile._save()

    response = {
        "success": result.success,
        "message": result.message,
        "forged": result.forged,
    }
    if result.forged:
        response["result"] = {
            "item_id": result.output_item_id,
            "name": result.output_name,
            "rarity": result.output_rarity,
            "affixes": result.output_affixes,
        }
    else:
        response["result"] = {
            "returned_materials": result.returned_materials,
        }
    response["player_inventory"] = player_profile.get_inventory()
    response["player_gold"] = player_profile.gold
    response["forge_streaks"] = player_profile.forge_streaks
    return response


@router.post("/forge/reroll")
async def forge_reroll(req: ForgeRerollRequest):
    from affix_system import reroll_single_affix, REROLL_COSTS
    item_id = req.item_id
    slot = req.slot

    if slot not in player_profile.equipment:
        return {"success": False, "message": "无效的装备槽位"}

    equipped_item_id = player_profile.equipment.get(slot)
    if not equipped_item_id or equipped_item_id != item_id:
        return {"success": False, "message": "该槽位没有装备该物品"}

    from item_system import ITEMS_DB
    item_info = ITEMS_DB.get(item_id, {})

    item_instance = {
        "item_id": item_id,
        "equip_slot": item_info.get("equip_slot", ""),
        "instance_affixes": player_profile.get_item_affixes_for_equipment(item_id, slot),
        "instance_rarity": player_profile.get_item_rarity_for_equipment(item_id, slot),
    }

    result = reroll_single_affix(item_instance, player_profile.level)

    if not result["success"]:
        return result

    cost = result["cost"]
    if player_profile.gold < cost:
        return {"success": False, "message": f"金币不足，需要 {cost} 金币"}

    player_profile.gold -= cost
    player_profile.update_equipment_affixes(slot, result["affixes"])
    player_profile._recalc_stats()
    player_profile._save()

    return {
        "success": True,
        "message": result["message"],
        "old_affix": result["old_affix"],
        "new_affix": result["new_affix"],
        "cost": cost,
        "player_gold": player_profile.gold,
        "equipment": player_profile._get_equipment_detail(),
    }


@router.get("/affixes/types")
async def get_affix_types():
    from affix_system import get_affix_categories
    return {"categories": get_affix_categories()}
