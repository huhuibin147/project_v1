import sys
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / "config.json"
EXAMPLE_PATH = ROOT_DIR / "config.json.example"


def ensure_config():
    """检查 config.json 是否存在，不存在则从模板复制并提示用户填写。"""
    if CONFIG_PATH.exists():
        return
    if not EXAMPLE_PATH.exists():
        print("错误：找不到 config.json.example 模板文件，请确认项目完整性。")
        sys.exit(1)
    shutil.copy(EXAMPLE_PATH, CONFIG_PATH)
    print("=" * 50)
    print("已创建 config.json，请编辑填入你的 API 配置：")
    print(f"  文件路径：{CONFIG_PATH}")
    print()
    print("  需要填写：")
    print('    "api_key"   — 你的 API Key')
    print('    "base_url"  — API 地址')
    print('    "model"     — 模型名称')
    print()
    print("填写完成后，重新执行启动命令即可。")
    print("=" * 50)
    sys.exit(0)


ensure_config()

import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from npc_agent import NPCAgent, NPC_CONFIG_FILE
from player_profile import player as player_profile
from item_system import Inventory, buy_item, sell_item, get_item_info, ITEMS_DB, ITEM_EFFECTS
from skill_system import format_skill_for_frontend
from quest_manager import QuestManager

quest_manager = QuestManager(player_profile)

app = FastAPI(title="LLM NPC Game")

FRONTEND_DIR = str(ROOT_DIR / "frontend")
DATA_DIR = ROOT_DIR / "data"


def migrate_old_saves():
    """将旧版平铺存档文件迁移到文件夹结构。"""
    DATA_DIR.mkdir(exist_ok=True)

    # 获取所有 NPC ID
    with open(NPC_CONFIG_FILE, "r", encoding="utf-8") as f:
        npc_ids = list(json.load(f).keys())

    for slot in range(1, 4):
        folder = DATA_DIR / f"save_{slot}"
        if folder.exists():
            continue

        old_player = DATA_DIR / f"save_{slot}.json"
        if not old_player.exists():
            continue

        # 有旧的平铺存档，迁移
        folder.mkdir(parents=True, exist_ok=True)
        old_player.rename(folder / "player.json")

        # 迁移旧格式 NPC 存档（save_{slot}_{npc_id}.json）
        for npc_id in npc_ids:
            old_npc = DATA_DIR / f"save_{slot}_{npc_id}.json"
            if old_npc.exists():
                old_npc.rename(folder / f"{npc_id}.json")

    # 迁移无槽位的旧版 NPC 存档（{npc_id}_save.json）到 save_1
    folder_1 = DATA_DIR / "save_1"
    for npc_id in npc_ids:
        legacy_npc = DATA_DIR / f"{npc_id}_save.json"
        if legacy_npc.exists():
            target = folder_1 / f"{npc_id}.json"
            if not target.exists():
                folder_1.mkdir(parents=True, exist_ok=True)
                legacy_npc.rename(target)


migrate_old_saves()

# 多 NPC 实例管理
npc_agents: dict[str, NPCAgent] = {}


def get_npc(npc_id: str) -> NPCAgent:
    """获取或创建 NPC Agent 实例。"""
    if npc_id not in npc_agents:
        slot = player_profile.current_slot
        npc_agents[npc_id] = NPCAgent(npc_id, slot=slot)
    return npc_agents[npc_id]


def sync_npc_slots():
    """同步所有 NPC 的存档槽到当前玩家存档槽。"""
    slot = player_profile.current_slot
    for npc_id, npc in npc_agents.items():
        npc.set_slot(slot)


def get_all_npc_ids() -> list[str]:
    """获取所有可用的 NPC ID。"""
    with open(NPC_CONFIG_FILE, "r", encoding="utf-8") as f:
        return list(json.load(f).keys())


class ChatRequest(BaseModel):
    message: str
    npc_id: str = "blacksmith"


class ChatResponse(BaseModel):
    reply: str
    intent: str
    mood: str
    affinity: int
    trade: bool = False
    player_inventory: list = []
    player_gold: int = 0
    shop_inventory: list = []
    shop_gold: int = 0


class TradeRequest(BaseModel):
    action: str  # "buy" 或 "sell"
    item_id: str
    quantity: int = 1
    npc_id: str = "blacksmith"


class PlayerUpdateRequest(BaseModel):
    name: str = None
    class_id: str = None


class NewGameRequest(BaseModel):
    name: str
    class_id: str
    slot: int = 1


class LoadSaveRequest(BaseModel):
    slot: int


class EquipRequest(BaseModel):
    item_id: str


class UnequipRequest(BaseModel):
    slot: str


class UseItemRequest(BaseModel):
    item_id: str


class HealServiceRequest(BaseModel):
    npc_id: str
    service_type: str  # "heal", "restore_mp", "cure"


class LearnSkillRequest(BaseModel):
    npc_id: str
    skill_id: str


class PositionRequest(BaseModel):
    x: int
    y: int


@app.get("/")
async def index():
    return FileResponse(f"{FRONTEND_DIR}/index.html")


@app.get("/api/npcs")
async def list_npcs():
    """返回所有可用 NPC 列表。"""
    with open(NPC_CONFIG_FILE, "r", encoding="utf-8") as f:
        all_npcs = json.load(f)
    result = []
    for npc_id, cfg in all_npcs.items():
        result.append({
            "npc_id": npc_id,
            "name": cfg["name"],
            "role": cfg["role"],
            "location": cfg["location"],
            "map_id": cfg.get("map_id", ""),
            "greeting": cfg["greeting"],
        })
    return result


@app.post("/api/chat")
async def chat(req: ChatRequest):
    npc = get_npc(req.npc_id)
    result = npc.chat(req.message)
    quest_updates = quest_manager.on_talk(req.npc_id)
    if quest_updates:
        result["quest_updates"] = quest_updates
    return result


@app.get("/api/npc/status")
async def npc_status(npc_id: str = "blacksmith"):
    npc = get_npc(npc_id)
    return npc.get_status()


@app.get("/api/npc/history")
async def npc_history(npc_id: str = "blacksmith"):
    """获取 NPC 对话历史。"""
    npc = get_npc(npc_id)
    return {"npc_id": npc_id, "history": npc.history}


@app.get("/api/npc/config")
async def npc_config(npc_id: str = "blacksmith"):
    """返回指定 NPC 的配置信息。"""
    npc = get_npc(npc_id)
    cfg = npc.cfg
    return {
        "npc_id": cfg["id"],
        "name": cfg["name"],
        "role": cfg["role"],
        "location": cfg["location"],
        "greeting": cfg["greeting"],
        "personality": cfg.get("personality_params", {}),
    }


@app.get("/api/inventory")
async def get_inventory():
    """获取玩家全局背包与金币。"""
    return {
        "items": player_profile.get_inventory(),
        "gold": player_profile.gold,
    }


@app.get("/api/shop")
async def get_shop(npc_id: str = "blacksmith"):
    """获取指定 NPC 商店库存。"""
    npc = get_npc(npc_id)
    return {
        "name": npc.cfg.get("shop", {}).get("name", npc.name + "的商店"),
        "items": npc.shop_inventory.to_list(),
        "gold": npc.shop_inventory.gold,
    }


@app.post("/api/trade")
async def trade(req: TradeRequest):
    """直接交易接口（使用全局玩家背包与金币）。"""
    from item_system import ITEMS_DB
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

        # 执行购买
        player_profile.spend_gold(total)
        player_profile.add_item(req.item_id, req.quantity)
        npc.shop_inventory.gold += total
        npc.shop_inventory.remove_item(req.item_id, req.quantity)
        message = f"好嘞！{req.quantity} 个{item_info['name']}，收你 {total} 金币。"
        # 任务进度：收集物品
        quest_manager.on_collect(req.item_id)

    elif req.action == "sell":
        sell_price = item_info["sell_price"]
        if sell_price <= 0:
            return {"success": False, "message": "这东西俺不收。"}
        total = sell_price * req.quantity
        player_qty = player_profile.get_item_quantity(req.item_id)
        if player_qty < req.quantity:
            return {"success": False, "message": f"你没有那么多{item_info['name']}。你只有 {player_qty} 个。"}
        
        # 确保 NPC 出售后至少保留 default_gold 的金币
        min_gold = npc.cfg.get("default_gold", 0)
        available_gold = npc.shop_inventory.gold - min_gold
        if available_gold < total:
            return {"success": False, "message": f"俺手头紧，最多只能收 {available_gold // max(sell_price, 1)} 个{item_info['name']}。"}

        # 执行出售
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


# ===== 玩家档案接口 =====

@app.get("/api/player")
async def get_player():
    """获取玩家信息。"""
    return player_profile.get_info()


@app.get("/api/player/classes")
async def get_player_classes():
    """获取可选职业列表。"""
    return player_profile.get_classes()


@app.post("/api/player/update")
async def update_player(req: PlayerUpdateRequest):
    """更新玩家信息（名字/职业）。"""
    if req.name:
        player_profile.set_name(req.name)
    if req.class_id:
        if not player_profile.set_class(req.class_id):
            raise HTTPException(status_code=400, detail=f"职业 '{req.class_id}' 不存在")
    return player_profile.get_info()


@app.post("/api/player/heal")
async def heal_player(amount: int = 999):
    player_profile.heal(amount)
    return player_profile.get_info()


# ===== 装备系统接口 =====

@app.get("/api/equipment")
async def get_equipment():
    return player_profile.get_equipment_info()


@app.post("/api/equip")
async def equip_item(req: EquipRequest):
    result = player_profile.equip_item(req.item_id)
    if not result["success"]:
        return result
    return {
        **result,
        "player_gold": player_profile.gold,
    }


@app.post("/api/unequip")
async def unequip_slot(req: UnequipRequest):
    result = player_profile.unequip_slot(req.slot)
    if not result["success"]:
        return result
    return {
        **result,
        "player_gold": player_profile.gold,
    }


@app.post("/api/use_item")
async def use_item(req: UseItemRequest):
    """使用消耗品、食物或技能书。"""
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


# ===== 存档管理接口 =====

@app.get("/api/saves")
async def list_saves():
    """获取所有存档槽信息。"""
    saves = player_profile.list_saves()
    # 添加最后加载的存档槽信息
    last_slot_file = DATA_DIR / "last_slot.json"
    last_slot = None
    if last_slot_file.exists():
        try:
            with open(last_slot_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_slot = data.get("last_slot")
        except:
            pass
    return {"saves": saves, "last_slot": last_slot}


@app.post("/api/saves/new")
async def new_game(req: NewGameRequest):
    """新建游戏存档。"""
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="名称不能为空")
    # 清空旧的 NPC 实例，确保加载新存档数据
    npc_agents.clear()
    success = player_profile.new_game(req.name.strip(), req.class_id, req.slot)
    if not success:
        raise HTTPException(status_code=400, detail="创建失败：无效的职业或存档槽")
    # 记录最后加载的存档槽
    last_slot_file = DATA_DIR / "last_slot.json"
    with open(last_slot_file, "w", encoding="utf-8") as f:
        json.dump({"last_slot": req.slot}, f)
    return {"success": True, "player_info": player_profile.get_info()}


@app.post("/api/saves/load")
async def load_save(req: LoadSaveRequest):
    """读取存档。"""
    success = player_profile.load_from_slot(req.slot)
    if not success:
        raise HTTPException(status_code=400, detail="存档不存在或已损坏")
    # 清空旧的 NPC 实例，确保加载新存档数据
    npc_agents.clear()
    # 记录最后加载的存档槽
    last_slot_file = DATA_DIR / "last_slot.json"
    with open(last_slot_file, "w", encoding="utf-8") as f:
        json.dump({"last_slot": req.slot}, f)
    return {"success": True, "player_info": player_profile.get_info()}


@app.delete("/api/saves/{slot}")
async def delete_save(slot: int):
    """删除存档。"""
    npc_agents.clear()
    success = player_profile.delete_slot(slot)
    if not success:
        raise HTTPException(status_code=400, detail="存档不存在")
    return {"success": True}


@app.post("/api/player/position")
async def save_position(req: PositionRequest):
    """保存玩家位置。"""
    player_profile.set_position(req.x, req.y)
    return {"success": True}


# ===== 地图系统接口 =====

MAPS_DIR = ROOT_DIR / "config" / "maps"
TILES_FILE = ROOT_DIR / "config" / "tiles.json"
MONSTERS_FILE = ROOT_DIR / "config" / "monsters.json"

MONSTERS_DB = {}
if MONSTERS_FILE.exists():
    with open(MONSTERS_FILE, "r", encoding="utf-8") as f:
        MONSTERS_DB = json.load(f)


class TransferRequest(BaseModel):
    target_map: str
    target_x: int
    target_y: int


class ObjectInteractRequest(BaseModel):
    map_id: str
    object_id: str
    action: str = "interact"


@app.get("/api/map/tiles")
async def get_tiles():
    """获取瓦片类型定义。"""
    if not TILES_FILE.exists():
        raise HTTPException(status_code=404, detail="瓦片配置文件不存在")
    with open(TILES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/map/{map_id}")
async def get_map(map_id: str):
    """获取地图数据。"""
    map_file = MAPS_DIR / f"{map_id}.json"
    if not map_file.exists():
        raise HTTPException(status_code=404, detail=f"地图 '{map_id}' 不存在")
    with open(map_file, "r", encoding="utf-8") as f:
        map_data = json.load(f)
    # 合并存档中的物件状态
    map_states = player_profile.map_states.get(map_id, {})
    object_states = map_states.get("objects", {})
    for obj in map_data.get("objects", []):
        if obj["id"] in object_states:
            obj["state"] = object_states[obj["id"]]
    return map_data


@app.post("/api/map/transfer")
async def transfer_map(req: TransferRequest):
    """地图切换（传送门）。"""
    map_file = MAPS_DIR / f"{req.target_map}.json"
    if not map_file.exists():
        raise HTTPException(status_code=404, detail=f"目标地图 '{req.target_map}' 不存在")
    # 保存当前地图状态
    player_profile.set_position(req.target_x, req.target_y)
    player_profile.current_map = req.target_map
    player_profile._save()
    # 返回目标地图数据
    with open(map_file, "r", encoding="utf-8") as f:
        map_data = json.load(f)
    return {"success": True, "map_data": map_data, "player_info": player_profile.get_info()}


@app.post("/api/map/object/interact")
async def interact_object(req: ObjectInteractRequest):
    """与地图物件交互。"""
    map_file = MAPS_DIR / f"{req.map_id}.json"
    if not map_file.exists():
        raise HTTPException(status_code=404, detail=f"地图 '{req.map_id}' 不存在")
    with open(map_file, "r", encoding="utf-8") as f:
        map_data = json.load(f)
    # 查找物件
    target_obj = None
    for obj in map_data.get("objects", []):
        if obj["id"] == req.object_id:
            target_obj = obj
            break
    if not target_obj:
        raise HTTPException(status_code=404, detail=f"物件 '{req.object_id}' 不存在")
    # 根据物件类型处理
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
            # 更新物件状态
            if req.map_id not in player_profile.map_states:
                player_profile.map_states[req.map_id] = {"objects": {}}
            player_profile.map_states[req.map_id]["objects"][req.object_id] = {"opened": True}
            player_profile._save()
            result["message"] = f"获得物品！"
            result["items"] = items
            # 任务进度：收集物品
            for item in items:
                quest_manager.on_collect(item["item_id"])
    elif obj_type == "gather":
        item_id = props.get("item_id")
        respawn_time = props.get("respawn_time", 60)
        if item_id:
            # 检查冷却时间
            if req.map_id in player_profile.map_states:
                obj_state = player_profile.map_states[req.map_id].get("objects", {}).get(req.object_id, {})
                last_gathered = obj_state.get("last_gathered", 0)
                import time
                current_time = int(time.time())
                if current_time - last_gathered < respawn_time:
                    remaining = respawn_time - (current_time - last_gathered)
                    result["success"] = False
                    result["message"] = f"采集点还在冷却中，还需等待 {remaining} 秒"
                    return result
            
            player_profile.add_item(item_id, 1)
            if req.map_id not in player_profile.map_states:
                player_profile.map_states[req.map_id] = {"objects": {}}
            import time
            player_profile.map_states[req.map_id]["objects"][req.object_id] = {"last_gathered": int(time.time())}
            player_profile._save()
            result["message"] = f"采集了 1 个物品。"
            quest_manager.on_collect(item_id)
    elif obj_type == "decoration":
        result["message"] = props.get("interact_text", "")
    else:
        result["message"] = "无法交互。"
    return result


# ===== NPC 服务接口 =====

@app.post("/api/npc/service/heal")
async def npc_heal_service(req: HealServiceRequest):
    """祭司/治疗师的服务：恢复生命、恢复魔法、解除异常。"""
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


@app.get("/api/npc/service/skills")
async def npc_available_skills(npc_id: str = "skill_master"):
    """获取导师可教授的技能列表。"""
    from skill_system import get_skill, can_learn_skill
    npc = get_npc(npc_id)
    cfg = npc.cfg
    services = cfg.get("services", {})

    if "learn_skill" not in services:
        return {"success": False, "message": "该NPC不提供技能教学服务"}

    # 获取所有技能书对应的技能
    shop_items = cfg.get("shop", {}).get("inventory", [])
    skill_ids = []
    for item in shop_items:
        item_id = item["item_id"]
        if item_id.startswith("scroll_"):
            effect = ITEM_EFFECTS.get(item_id)
            if effect and effect.get("type") == "learn_skill":
                skill_ids.append(effect["skill_id"])

    # 检查每个技能的学习条件
    available = []
    all_known = player_profile.skills + player_profile.learned_skills
    for sid in skill_ids:
        skill = get_skill(sid)
        if not skill:
            continue
        can_learn, reason = can_learn_skill(sid, player_profile.class_id, player_profile.level, all_known)
        # 计算学费（技能书价格 × 倍率）
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


@app.post("/api/npc/service/learn_skill")
async def npc_learn_skill(req: LearnSkillRequest):
    """向导师学习技能（无需技能书）。"""
    from skill_system import can_learn_skill, get_skill
    npc = get_npc(req.npc_id)
    cfg = npc.cfg
    services = cfg.get("services", {})

    if "learn_skill" not in services:
        return {"success": False, "message": "该NPC不提供技能教学服务"}

    skill = get_skill(req.skill_id)
    if not skill:
        return {"success": False, "message": "技能不存在"}

    # 计算学费
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

    # 扣除金币并学习技能
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


# ===== 天赋系统 =====

class TalentLearnRequest(BaseModel):
    talent_id: str

@app.get("/api/talents")
async def get_talents():
    return player_profile.get_talent_info()

@app.post("/api/talents/learn")
async def learn_talent(req: TalentLearnRequest):
    result = player_profile.learn_talent(req.talent_id)
    return result

@app.post("/api/talents/reset")
async def reset_talents():
    result = player_profile.reset_talents()
    return result


# ===== 任务系统 =====

class QuestAcceptRequest(BaseModel):
    quest_id: str

class QuestAbandonRequest(BaseModel):
    quest_id: str

class QuestCompleteRequest(BaseModel):
    quest_id: str

class QuestProgressRequest(BaseModel):
    event_type: str
    data: dict = {}


@app.get("/api/quests")
async def get_quests():
    return {"quests": quest_manager.get_all_quests()}


@app.get("/api/quests/active")
async def get_active_quests():
    return {"quests": quest_manager.get_active_quests()}


@app.get("/api/quests/npc/{npc_id}")
async def get_npc_quests(npc_id: str):
    return {"quests": quest_manager.get_npc_quests(npc_id)}


@app.post("/api/quests/accept")
async def accept_quest(req: QuestAcceptRequest):
    result = quest_manager.accept_quest(req.quest_id)
    if result["success"]:
        result["player_info"] = player_profile.get_info()
    return result


@app.post("/api/quests/abandon")
async def abandon_quest(req: QuestAbandonRequest):
    return quest_manager.abandon_quest(req.quest_id)


@app.post("/api/quests/complete")
async def complete_quest(req: QuestCompleteRequest):
    result = quest_manager.complete_quest(req.quest_id)
    if result["success"]:
        result["player_info"] = player_profile.get_info()
    return result


@app.post("/api/quests/progress")
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


# ===== 战斗系统 =====

from combat_engine import (
    create_combat_session, get_session, remove_session,
    resolve_turn, CombatPhase, cleanup_expired_sessions
)


@app.get("/api/monsters")
async def get_monsters_config():
    """返回所有怪物定义（供前端渲染使用）。"""
    return MONSTERS_DB


class CombatStartRequest(BaseModel):
    monster_instance_id: str
    map_id: str


class CombatActionRequest(BaseModel):
    session_id: str
    action: str
    item_id: str = None
    skill_id: str = None


class CombatEndRequest(BaseModel):
    session_id: str


@app.post("/api/combat/start")
async def combat_start(req: CombatStartRequest):
    """发起战斗。"""
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

    from skill_system import format_skill_for_frontend
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


@app.post("/api/combat/action")
async def combat_action(req: CombatActionRequest):
    """提交战斗动作。"""
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

        # Add item names to drops for frontend display
        for drop in state.get("drops", []):
            item_info = ITEMS_DB.get(drop["item_id"], {})
            drop["name"] = item_info.get("name", drop["item_id"])

        state["player_inventory"] = player_profile.get_inventory()
        state["player_gold"] = player_profile.gold

        # 任务进度：击杀怪物
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


@app.post("/api/combat/end")
async def combat_end(req: CombatEndRequest):
    """结束战斗会话。"""
    remove_session(req.session_id)
    player_profile._save()
    return {"success": True, "player_info": player_profile.get_info()}


# ===== 锻造系统接口 =====

class ForgeCraftRequest(BaseModel):
    recipe_id: str
    npc_id: str = "blacksmith"


@app.get("/api/forge/recipes")
async def get_forge_recipes(npc_id: str = "blacksmith"):
    from forge_system import get_all_recipes, get_recipes_by_category, format_recipe_for_frontend
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


@app.post("/api/forge/craft")
async def forge_craft(req: ForgeCraftRequest):
    from forge_system import execute_forge
    result = execute_forge(
        req.recipe_id, player_profile.level, player_profile.gold, player_profile.inventory
    )
    if result.player_inventory is not None:
        player_profile.inventory = result.player_inventory
    player_profile.gold = result.player_gold
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
    return response


# ===== 词条系统接口 =====

@app.get("/api/affixes/types")
async def get_affix_types():
    from affix_system import get_affix_categories
    return {"categories": get_affix_categories()}


# 挂载静态文件（放在路由之后）
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
