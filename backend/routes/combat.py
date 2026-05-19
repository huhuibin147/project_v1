"""Combat related routes: start, action, end - with multi-enemy support."""

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


@router.get("/monsters/drop_map")
async def get_monsters_drop_map():
    drop_map = {}
    for monster_id, monster in MONSTERS_DB.items():
        monster_name = monster.get("name", monster_id)
        for drop in monster.get("drops", []):
            item_id = drop.get("item_id") if isinstance(drop, dict) else drop
            if not item_id:
                continue
            chance = drop.get("chance") if isinstance(drop, dict) else None
            if item_id not in drop_map:
                drop_map[item_id] = []
            drop_map[item_id].append({
                "monster_id": monster_id,
                "monster_name": monster_name,
                "chance": chance,
            })
    return {"drop_map": drop_map}


@router.post("/combat/start")
async def combat_start(req: CombatStartRequest):
    cleanup_expired_sessions()

    map_file = MAPS_DIR / f"{req.map_id}.json"
    if not map_file.exists():
        raise HTTPException(404, "地图不存在")
    with open(map_file, "r", encoding="utf-8") as f:
        map_data = json.load(f)

    monster_configs = []

    if req.monster_group_id:
        groups = map_data.get("monster_groups", [])
        group = None
        for g in groups:
            if g.get("group_id") == req.monster_group_id:
                group = g
                break
        if not group:
            raise HTTPException(404, "怪物组不存在")

        for entry in group.get("monsters", []):
            mid = entry["monster_id"]
            mc = MONSTERS_DB.get(mid)
            if not mc:
                raise HTTPException(404, f"怪物配置不存在: {mid}")
            config_copy = json.loads(json.dumps(mc))
            if "count" in entry and entry["count"] > 1:
                for i in range(entry["count"]):
                    c = json.loads(json.dumps(config_copy))
                    if entry["count"] > 1:
                        c["name"] = f"{c['name']} {chr(65 + i)}"
                    c["id"] = mid
                    monster_configs.append(c)
            else:
                config_copy["id"] = mid
                monster_configs.append(config_copy)
    else:
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

        config_copy = json.loads(json.dumps(monster_config))
        config_copy["id"] = monster_id
        monster_configs.append(config_copy)

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
        "element": player_profile.element if hasattr(player_profile, "element") else "none",
    }

    session = create_combat_session(monster_configs, player_snapshot)

    formatted_skills = [format_skill_for_frontend(s) for s in session.player_skills]
    formatted_skills = [s for s in formatted_skills if s is not None]

    from combat.monster_ai import decide_action
    monsters_data = []
    for m in session.monsters:
        next_action = decide_action(session, m) if m.alive else ""
        monsters_data.append(m.to_dict(next_action=next_action))

    return {
        "session_id": session.session_id,
        "monsters": monsters_data,
        "monster": monsters_data[0] if monsters_data else None,
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
        "target_index": session.target_index,
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
    if req.target_index is not None:
        action_data["target_index"] = req.target_index
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

        all_tags = set()
        all_monster_ids = []
        for m in session.monsters:
            all_monster_ids.append(m.monster_id)
            all_tags.update(m.config.get("tags", []))

        quest_updates = []
        for mid in all_monster_ids:
            qu = quest_manager.on_kill(mid, list(all_tags))
            if qu:
                quest_updates.extend(qu)

        if quest_updates:
            state["quest_updates"] = quest_updates

    elif session.phase == CombatPhase.DEFEAT:
        gold_rewards = [m.config.get("gold_reward", [10])[0] for m in session.monsters]
        gold_loss = min(player_profile.gold, max(10, max(gold_rewards) if gold_rewards else 10))
        if gold_loss > 0:
            player_profile.spend_gold(gold_loss)
        player_profile.hp = 1
        session.player_hp = 1
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

    return state


@router.post("/combat/end")
async def combat_end(req: CombatEndRequest):
    remove_session(req.session_id)
    player_profile._save()
    return {"success": True, "player_info": player_profile.get_info()}
