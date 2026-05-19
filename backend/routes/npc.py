"""NPC related routes: chat, status, history, config, shop, trade, services."""

import json
from fastapi import APIRouter

from routes.context import (
    get_npc, get_all_npc_ids, npc_agents,
    player_profile, quest_manager,
    NPC_CONFIG_FILE, ITEMS_DB, ITEM_EFFECTS,
    format_skill_for_frontend,
)
from routes.models import ChatRequest, TradeRequest, HealServiceRequest, LearnSkillRequest, GenericServiceRequest
from skill_system import get_skill, can_learn_skill

router = APIRouter(prefix="/api", tags=["npc"])


@router.get("/npcs")
async def list_npcs():
    with open(NPC_CONFIG_FILE, "r", encoding="utf-8") as f:
        all_npcs = json.load(f)
    return [
        {
            "npc_id": npc_id,
            "name": cfg["name"],
            "role": cfg["role"],
            "location": cfg["location"],
            "map_id": cfg.get("map_id", ""),
            "greeting": cfg["greeting"],
            "appearance": cfg.get("appearance", None),
            "services": cfg.get("services", {}),
            "interaction_buttons": cfg.get("interaction_buttons", ["talk", "quest", "shop"]),
        }
        for npc_id, cfg in all_npcs.items()
    ]


@router.post("/chat")
async def chat(req: ChatRequest):
    npc = get_npc(req.npc_id)
    result = npc.chat(req.message)
    quest_updates = quest_manager.on_talk(req.npc_id)
    if quest_updates:
        result["quest_updates"] = quest_updates
    return result


@router.get("/npc/status")
async def npc_status(npc_id: str = "blacksmith"):
    return get_npc(npc_id).get_status()


@router.get("/npc/history")
async def npc_history(npc_id: str = "blacksmith"):
    return {"npc_id": npc_id, "history": get_npc(npc_id).history}


@router.get("/npc/config")
async def npc_config(npc_id: str = "blacksmith"):
    cfg = get_npc(npc_id).cfg
    return {
        "npc_id": cfg["id"],
        "name": cfg["name"],
        "role": cfg["role"],
        "location": cfg["location"],
        "greeting": cfg["greeting"],
        "personality": cfg.get("personality_params", {}),
    }


@router.get("/shop")
async def get_shop(npc_id: str = "blacksmith"):
    npc = get_npc(npc_id)
    return {
        "name": npc.cfg.get("shop", {}).get("name", npc.name + "的商店"),
        "items": npc.shop_inventory.to_list(),
        "gold": npc.shop_inventory.gold,
    }


@router.post("/trade")
async def trade(req: TradeRequest):
    npc = get_npc(req.npc_id)
    item_info = ITEMS_DB.get(req.item_id)
    if not item_info:
        return {"success": False, "message": "未知物品。"}

    if req.action == "buy":
        buy_price = item_info["buy_price"]
        if buy_price <= 0:
            return {"success": False, "message": "这个东西不卖的。"}
        total = buy_price * req.quantity
        npc_qty = npc.shop_inventory.get_quantity(req.item_id)
        if npc_qty < req.quantity:
            return {"success": False, "message": f"库存不足，只剩 {npc_qty} 个。"}
        if player_profile.gold < total:
            return {"success": False, "message": f"你的金币不够！需要 {total}，你只有 {player_profile.gold}。"}

        player_profile.spend_gold(total)
        player_profile.add_item(req.item_id, req.quantity)
        npc.shop_inventory.gold += total
        npc.shop_inventory.remove_item(req.item_id, req.quantity)
        message = f"好嘞！{req.quantity} 个{item_info['name']}，收你 {total} 金币。"
        quest_manager.on_collect(req.item_id)

    elif req.action == "sell":
        sell_price = item_info["sell_price"]
        if sell_price <= 0:
            return {"success": False, "message": "这东西俺不收。"}
        total = sell_price * req.quantity
        player_qty = player_profile.get_item_quantity(req.item_id)
        if player_qty < req.quantity:
            return {"success": False, "message": f"你没有那么多{item_info['name']}。你只有 {player_qty} 个。"}

        min_gold = npc.cfg.get("default_gold", 0)
        available_gold = npc.shop_inventory.gold - min_gold
        if available_gold < total:
            return {"success": False, "message": f"俺手头紧，最多只能收 {available_gold // max(sell_price, 1)} 个{item_info['name']}。"}

        player_profile.add_gold(total)
        player_profile.remove_item(req.item_id, req.quantity)
        npc.shop_inventory.gold -= total
        npc.acquired_inventory.add_item(req.item_id, req.quantity)
        message = f"行！{req.quantity} 个{item_info['name']}，给你 {total} 金币。"
    else:
        return {"success": False, "message": "未知交易类型"}

    return {
        "success": True,
        "message": message,
        "player_inventory": player_profile.get_inventory(),
        "player_gold": player_profile.gold,
        "shop_inventory": npc.shop_inventory.to_list(),
        "shop_gold": npc.shop_inventory.gold,
    }


@router.post("/npc/service/heal")
async def npc_heal_service(req: HealServiceRequest):
    npc = get_npc(req.npc_id)
    cfg = npc.cfg
    services = cfg.get("services", {})

    if req.service_type not in services:
        return {"success": False, "message": "该NPC不提供此服务"}

    service = services[req.service_type]
    cost = service.get("cost", 0)

    if player_profile.gold < cost:
        return {"success": False, "message": f"金币不足，需要 {cost} 金币"}

    msg = ""
    if req.service_type == "heal":
        before = player_profile.hp
        player_profile.hp = player_profile.max_hp
        healed = player_profile.hp - before
        msg = f"恢复了 {healed} 点生命值，感觉焕然一新！"
    elif req.service_type == "restore_mp":
        before = player_profile.mp
        player_profile.mp = player_profile.max_mp
        restored = player_profile.mp - before
        msg = f"恢复了 {restored} 点魔法值，精神饱满！"
    elif req.service_type == "cure":
        player_profile.status_effects = []
        msg = "解除了所有负面状态效果，身体轻松了许多。"

    player_profile.spend_gold(cost)
    return {
        "success": True,
        "message": msg,
        "cost": cost,
        "player_info": player_profile.get_info(),
    }


@router.get("/npc/service/skills")
async def npc_available_skills(npc_id: str = "skill_master"):
    npc = get_npc(npc_id)
    cfg = npc.cfg
    services = cfg.get("services", {})

    if "learn_skill" not in services:
        return {"success": False, "message": "该NPC不提供技能教学服务"}

    shop_items = cfg.get("shop", {}).get("inventory", [])
    skill_ids = []
    for item in shop_items:
        item_id = item["item_id"]
        if item_id.startswith("scroll_"):
            effect = ITEM_EFFECTS.get(item_id)
            if effect and effect.get("type") == "learn_skill":
                skill_ids.append(effect["skill_id"])

    available = []
    all_known = player_profile.skills + player_profile.learned_skills
    for sid in skill_ids:
        skill = get_skill(sid)
        if not skill:
            continue
        can_learn, reason = can_learn_skill(sid, player_profile.class_id, player_profile.level, all_known)
        scroll_id = None
        for item in shop_items:
            eff = ITEM_EFFECTS.get(item["item_id"])
            if eff and eff.get("skill_id") == sid:
                scroll_id = item["item_id"]
                break
        base_price = ITEMS_DB.get(scroll_id, {}).get("buy_price", 0) if scroll_id else 0
        cost_multiplier = services["learn_skill"].get("cost_multiplier", 1.5)
        learn_cost = int(base_price * cost_multiplier)

        available.append({
            "skill_id": sid,
            "name": skill["name"],
            "description": skill["description"],
            "mp_cost": skill["mp_cost"],
            "cooldown": skill["cooldown"],
            "type": skill["type"],
            "class_requirement": skill.get("class_requirement", []),
            "level_requirement": skill.get("level_requirement", 1),
            "can_learn": can_learn,
            "reason": reason,
            "cost": learn_cost,
        })

    return {"success": True, "skills": available}


@router.post("/npc/service/learn_skill")
async def npc_learn_skill(req: LearnSkillRequest):
    npc = get_npc(req.npc_id)
    cfg = npc.cfg
    services = cfg.get("services", {})

    if "learn_skill" not in services:
        return {"success": False, "message": "该NPC不提供技能教学服务"}

    skill = get_skill(req.skill_id)
    if not skill:
        return {"success": False, "message": "技能不存在"}

    shop_items = cfg.get("shop", {}).get("inventory", [])
    scroll_id = None
    for item in shop_items:
        eff = ITEM_EFFECTS.get(item["item_id"])
        if eff and eff.get("skill_id") == req.skill_id:
            scroll_id = item["item_id"]
            break
    base_price = ITEMS_DB.get(scroll_id, {}).get("buy_price", 0) if scroll_id else 0
    cost_multiplier = services["learn_skill"].get("cost_multiplier", 1.5)
    learn_cost = int(base_price * cost_multiplier)

    if player_profile.gold < learn_cost:
        return {"success": False, "message": f"金币不足，需要 {learn_cost} 金币"}

    all_known = player_profile.skills + player_profile.learned_skills
    can_learn, reason = can_learn_skill(req.skill_id, player_profile.class_id, player_profile.level, all_known)
    if not can_learn:
        return {"success": False, "message": f"无法学习：{reason}"}

    player_profile.spend_gold(learn_cost)
    if req.skill_id not in player_profile.skills:
        player_profile.skills.append(req.skill_id)
    if req.skill_id not in player_profile.learned_skills:
        player_profile.learned_skills.append(req.skill_id)
    player_profile._save()

    return {
        "success": True,
        "message": f"成功学会了「{skill['name']}」！",
        "cost": learn_cost,
        "skills": [format_skill_for_frontend(s) for s in player_profile.skills],
        "player_info": player_profile.get_info(),
    }


SERVICE_DIALOGUES = {
    "rest": {
        "innkeeper": "来来来，楼上房间已经给你准备好了。好好休息一晚，明天又是元气满满的一天！",
        "_default": "这里可以休息一下，恢复体力。",
    },
    "rumor": {
        "innkeeper": "听说最近王城地下出现了一些奇怪的动静，有人说是古墓的入口……不过谁知道呢，可能是老鼠吧。",
        "_default": "最近没什么特别的消息。",
    },
    "cave_guide": {
        "cave_explorer": "这个洞穴我走了不下百遍了！往东走大概五十步有个岔路，左边通向矿脉区，右边比较危险，有骷髅兵出没。你要是找到什么好东西，记得分我一份啊！",
        "_default": "我对这里不太了解，你自己小心探索吧。",
    },
}


@router.post("/npc/service/generic")
async def npc_generic_service(req: GenericServiceRequest):
    npc = get_npc(req.npc_id)
    cfg = npc.cfg
    services = cfg.get("services", {})

    if req.service_type not in services:
        return {"success": False, "message": f"该NPC不提供此服务"}

    service_cfg = services[req.service_type]
    cost = service_cfg.get("cost", 0)

    if cost > 0 and player_profile.gold < cost:
        return {"success": False, "message": f"金币不足，需要 {cost} 金币"}

    if cost > 0:
        player_profile.spend_gold(cost)
        player_profile._save()

    dialogues = SERVICE_DIALOGUES.get(req.service_type, {})
    dialogue = dialogues.get(req.npc_id, dialogues.get("_default", f"你使用了{service_cfg.get('name', '服务')}。"))

    result = {
        "success": True,
        "dialogue": dialogue,
        "cost": cost,
    }

    if req.service_type == "rest":
        player_profile.hp = player_profile.max_hp
        player_profile.mp = player_profile.max_mp
        player_profile._save()
        result["player_info"] = player_profile.get_info()

    return result
