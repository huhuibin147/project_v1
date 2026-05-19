"""Map related routes: tiles, map data, transfer, object interaction."""

import json
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException

from routes.context import player_profile, quest_manager
from routes.models import TransferRequest, ObjectInteractRequest, ExploredTilesRequest

router = APIRouter(prefix="/api", tags=["map"])

MAPS_DIR = Path(__file__).parent.parent.parent / "config" / "maps"
TILES_FILE = Path(__file__).parent.parent.parent / "config" / "tiles.json"


@router.get("/maps")
async def list_maps():
    result = []
    for map_file in sorted(MAPS_DIR.glob("*.json")):
        with open(map_file, "r", encoding="utf-8") as f:
            d = json.load(f)
        meta = d.get("metadata", {})
        env = meta.get("environment", {})
        result.append({
            "id": d["id"],
            "name": d["name"],
            "width": d["width"],
            "height": d["height"],
            "level_range": meta.get("level_range", [1, 1]),
            "region": meta.get("region", ""),
            "environment": {
                "particles": env.get("particles", []),
                "ambient_color": env.get("ambient_color"),
                "danger_zone": env.get("danger_zone", False),
            },
            "map_names": meta.get("map_names", {}),
        })
    return result


@router.post("/map/explored")
async def update_explored_tiles(req: ExploredTilesRequest):
    existing = set(player_profile.explored_tiles.get(req.map_id, []))
    existing.update(req.tiles)
    player_profile.explored_tiles[req.map_id] = list(existing)
    player_profile._save()
    return {"success": True, "count": len(existing)}


@router.get("/map/tiles")
async def get_tiles():
    if not TILES_FILE.exists():
        raise HTTPException(status_code=404, detail="瓦片配置文件不存在")
    with open(TILES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/map/{map_id}")
async def get_map(map_id: str):
    map_file = MAPS_DIR / f"{map_id}.json"
    if not map_file.exists():
        raise HTTPException(status_code=404, detail=f"地图 '{map_id}' 不存在")
    with open(map_file, "r", encoding="utf-8") as f:
        map_data = json.load(f)
    map_states = player_profile.map_states.get(map_id, {})
    object_states = map_states.get("objects", {})
    for obj in map_data.get("objects", []):
        if obj["id"] in object_states:
            obj["state"] = object_states[obj["id"]]
    map_data["explored_tiles"] = player_profile.explored_tiles.get(map_id, [])
    return map_data


@router.post("/map/transfer")
async def transfer_map(req: TransferRequest):
    map_file = MAPS_DIR / f"{req.target_map}.json"
    if not map_file.exists():
        raise HTTPException(status_code=404, detail=f"目标地图 '{req.target_map}' 不存在")
    player_profile.set_position(req.target_x, req.target_y)
    player_profile.current_map = req.target_map
    player_profile._save()
    with open(map_file, "r", encoding="utf-8") as f:
        map_data = json.load(f)
    
    result = {"success": True, "map_data": map_data, "player_info": player_profile.get_info()}
    
    quest_updates = quest_manager.on_explore(req.target_map, req.target_x, req.target_y)
    if quest_updates:
        result["quest_updates"] = quest_updates
    
    return result


@router.post("/map/object/interact")
async def interact_object(req: ObjectInteractRequest):
    map_file = MAPS_DIR / f"{req.map_id}.json"
    if not map_file.exists():
        raise HTTPException(status_code=404, detail=f"地图 '{req.map_id}' 不存在")
    with open(map_file, "r", encoding="utf-8") as f:
        map_data = json.load(f)

    target_obj = None
    for obj in map_data.get("objects", []):
        if obj["id"] == req.object_id:
            target_obj = obj
            break
    if not target_obj:
        raise HTTPException(status_code=404, detail=f"物件 '{req.object_id}' 不存在")

    obj_type = target_obj.get("type")
    props = target_obj.get("properties", {})
    result = {"success": True, "type": obj_type}

    if obj_type == "chest":
        if target_obj.get("state", {}).get("opened"):
            result["message"] = "这个宝箱已经打开了。"
        else:
            items = props.get("items", [])
            for item in items:
                player_profile.add_item(item["item_id"], item["quantity"])
            if req.map_id not in player_profile.map_states:
                player_profile.map_states[req.map_id] = {"objects": {}}
            player_profile.map_states[req.map_id]["objects"][req.object_id] = {"opened": True}
            player_profile._save()
            result["message"] = "获得物品！"
            result["items"] = items
            for item in items:
                quest_manager.on_collect(item["item_id"])

    elif obj_type == "gather":
        item_id = props.get("item_id")
        respawn_time = props.get("respawn_time", 60)
        if item_id:
            if req.map_id in player_profile.map_states:
                obj_state = player_profile.map_states[req.map_id].get("objects", {}).get(req.object_id, {})
                last_gathered = obj_state.get("last_gathered", 0)
                current_time = int(time.time())
                if current_time - last_gathered < respawn_time:
                    remaining = respawn_time - (current_time - last_gathered)
                    result["success"] = False
                    result["message"] = f"采集点还在冷却中，还需等待 {remaining} 秒"
                    return result

            player_profile.add_item(item_id, 1)
            if req.map_id not in player_profile.map_states:
                player_profile.map_states[req.map_id] = {"objects": {}}
            player_profile.map_states[req.map_id]["objects"][req.object_id] = {"last_gathered": int(time.time())}
            player_profile._save()
            result["message"] = "采集了 1 个物品。"
            quest_manager.on_collect(item_id)

    elif obj_type == "decoration":
        result["message"] = props.get("interact_text", "")
    else:
        result["message"] = "无法交互。"

    return result
