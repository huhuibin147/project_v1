import sys
import shutil
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / "config.json"
EXAMPLE_PATH = ROOT_DIR / "config.json.example"


def ensure_config():
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
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError

from routes.context import player_profile, npc_agents, sync_npc_slots
from routes.models import (
    ChatRequest, TradeRequest, PlayerUpdateRequest, NewGameRequest,
    LoadSaveRequest, EquipRequest, UnequipRequest, UseItemRequest,
    HealServiceRequest, LearnSkillRequest, PositionRequest,
    TransferRequest, ObjectInteractRequest, TalentLearnRequest,
    QuestAcceptRequest, QuestAbandonRequest, QuestCompleteRequest,
    QuestProgressRequest, CombatStartRequest, CombatActionRequest,
    CombatEndRequest, ForgeCraftRequest,
)
from routes.npc import router as npc_router
from routes.player import router as player_router
from routes.map import router as map_router
from routes.combat import router as combat_router
from routes.forge import router as forge_router
from routes.quest import router as quest_router

app = FastAPI(title="LLM NPC Game")

FRONTEND_DIR = str(ROOT_DIR / "frontend")
DATA_DIR = ROOT_DIR / "data"


def migrate_old_saves():
    DATA_DIR.mkdir(exist_ok=True)
    from npc_agent import NPC_CONFIG_FILE
    with open(NPC_CONFIG_FILE, "r", encoding="utf-8") as f:
        npc_ids = list(json.load(f).keys())

    for slot in range(1, 4):
        folder = DATA_DIR / f"save_{slot}"
        if folder.exists():
            continue
        old_player = DATA_DIR / f"save_{slot}.json"
        if not old_player.exists():
            continue
        folder.mkdir(parents=True, exist_ok=True)
        old_player.rename(folder / "player.json")
        for npc_id in npc_ids:
            old_npc = DATA_DIR / f"save_{slot}_{npc_id}.json"
            if old_npc.exists():
                old_npc.rename(folder / f"{npc_id}.json")

    folder_1 = DATA_DIR / "save_1"
    from npc_agent import NPC_CONFIG_FILE
    with open(NPC_CONFIG_FILE, "r", encoding="utf-8") as f:
        npc_ids = list(json.load(f).keys())
    for npc_id in npc_ids:
        legacy_npc = DATA_DIR / f"{npc_id}_save.json"
        if legacy_npc.exists():
            target = folder_1 / f"{npc_id}.json"
            if not target.exists():
                folder_1.mkdir(parents=True, exist_ok=True)
                legacy_npc.rename(target)


migrate_old_saves()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return {
        "success": False,
        "error": "validation_error",
        "detail": exc.errors(),
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "success": False,
        "error": "internal_error",
        "message": "服务器内部错误",
    }


app.include_router(npc_router)
app.include_router(player_router)
app.include_router(map_router)
app.include_router(combat_router)
app.include_router(forge_router)
app.include_router(quest_router)


@app.get("/")
async def index():
    return FileResponse(f"{FRONTEND_DIR}/index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
