"""Shared application context for route modules."""

import json
from pathlib import Path

from npc_agent import NPCAgent, NPC_CONFIG_FILE
from player_profile import player as player_profile
from item_system import Inventory, buy_item, sell_item, get_item_info, ITEMS_DB, ITEM_EFFECTS
from skill_system import format_skill_for_frontend
from quest_manager import QuestManager

quest_manager = QuestManager(player_profile)

npc_agents: dict[str, NPCAgent] = {}


def get_npc(npc_id: str) -> NPCAgent:
    if npc_id not in npc_agents:
        slot = player_profile.current_slot
        npc_agents[npc_id] = NPCAgent(npc_id, slot=slot)
    return npc_agents[npc_id]


def sync_npc_slots():
    slot = player_profile.current_slot
    for npc_id, npc in npc_agents.items():
        npc.set_slot(slot)


def get_all_npc_ids() -> list[str]:
    with open(NPC_CONFIG_FILE, "r", encoding="utf-8") as f:
        return list(json.load(f).keys())
