"""层级4：API 集成测试 - 使用 FastAPI TestClient 测试所有 API 端点"""
import json
import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
CONFIG_DIR = ROOT_DIR / "config"
TEST_DATA_DIR = ROOT_DIR / "data" / "save_test"


class TestAPIIntegration(unittest.TestCase):
    """API 集成测试"""

    @classmethod
    def setUpClass(cls):
        if TEST_DATA_DIR.exists():
            shutil.rmtree(TEST_DATA_DIR)
        TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if TEST_DATA_DIR.exists():
            shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)

    def _get_client(self):
        modules_to_clear = ["main", "player_profile", "npc_agent", "quest_manager", "npc_dialogue", "item_system", "skill_system", "combat_engine"]
        for mod in modules_to_clear:
            sys.modules.pop(mod, None)

        import player_profile
        import npc_agent
        player_profile.DATA_DIR = TEST_DATA_DIR
        npc_agent.DATA_DIR = TEST_DATA_DIR

        from fastapi.testclient import TestClient
        from main import app
        import main
        main.DATA_DIR = TEST_DATA_DIR

        client = TestClient(app)
        return client

    def _create_new_game(self, client):
        """Helper: create a new game"""
        resp = client.post("/api/saves/new", json={
            "name": "测试勇者",
            "class_id": "warrior",
            "slot": 1,
        })
        self.assertEqual(resp.status_code, 200)
        return resp.json()

    # ---- API-01: GET /api/player ----

    def test_api_01_get_player(self):
        client = self._get_client()
        resp = client.get("/api/player")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("name", data)
        self.assertIn("level", data)
        self.assertIn("hp", data)
        self.assertIn("max_hp", data)
        self.assertIn("attack", data)
        self.assertIn("defense", data)

    # ---- API-02: POST /api/player/position ----

    def test_api_02_save_position(self):
        client = self._get_client()
        resp = client.post("/api/player/position", json={"x": 10, "y": 15})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))

    # ---- API-03: GET /api/npcs ----

    def test_api_03_get_npcs(self):
        client = self._get_client()
        resp = client.get("/api/npcs")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        if data:
            self.assertIn("npc_id", data[0])
            self.assertIn("name", data[0])

    # ---- API-04: GET /api/inventory ----

    def test_api_04_get_inventory(self):
        client = self._get_client()
        resp = client.get("/api/inventory")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("items", data)
        self.assertIn("gold", data)

    # ---- API-05: GET /api/equipment ----

    def test_api_05_get_equipment(self):
        client = self._get_client()
        resp = client.get("/api/equipment")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("equipment", data)

    # ---- API-06: GET /api/quests ----

    def test_api_06_get_quests(self):
        client = self._get_client()
        resp = client.get("/api/quests")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("quests", data)

    # ---- API-07: GET /api/quests/active ----

    def test_api_07_get_active_quests(self):
        client = self._get_client()
        resp = client.get("/api/quests/active")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("quests", data)

    # ---- API-08: GET /api/map/tiles ----

    def test_api_08_get_tiles(self):
        client = self._get_client()
        resp = client.get("/api/map/tiles")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, dict)

    # ---- API-09: GET /api/map/{map_id} ----

    def test_api_09_get_map(self):
        client = self._get_client()
        resp = client.get("/api/map/village")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("id", data)
        self.assertIn("layers", data)
        self.assertEqual(data["id"], "village")

    def test_api_09_get_map_not_found(self):
        client = self._get_client()
        resp = client.get("/api/map/nonexistent_map")
        self.assertEqual(resp.status_code, 404)

    # ---- API-10: GET /api/monsters ----

    def test_api_10_get_monsters(self):
        client = self._get_client()
        resp = client.get("/api/monsters")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, dict)

    # ---- API-11: GET /api/talents ----

    def test_api_11_get_talents(self):
        client = self._get_client()
        resp = client.get("/api/talents")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("trees", data)

    # ---- API-12: GET /api/saves ----

    def test_api_12_get_saves(self):
        client = self._get_client()
        resp = client.get("/api/saves")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("saves", data)

    # ---- API-13: POST /api/saves/new ----

    def test_api_13_new_game(self):
        client = self._get_client()
        resp = client.post("/api/saves/new", json={
            "name": "测试勇者",
            "class_id": "warrior",
            "slot": 1,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertIn("player_info", data)

    # ---- API-14: POST /api/saves/load ----

    def test_api_14_load_save(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.post("/api/saves/load", json={"slot": 1})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))

    # ---- API-15: POST /api/map/transfer ----

    def test_api_15_map_transfer(self):
        client = self._get_client()
        resp = client.post("/api/map/transfer", json={
            "target_map": "forest",
            "target_x": 30,
            "target_y": 26,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))

    def test_api_15_map_transfer_not_found(self):
        client = self._get_client()
        resp = client.post("/api/map/transfer", json={
            "target_map": "nonexistent",
            "target_x": 0,
            "target_y": 0,
        })
        self.assertEqual(resp.status_code, 404)

    # ---- API-16: GET /api/player/classes ----

    def test_api_16_get_classes(self):
        client = self._get_client()
        resp = client.get("/api/player/classes")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("warrior", data)

    # ---- API-17: NPC 配置接口 ----

    def test_api_17_npc_config(self):
        client = self._get_client()
        with open(CONFIG_DIR / "npcs.json", "r", encoding="utf-8") as f:
            npcs = json.load(f)
        if npcs:
            first_npc_id = list(npcs.keys())[0]
            resp = client.get(f"/api/npc/config?npc_id={first_npc_id}")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("name", data)

    # ---- API-18: 商店接口 ----

    def test_api_18_get_shop(self):
        client = self._get_client()
        with open(CONFIG_DIR / "npcs.json", "r", encoding="utf-8") as f:
            npcs = json.load(f)
        shop_npcs = [nid for nid, cfg in npcs.items() if "shop" in cfg]
        if shop_npcs:
            resp = client.get(f"/api/shop?npc_id={shop_npcs[0]}")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("items", data)

    # ---- API-19: POST /api/chat ----

    def test_api_19_chat(self):
        client = self._get_client()
        with open(CONFIG_DIR / "npcs.json", "r", encoding="utf-8") as f:
            npcs = json.load(f)
        first_npc_id = list(npcs.keys())[0]
        resp = client.post("/api/chat", json={
            "message": "你好",
            "npc_id": first_npc_id,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("reply", data)

    # ---- API-20: POST /api/trade ----

    def test_api_20_trade_buy(self):
        client = self._get_client()
        self._create_new_game(client)
        with open(CONFIG_DIR / "npcs.json", "r", encoding="utf-8") as f:
            npcs = json.load(f)
        shop_npcs = [nid for nid, cfg in npcs.items() if "shop" in cfg]
        if shop_npcs:
            npc_id = shop_npcs[0]
            shop_resp = client.get(f"/api/shop?npc_id={npc_id}")
            self.assertEqual(shop_resp.status_code, 200)
            shop_data = shop_resp.json()
            if shop_data.get("items"):
                item_id = shop_data["items"][0]["item_id"]
                trade_resp = client.post("/api/trade", json={
                    "action": "buy",
                    "item_id": item_id,
                    "quantity": 1,
                    "npc_id": npc_id,
                })
                self.assertEqual(trade_resp.status_code, 200)
                trade_data = trade_resp.json()
                self.assertIn("success", trade_data)

    # ---- API-21: POST /api/equip ----

    def test_api_21_equip_item(self):
        client = self._get_client()
        self._create_new_game(client)
        client.post("/api/trade", json={
            "action": "buy",
            "item_id": "wood_sword",
            "quantity": 1,
            "npc_id": "blacksmith",
        })
        resp = client.post("/api/equip", json={"item_id": "wood_sword"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("success", data)

    # ---- API-22: POST /api/unequip ----

    def test_api_22_unequip_item(self):
        client = self._get_client()
        self._create_new_game(client)
        client.post("/api/trade", json={
            "action": "buy",
            "item_id": "wood_sword",
            "quantity": 1,
            "npc_id": "blacksmith",
        })
        client.post("/api/equip", json={"item_id": "wood_sword"})
        resp = client.post("/api/unequip", json={"slot": "weapon"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("success", data)

    # ---- API-23: POST /api/use_item ----

    def test_api_23_use_item(self):
        client = self._get_client()
        self._create_new_game(client)
        client.post("/api/trade", json={
            "action": "buy",
            "item_id": "health_potion",
            "quantity": 1,
            "npc_id": "blacksmith",
        })
        resp = client.post("/api/use_item", json={"item_id": "health_potion"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("success", data)

    # ---- API-24: POST /api/map/object/interact ----

    def test_api_24_object_interact(self):
        client = self._get_client()
        resp = client.post("/api/map/object/interact", json={
            "map_id": "village",
            "object_id": "test_object",
            "action": "interact",
        })
        self.assertIn(resp.status_code, [200, 404])

    # ---- API-25: POST /api/talents/learn ----

    def test_api_25_talents_learn(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.post("/api/talents/learn", json={"talent_id": "test_talent"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("success", data)

    # ---- API-26: POST /api/talents/reset ----

    def test_api_26_talents_reset(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.post("/api/talents/reset")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("success", data)

    # ---- API-27: POST /api/quests/accept ----

    def test_api_27_quest_accept(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.get("/api/quests")
        data = resp.json()
        if data.get("quests"):
            # quests is a list, get first quest_id
            first_quest = data["quests"][0]
            quest_id = first_quest.get("quest_id") or first_quest.get("id")
            if quest_id:
                resp = client.post("/api/quests/accept", json={"quest_id": quest_id})
                self.assertEqual(resp.status_code, 200)
                accept_data = resp.json()
                self.assertIn("success", accept_data)

    # ---- API-28: POST /api/quests/abandon ----

    def test_api_28_quest_abandon(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.post("/api/quests/abandon", json={"quest_id": "test_quest"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("success", data)

    # ---- API-29: POST /api/quests/complete ----

    def test_api_29_quest_complete(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.post("/api/quests/complete", json={"quest_id": "test_quest"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("success", data)

    # ---- API-30: POST /api/quests/progress ----

    def test_api_30_quest_progress(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.post("/api/quests/progress", json={
            "event_type": "explore",
            "data": {"map_id": "village", "x": 25, "y": 20},
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("updated", data)

    # ---- API-31: DELETE /api/saves/{slot} ----

    def test_api_31_delete_save(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.delete("/api/saves/1")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))

    # ---- API-32: POST /api/combat/start ----

    def test_api_32_combat_start(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.get("/api/monsters")
        monsters_data = resp.json()
        if monsters_data.get("monsters"):
            first_monster = list(monsters_data["monsters"].values())[0]
            monster_instance_id = first_monster.get("id", "wolf")
            resp = client.post("/api/combat/start", json={
                "monster_instance_id": monster_instance_id,
                "map_id": "village",
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("session_id", data)
            if data.get("session_id"):
                client.post("/api/combat/end", json={"session_id": data["session_id"]})

    # ---- API-33: POST /api/combat/action ----

    def test_api_33_combat_action(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.get("/api/monsters")
        monsters_data = resp.json()
        if monsters_data.get("monsters"):
            first_monster = list(monsters_data["monsters"].values())[0]
            monster_instance_id = first_monster.get("id", "wolf")
            start_resp = client.post("/api/combat/start", json={
                "monster_instance_id": monster_instance_id,
                "map_id": "village",
            })
            if start_resp.status_code == 200:
                session_id = start_resp.json().get("session_id")
                if session_id:
                    action_resp = client.post("/api/combat/action", json={
                        "session_id": session_id,
                        "action": "attack",
                    })
                    self.assertEqual(action_resp.status_code, 200)
                    client.post("/api/combat/end", json={"session_id": session_id})

    # ---- API-34: GET /api/npc/status ----

    def test_api_34_npc_status(self):
        client = self._get_client()
        with open(CONFIG_DIR / "npcs.json", "r", encoding="utf-8") as f:
            npcs = json.load(f)
        first_npc_id = list(npcs.keys())[0]
        resp = client.get(f"/api/npc/status?npc_id={first_npc_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("name", data)

    # ---- API-35: GET /api/npc/history ----

    def test_api_35_npc_history(self):
        client = self._get_client()
        with open(CONFIG_DIR / "npcs.json", "r", encoding="utf-8") as f:
            npcs = json.load(f)
        first_npc_id = list(npcs.keys())[0]
        resp = client.get(f"/api/npc/history?npc_id={first_npc_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("history", data)

    # ---- API-36: POST /api/npc/service/heal ----

    def test_api_36_npc_heal_service(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.post("/api/npc/service/heal", json={
            "npc_id": "priest",
            "service_type": "heal",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("success", data)

    # ---- API-37: GET /api/npc/service/skills ----

    def test_api_37_npc_skills(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.get("/api/npc/service/skills?npc_id=skill_master")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("success", data)

    # ---- API-38: POST /api/npc/service/learn_skill ----

    def test_api_38_npc_learn_skill(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.post("/api/npc/service/learn_skill", json={
            "npc_id": "skill_master",
            "skill_id": "test_skill",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("success", data)

    # ---- API-39: GET /api/forge/recipes ----

    def test_api_39_forge_recipes(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.get("/api/forge/recipes?npc_id=blacksmith")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("recipes", data)

    # ---- API-40: POST /api/forge/craft ----

    def test_api_40_forge_craft(self):
        client = self._get_client()
        self._create_new_game(client)
        resp = client.get("/api/forge/recipes?npc_id=blacksmith")
        data = resp.json()
        if data.get("recipes"):
            recipe_id = data["recipes"][0].get("recipe_id")
            if recipe_id:
                resp = client.post("/api/forge/craft", json={
                    "recipe_id": recipe_id,
                    "npc_id": "blacksmith",
                })
                self.assertEqual(resp.status_code, 200)
                craft_data = resp.json()
                self.assertIn("success", craft_data)


if __name__ == "__main__":
    unittest.main()
