import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"
DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_FILE = CONFIG_DIR / "player_default.json"
SAVE_FILE = DATA_DIR / "player_save.json"


def load_defaults() -> dict:
    with open(DEFAULT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


class PlayerProfile:
    def __init__(self):
        defaults = load_defaults()
        self.name = defaults["name"]
        self.class_id = defaults["class"]
        self.classes = defaults["classes"]
        self.level = defaults["level"]
        self.exp = defaults["exp"]
        self.exp_to_next = defaults["exp_to_next"]
        self.status_effects = defaults["status_effects"]

        # 从职业配置计算基础属性
        cls = self.classes[self.class_id]
        self.max_hp = cls["base_hp"]
        self.hp = self.max_hp
        self.attack = cls["base_attack"]
        self.defense = cls["base_defense"]
        self.speed = cls["base_speed"]

        # 统一钱包与背包
        self.gold = 0
        self.inventory = []  # [{item_id, quantity}]

        self._load()

    def _save(self):
        DATA_DIR.mkdir(exist_ok=True)
        data = {
            "name": self.name,
            "class_id": self.class_id,
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "status_effects": self.status_effects,
            "gold": self.gold,
            "inventory": self.inventory,
        }
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self):
        if not SAVE_FILE.exists():
            self._save()
            return
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.name = data.get("name", self.name)
            self.class_id = data.get("class_id", self.class_id)
            self.level = data.get("level", self.level)
            self.exp = data.get("exp", self.exp)
            self.exp_to_next = data.get("exp_to_next", self.exp_to_next)
            self.hp = data.get("hp", self.hp)
            self.max_hp = data.get("max_hp", self.max_hp)
            self.attack = data.get("attack", self.attack)
            self.defense = data.get("defense", self.defense)
            self.speed = data.get("speed", self.speed)
            self.status_effects = data.get("status_effects", [])
            self.gold = data.get("gold", 0)
            self.inventory = data.get("inventory", [])
        except (json.JSONDecodeError, KeyError):
            self._save()

    def get_class_name(self) -> str:
        return self.classes.get(self.class_id, {}).get("name", "未知")

    def get_class_desc(self) -> str:
        return self.classes.get(self.class_id, {}).get("description", "")

    def gain_exp(self, amount: int) -> dict:
        """获得经验值，返回是否升级。"""
        self.exp += amount
        leveled = False
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self._level_up()
            leveled = True
        self._save()
        return {
            "leveled": leveled,
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
        }

    def _level_up(self):
        """升级时属性增长。"""
        self.max_hp += 10
        self.hp = self.max_hp  # 升级回满血
        self.attack += 3
        self.defense += 2
        self.speed += 1
        self.exp_to_next = int(self.exp_to_next * 1.5)

    def heal(self, amount: int):
        """回复生命值。"""
        self.hp = min(self.max_hp, self.hp + amount)
        self._save()

    def take_damage(self, amount: int) -> int:
        """受到伤害，返回实际伤害值。"""
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
        cls = self.classes[class_id]
        self.max_hp = cls["base_hp"] + (self.level - 1) * 10
        self.hp = min(self.hp, self.max_hp)
        self.attack = cls["base_attack"] + (self.level - 1) * 3
        self.defense = cls["base_defense"] + (self.level - 1) * 2
        self.speed = cls["base_speed"] + (self.level - 1) * 1
        self._save()
        return True

    def get_info(self) -> dict:
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
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "status_effects": self.status_effects,
            "gold": self.gold,
        }

    def get_classes(self) -> dict:
        return self.classes

    # ===== 统一背包与金币操作 =====

    def get_inventory(self) -> list[dict]:
        """返回带物品详情的背包列表。"""
        from item_system import ITEMS_DB
        result = []
        for item in self.inventory:
            item_id = item["item_id"]
            info = ITEMS_DB.get(item_id, {})
            result.append({
                "item_id": item_id,
                "name": info.get("name", item_id),
                "type": info.get("type", "unknown"),
                "description": info.get("description", ""),
                "quantity": item["quantity"],
                "buy_price": info.get("buy_price", 0),
                "sell_price": info.get("sell_price", 0),
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


# 全局单例
player = PlayerProfile()
