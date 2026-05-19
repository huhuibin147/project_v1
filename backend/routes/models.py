"""Pydantic models for API request/response validation."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    npc_id: str = "blacksmith"


class TradeRequest(BaseModel):
    action: str
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
    service_type: str


class LearnSkillRequest(BaseModel):
    npc_id: str
    skill_id: str


class PositionRequest(BaseModel):
    x: int
    y: int


class TransferRequest(BaseModel):
    target_map: str
    target_x: int
    target_y: int


class ObjectInteractRequest(BaseModel):
    map_id: str
    object_id: str
    action: str = "interact"


class TalentLearnRequest(BaseModel):
    talent_id: str


class QuestAcceptRequest(BaseModel):
    quest_id: str


class QuestAbandonRequest(BaseModel):
    quest_id: str


class QuestCompleteRequest(BaseModel):
    quest_id: str


class QuestProgressRequest(BaseModel):
    event_type: str
    data: dict = {}


class CombatStartRequest(BaseModel):
    monster_instance_id: str = None
    monster_group_id: str = None
    map_id: str


class CombatActionRequest(BaseModel):
    session_id: str
    action: str
    item_id: str = None
    skill_id: str = None
    target_index: int = None


class CombatEndRequest(BaseModel):
    session_id: str


class ForgeCraftRequest(BaseModel):
    recipe_id: str
    npc_id: str = "blacksmith"


class ForgeRerollRequest(BaseModel):
    item_id: str
    slot: str


class GenericServiceRequest(BaseModel):
    npc_id: str
    service_type: str


class ExploredTilesRequest(BaseModel):
    map_id: str
    tiles: list[str]
