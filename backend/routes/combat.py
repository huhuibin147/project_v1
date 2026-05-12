"""Combat related routes: start, action, end."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

from routes.context import player_profile, quest_manager, ITEMS_DB
from routes.models import CombatStartRequest, CombatActionRequest, CombatEndRequest

from combat.engine import (
    create_combat_session, get_session, remove_session,
    resolve_turn, CombatPhase, cleanup_expired_sessions,
)
from skill_system import format_skill_for_frontend

router = APIRouter(prefix="/api", tags=["combat"])

MAPS_DIR = Path(__file__).parent.parent.parent / "config" / "maps"
MONSTERS_FILE = Path(__file__).parent.parent.parent / "config" / "monsters.json"

MONSTERS_DB = {}
if MONSTERS_FILE.exists():
    with open(MONSTERS_FILE, "r", encoding="utf-8") as f:
        MONSTERS_DB = json.load(f)


@router.get("/monsters")
async def get_monsters_config():
    return MONSTERS_DB


@router.post("/combat/start")
async def combat_start(req: CombatStartRequest):
    cleanup_expired_sessions()

    map_file = MAPS_DIR / f"{req.map_id}.json"
    if not map_file.exists():
        raise HTTPException(404, "地图不存在")
    with open(map_file, "r", encoding="utf-8") as f:
        map_data = json.load(f)

    monster_spawn = None
    monsters_list = map_data.get("monsters", [])
    for idx, m in enumerate(monsters_list):
        instance_id = f"{m['monster_id']}_{idx}"
        if instance_id == req.monster_instance_id:
            monster_spawn = m
            break

    if not monster_spawn:
        raise HTTPException(404, "怪物不存在")

    monster_id = monster_spawn["monster_id"]
    monster_config = MONSTERS_DB.get(monster_id)
    if not monster_config:
        raise HTTPException(404, "怪物配置不存在")

    player_snapshot = {
        "hp": player_profile.hp,
        "max_hp": player_profile.max_hp,
        "mp": getattr(player_profile, "mp", 0),
        "max_mp": getattr(player_profile, "max_mp", 0),
        "attack": player_profile.attack,
        "defense": player_profile.defense,
        "speed": player_profile.speed,
        "skills": getattr(player_profile, "skills", []),
        "talent_passives": player_profile.get_talent_passives() if hasattr(player_profile, "get_talent_passives") else {},
        "equipment_affixes": player_profile.get_equipment_affixes() if hasattr(player_profile, "get_equipment_affixes") else [],
    }

    session = create_combat_session(monster_id, monster_config, player_snapshot)

    formatted_skills = [format_skill_for_frontend(s) for s in session.player_skills]
    formatted_skills = [s for s in formatted_skills if s is not None]

    return {
        "session_id": session.session_id,
        "monster": {
            "id": monster_id,
            "name": monster_config["name"],
            "hp": session.monster_hp,
            "max_hp": session.monster_max_hp,
            "sprite_color": monster_config.get("sprite_color", "#888"),
            "sprite_accent": monster_config.get("sprite_accent", "#555"),
        },
        "player": {
            "hp": session.player_hp,
            "max_hp": session.player_max_hp,
            "mp": session.player_mp,
            "max_mp": session.player_max_mp,
            "attack": session.player_attack,
            "defense": session.player_defense,
            "speed": session.player_speed,
            "skills": formatted_skills,
        },
        "phase": session.phase.value,
        "log": session.log,
    }


@router.post("/combat/action")
async def combat_action(req: CombatActionRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(404, "战斗会话不存在或已过期")

    if session.phase != CombatPhase.PLAYER_TURN:
        raise HTTPException(400, "当前不是你的回合")

    if req.action == "use_item":
        if not req.item_id:
            raise HTTPException(400, "使用物品需要指定item_id")
        if player_profile.get_item_quantity(req.item_id) <= 0:
            raise HTTPException(400, "你没有这个物品")
        player_profile.remove_item(req.item_id, 1)

    action_data = {"item_id": req.item_id}
    if req.action == "skill" and req.skill_id:
        action_data["skill_id"] = req.skill_id
    state = resolve_turn(session, req.action, action_data)

    if session.phase == CombatPhase.VICTORY and not state.get("fled"):
        exp_leveled = player_profile.gain_exp(session.exp_reward)
        state["level_up"] = exp_leveled

        if session.gold_reward > 0:
            player_profile.add_gold(session.gold_reward)

        for drop in session.drops:
            player_profile.add_item(drop["item_id"], drop["quantity"])

        for drop in state.get("drops", []):
            item_info = ITEMS_DB.get(drop["item_id"], {})
            drop["name"] = item_info.get("name", drop["item_id"])

        state["player_inventory"] = player_profile.get_inventory()
        state["player_gold"] = player_profile.gold

        monster_tags = session.monster_config.get("tags", [])
        quest_updates = quest_manager.on_kill(session.monster_id, monster_tags)
        if quest_updates:
            state["quest_updates"] = quest_updates

    elif session.phase == CombatPhase.DEFEAT:
        gold_loss = min(player_profile.gold, max(10, session.monster_config.get("gold_reward", [10])[0]))
        if gold_loss > 0:
            player_profile.spend_gold(gold_loss)
        player_profile.hp = 1
        player_profile._save()
        state["gold_lost"] = gold_loss

    if session.phase == CombatPhase.PLAYER_TURN:
        player_profile.hp = session.player_hp
        player_profile.mp = session.player_mp
        player_profile._save()

    state["phase"] = session.phase.value
    state["player_hp"] = session.player_hp
    state["player_max_hp"] = session.player_max_hp
    state["player_mp"] = session.player_mp
    state["player_max_mp"] = session.player_max_mp
    state["monster_hp"] = session.monster_hp
    state["monster_max_hp"] = session.monster_max_hp

    return state


@router.post("/combat/end")
async def combat_end(req: CombatEndRequest):
    remove_session(req.session_id)
    player_profile._save()
    return {"success": True, "player_info": player_profile.get_info()}
