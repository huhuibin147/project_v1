import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from npc_affinity import AffinitySystem

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
QUESTS_FILE = CONFIG_DIR / "quests.json"
NPCS_FILE = CONFIG_DIR / "npcs.json"

_QUESTS_DB = {}


def load_quests_db():
    global _QUESTS_DB
    if not QUESTS_FILE.exists():
        _QUESTS_DB = {}
        return
    with open(QUESTS_FILE, "r", encoding="utf-8") as f:
        _QUESTS_DB = json.load(f)


load_quests_db()


def get_quest_config(quest_id: str) -> dict | None:
    return _QUESTS_DB.get(quest_id)


def get_npc_name(npc_id: str) -> str:
    if not NPCS_FILE.exists():
        return npc_id
    try:
        with open(NPCS_FILE, "r", encoding="utf-8") as f:
            npcs = json.load(f)
        cfg = npcs.get(npc_id, {})
        return cfg.get("name", npc_id)
    except Exception:
        return npc_id


class QuestManager:
    def __init__(self, player_profile):
        self.player = player_profile
        self._ensure_quest_data()

    def _ensure_quest_data(self):
        if not hasattr(self.player, "quests") or self.player.quests is None:
            self.player.quests = {
                "active": {},
                "completed": [],
                "daily_reset": "",
            }
        if "active" not in self.player.quests:
            self.player.quests["active"] = {}
        if "completed" not in self.player.quests:
            self.player.quests["completed"] = []
        if "daily_reset" not in self.player.quests:
            self.player.quests["daily_reset"] = ""

    def _save(self):
        self.player._save()

    def get_quest_status(self, quest_id: str) -> str:
        self._ensure_quest_data()
        if quest_id in self.player.quests.get("completed", []):
            return "completed"
        if quest_id in self.player.quests.get("active", {}):
            return "active"
        cfg = get_quest_config(quest_id)
        if not cfg:
            return "locked"
        if self._check_prerequisites(cfg):
            return "available"
        return "locked"

    def _check_prerequisites(self, quest_cfg: dict) -> bool:
        prereq = quest_cfg.get("prerequisites", {})
        if self.player.level < prereq.get("level", 1):
            return False
        for qid in prereq.get("quests_completed", []):
            if qid not in self.player.quests.get("completed", []):
                return False
        required_affinity = prereq.get("npc_affinity", 0)
        if required_affinity > 0:
            npc_id = quest_cfg.get("npc_id", "")
            npc_data = self._get_npc_data(npc_id)
            if npc_data and npc_data.get("affinity", 0) < required_affinity:
                return False
        return True

    def _get_npc_data(self, npc_id: str) -> dict | None:
        save_dir = Path(__file__).parent.parent / "data"
        slot = self.player.current_slot
        if slot is None:
            return None
        npc_file = save_dir / f"save_{slot}" / f"{npc_id}.json"
        if npc_file.exists():
            try:
                with open(npc_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def accept_quest(self, quest_id: str) -> dict:
        self._ensure_quest_data()
        cfg = get_quest_config(quest_id)
        if not cfg:
            return {"success": False, "message": "任务不存在"}
        status = self.get_quest_status(quest_id)
        if status == "active":
            return {"success": False, "message": "任务已接取"}
        if status == "completed":
            return {"success": False, "message": "任务已完成"}
        if status != "available":
            return {"success": False, "message": "前置条件未满足"}
        objectives_progress = []
        for obj in cfg.get("objectives", []):
            if obj["type"] == "collect":
                current = self.player.get_item_quantity(obj.get("item_id", ""))
                objectives_progress.append(min(current, obj.get("count", 1)))
            elif obj["type"] == "kill":
                objectives_progress.append(0)
            elif obj["type"] == "talk":
                objectives_progress.append(0)
            elif obj["type"] == "deliver":
                objectives_progress.append(0)
            elif obj["type"] == "explore":
                objectives_progress.append(0)
            else:
                objectives_progress.append(0)
        self.player.quests["active"][quest_id] = {
            "status": "active",
            "objectives_progress": objectives_progress,
            "accepted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._save()
        return {
            "success": True,
            "message": cfg.get("dialogue", {}).get("accept", "任务已接取！"),
            "quest": self._format_quest(quest_id, cfg, "active", objectives_progress),
        }

    def abandon_quest(self, quest_id: str) -> dict:
        self._ensure_quest_data()
        if quest_id not in self.player.quests.get("active", {}):
            return {"success": False, "message": "没有进行中的该任务"}
        del self.player.quests["active"][quest_id]
        self._save()
        return {"success": True, "message": "已放弃任务"}

    def complete_quest(self, quest_id: str) -> dict:
        self._ensure_quest_data()
        if quest_id not in self.player.quests.get("active", {}):
            return {"success": False, "message": "没有进行中的该任务"}
        cfg = get_quest_config(quest_id)
        if not cfg:
            return {"success": False, "message": "任务配置不存在"}
        quest_data = self.player.quests["active"][quest_id]
        progress = quest_data.get("objectives_progress", [])
        objectives = cfg.get("objectives", [])
        for i, obj in enumerate(objectives):
            if i >= len(progress):
                return {"success": False, "message": "任务目标未完成"}
            if obj["type"] == "kill":
                if progress[i] < obj.get("count", 1):
                    return {"success": False, "message": "任务目标未完成"}
            elif obj["type"] == "collect":
                if progress[i] < obj.get("count", 1):
                    return {"success": False, "message": "任务目标未完成"}
            elif obj["type"] == "talk":
                if progress[i] < 1:
                    return {"success": False, "message": "任务目标未完成"}
            elif obj["type"] == "deliver":
                if progress[i] < 1:
                    return {"success": False, "message": "任务目标未完成"}
            elif obj["type"] == "explore":
                if progress[i] < 1:
                    return {"success": False, "message": "任务目标未完成"}
        for i, obj in enumerate(objectives):
            if obj["type"] == "deliver":
                item_id = obj.get("item_id", "")
                count = obj.get("count", 1)
                self.player.remove_item(item_id, count)
        rewards = cfg.get("rewards", {})
        reward_details = {"exp": 0, "gold": 0, "items": [], "affinity": 0}
        quest_npc_id = cfg.get("npc_id", "")
        reward_mult = 1.0
        if quest_npc_id:
            quest_npc_affinity = self._get_npc_affinity(quest_npc_id)
            reward_mult = AffinitySystem(quest_npc_affinity).get_quest_reward_multiplier()
        exp = rewards.get("exp", 0)
        if exp > 0:
            adjusted_exp = int(exp * reward_mult)
            self.player.gain_exp(adjusted_exp)
            reward_details["exp"] = adjusted_exp
        gold = rewards.get("gold", 0)
        if gold > 0:
            adjusted_gold = int(gold * reward_mult)
            self.player.add_gold(adjusted_gold)
            reward_details["gold"] = adjusted_gold
        for item_reward in rewards.get("items", []):
            self.player.add_item(item_reward["item_id"], item_reward.get("quantity", 1))
            from item_system import ITEMS_DB
            item_info = ITEMS_DB.get(item_reward["item_id"], {})
            reward_details["items"].append({
                "item_id": item_reward["item_id"],
                "name": item_info.get("name", item_reward["item_id"]),
                "quantity": item_reward.get("quantity", 1),
            })
        affinity_info = rewards.get("affinity", {})
        if affinity_info:
            npc_id = affinity_info.get("npc_id", cfg.get("npc_id", ""))
            affinity_value = affinity_info.get("value", 0)
            self._add_npc_affinity(npc_id, affinity_value)
            reward_details["affinity"] = affinity_value
            reward_details["affinity_npc"] = get_npc_name(npc_id)
        del self.player.quests["active"][quest_id]
        if quest_id not in self.player.quests["completed"]:
            self.player.quests["completed"].append(quest_id)
        self._save()
        reward_msgs = []
        if reward_details["exp"] > 0:
            reward_msgs.append(f"{reward_details['exp']}经验")
        if reward_details["gold"] > 0:
            reward_msgs.append(f"{reward_details['gold']}金币")
        if reward_mult != 1.0 and quest_npc_id:
            npc_name = get_npc_name(quest_npc_id)
            pct = int((reward_mult - 1.0) * 100)
            if pct > 0:
                reward_msgs.append(f"{npc_name}好感加成+{pct}%")
            elif pct < 0:
                reward_msgs.append(f"{npc_name}好感惩罚{pct}%")
        if reward_details["items"]:
            for it in reward_details["items"]:
                reward_msgs.append(f"{it['name']}×{it['quantity']}")
        if reward_details["affinity"] > 0:
            reward_msgs.append(f"{reward_details['affinity_npc']}好感+{reward_details['affinity']}")
        message = f"任务完成！获得：{'、'.join(reward_msgs)}"
        
        result = {
            "success": True,
            "message": message,
            "rewards": reward_details,
            "dialogue": cfg.get("dialogue", {}).get("complete", ""),
        }
        
        next_quest_id = cfg.get("next_in_chain")
        if next_quest_id:
            next_cfg = get_quest_config(next_quest_id)
            if next_cfg and self._check_prerequisites(next_cfg):
                accept_result = self.accept_quest(next_quest_id)
                if accept_result["success"]:
                    result["next_quest"] = {
                        "quest_id": next_quest_id,
                        "quest_name": next_cfg.get("name"),
                        "message": next_cfg.get("dialogue", {}).get("offer", "")
                    }
        
        return result

    def _add_npc_affinity(self, npc_id: str, value: int):
        save_dir = Path(__file__).parent.parent / "data"
        slot = self.player.current_slot
        if slot is None:
            return
        npc_file = save_dir / f"save_{slot}" / f"{npc_id}.json"
        if not npc_file.exists():
            return
        try:
            with open(npc_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["affinity"] = max(0, min(100, data.get("affinity", 50) + value))
            with open(npc_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _get_npc_affinity(self, npc_id: str) -> int:
        save_dir = Path(__file__).parent.parent / "data"
        slot = self.player.current_slot
        if slot is None:
            return 50
        npc_file = save_dir / f"save_{slot}" / f"{npc_id}.json"
        if not npc_file.exists():
            return 50
        try:
            with open(npc_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("affinity", 50)
        except Exception:
            return 50

    def on_kill(self, monster_id: str, monster_tags: list[str]) -> list[dict]:
        self._ensure_quest_data()
        updated = []
        for quest_id, quest_data in list(self.player.quests.get("active", {}).items()):
            cfg = get_quest_config(quest_id)
            if not cfg:
                continue
            objectives = cfg.get("objectives", [])
            progress = quest_data.get("objectives_progress", [])
            changed = False
            for i, obj in enumerate(objectives):
                if i >= len(progress):
                    break
                if obj["type"] != "kill":
                    continue
                if progress[i] >= obj.get("count", 1):
                    continue
                matched = False
                if obj.get("target") and obj["target"] == monster_id:
                    matched = True
                if not matched and obj.get("target_tags"):
                    for tag in obj["target_tags"]:
                        if tag in monster_tags:
                            matched = True
                            break
                if matched:
                    progress[i] = min(progress[i] + 1, obj["count"])
                    changed = True
            if changed:
                quest_data["objectives_progress"] = progress
                self.player.quests["active"][quest_id] = quest_data
                updated.append({
                    "quest_id": quest_id,
                    "quest_name": cfg.get("name", quest_id),
                    "objectives": self._format_objectives(cfg, progress),
                })
        if updated:
            self._save()
        return updated

    def on_collect(self, item_id: str) -> list[dict]:
        self._ensure_quest_data()
        updated = []
        for quest_id, quest_data in list(self.player.quests.get("active", {}).items()):
            cfg = get_quest_config(quest_id)
            if not cfg:
                continue
            objectives = cfg.get("objectives", [])
            progress = quest_data.get("objectives_progress", [])
            changed = False
            for i, obj in enumerate(objectives):
                if i >= len(progress):
                    break
                if obj["type"] == "collect" and obj.get("item_id") == item_id:
                    current_qty = self.player.get_item_quantity(item_id)
                    new_progress = min(current_qty, obj.get("count", 1))
                    if new_progress != progress[i]:
                        progress[i] = new_progress
                        changed = True
            if changed:
                quest_data["objectives_progress"] = progress
                self.player.quests["active"][quest_id] = quest_data
                updated.append({
                    "quest_id": quest_id,
                    "quest_name": cfg.get("name", quest_id),
                    "objectives": self._format_objectives(cfg, progress),
                })
        if updated:
            self._save()
        return updated

    def on_talk(self, npc_id: str) -> list[dict]:
        self._ensure_quest_data()
        updated = []
        for quest_id, quest_data in list(self.player.quests.get("active", {}).items()):
            cfg = get_quest_config(quest_id)
            if not cfg:
                continue
            objectives = cfg.get("objectives", [])
            progress = quest_data.get("objectives_progress", [])
            changed = False
            for i, obj in enumerate(objectives):
                if i >= len(progress):
                    break
                if obj["type"] == "talk" and obj.get("npc_id") == npc_id:
                    if progress[i] < 1:
                        progress[i] = 1
                        changed = True
                elif obj["type"] == "deliver" and obj.get("target_npc_id") == npc_id:
                    item_id = obj.get("item_id", "")
                    count = obj.get("count", 1)
                    if self.player.get_item_quantity(item_id) >= count:
                        if progress[i] < 1:
                            progress[i] = 1
                            changed = True
            if changed:
                quest_data["objectives_progress"] = progress
                self.player.quests["active"][quest_id] = quest_data
                updated.append({
                    "quest_id": quest_id,
                    "quest_name": cfg.get("name", quest_id),
                    "objectives": self._format_objectives(cfg, progress),
                })
        if updated:
            self._save()
        return updated

    def on_explore(self, map_id: str, x: int, y: int) -> list[dict]:
        self._ensure_quest_data()
        updated = []
        for quest_id, quest_data in list(self.player.quests.get("active", {}).items()):
            cfg = get_quest_config(quest_id)
            if not cfg:
                continue
            objectives = cfg.get("objectives", [])
            progress = quest_data.get("objectives_progress", [])
            changed = False
            for i, obj in enumerate(objectives):
                if i >= len(progress):
                    break
                if obj["type"] == "explore":
                    if (obj.get("map_id") == map_id and
                            progress[i] < 1):
                        tx = obj.get("x", 0)
                        ty = obj.get("y", 0)
                        radius = obj.get("radius", 3)
                        dist = ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5
                        if dist <= radius:
                            progress[i] = 1
                            changed = True
            if changed:
                quest_data["objectives_progress"] = progress
                self.player.quests["active"][quest_id] = quest_data
                updated.append({
                    "quest_id": quest_id,
                    "quest_name": cfg.get("name", quest_id),
                    "objectives": self._format_objectives(cfg, progress),
                })
        if updated:
            self._save()
        return updated

    def get_all_quests(self) -> list[dict]:
        self._ensure_quest_data()
        result = []
        for quest_id, cfg in _QUESTS_DB.items():
            status = self.get_quest_status(quest_id)
            progress = None
            if status == "active":
                quest_data = self.player.quests["active"].get(quest_id, {})
                progress = quest_data.get("objectives_progress", [])
            result.append(self._format_quest(quest_id, cfg, status, progress))
        return result

    def get_npc_quests(self, npc_id: str) -> list[dict]:
        self._ensure_quest_data()
        result = []
        for quest_id, cfg in _QUESTS_DB.items():
            if cfg.get("npc_id") != npc_id:
                continue
            status = self.get_quest_status(quest_id)
            progress = None
            if status == "active":
                quest_data = self.player.quests["active"].get(quest_id, {})
                progress = quest_data.get("objectives_progress", [])
            result.append(self._format_quest(quest_id, cfg, status, progress))
        return result

    def get_active_quests(self) -> list[dict]:
        self._ensure_quest_data()
        result = []
        for quest_id in self.player.quests.get("active", {}):
            cfg = get_quest_config(quest_id)
            if not cfg:
                continue
            quest_data = self.player.quests["active"][quest_id]
            progress = quest_data.get("objectives_progress", [])
            result.append(self._format_quest(quest_id, cfg, "active", progress))
        return result

    def is_quest_completeable(self, quest_id: str) -> bool:
        self._ensure_quest_data()
        if quest_id not in self.player.quests.get("active", {}):
            return False
        cfg = get_quest_config(quest_id)
        if not cfg:
            return False
        quest_data = self.player.quests["active"][quest_id]
        progress = quest_data.get("objectives_progress", [])
        objectives = cfg.get("objectives", [])
        for i, obj in enumerate(objectives):
            if i >= len(progress):
                return False
            required = obj.get("count", 1)
            if obj["type"] in ("talk", "deliver", "explore"):
                required = 1
            if progress[i] < required:
                return False
        return True

    def _format_quest(self, quest_id: str, cfg: dict, status: str, progress: list | None = None) -> dict:
        return {
            "id": quest_id,
            "name": cfg.get("name", quest_id),
            "description": cfg.get("description", ""),
            "type": cfg.get("type", "side"),
            "npc_id": cfg.get("npc_id", ""),
            "npc_name": get_npc_name(cfg.get("npc_id", "")),
            "status": status,
            "objectives": self._format_objectives(cfg, progress),
            "rewards": cfg.get("rewards", {}),
            "can_accept": status == "available",
            "can_complete": self.is_quest_completeable(quest_id) if status == "active" else False,
            "dialogue": cfg.get("dialogue", {}),
        }

    def _format_objectives(self, cfg: dict, progress: list | None = None) -> list[dict]:
        objectives = cfg.get("objectives", [])
        result = []
        for i, obj in enumerate(objectives):
            current = 0
            if progress and i < len(progress):
                current = progress[i]
            required = obj.get("count", 1)
            if obj["type"] in ("talk", "deliver", "explore"):
                required = 1
            result.append({
                "type": obj["type"],
                "description": obj.get("description", ""),
                "count": required,
                "progress": current,
                "completed": current >= required,
            })
        return result

    def _should_reset_daily(self) -> bool:
        now_utc = datetime.now(timezone.utc)
        reset_time = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        
        last_reset_str = self.player.quests.get("daily_reset", "")
        if not last_reset_str:
            return True
        
        try:
            last_reset = datetime.fromisoformat(last_reset_str)
            if last_reset.tzinfo is None:
                last_reset = last_reset.replace(tzinfo=timezone.utc)
            return now_utc >= reset_time and last_reset < reset_time
        except ValueError:
            return True

    def reset_daily_quests(self) -> list[str]:
        if not self._should_reset_daily():
            return []
        
        self.player.quests["daily_reset"] = datetime.now(timezone.utc).isoformat()
        reset_quests = []
        
        for quest_id, quest_data in list(self.player.quests.get("active", {}).items()):
            cfg = get_quest_config(quest_id)
            if cfg and cfg.get("type") == "daily":
                quest_data["objectives_progress"] = [0] * len(cfg.get("objectives", []))
                quest_data["accepted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reset_quests.append(quest_id)
        
        if reset_quests:
            self._save()
        return reset_quests

    def get_quest_chain(self, quest_id: str) -> dict | None:
        cfg = get_quest_config(quest_id)
        if not cfg:
            return None
        
        chain_id = cfg.get("chain")
        if not chain_id:
            return None
        
        chain_quests = []
        for qid, qcfg in _QUESTS_DB.items():
            if qcfg.get("chain") == chain_id:
                chain_quests.append({
                    "quest_id": qid,
                    "quest_name": qcfg.get("name"),
                    "order": qcfg.get("chain_order", 0),
                    "status": self.get_quest_status(qid),
                })
        
        chain_quests.sort(key=lambda x: x["order"])
        return {
            "chain_id": chain_id,
            "quests": chain_quests,
        }
