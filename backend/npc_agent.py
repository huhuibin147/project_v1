import json
from pathlib import Path
from llm_client import chat_completion
from item_system import Inventory, buy_item, sell_item, get_item_info, ITEMS_DB
from player_profile import player as player_profile

MAX_HISTORY = 10
DATA_DIR = Path(__file__).parent.parent / "data"
NPC_CONFIG_FILE = Path(__file__).parent.parent / "config" / "npcs.json"

INTENT_OPTIONS = """
意图说明：
- chat：闲聊、打招呼、问你个人的事情
- quest：玩家想接任务、问有没有需要帮忙的
- trade：玩家想买卖物品
- unknown：无法判断意图"""

RESPONSE_FORMAT = """
请严格按以下 JSON 格式回复（不要输出 JSON 以外的内容）：
{{
  "reply": "你的对话回复（1-3句话，保持角色一致性）",
  "intent": "chat 或 quest 或 trade 或 unknown",
  "mood": "当前你的情绪",
  "affinity_change": 好感度变化整数值(-10 到 +10),
  "trade_action": null 或 {{"action": "buy" 或 "sell", "item_id": "物品ID", "quantity": 数量}}
}}

trade_action 说明：
- 当玩家明确要购买某样物品时，填 {{"action": "buy", "item_id": "物品ID", "quantity": 数量}}
- 当玩家明确要出售某样物品时，填 {{"action": "sell", "item_id": "物品ID", "quantity": 数量}}
- 如果不是交易意图，填 null
- item_id 必须是以下物品之一：{item_ids}
"""


def load_npc_config(npc_id: str) -> dict:
    with open(NPC_CONFIG_FILE, "r", encoding="utf-8") as f:
        all_npcs = json.load(f)
    if npc_id not in all_npcs:
        raise ValueError(f"NPC '{npc_id}' 不存在于 npcs.json 中")
    return all_npcs[npc_id]


def build_system_prompt(cfg: dict, mood: str, affinity: int,
                        history_text: str, shop_info: str,
                        shop_item_ids: list[str]) -> str:
    p = cfg["personality"]

    pp = cfg.get("personality_params", {})
    params_desc = ""
    if pp:
        parts = []
        if "friendliness" in pp:
            parts.append(f"友善度={pp['friendliness']}")
        if "courage" in pp:
            parts.append(f"勇气={pp['courage']}")
        if "greed" in pp:
            parts.append(f"贪婪度={pp['greed']}")
        if "humor" in pp:
            parts.append(f"幽默感={pp['humor']}")
        params_desc = f"\n性格参数：{', '.join(parts)}"

    # 只列出该 NPC 自己卖的物品 ID
    item_ids = ", ".join(shop_item_ids) if shop_item_ids else "（无商品）"

    prompt = f"""你是{cfg['name']}，身份是{cfg['role']}，位于{cfg['location']}。
性格：{p['traits']}，喜欢用"{p['pronoun']}"自称。
说话风格：{p['style']}。
喜欢：{p['likes']}。讨厌：{p['dislikes']}。
背景：{cfg['backstory']}{params_desc}

当前状态：
- 情绪：{mood}
- 对玩家好感度：{affinity}/100

你的商店信息：
{shop_info}

注意：你只卖上面列出的物品。如果玩家要买你没有的东西，请告诉他你这里没有。
你也可以收购玩家手里的物品，但价格要合理。

玩家和你的对话历史：
{history_text if history_text else "（第一次对话）"}
{RESPONSE_FORMAT.format(item_ids=item_ids)}
{INTENT_OPTIONS}"""

    return prompt


class NPCAgent:
    def __init__(self, npc_id: str = "blacksmith"):
        self.npc_id = npc_id
        self.cfg = load_npc_config(npc_id)
        self.name = self.cfg["name"]
        self.mood = self.cfg.get("default_mood", "平静")
        self.affinity = self.cfg.get("default_affinity", 50)
        self.history: list[dict] = []
        self._save_file = DATA_DIR / f"{npc_id}_save.json"

        # 物品系统：NPC 商店库存和玩家背包
        self.shop_inventory = self._init_shop_inventory()
        self.acquired_inventory = Inventory(gold=0)  # 从玩家处收购的物品，独立存放

        self._load()

    def _init_shop_inventory(self) -> Inventory:
        """从 NPC 配置初始化商店库存。"""
        shop_cfg = self.cfg.get("shop", {})
        inv = Inventory(gold=shop_cfg.get("gold", 0))
        for slot in shop_cfg.get("inventory", []):
            inv.add_item(slot["item_id"], slot["quantity"])
        return inv

    def _save(self):
        DATA_DIR.mkdir(exist_ok=True)
        data = {
            "npc_id": self.npc_id,
            "name": self.name,
            "mood": self.mood,
            "affinity": self.affinity,
            "history": self.history,
            "shop_inventory": self.shop_inventory.to_save(),
            "acquired_inventory": self.acquired_inventory.to_save(),
        }
        with open(self._save_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self):
        if not self._save_file.exists():
            return
        try:
            with open(self._save_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.mood = data.get("mood", self.mood)
            self.affinity = data.get("affinity", self.affinity)
            self.history = data.get("history", [])
            if "shop_inventory" in data:
                self.shop_inventory = Inventory.from_save(data["shop_inventory"])
            if "acquired_inventory" in data:
                self.acquired_inventory = Inventory.from_save(data["acquired_inventory"])
        except (json.JSONDecodeError, KeyError):
            pass

    def _get_shop_info(self) -> str:
        """生成商店库存描述，注入 LLM 上下文。"""
        items = self.shop_inventory.to_list()
        if not items:
            return "（商店暂时没有货物）"
        lines = []
        for item in items:
            lines.append(f"- {item['name']}（{item['item_id']}）：{item['quantity']} 个，售价 {item['buy_price']} 金币，收购价 {item['sell_price']} 金币")
        return "\n".join(lines)

    def _build_messages(self, player_input: str) -> list[dict]:
        history_text = ""
        for h in self.history[-MAX_HISTORY * 2:]:
            role = "玩家" if h["role"] == "player" else self.name
            history_text += f"{role}：{h['content']}\n"

        shop_info = self._get_shop_info()
        # 只传入该 NPC 商店实际有的物品 ID
        shop_item_ids = [item["item_id"] for item in self.shop_inventory.items]
        system = build_system_prompt(self.cfg, self.mood, self.affinity,
                                     history_text, shop_info, shop_item_ids)
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": player_input},
        ]

    def _try_trade(self, trade_action: dict | None) -> str | None:
        """尝试执行交易，使用全局玩家背包，返回结果消息或 None。"""
        if not trade_action:
            return None

        action = trade_action.get("action")
        item_id = trade_action.get("item_id")
        quantity = trade_action.get("quantity", 1)

        if not item_id:
            return None

        item_info = ITEMS_DB.get(item_id)
        if not item_info:
            return None

        if action == "buy":
            buy_price = item_info["buy_price"]
            if buy_price <= 0:
                return "这个东西不卖的。"
            total = buy_price * quantity
            npc_qty = self.shop_inventory.get_quantity(item_id)
            if npc_qty < quantity:
                return f"俺这里只剩 {npc_qty} 个{item_info['name']}了。"
            if player_profile.gold < total:
                return f"你的金币不够！需要 {total} 金币，你只有 {player_profile.gold}。"
            player_profile.spend_gold(total)
            player_profile.add_item(item_id, quantity)
            self.shop_inventory.gold += total
            self.shop_inventory.remove_item(item_id, quantity)
            return f"好嘞！{quantity} 个{item_info['name']}，收你 {total} 金币。"

        elif action == "sell":
            sell_price = item_info["sell_price"]
            if sell_price <= 0:
                return "这东西俺不收。"
            total = sell_price * quantity
            player_qty = player_profile.get_item_quantity(item_id)
            if player_qty < quantity:
                return f"你没有那么多{item_info['name']}。你只有 {player_qty} 个。"
            if self.shop_inventory.gold < total:
                return "俺手头紧，没那么多金币收你的货。"
            player_profile.add_gold(total)
            player_profile.remove_item(item_id, quantity)
            self.shop_inventory.gold -= total
            self.acquired_inventory.add_item(item_id, quantity)
            return f"行！{quantity} 个{item_info['name']}，给你 {total} 金币。"

        return None

    def chat(self, player_input: str) -> dict:
        messages = self._build_messages(player_input)
        raw = chat_completion(messages, temperature=0.8)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(raw[start:end])
            else:
                data = {
                    "reply": raw.strip()[:200],
                    "intent": "unknown",
                    "mood": self.mood,
                    "affinity_change": 0,
                    "trade_action": None,
                }

        self.mood = data.get("mood", self.mood)
        change = data.get("affinity_change", 0)
        self.affinity = max(0, min(100, self.affinity + change))

        # 尝试执行交易
        trade_action = data.get("trade_action")
        trade_message = self._try_trade(trade_action)

        # 如果交易成功，将交易结果附加到回复中
        reply = data["reply"]
        if trade_message:
            reply = f"{reply}\n【{trade_message}】"

        self.history.append({"role": "player", "content": player_input})
        self.history.append({"role": "npc", "content": reply})
        self._save()

        return {
            "reply": reply,
            "intent": data.get("intent", "unknown"),
            "mood": self.mood,
            "affinity": self.affinity,
            "trade": trade_action is not None and trade_message is not None,
            "player_inventory": player_profile.get_inventory(),
            "player_gold": player_profile.gold,
            "shop_inventory": self.shop_inventory.to_list(),
            "shop_gold": self.shop_inventory.gold,
        }

    def get_status(self) -> dict:
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "mood": self.mood,
            "affinity": self.affinity,
            "personality": self.cfg.get("personality_params", {}),
            "player_gold": player_profile.gold,
            "shop_gold": self.shop_inventory.gold,
        }
