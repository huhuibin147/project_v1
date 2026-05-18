# NPC 对话系统优化设计

## 一、优化目标

### 1.1 当前问题
- **LLM 调用成本高**：每次对话都调用 LLM API，响应慢且有费用
- **意图识别不稳定**：依赖 LLM 输出 JSON 格式，可能因模型输出格式问题导致解析失败
- **记忆系统简单**：只保留最近 10 条对话历史，缺少长期记忆和关键事件记录
- **好感度影响有限**：好感度变化只影响 mood 字段，未深度影响 NPC 行为
- **无对话缓存**：相同问题的回答每次都重新生成

### 1.2 优化目标
- 降低 LLM 调用频率 50% 以上
- 提高意图识别准确率至 95%+
- 实现分层记忆系统
- 好感度深度影响 NPC 行为
- 实现常见问题缓存机制

## 二、设计方案

### 2.1 本地意图分类器

**设计思路**：
- 使用规则 + 关键词匹配进行初步意图分类
- 仅对复杂对话调用 LLM
- 支持交易意图的精确识别

**实现方案**：
```python
# 意图分类规则
INTENT_RULES = {
    "trade": {
        "buy_keywords": ["买", "购买", "我要买", "给我来", "多少钱", "价格"],
        "sell_keywords": ["卖", "出售", "我要卖", "卖给你", "收购"],
    },
    "quest": {
        "keywords": ["任务", "帮忙", "需要", "委托", "工作", "悬赏"],
    },
    "chat": {
        "keywords": ["你好", "hello", "嗨", "最近怎么样", "你是谁", "介绍"],
    },
}

def classify_intent(player_input: str) -> str:
    input_lower = player_input.lower()
    
    # 交易意图检测
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
```

### 2.2 分层记忆系统

**设计思路**：
- **短期记忆**：最近 10 条对话（现有机制保留）
- **长期记忆**：关键事件记录（任务完成、重要对话、好感度变化）
- **记忆摘要**：定期生成对话摘要，减少上下文长度

**实现方案**：
```python
# 长期记忆结构
self.long_term_memory = {
    "key_events": [],  # 关键事件列表
    "player_preferences": {},  # 玩家偏好记录
    "conversation_summary": "",  # 对话摘要
    "last_interaction": "",  # 上次交互时间
}

# 关键事件类型
KEY_EVENT_TYPES = [
    "quest_completed",  # 任务完成
    "trade_completed",  # 交易完成
    "affinity_milestone",  # 好感度里程碑
    "important_topic",  # 重要话题
]

def add_long_term_memory(self, event_type: str, content: str, importance: int = 1):
    """添加长期记忆"""
    self.long_term_memory["key_events"].append({
        "type": event_type,
        "content": content,
        "importance": importance,
        "timestamp": datetime.now().isoformat(),
    })
    
    # 保持长期记忆不超过 50 条
    if len(self.long_term_memory["key_events"]) > 50:
        self.long_term_memory["key_events"] = self.long_term_memory["key_events"][-50:]
```

### 2.3 好感度深度影响

**设计思路**：
- 好感度影响商店折扣（0-100 对应 0%-20% 折扣）
- 好感度影响任务奖励（高好感度获得更好奖励）
- 好感度影响 NPC 对话风格（低好感度更冷淡，高好感度更热情）

**实现方案**：
```python
def get_affinity_discount(self) -> float:
    """根据好感度计算折扣率"""
    if self.affinity >= 80:
        return 0.8  # 20% 折扣
    elif self.affinity >= 60:
        return 0.9  # 10% 折扣
    elif self.affinity >= 40:
        return 1.0  # 无折扣
    elif self.affinity >= 20:
        return 1.1  # 10% 加价
    else:
        return 1.2  # 20% 加价

def get_affinity_dialog_style(self) -> str:
    """根据好感度返回对话风格"""
    if self.affinity >= 80:
        return "热情友好"
    elif self.affinity >= 60:
        return "友善"
    elif self.affinity >= 40:
        return "中性"
    elif self.affinity >= 20:
        return "冷淡"
    else:
        return "敌对"
```

### 2.4 常见问题缓存

**设计思路**：
- 基于关键词匹配缓存常见问题回答
- 相同问题在好感度不变时直接返回缓存
- 缓存支持过期时间（避免永远不变）

**实现方案**：
```python
# 缓存结构
self.response_cache = {
    "cache_entries": {},  # {keyword_hash: {"response": "", "affinity": 0, "timestamp": ""}}
    "max_entries": 100,  # 最大缓存条目数
    "ttl_seconds": 3600,  # 缓存有效期 1 小时
}

def get_cached_response(self, player_input: str, current_affinity: int) -> str | None:
    """获取缓存回答"""
    keyword = self._extract_keywords(player_input)
    cache_key = hash(keyword)
    
    if cache_key in self.response_cache["cache_entries"]:
        entry = self.response_cache["cache_entries"][cache_key]
        # 检查缓存是否有效
        if (entry["affinity"] == current_affinity and 
            time.time() - entry["timestamp"] < self.response_cache["ttl_seconds"]):
            return entry["response"]
    
    return None

def cache_response(self, player_input: str, response: str, affinity: int):
    """缓存回答"""
    keyword = self._extract_keywords(player_input)
    cache_key = hash(keyword)
    
    self.response_cache["cache_entries"][cache_key] = {
        "response": response,
        "affinity": affinity,
        "timestamp": time.time(),
    }
    
    # 清理过期缓存
    self._cleanup_cache()
```

## 三、架构设计

### 3.1 模块划分
```
npc_agent.py
├── IntentClassifier      # 意图分类器
├── MemoryManager         # 记忆管理器
├── AffinitySystem        # 好感度系统
├── ResponseCache         # 回答缓存
└── NPCAgent              # NPC 代理主类
```

### 3.2 数据流
```
玩家输入 → 意图分类器 → 本地处理（交易/任务/闲聊）
                ↓
            是否需要 LLM？
                ↓ 是
            检查缓存 → 有缓存？ → 返回缓存
                ↓ 否
            调用 LLM → 缓存结果
                ↓
            更新记忆 → 更新好感度 → 保存存档
```

## 四、实现阶段

### Phase 1: 意图分类器 + 缓存
- 实现本地意图分类器
- 实现常见问题缓存
- 集成到现有 NPC 对话流程

### Phase 2: 分层记忆系统
- 实现长期记忆存储
- 实现记忆摘要生成
- 集成到 LLM 上下文

### Phase 3: 好感度深度影响
- 实现商店折扣系统
- 实现任务奖励影响
- 实现对话风格变化

## 五、预期效果

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| LLM 调用频率 | 100% | <50% | 降低 50%+ |
| 意图识别准确率 | ~85% | >95% | 提升 10%+ |
| 响应时间 | 1-3 秒 | <0.5 秒（缓存命中） | 提升 60%+ |
| 记忆持久性 | 10 条对话 | 50 条事件 + 摘要 | 提升 5 倍 |
| 好感度影响 | 仅 mood 字段 | 折扣/奖励/风格 | 深度影响 |

---

## 六、完成状态

> 更新日期：2026-05-18
> 状态：✅ 已完成（除记忆摘要和好感度任务奖励）

| 优化项 | 状态 | 说明 |
|--------|------|------|
| 本地意图分类器 | ✅ 完成 | `IntentClassifier` 支持 trade/quest/chat/unknown 四种意图，交易意图完全本地处理 |
| 分层记忆系统 | ✅ 完成 | `MemoryManager`：短期记忆（最近 10 条对话）+ 长期记忆（关键事件，最多 50 条） |
| 好感度深度影响 | ✅ 部分 | `AffinitySystem`：5 个等级（敌对→亲密），影响商店折扣（+20%→-20%）和对话风格 |
| 常见问题缓存 | ✅ 完成 | `ResponseCache`：TTL 1 小时，最大 100 条，相同好感度等级下返回缓存 |
| 记忆摘要生成 | ❌ 未实现 | 长期记忆较多时缺少自动摘要（P2） |
| 好感度影响任务奖励 | ❌ 未实现 | 当前仅影响商店价格（P2） |

**新增模块**：[`intent_classifier.py`](file:///Users/huhuibin/code/aiproj/project_v1/backend/intent_classifier.py)、[`npc_memory.py`](file:///Users/huhuibin/code/aiproj/project_v1/backend/npc_memory.py)、[`npc_affinity.py`](file:///Users/huhuibin/code/aiproj/project_v1/backend/npc_affinity.py)、[`npc_cache.py`](file:///Users/huhuibin/code/aiproj/project_v1/backend/npc_cache.py)
