"""NPC 记忆管理系统"""

import time
from datetime import datetime


class MemoryManager:
    """管理 NPC 的短期和长期记忆"""
    
    MAX_SHORT_TERM = 10  # 短期记忆最大条数
    MAX_LONG_TERM = 50   # 长期记忆最大条数
    
    def __init__(self):
        self.short_term_memory: list[dict] = []  # 最近对话
        self.long_term_memory: list[dict] = []   # 关键事件
        self.conversation_summary: str = ""      # 对话摘要
    
    def add_short_term(self, role: str, content: str):
        """添加短期记忆（对话）"""
        self.short_term_memory.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        
        # 保持不超过最大值
        if len(self.short_term_memory) > self.MAX_SHORT_TERM * 2:
            self.short_term_memory = self.short_term_memory[-self.MAX_SHORT_TERM * 2:]
    
    def add_long_term(self, event_type: str, content: str, importance: int = 1):
        """添加长期记忆（关键事件）"""
        self.long_term_memory.append({
            "type": event_type,
            "content": content,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
        })
        
        # 保持不超过最大值
        if len(self.long_term_memory) > self.MAX_LONG_TERM:
            self.long_term_memory = self.long_term_memory[-self.MAX_LONG_TERM:]
    
    def get_short_term_history(self) -> str:
        """获取短期记忆历史文本"""
        lines = []
        for h in self.short_term_memory[-self.MAX_SHORT_TERM * 2:]:
            role = "玩家" if h["role"] == "player" else "NPC"
            lines.append(f"{role}：{h['content']}")
        return "\n".join(lines) if lines else "（第一次对话）"
    
    def get_long_term_context(self) -> str:
        """获取长期记忆上下文"""
        if not self.long_term_memory:
            return ""
        
        lines = ["\n重要记忆："]
        for event in self.long_term_memory[-10:]:  # 只取最近 10 条长期记忆
            lines.append(f"- [{event['type']}] {event['content']}")
        return "\n".join(lines)
    
    def to_save(self) -> dict:
        """序列化记忆"""
        return {
            "short_term": self.short_term_memory,
            "long_term": self.long_term_memory,
            "summary": self.conversation_summary,
        }
    
    def from_save(self, data: dict):
        """从存档加载记忆"""
        self.short_term_memory = data.get("short_term", [])
        self.long_term_memory = data.get("long_term", [])
        self.conversation_summary = data.get("summary", "")
