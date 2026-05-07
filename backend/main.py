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

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from npc_agent import npc, load_npc_config

app = FastAPI(title="LLM NPC Game")

# 静态文件服务
FRONTEND_DIR = str(ROOT_DIR / "frontend")


class ChatRequest(BaseModel):
    message: str


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


@app.get("/")
async def index():
    return FileResponse(f"{FRONTEND_DIR}/index.html")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = npc.chat(req.message)
    return ChatResponse(**result)


@app.get("/api/npc/status")
async def npc_status():
    return npc.get_status()


@app.get("/api/npc/config")
async def npc_config():
    """返回当前 NPC 的配置信息（前端用）。"""
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
    """获取玩家背包。"""
    return {
        "items": npc.player_inventory.to_list(),
        "gold": npc.player_inventory.gold,
    }


@app.get("/api/shop")
async def get_shop():
    """获取 NPC 商店库存。"""
    return {
        "name": npc.cfg.get("shop", {}).get("name", npc.name + "的商店"),
        "items": npc.shop_inventory.to_list(),
        "gold": npc.shop_inventory.gold,
    }


@app.post("/api/trade")
async def trade(req: TradeRequest):
    """直接交易接口（不经过 LLM）。"""
    from item_system import buy_item, sell_item
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


# 挂载静态文件（放在路由之后）
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
