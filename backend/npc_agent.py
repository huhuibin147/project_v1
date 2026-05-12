import json
from pathlib import Path
from llm_client import chat_completion
from item_system import Inventory, buy_item, sell_item, get_item_info, ITEMS_DB
from player_profile import player as player_profile
from intent_classifier import classify_intent, extract_trade_action
from npc_memory import MemoryManager
from npc_affinity import AffinitySystem
from npc_cache import ResponseCache

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

trade_action 详细说明：
1. 当玩家明确要购买物品时（例如："我要买xxx"、"给我来个xxx"、"买xxx"），填写：
   {{"action": "buy", "item_id": "物品ID", "quantity": 数量}}
   
2. 当玩家明确要出售物品给你时（例如："我要卖xxx"、"这个xxx卖给你"、"卖xxx"），填写：
   {{"action": "sell", "item_id": "物品ID", "quantity": 数量}}
   
3. 如果玩家只是在询问价格、查看商品、或者没有明确买卖意图，填写：null

重要规则：
- 只有当玩家明确说出"买"或"卖"时才填写trade_action
- 购买时，item_id 必须是你商店里有的物品：{item_ids}
- 出售时，item_id 必须是玩家背包里有的物品（见上方玩家背包信息）
- quantity 默认为1，如果玩家明确说了数量则使用该数量
- 如果玩家要买你没有的物品，在reply中告诉他你没有，trade_action填null
- 如果玩家要卖他背包里没有的物品，在reply中告诉他没有这个物品，trade_action填null

示例：
玩家："我要买一把铁剑" -> trade_action: {{"action": "buy", "item_id": "iron_sword", "quantity": 1}}
玩家："给我来3个生命药水" -> trade_action: {{"action": "buy", "item_id": "health_potion", "quantity": 3}}
玩家："我想卖给你一个草药" -> trade_action: {{"action": "sell", "item_id": "herb", "quantity": 1}}
玩家："你这里有什么？" -> trade_action: null
玩家："铁剑多少钱？" -> trade_action: null
"""


def load_npc_config(npc_id: str) -> dict:
    with open(NPC_CONFIG_FILE, "r", encoding="utf-8") as f:
        all_npcs = json.load(f)
    if npc_id not in all_npcs:
        raise ValueError(f"NPC '{npc_id}' 不存在于 npcs.json 中")
    return all_npcs[npc_id]


def build_system_prompt(cfg: dict, mood: str, affinity: int, affinity_context: str,
                        history_text: str, long_term_context: str, shop_info: str,
                        shop_item_ids: list[str], player_inventory: list[dict] = None) -> str:
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

    item_ids = ", ".join(shop_item_ids) if shop_item_ids else "（无商品）"
    
    player_items_info = ""
    if player_inventory:
        player_items = []
        for item in player_inventory:
            player_items.append(f"{item['name']}({item['item_id']}): {item['quantity']}个")
        player_items_info = f"\n玩家背包里的物品：\n{chr(10).join(player_items)}"

    prompt = f"""你是{cfg['name']}，身份是{cfg['role']}，位于{cfg['location']}。
性格：{p['traits']}，喜欢用"{p['pronoun']}"自称。
说话风格：{p['style']}。
喜欢：{p['likes']}。讨厌：{p['dislikes']}。
背景：{cfg['backstory']}{params_desc}

当前状态：
- 情绪：{mood}
- 对玩家好感度：{affinity}/100
- {affinity_context}

你的商店信息：
{shop_info}

注意：你只卖上面列出的物品。如果玩家要买你没有的东西，请告诉他你这里没有。
你也可以收购玩家手里的物品，但价格要合理。
{player_items_info}

{long_term_context}

玩家和你的对话历史：
{history_text if history_text else "（第一次对话）"}
{RESPONSE_FORMAT.format(item_ids=item_ids)}
{INTENT_OPTIONS}"""

    return prompt


class NPCAgent:
    def __init__(self, npc_id: str = "blacksmith", slot: int = None):
        self.npc_id = npc_id
        self.cfg = load_npc_config(npc_id)
        self.name = self.cfg["name"]
        self.mood = self.cfg.get("default_mood", "平静")
        self.slot = slot
        self._update_save_file()

        # 物品系统：NPC 商店库存和玩家背包
        self.shop_inventory = self._init_shop_inventory()
        self.acquired_inventory = Inventory(gold=0)

        # 优化模块
        self.memory = MemoryManager()
        self.affinity_system = AffinitySystem(self.cfg.get("default_affinity", 50))
        self.response_cache = ResponseCache()

        self._load()

    def _update_save_file(self):
        """根据存档槽更新保存文件路径。"""
        if self.slot is not None:
            self._save_file = DATA_DIR / f"save_{self.slot}" / f"{self.npc_id}.json"
        else:
            self._save_file = DATA_DIR / f"{self.npc_id}_save.json"

    def set_slot(self, slot: int):
        """切换存档槽。"""
        self.slot = slot
        self._update_save_file()
        # 重置状态并加载新存档
        self.mood = self.cfg.get("default_mood", "平静")
        self.shop_inventory = self._init_shop_inventory()
        self.acquired_inventory = Inventory(gold=0)
        self.memory = MemoryManager()
        self.affinity_system = AffinitySystem(self.cfg.get("default_affinity", 50))
        self.response_cache = ResponseCache()
        self._load()

    def _init_shop_inventory(self) -> Inventory:
        """从 NPC 配置初始化商店库存。"""
        shop_cfg = self.cfg.get("shop", {})
        inv = Inventory(gold=shop_cfg.get("gold", 0))
        for slot in shop_cfg.get("inventory", []):
            inv.add_item(slot["item_id"], slot["quantity"])
        return inv

    def _save(self):
        self._save_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "npc_id": self.npc_id,
            "name": self.name,
            "mood": self.mood,
            "affinity": self.affinity_system.affinity,
            "history": self.memory.short_term_memory,
            "shop_inventory": self.shop_inventory.to_save(),
            "acquired_inventory": self.acquired_inventory.to_save(),
            "memory": self.memory.to_save(),
            "response_cache": self.response_cache.to_save(),
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
            self.affinity_system.affinity = data.get("affinity", self.affinity_system.affinity)
            if "history" in data:
                self.memory.short_term_memory = data.get("history", [])
            if "shop_inventory" in data:
                self.shop_inventory = Inventory.from_save(data["shop_inventory"])
                self._merge_new_shop_items()
            if "acquired_inventory" in data:
                self.acquired_inventory = Inventory.from_save(data["acquired_inventory"])
            if "memory" in data:
                self.memory.from_save(data["memory"])
            if "response_cache" in data:
                self.response_cache.from_save(data["response_cache"])
        except (json.JSONDecodeError, KeyError):
            pass

    def _merge_new_shop_items(self):
        saved_ids = {item["item_id"] for item in self.shop_inventory.items}
        shop_cfg = self.cfg.get("shop", {})
        for slot in shop_cfg.get("inventory", []):
            if slot["item_id"] not in saved_ids:
                self.shop_inventory.add_item(slot["item_id"], slot["quantity"])

    def _get_shop_info(self) -> str:
        """生成商店库存描述，注入 LLM 上下文。"""
        items = self.shop_inventory.to_list()
        if not items:
            return "（商店暂时没有货物）"
        lines = []
        for item in items:
            discount = self.affinity_system.get_discount_multiplier()
            buy_price = int(item["buy_price"] * discount)
            lines.append(f"- {item['name']}（{item['item_id']}）：{item['quantity']} 个，售价 {buy_price} 金币，收购价 {item['sell_price']} 金币")
        return "\n".join(lines)

    def _build_messages(self, player_input: str) -> list[dict]:
        history_text = self.memory.get_short_term_history()
        long_term_context = self.memory.get_long_term_context()
        affinity_context = self.affinity_system.get_context_description()

        shop_info = self._get_shop_info()
        shop_item_ids = [item["item_id"] for item in self.shop_inventory.items]
        player_inventory = player_profile.get_inventory()
        system = build_system_prompt(self.cfg, self.mood, self.affinity_system.affinity,
                                     affinity_context, history_text, long_term_context,
                                     shop_info, shop_item_ids, player_inventory)
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
            discount = self.affinity_system.get_discount_multiplier()
            buy_price = int(item_info["buy_price"] * discount)
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
            
            discount_text = f"（给你打了折，原价 {item_info['buy_price'] * quantity}，现价 {total}）" if discount < 1.0 else ""
            return f"好嘞！{quantity} 个{item_info['name']}，收你 {total} 金币。{discount_text}"

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
        # 1. 本地意图分类
        local_intent = classify_intent(player_input)
        
        # 2. 检查缓存（仅对闲聊意图）
        if local_intent == "chat":
            affinity_level = self.affinity_system.get_level()
            cached_response = self.response_cache.get(player_input, affinity_level)
            if cached_response:
                self.memory.add_short_term("player", player_input)
                self.memory.add_short_term("npc", cached_response)
                self._save()
                return {
                    "reply": cached_response,
                    "intent": "chat",
                    "mood": self.mood,
                    "affinity": self.affinity_system.affinity,
                    "trade": False,
                    "player_inventory": player_profile.get_inventory(),
                    "player_gold": player_profile.gold,
                    "shop_inventory": self.shop_inventory.to_list(),
                    "shop_gold": self.shop_inventory.gold,
                    "cached": True,
                }
        
        # 3. 如果是交易意图，尝试直接处理
        if local_intent == "trade":
            shop_item_ids = [item["item_id"] for item in self.shop_inventory.items]
            player_inventory = player_profile.get_inventory()
            trade_action = extract_trade_action(player_input, shop_item_ids, player_inventory)
            
            if trade_action:
                trade_message = self._try_trade(trade_action)
                if trade_message:
                    reply = trade_message
                    self.memory.add_short_term("player", player_input)
                    self.memory.add_short_term("npc", reply)
                    self.memory.add_long_term("trade_completed", f"玩家{trade_action['action']}了{trade_action['quantity']}个{trade_action['item_id']}", importance=2)
                    self._save()
                    return {
                        "reply": reply,
                        "intent": "trade",
                        "mood": self.mood,
                        "affinity": self.affinity_system.affinity,
                        "trade": True,
                        "player_inventory": player_profile.get_inventory(),
                        "player_gold": player_profile.gold,
                        "shop_inventory": self.shop_inventory.to_list(),
                        "shop_gold": self.shop_inventory.gold,
                        "cached": False,
                    }
        
        # 4. 调用 LLM（复杂对话）
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
                    "intent": local_intent if local_intent != "unknown" else "unknown",
                    "mood": self.mood,
                    "affinity_change": 0,
                    "trade_action": None,
                }

        self.mood = data.get("mood", self.mood)
        change = data.get("affinity_change", 0)
        self.affinity_system.update_affinity(change)

        # 尝试执行交易
        trade_action = data.get("trade_action")
        trade_message = self._try_trade(trade_action)

        reply = data["reply"]
        if trade_message:
            reply = f"{reply}\n【{trade_message}】"

        self.memory.add_short_term("player", player_input)
        self.memory.add_short_term("npc", reply)
        
        # 记录长期记忆
        intent = data.get("intent", "unknown")
        if intent == "quest":
            self.memory.add_long_term("quest_topic", f"玩家询问任务相关：{player_input[:50]}", importance=3)
        elif trade_action:
            self.memory.add_long_term("trade_completed", f"玩家{trade_action.get('action', 'unknown')}了{trade_action.get('quantity', 1)}个{trade_action.get('item_id', 'unknown')}", importance=2)
        
        # 缓存闲聊回答
        if intent == "chat":
            affinity_level = self.affinity_system.get_level()
            self.response_cache.put(player_input, affinity_level, reply)

        self._save()

        return {
            "reply": reply,
            "intent": intent,
            "mood": self.mood,
            "affinity": self.affinity_system.affinity,
            "trade": trade_action is not None and trade_message is not None,
            "player_inventory": player_profile.get_inventory(),
            "player_gold": player_profile.gold,
            "shop_inventory": self.shop_inventory.to_list(),
            "shop_gold": self.shop_inventory.gold,
            "cached": False,
        }

    def get_status(self) -> dict:
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "mood": self.mood,
            "affinity": self.affinity_system.affinity,
            "affinity_level": self.affinity_system.get_level(),
            "affinity_style": self.affinity_system.get_dialog_style(),
            "discount_multiplier": self.affinity_system.get_discount_multiplier(),
            "personality": self.cfg.get("personality_params", {}),
            "player_gold": player_profile.gold,
            "shop_gold": self.shop_inventory.gold,
            "memory_count": len(self.memory.long_term_memory),
        }
