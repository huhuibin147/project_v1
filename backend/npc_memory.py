"""NPC 记忆管理系统"""

import time
from datetime import datetime


class MemoryManager:
    """管理 NPC 的短期和长期记忆"""
    
    MAX_SHORT_TERM = 10
    MAX_LONG_TERM = 50
    SUMMARIZE_THRESHOLD = 30
    SUMMARIZE_KEEP_IMPORTANCE = 3
    
    def __init__(self):
        self.short_term_memory: list[dict] = []
        self.long_term_memory: list[dict] = []
        self.conversation_summary: str = ""
    
    def add_short_term(self, role: str, content: str):
        self.short_term_memory.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        
        if len(self.short_term_memory) > self.MAX_SHORT_TERM * 2:
            self.short_term_memory = self.short_term_memory[-self.MAX_SHORT_TERM * 2:]
    
    def add_long_term(self, event_type: str, content: str, importance: int = 1):
        self.long_term_memory.append({
            "type": event_type,
            "content": content,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
        })
        
        if len(self.long_term_memory) > self.MAX_LONG_TERM:
            self.long_term_memory = self.long_term_memory[-self.MAX_LONG_TERM:]
        
        if len(self.long_term_memory) >= self.SUMMARIZE_THRESHOLD:
            self._auto_summarize()
    
    def _auto_summarize(self):
        low_importance = [m for m in self.long_term_memory if m.get("importance", 1) < self.SUMMARIZE_KEEP_IMPORTANCE]
        high_importance = [m for m in self.long_term_memory if m.get("importance", 1) >= self.SUMMARIZE_KEEP_IMPORTANCE]
        
        if len(low_importance) < 5:
            return
        
        summary_parts = []
        type_groups = {}
        for m in low_importance:
            t = m.get("type", "other")
            if t not in type_groups:
                type_groups[t] = []
            type_groups[t].append(m)
        
        for event_type, events in type_groups.items():
            if event_type == "trade_completed":
                count = len(events)
                summary_parts.append(f"进行了{count}次交易")
            elif event_type == "chat":
                count = len(events)
                summary_parts.append(f"有{count}次闲聊")
            elif event_type == "quest_topic":
                count = len(events)
                summary_parts.append(f"讨论了{count}次任务话题")
            else:
                count = len(events)
                summary_parts.append(f"有{count}次{event_type}相关互动")
        
        new_summary = "、".join(summary_parts)
        if self.conversation_summary:
            self.conversation_summary = f"{self.conversation_summary}；此外{new_summary}"
        else:
            self.conversation_summary = f"过往互动摘要：{new_summary}"
        
        self.long_term_memory = high_importance
    
    def get_short_term_history(self) -> str:
        lines = []
        for h in self.short_term_memory[-self.MAX_SHORT_TERM * 2:]:
            role = "玩家" if h["role"] == "player" else "NPC"
            lines.append(f"{role}：{h['content']}")
        return "\n".join(lines) if lines else "（第一次对话）"
    
    def get_long_term_context(self) -> str:
        parts = []
        if self.conversation_summary:
            parts.append(f"\n互动摘要：{self.conversation_summary}")
        if self.long_term_memory:
            lines = ["\n重要记忆："]
            for event in self.long_term_memory[-10:]:
                lines.append(f"- [{event['type']}] {event['content']}")
            parts.append("\n".join(lines))
        return "".join(parts)
    
    def to_save(self) -> dict:
        return {
            "short_term": self.short_term_memory,
            "long_term": self.long_term_memory,
            "summary": self.conversation_summary,
        }
    
    def from_save(self, data: dict):
        self.short_term_memory = data.get("short_term", [])
        self.long_term_memory = data.get("long_term", [])
        self.conversation_summary = data.get("summary", "")
