"""NPC 好感度系统"""


class AffinitySystem:
    """管理 NPC 好感度及其影响"""
    
    # 好感度等级
    AFFINITY_LEVELS = [
        (0, 20, "敌对", 1.2, "冷淡敌视"),
        (21, 40, "冷淡", 1.1, "态度冷淡"),
        (41, 60, "中性", 1.0, "公事公办"),
        (61, 80, "友善", 0.9, "热情友好"),
        (81, 100, "亲密", 0.8, "非常亲近"),
    ]
    
    def __init__(self, initial_affinity: int = 50):
        self.affinity = max(0, min(100, initial_affinity))
    
    def update_affinity(self, change: int) -> int:
        """更新好感度，返回变化后的值"""
        self.affinity = max(0, min(100, self.affinity + change))
        return self.affinity
    
    def get_level(self) -> str:
        """获取好感度等级名称"""
        for min_val, max_val, name, _, _ in self.AFFINITY_LEVELS:
            if min_val <= self.affinity <= max_val:
                return name
        return "中性"
    
    def get_dialog_style(self) -> str:
        """获取对话风格描述"""
        for min_val, max_val, _, _, style in self.AFFINITY_LEVELS:
            if min_val <= self.affinity <= max_val:
                return style
        return "公事公办"
    
    def get_discount_multiplier(self) -> float:
        """获取商店价格乘数（<1.0 为折扣，>1.0 为加价）"""
        for min_val, max_val, _, multiplier, _ in self.AFFINITY_LEVELS:
            if min_val <= self.affinity <= max_val:
                return multiplier
        return 1.0
    
    def get_context_description(self) -> str:
        """获取好感度上下文描述（用于注入 LLM）"""
        level = self.get_level()
        style = self.get_dialog_style()
        discount = self.get_discount_multiplier()
        
        discount_text = ""
        if discount < 1.0:
            discount_text = f"（购买折扣 {int((1 - discount) * 100)}%）"
        elif discount > 1.0:
            discount_text = f"（购买加价 {int((discount - 1) * 100)}%）"
        
        return f"好感度等级：{level}，对话风格：{style}{discount_text}"
