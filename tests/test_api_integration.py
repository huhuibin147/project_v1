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
        client.post("/api/saves/new", json={
            "name": "测试勇者",
            "class_id": "warrior",
            "slot": 1,
        })
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


if __name__ == "__main__":
    unittest.main()
