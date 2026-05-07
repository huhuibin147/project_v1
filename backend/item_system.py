import json
from pathlib import Path
from dataclasses import dataclass, field

CONFIG_DIR = Path(__file__).parent.parent / "config"
ITEMS_FILE = CONFIG_DIR / "items.json"


def load_items_config() -> dict:
    with open(ITEMS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


ITEMS_DB = load_items_config()


@dataclass
class Inventory:
    """背包：物品列表 + 金币。"""
    items: list[dict] = field(default_factory=list)  # [{item_id, quantity}]
    gold: int = 0

    def get_quantity(self, item_id: str) -> int:
        for item in self.items:
            if item["item_id"] == item_id:
                return item["quantity"]
        return 0

    def add_item(self, item_id: str, quantity: int = 1):
        for item in self.items:
            if item["item_id"] == item_id:
                item["quantity"] += quantity
                return
        self.items.append({"item_id": item_id, "quantity": quantity})

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        for item in self.items:
            if item["item_id"] == item_id:
                if item["quantity"] < quantity:
                    return False
                item["quantity"] -= quantity
                if item["quantity"] == 0:
                    self.items.remove(item)
                return True
        return False

    def to_list(self) -> list[dict]:
        """返回带物品详情的列表。"""
        result = []
        for item in self.items:
            item_id = item["item_id"]
            info = ITEMS_DB.get(item_id, {})
            result.append({
                "item_id": item_id,
                "name": info.get("name", item_id),
                "type": info.get("type", "unknown"),
                "description": info.get("description", ""),
                "quantity": item["quantity"],
                "buy_price": info.get("buy_price", 0),
                "sell_price": info.get("sell_price", 0),
            })
        return result

    def to_save(self) -> dict:
        return {"items": self.items, "gold": self.gold}

    @classmethod
    def from_save(cls, data: dict) -> "Inventory":
        return cls(items=data.get("items", []), gold=data.get("gold", 0))


@dataclass
class TradeResult:
    success: bool
    message: str
    player_inventory: Inventory = None
    npc_inventory: Inventory = None


def buy_item(player_inv: Inventory, npc_inv: Inventory,
             item_id: str, quantity: int = 1) -> TradeResult:
    """玩家从 NPC 商店购买物品。"""
    item_info = ITEMS_DB.get(item_id)
    if not item_info:
        return TradeResult(False, "这个东西俺这里没有。")

    buy_price = item_info["buy_price"]
    if buy_price <= 0:
        return TradeResult(False, "这个东西不卖的。")

    total = buy_price * quantity

    # 检查 NPC 库存
    npc_qty = npc_inv.get_quantity(item_id)
    if npc_qty < quantity:
        if npc_qty == 0:
            return TradeResult(False, f"俺这里没有足够的{item_info['name']}了。")
        return TradeResult(False, f"俺这里只剩 {npc_qty} 个{item_info['name']}了。")

    # 检查玩家金币
    if player_inv.gold < total:
        return TradeResult(False, f"你的金币不够！需要 {total} 金币，你只有 {player_inv.gold}。")

    # 执行交易
    player_inv.gold -= total
    player_inv.add_item(item_id, quantity)
    npc_inv.gold += total
    npc_inv.remove_item(item_id, quantity)

    return TradeResult(
        True,
        f"好嘞！{quantity} 个{item_info['name']}，收你 {total} 金币。",
        player_inv,
        npc_inv,
    )


def sell_item(player_inv: Inventory, npc_inv: Inventory,
              item_id: str, quantity: int = 1) -> TradeResult:
    """玩家向 NPC 出售物品。"""
    item_info = ITEMS_DB.get(item_id)
    if not item_info:
        return TradeResult(False, "这是啥东西？俺不认识。")

    sell_price = item_info["sell_price"]
    if sell_price <= 0:
        return TradeResult(False, "这东西俺不收。")

    # 检查玩家库存
    player_qty = player_inv.get_quantity(item_id)
    if player_qty < quantity:
        return TradeResult(False, f"你没有那么多{item_info['name']}。你只有 {player_qty} 个。")

    # 检查 NPC 金币
    total = sell_price * quantity
    if npc_inv.gold < total:
        return TradeResult(False, f"俺手头紧，没那么多金币收你的货。")

    # 执行交易
    player_inv.gold += total
    player_inv.remove_item(item_id, quantity)
    npc_inv.gold -= total
    npc_inv.add_item(item_id, quantity)

    return TradeResult(
        True,
        f"行！{quantity} 个{item_info['name']}，给你 {total} 金币。",
        player_inv,
        npc_inv,
    )


def get_item_info(item_id: str) -> dict | None:
    """查询物品信息。"""
    return ITEMS_DB.get(item_id)
