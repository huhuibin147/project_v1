"""NPC 对话缓存系统"""

import time
import hashlib


class ResponseCache:
    """缓存 NPC 对常见问题的回答"""
    
    MAX_ENTRIES = 100
    TTL_SECONDS = 3600  # 1 小时
    
    def __init__(self):
        self.cache: dict[str, dict] = {}
    
    def _make_key(self, player_input: str, affinity_level: str) -> str:
        """生成缓存键"""
        # 提取关键词用于缓存
        keywords = self._extract_keywords(player_input)
        raw_key = f"{keywords}_{affinity_level}"
        return hashlib.md5(raw_key.encode()).hexdigest()
    
    def _extract_keywords(self, text: str) -> str:
        """提取关键词"""
        # 简单实现：去除停用词，保留关键内容
        stopwords = ["的", "了", "是", "在", "我", "你", "他", "她", "它", "们", "这", "那", "有", "没有", "什么", "一个"]
        keywords = []
        for char in text:
            if char not in stopwords and char.isalnum():
                keywords.append(char)
        return "".join(keywords[:20])  # 限制长度
    
    def get(self, player_input: str, affinity_level: str) -> str | None:
        """获取缓存回答"""
        key = self._make_key(player_input, affinity_level)
        
        if key in self.cache:
            entry = self.cache[key]
            # 检查是否过期
            if time.time() - entry["timestamp"] < self.TTL_SECONDS:
                return entry["response"]
            else:
                # 删除过期条目
                del self.cache[key]
        
        return None
    
    def put(self, player_input: str, affinity_level: str, response: str):
        """缓存回答"""
        key = self._make_key(player_input, affinity_level)
        
        self.cache[key] = {
            "response": response,
            "timestamp": time.time(),
        }
        
        # 清理超出限制的缓存
        if len(self.cache) > self.MAX_ENTRIES:
            self._cleanup()
    
    def _cleanup(self):
        """清理最旧的缓存条目"""
        sorted_keys = sorted(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
        for key in sorted_keys[:len(self.cache) - self.MAX_ENTRIES]:
            del self.cache[key]
    
    def clear_expired(self):
        """清理所有过期条目"""
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - entry["timestamp"] >= self.TTL_SECONDS
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def to_save(self) -> dict:
        """序列化缓存"""
        return {
            "cache": self.cache,
        }
    
    def from_save(self, data: dict):
        """从存档加载缓存"""
        self.cache = data.get("cache", {})
        # 加载时清理过期条目
        self.clear_expired()
