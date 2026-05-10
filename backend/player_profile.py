import json
from pathlib import Path
from datetime import datetime

CONFIG_DIR = Path(__file__).parent.parent / "config"
DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_FILE = CONFIG_DIR / "player_default.json"
SAVE_SLOTS = 3

EQUIP_SLOTS = ["weapon", "shield", "head", "body", "accessory"]
DEFAULT_EQUIPMENT = {s: None for s in EQUIP_SLOTS}


def load_defaults() -> dict:
    with open(DEFAULT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_dir(slot: int) -> Path:
    return DATA_DIR / f"save_{slot}"


def save_path(slot: int) -> Path:
    return save_dir(slot) / "player.json"


class PlayerProfile:
    def __init__(self):
        defaults = load_defaults()
        self.classes = defaults["classes"]
        self.current_slot = None
        self._reset_to_defaults(defaults)

    def _reset_to_defaults(self, defaults=None):
        if defaults is None:
            defaults = load_defaults()
        self.name = defaults["name"]
        self.class_id = defaults["class"]
        self.level = defaults["level"]
        self.exp = defaults["exp"]
        self.exp_to_next = defaults["exp_to_next"]
        self.status_effects = defaults["status_effects"]
        cls = self.classes[self.class_id]
        self.max_hp = cls["base_hp"]
        self.hp = self.max_hp
        self.max_mp = cls.get("base_mp", 30)
        self.mp = self.max_mp
        self.attack = cls["base_attack"]
        self.defense = cls["base_defense"]
        self.speed = cls["base_speed"]
        self.gold = 200
        self.inventory = []
        self.equipment = dict(DEFAULT_EQUIPMENT)
        self.player_x = 25
        self.player_y = 20
        self.current_map = "village"
        self.map_states = {}
        self.skills = list(defaults.get("skills", {}).get(self.class_id, []))
        self.learned_skills = []  # 通过技能书学习的技能

    def _save(self):
        if self.current_slot is None:
            return
        save_dir(self.current_slot).mkdir(parents=True, exist_ok=True)
        data = {
            "name": self.name,
            "class_id": self.class_id,
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mp": self.mp,
            "max_mp": self.max_mp,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "status_effects": self.status_effects,
            "gold": self.gold,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "skills": self.skills,
            "learned_skills": self.learned_skills,
            "player_x": self.player_x,
            "player_y": self.player_y,
            "current_map": self.current_map,
            "map_states": self.map_states,
            "save_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(save_path(self.current_slot), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_from_file(self, slot: int):
        path = save_path(slot)
        if not path.exists():
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.current_slot = slot
            self.name = data.get("name", self.name)
            self.class_id = data.get("class_id", self.class_id)
            self.level = data.get("level", self.level)
            self.exp = data.get("exp", self.exp)
            self.exp_to_next = data.get("exp_to_next", self.exp_to_next)
            self.hp = data.get("hp", self.hp)
            self.max_hp = data.get("max_hp", self.max_hp)
            self.mp = data.get("mp", getattr(self, "mp", self.max_mp))
            self.max_mp = data.get("max_mp", getattr(self, "max_mp", 30))
            self.attack = data.get("attack", self.attack)
            self.defense = data.get("defense", self.defense)
            self.speed = data.get("speed", self.speed)
            self.status_effects = data.get("status_effects", [])
            self.gold = data.get("gold", 0)
            self.inventory = data.get("inventory", [])
            self.equipment = data.get("equipment", dict(DEFAULT_EQUIPMENT))
            self.skills = data.get("skills", [])
            self.learned_skills = data.get("learned_skills", [])
            for s in EQUIP_SLOTS:
                if s not in self.equipment:
                    self.equipment[s] = None
            self.player_x = data.get("player_x", 25)
            self.player_y = data.get("player_y", 20)
            self.current_map = data.get("current_map", "village")
            self.map_states = data.get("map_states", {})
            self._recalc_stats()
            return True
        except (json.JSONDecodeError, KeyError):
            return False

    # ===== 装备系统 =====

    def _calc_equip_bonus(self) -> dict:
        from item_system import ITEMS_DB
        bonus = {"attack": 0, "defense": 0, "speed": 0, "max_hp": 0, "max_mp": 0}
        for slot_name, item_id in self.equipment.items():
            if item_id:
                info = ITEMS_DB.get(item_id, {})
                stats = info.get("stats", {})
                for key in bonus:
                    bonus[key] += stats.get(key, 0)
        return bonus

    def _recalc_stats(self):
        cls = self.classes[self.class_id]
        level_bonus = self.level - 1
        base_attack = cls["base_attack"] + level_bonus * 3
        base_defense = cls["base_defense"] + level_bonus * 2
        base_speed = cls["base_speed"] + level_bonus * 1
        base_max_hp = cls["base_hp"] + level_bonus * 10
        base_max_mp = cls.get("base_mp", 30) + level_bonus * 3

        bonus = self._calc_equip_bonus()
        self.attack = base_attack + bonus["attack"]
        self.defense = base_defense + bonus["defense"]
        self.speed = base_speed + bonus["speed"]
        new_max_hp = base_max_hp + bonus["max_hp"]
        if new_max_hp != self.max_hp:
            old_max = self.max_hp
            self.max_hp = new_max_hp
            if self.max_hp < old_max:
                self.hp = min(self.hp, self.max_hp)
        new_max_mp = base_max_mp + bonus["max_mp"]
        if new_max_mp != getattr(self, "max_mp", 30):
            old_max_mp = getattr(self, "max_mp", 30)
            self.max_mp = new_max_mp
            if self.max_mp < old_max_mp:
                self.mp = min(getattr(self, "mp", self.max_mp), self.max_mp)
        self._save()

    def equip_item(self, item_id: str) -> dict:
        from item_system import ITEMS_DB
        item_info = ITEMS_DB.get(item_id)
        if not item_info:
            return {"success": False, "message": "未知物品"}

        equip_slot = item_info.get("equip_slot")
        if not equip_slot:
            return {"success": False, "message": "该物品无法装备"}

        if self.get_item_quantity(item_id) <= 0:
            return {"success": False, "message": "背包中没有该物品"}

        required_class = item_info.get("required_class")
        if required_class and self.class_id != required_class:
            class_names = {"warrior": "战士", "rogue": "盗贼", "mage": "法师"}
            return {"success": False, "message": f"该装备仅限{class_names.get(required_class, required_class)}使用"}

        unequipped = None
        old_item_id = self.equipment.get(equip_slot)
        if old_item_id:
            self.add_item(old_item_id, 1)
            unequipped = {"slot": equip_slot, "item_id": old_item_id,
                          "name": ITEMS_DB.get(old_item_id, {}).get("name", old_item_id)}

        self.remove_item(item_id, 1)
        self.equipment[equip_slot] = item_id
        self._recalc_stats()

        message = f"装备了{item_info['name']}"
        if unequipped:
            message = f"卸下了{unequipped['name']}，{message}"

        return {
            "success": True,
            "message": message,
            "equipment": self._get_equipment_detail(),
            "unequipped": unequipped,
            "player_attack": self.attack,
            "player_defense": self.defense,
            "player_speed": self.speed,
            "player_max_hp": self.max_hp,
            "player_hp": self.hp,
            "player_inventory": self.get_inventory(),
        }

    def unequip_slot(self, slot: str) -> dict:
        from item_system import ITEMS_DB
        if slot not in EQUIP_SLOTS:
            return {"success": False, "message": "无效的装备槽位"}

        item_id = self.equipment.get(slot)
        if not item_id:
            return {"success": False, "message": "该槽位没有装备"}

        item_info = ITEMS_DB.get(item_id, {})
        self.add_item(item_id, 1)
        self.equipment[slot] = None
        self._recalc_stats()

        return {
            "success": True,
            "message": f"卸下了{item_info.get('name', item_id)}",
            "equipment": self._get_equipment_detail(),
            "player_attack": self.attack,
            "player_defense": self.defense,
            "player_speed": self.speed,
            "player_max_hp": self.max_hp,
            "player_hp": self.hp,
            "player_inventory": self.get_inventory(),
        }

    def _get_equipment_detail(self) -> dict:
        from item_system import ITEMS_DB
        result = {}
        for slot_name in EQUIP_SLOTS:
            item_id = self.equipment.get(slot_name)
            if item_id:
                info = ITEMS_DB.get(item_id, {})
                result[slot_name] = {
                    "item_id": item_id,
                    "name": info.get("name", item_id),
                    "type": info.get("type", "unknown"),
                    "description": info.get("description", ""),
                    "stats": info.get("stats", {}),
                    "rarity": info.get("rarity", "common"),
                    "tier": info.get("tier"),
                    "level_range": info.get("level_range"),
                    "affixes": info.get("affixes", []),
                }
            else:
                result[slot_name] = None
        return result

    def get_equipment_info(self) -> dict:
        bonus = self._calc_equip_bonus()
        cls = self.classes[self.class_id]
        level_bonus = self.level - 1
        base_stats = {
            "attack": cls["base_attack"] + level_bonus * 3,
            "defense": cls["base_defense"] + level_bonus * 2,
            "speed": cls["base_speed"] + level_bonus * 1,
            "max_hp": cls["base_hp"] + level_bonus * 10,
            "max_mp": cls.get("base_mp", 30) + level_bonus * 3,
        }
        return {
            "equipment": self._get_equipment_detail(),
            "base_stats": base_stats,
            "equip_bonus": bonus,
            "total_stats": {
                "attack": self.attack,
                "defense": self.defense,
                "speed": self.speed,
                "max_hp": self.max_hp,
                "max_mp": getattr(self, "max_mp", 30),
            },
        }

    # ===== 存档管理 =====

    @staticmethod
    def list_saves() -> list[dict]:
        saves = []
        for slot in range(1, SAVE_SLOTS + 1):
            path = save_path(slot)
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    saves.append({
                        "slot": slot,
                        "name": data.get("name", "未知"),
                        "class_id": data.get("class_id", "warrior"),
                        "level": data.get("level", 1),
                        "save_time": data.get("save_time", ""),
                        "exists": True,
                    })
                except (json.JSONDecodeError, KeyError):
                    saves.append({"slot": slot, "exists": False})
            else:
                saves.append({"slot": slot, "exists": False})
        return saves

    def new_game(self, name: str, class_id: str, slot: int) -> bool:
        if class_id not in self.classes:
            return False
        if slot < 1 or slot > SAVE_SLOTS:
            return False
        defaults = load_defaults()
        self._reset_to_defaults(defaults)
        self.name = name
        self.class_id = class_id
        cls = self.classes[class_id]
        self.max_hp = cls["base_hp"]
        self.hp = self.max_hp
        self.max_mp = cls.get("base_mp", 30)
        self.mp = self.max_mp
        self.attack = cls["base_attack"]
        self.defense = cls["base_defense"]
        self.speed = cls["base_speed"]
        self.skills = list(defaults.get("skills", {}).get(class_id, []))
        self.learned_skills = []
        self.current_slot = slot
        self._save()
        return True

    def load_from_slot(self, slot: int) -> bool:
        return self._load_from_file(slot)

    def delete_slot(self, slot: int) -> bool:
        folder = save_dir(slot)
        if folder.exists():
            import shutil
            shutil.rmtree(folder)
            if self.current_slot == slot:
                self.current_slot = None
                self._reset_to_defaults()
            return True
        return False

    def get_class_name(self) -> str:
        return self.classes.get(self.class_id, {}).get("name", "未知")

    def get_class_desc(self) -> str:
        return self.classes.get(self.class_id, {}).get("description", "")

    def gain_exp(self, amount: int) -> dict:
        self.exp += amount
        leveled = False
        level_ups = 0
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            level_ups += 1
            self._level_up()
            leveled = True
        self._save()
        return {
            "leveled": leveled,
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
            "level_ups": level_ups,
        }

    def _level_up(self):
        self._recalc_stats()
        self.hp = self.max_hp
        self.mp = self.max_mp
        # 升级后经验值需求增加
        self.exp_to_next = int(self.exp_to_next * 1.5)

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)
        self._save()

    def use_item(self, item_id: str, effect: dict) -> dict:
        """使用消耗品/食物，返回结果。"""
        if not self.remove_item(item_id, 1):
            return {"success": False, "message": "物品不足"}
        msg = ""
        result = {"success": True, "message": msg, "hp": self.hp, "max_hp": self.max_hp}
        if effect["type"] == "heal":
            before = self.hp
            self.heal(effect["value"])
            restored = self.hp - before
            msg = f"恢复了 {restored} 点生命值"
        elif effect["type"] == "restore_mp":
            before = self.mp
            self.mp = min(self.max_mp, self.mp + effect["value"])
            restored = self.mp - before
            msg = f"恢复了 {restored} 点魔法值"
            result["mp"] = self.mp
            result["max_mp"] = self.max_mp
        elif effect["type"] == "cure":
            msg = "解除了状态异常"
        elif effect["type"] == "buff":
            msg = "获得了临时增益效果"
        elif effect["type"] == "learn_skill":
            from skill_system import can_learn_skill
            skill_id = effect["skill_id"]
            all_known = self.skills + self.learned_skills
            can_learn, reason = can_learn_skill(skill_id, self.class_id, self.level, all_known)
            if can_learn:
                if skill_id not in self.skills:
                    self.skills.append(skill_id)
                if skill_id not in self.learned_skills:
                    self.learned_skills.append(skill_id)
                self._save()
                msg = f"学会了新技能！"
            else:
                self.add_item(item_id, 1)
                return {"success": False, "message": f"无法学习：{reason}"}
        result["message"] = msg
        return result

    def take_damage(self, amount: int) -> int:
        actual = max(1, amount - self.defense // 3)
        self.hp = max(0, self.hp - actual)
        self._save()
        return actual

    def set_name(self, name: str):
        self.name = name
        self._save()

    def set_class(self, class_id: str) -> bool:
        if class_id not in self.classes:
            return False
        self.class_id = class_id
        self._recalc_stats()
        return True

    def get_info(self) -> dict:
        from skill_system import format_skill_for_frontend
        return {
            "name": self.name,
            "class_id": self.class_id,
            "class_name": self.get_class_name(),
            "class_desc": self.get_class_desc(),
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mp": getattr(self, "mp", 0),
            "max_mp": getattr(self, "max_mp", 0),
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "status_effects": self.status_effects,
            "gold": self.gold,
            "equipment": self._get_equipment_detail(),
            "skills": [format_skill_for_frontend(s) for s in self.skills],
            "player_x": self.player_x,
            "player_y": self.player_y,
            "current_map": self.current_map,
            "map_states": self.map_states,
        }

    def set_position(self, x: int, y: int):
        self.player_x = x
        self.player_y = y
        self._save()

    def get_position(self) -> dict:
        return {"x": self.player_x, "y": self.player_y}

    def get_classes(self) -> dict:
        return self.classes

    # ===== 统一背包与金币操作 =====

    def get_inventory(self) -> list[dict]:
        from item_system import ITEMS_DB, ITEM_EFFECTS
        result = []
        for item in self.inventory:
            item_id = item["item_id"]
            info = ITEMS_DB.get(item_id, {})
            effect = ITEM_EFFECTS.get(item_id, {})
            heal_value = effect.get("value") if effect.get("type") == "heal" else None
            mp_value = effect.get("value") if effect.get("type") == "restore_mp" else None
            result.append({
                "item_id": item_id,
                "name": info.get("name", item_id),
                "type": info.get("type", "unknown"),
                "description": info.get("description", ""),
                "quantity": item["quantity"],
                "buy_price": info.get("buy_price", 0),
                "sell_price": info.get("sell_price", 0),
                "equip_slot": info.get("equip_slot"),
                "stats": info.get("stats"),
                "heal_value": heal_value,
                "mp_value": mp_value,
                "rarity": info.get("rarity", "common"),
                "tier": info.get("tier"),
                "level_range": info.get("level_range"),
                "affixes": info.get("affixes", []),
                "required_class": info.get("required_class"),
            })
        return result

    def get_item_quantity(self, item_id: str) -> int:
        for item in self.inventory:
            if item["item_id"] == item_id:
                return item["quantity"]
        return 0

    def add_item(self, item_id: str, quantity: int = 1):
        for item in self.inventory:
            if item["item_id"] == item_id:
                item["quantity"] += quantity
                self._save()
                return
        self.inventory.append({"item_id": item_id, "quantity": quantity})
        self._save()

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        for item in self.inventory:
            if item["item_id"] == item_id:
                if item["quantity"] < quantity:
                    return False
                item["quantity"] -= quantity
                if item["quantity"] == 0:
                    self.inventory.remove(item)
                self._save()
                return True
        return False

    def add_gold(self, amount: int):
        self.gold += amount
        self._save()

    def spend_gold(self, amount: int) -> bool:
        if self.gold < amount:
            return False
        self.gold -= amount
        self._save()
        return True


player = PlayerProfile()
