"""Quest, talent, and skill related routes."""

from fastapi import APIRouter

from routes.context import player_profile, quest_manager
from routes.models import TalentLearnRequest, SkillUpgradeRequest, QuestAcceptRequest, QuestAbandonRequest, QuestCompleteRequest, QuestProgressRequest

router = APIRouter(prefix="/api", tags=["quest"])


@router.get("/skills")
async def get_skills():
    return player_profile.get_skills_info()


@router.post("/skills/upgrade")
async def upgrade_skill(req: SkillUpgradeRequest):
    result = player_profile.upgrade_skill(req.skill_id)
    if result["success"]:
        result["player_info"] = player_profile.get_info()
    return result


@router.get("/talents")
async def get_talents():
    return player_profile.get_talent_info()


@router.post("/talents/learn")
async def learn_talent(req: TalentLearnRequest):
    return player_profile.learn_talent(req.talent_id)


@router.post("/talents/reset")
async def reset_talents():
    return player_profile.reset_talents()


@router.get("/quests")
async def get_quests():
    return {"quests": quest_manager.get_all_quests()}


@router.get("/quests/active")
async def get_active_quests():
    return {"quests": quest_manager.get_active_quests()}


@router.get("/quests/npc/{npc_id}")
async def get_npc_quests(npc_id: str):
    return {"quests": quest_manager.get_npc_quests(npc_id)}


@router.post("/quests/accept")
async def accept_quest(req: QuestAcceptRequest):
    result = quest_manager.accept_quest(req.quest_id)
    if result["success"]:
        result["player_info"] = player_profile.get_info()
    return result


@router.post("/quests/abandon")
async def abandon_quest(req: QuestAbandonRequest):
    return quest_manager.abandon_quest(req.quest_id)


@router.post("/quests/complete")
async def complete_quest(req: QuestCompleteRequest):
    result = quest_manager.complete_quest(req.quest_id)
    if result["success"]:
        result["player_info"] = player_profile.get_info()
    return result


@router.post("/quests/progress")
async def update_quest_progress(req: QuestProgressRequest):
    updated = []
    if req.event_type == "kill":
        monster_id = req.data.get("monster_id", "")
        monster_tags = req.data.get("monster_tags", [])
        updated = quest_manager.on_kill(monster_id, monster_tags)
    elif req.event_type == "collect":
        item_id = req.data.get("item_id", "")
        updated = quest_manager.on_collect(item_id)
    elif req.event_type == "talk":
        npc_id = req.data.get("npc_id", "")
        updated = quest_manager.on_talk(npc_id)
    elif req.event_type == "explore":
        map_id = req.data.get("map_id", "")
        x = req.data.get("x", 0)
        y = req.data.get("y", 0)
        updated = quest_manager.on_explore(map_id, x, y)
    return {"updated": updated}


@router.get("/quests/chain/{quest_id}")
async def get_quest_chain(quest_id: str):
    chain = quest_manager.get_quest_chain(quest_id)
    if chain:
        return {"chain": chain}
    return {"chain": None}


@router.post("/quests/daily/reset")
async def reset_daily_quests():
    reset_quests = quest_manager.reset_daily_quests()
    return {
        "success": True,
        "reset_quests": reset_quests,
        "message": f"已重置 {len(reset_quests)} 个每日任务" if reset_quests else "每日任务无需重置"
    }
