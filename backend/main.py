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

app = FastAPI(title="LLM NPC Game")

FRONTEND_DIR = str(ROOT_DIR / "frontend")

# 多 NPC 实例管理
npc_agents: dict[str, NPCAgent] = {}


def get_npc(npc_id: str) -> NPCAgent:
    """获取或创建 NPC Agent 实例。"""
    if npc_id not in npc_agents:
        npc_agents[npc_id] = NPCAgent(npc_id)
    return npc_agents[npc_id]


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
async def get_inventory(npc_id: str = "blacksmith"):
    """获取玩家背包（每个 NPC 独立存档，背包数据跟着 NPC 走）。"""
    npc = get_npc(npc_id)
    return {
        "items": npc.player_inventory.to_list(),
        "gold": npc.player_inventory.gold,
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
    """直接交易接口。"""
    from item_system import buy_item, sell_item
    npc = get_npc(req.npc_id)
    if req.action == "buy":
        result = buy_item(npc.player_inventory, npc.shop_inventory, req.item_id, req.quantity)
    elif req.action == "sell":
        result = sell_item(npc.player_inventory, npc.shop_inventory, req.item_id, req.quantity)
    else:
        return {"success": False, "message": "未知交易类型"}
    return {
        "success": result.success,
        "message": result.message,
        "player_inventory": npc.player_inventory.to_list(),
        "player_gold": npc.player_inventory.gold,
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


# 挂载静态文件（放在路由之后）
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
