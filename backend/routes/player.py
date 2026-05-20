"""Player related routes: profile, inventory, equipment, saves."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

from routes.context import (
    player_profile, quest_manager, npc_agents,
    ITEMS_DB, ITEM_EFFECTS, format_skill_for_frontend,
)
from routes.models import NewGameRequest, LoadSaveRequest, PlayerUpdateRequest, EquipRequest, UnequipRequest, UseItemRequest, PositionRequest
import player_profile as _player_profile_module

router = APIRouter(prefix="/api", tags=["player"])


@router.get("/inventory")
async def get_inventory():
    return {
        "items": player_profile.get_inventory(),
        "gold": player_profile.gold,
    }


@router.get("/player")
async def get_player():
    return player_profile.get_info()


@router.get("/player/classes")
async def get_player_classes():
    return player_profile.get_classes()


@router.post("/player/update")
async def update_player(req: PlayerUpdateRequest):
    if req.name:
        player_profile.set_name(req.name)
    if req.class_id:
        if not player_profile.set_class(req.class_id):
            raise HTTPException(status_code=400, detail=f"职业 '{req.class_id}' 不存在")
    return player_profile.get_info()


@router.post("/player/heal")
async def heal_player(amount: int = 999):
    player_profile.heal(amount)
    return player_profile.get_info()


@router.get("/equipment")
async def get_equipment():
    return player_profile.get_equipment_info()


@router.post("/equip")
async def equip_item(req: EquipRequest):
    result = player_profile.equip_item(req.item_id)
    if not result["success"]:
        return result
    return {
        **result,
        "player_gold": player_profile.gold,
    }


@router.post("/unequip")
async def unequip_slot(req: UnequipRequest):
    result = player_profile.unequip_slot(req.slot)
    if not result["success"]:
        return result
    return {
        **result,
        "player_gold": player_profile.gold,
    }


@router.post("/use_item")
async def use_item(req: UseItemRequest):
    item = ITEMS_DB.get(req.item_id)
    if not item:
        return {"success": False, "message": "物品不存在"}
    if item["type"] not in ("consumable", "food"):
        return {"success": False, "message": "该物品无法使用"}
    effect = ITEM_EFFECTS.get(req.item_id)
    if not effect:
        return {"success": False, "message": "该物品没有效果"}
    result = player_profile.use_item(req.item_id, effect)
    if result["success"] and effect.get("type") == "learn_skill":
        result["skills"] = [format_skill_for_frontend(s) for s in player_profile.skills]
    return result


@router.get("/saves")
async def list_saves():
    saves = player_profile.list_saves()
    last_slot_file = _player_profile_module.DATA_DIR / "last_slot.json"
    last_slot = None
    if last_slot_file.exists():
        try:
            with open(last_slot_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_slot = data.get("last_slot")
        except Exception:
            pass
    return {"saves": saves, "last_slot": last_slot}


@router.post("/saves/new")
async def new_game(req: NewGameRequest):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="名称不能为空")
    npc_agents.clear()
    success = player_profile.new_game(req.name.strip(), req.class_id, req.slot)
    if not success:
        raise HTTPException(status_code=400, detail="创建失败：无效的职业或存档槽")
    return {"success": True, "player_info": player_profile.get_info()}


@router.post("/saves/load")
async def load_save(req: LoadSaveRequest):
    success = player_profile.load_from_slot(req.slot)
    if not success:
        raise HTTPException(status_code=400, detail="存档不存在或已损坏")
    npc_agents.clear()
    last_slot_file = _player_profile_module.DATA_DIR / "last_slot.json"
    with open(last_slot_file, "w", encoding="utf-8") as f:
        json.dump({"last_slot": req.slot}, f)
    return {"success": True, "player_info": player_profile.get_info()}


@router.delete("/saves/{slot}")
async def delete_save(slot: int):
    npc_agents.clear()
    success = player_profile.delete_slot(slot)
    if not success:
        raise HTTPException(status_code=400, detail="存档不存在")
    return {"success": True}


@router.post("/player/position")
async def save_position(req: PositionRequest):
    player_profile.set_position(req.x, req.y)
    return {"success": True}
