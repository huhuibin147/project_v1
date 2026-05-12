"""本地意图分类器 - 基于规则和关键词匹配"""

INTENT_RULES = {
    "trade": {
        "buy_keywords": ["买", "购买", "我要买", "给我来", "多少钱", "价格", "贵", "便宜"],
        "sell_keywords": ["卖", "出售", "我要卖", "卖给你", "收购", "换钱"],
    },
    "quest": {
        "keywords": ["任务", "帮忙", "需要", "委托", "工作", "悬赏", "求助", "有什么事"],
    },
    "chat": {
        "keywords": ["你好", "hello", "嗨", "最近怎么样", "你是谁", "介绍", "聊聊", "在吗", "早上好", "晚上好"],
    },
}


def classify_intent(player_input: str) -> str:
    """
    根据关键词和规则分类玩家意图
    
    返回: "trade", "quest", "chat", 或 "unknown"
    """
    input_lower = player_input.lower()
    
    # 交易意图检测（优先级最高）
    for keyword in INTENT_RULES["trade"]["buy_keywords"]:
        if keyword in input_lower:
            return "trade"
    for keyword in INTENT_RULES["trade"]["sell_keywords"]:
        if keyword in input_lower:
            return "trade"
    
    # 任务意图检测
    for keyword in INTENT_RULES["quest"]["keywords"]:
        if keyword in input_lower:
            return "quest"
    
    # 闲聊意图检测
    for keyword in INTENT_RULES["chat"]["keywords"]:
        if keyword in input_lower:
            return "chat"
    
    return "unknown"


def extract_trade_action(player_input: str, shop_item_ids: list[str], player_inventory: list[dict]) -> dict | None:
    """
    从交易意图中提取具体的交易动作
    
    返回: {"action": "buy"|"sell", "item_id": str, "quantity": int} 或 None
    """
    input_lower = player_input.lower()
    
    # 检测购买意图
    for keyword in INTENT_RULES["trade"]["buy_keywords"]:
        if keyword in input_lower:
            # 尝试匹配物品
            for item_id in shop_item_ids:
                if item_id in input_lower:
                    # 提取数量（默认为 1）
                    quantity = 1
                    for num in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                        if num in input_lower:
                            quantity = int(num)
                            break
                    
                    return {"action": "buy", "item_id": item_id, "quantity": quantity}
    
    # 检测出售意图
    for keyword in INTENT_RULES["trade"]["sell_keywords"]:
        if keyword in input_lower:
            # 尝试匹配玩家背包中的物品
            player_item_ids = [item["item_id"] for item in player_inventory]
            for item_id in player_item_ids:
                if item_id in input_lower:
                    quantity = 1
                    for num in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                        if num in input_lower:
                            quantity = int(num)
                            break
                    
                    return {"action": "sell", "item_id": item_id, "quantity": quantity}
    
    return None
