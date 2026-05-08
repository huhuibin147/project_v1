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
from item_system import Inventory, buy_item, sell_item, get_item_info, ITEMS_DB

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
            "greeting": cfg["greeting"],
        })
    return result


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    npc = get_npc(req.npc_id)
    result = npc.chat(req.message)
    return ChatResponse(**result)


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

    elif req.action == "sell":
        sell_price = item_info["sell_price"]
        if sell_price <= 0:
            return {"success": False, "message": "这东西俺不收。"}
        total = sell_price * req.quantity
        player_qty = player_profile.get_item_quantity(req.item_id)
        if player_qty < req.quantity:
            return {"success": False, "message": f"你没有那么多{item_info['name']}。你只有 {player_qty} 个。"}
        if npc.shop_inventory.gold < total:
            return {"success": False, "message": "俺手头紧，没那么多金币收你的货。"}

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
    """回复生命值。"""
    player_profile.heal(amount)
    return player_profile.get_info()


# ===== 存档管理接口 =====

@app.get("/api/saves")
async def list_saves():
    """获取所有存档槽信息。"""
    return player_profile.list_saves()


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
    return {"success": True, "player_info": player_profile.get_info()}


@app.post("/api/saves/load")
async def load_save(req: LoadSaveRequest):
    """读取存档。"""
    success = player_profile.load_from_slot(req.slot)
    if not success:
        raise HTTPException(status_code=400, detail="存档不存在或已损坏")
    # 清空旧的 NPC 实例，确保加载新存档数据
    npc_agents.clear()
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


# 挂载静态文件（放在路由之后）
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
