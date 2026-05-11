"""层级3：地图系统测试 - 地图数据完整性、可达性、封闭区域、传送门校验"""
import json
import unittest
from pathlib import Path
from collections import deque

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
MAPS_DIR = CONFIG_DIR / "maps"


def _load_tiles():
    tiles_file = CONFIG_DIR / "tiles.json"
    with open(tiles_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _is_walkable(tiles_config, tile_id):
    tile_info = tiles_config.get(str(tile_id), {})
    return tile_info.get("walkable", True)


class TestMapSystem(unittest.TestCase):
    """地图系统测试"""

    @classmethod
    def setUpClass(cls):
        cls.tiles_config = _load_tiles()
        cls.maps = {}
        if MAPS_DIR.exists():
            for fp in MAPS_DIR.glob("*.json"):
                with open(fp, "r", encoding="utf-8") as f:
                    cls.maps[fp.stem] = json.load(f)

    # ---- MAP-01: 地图 JSON 可解析 ----

    def test_map_01_parseable(self):
        self.assertGreater(len(self.maps), 0, "没有找到任何地图文件")
        for map_id, map_data in self.maps.items():
            with self.subTest(map=map_id):
                self.assertIsInstance(map_data, dict)
                self.assertIn("layers", map_data)

    # ---- MAP-02: 地图尺寸与声明一致 ----

    def test_map_02_dimensions_match(self):
        for map_id, map_data in self.maps.items():
            ground = map_data.get("layers", {}).get("ground", [])
            declared_height = map_data.get("height", 0)
            declared_width = map_data.get("width", 0)
            with self.subTest(map=map_id):
                self.assertEqual(len(ground), declared_height,
                                 f"地图 {map_id}: 实际高度 {len(ground)} != 声明 {declared_height}")
                if ground:
                    self.assertEqual(len(ground[0]), declared_width,
                                     f"地图 {map_id}: 实际宽度 {len(ground[0])} != 声明 {declared_width}")

    # ---- MAP-03: 玩家出生点在可行走格子上 ----

    def test_map_03_spawn_walkable(self):
        for map_id, map_data in self.maps.items():
            spawn = map_data.get("player_spawn", {})
            sx, sy = spawn.get("x", -1), spawn.get("y", -1)
            ground = map_data.get("layers", {}).get("ground", [])
            with self.subTest(map=map_id):
                self.assertTrue(0 <= sy < len(ground), f"地图 {map_id}: 出生点 y 超出范围")
                if 0 <= sy < len(ground) and 0 <= sx < len(ground[0]):
                    tile_id = ground[sy][sx]
                    self.assertTrue(_is_walkable(self.tiles_config, tile_id),
                                    f"地图 {map_id}: 出生点 ({sx},{sy}) 瓦片 {tile_id} 不可行走")

    # ---- MAP-04: 所有 NPC 在可行走格子上 ----

    def test_map_04_npcs_walkable(self):
        for map_id, map_data in self.maps.items():
            ground = map_data.get("layers", {}).get("ground", [])
            npcs = map_data.get("npcs", [])
            for npc in npcs:
                nx, ny = npc.get("x", -1), npc.get("y", -1)
                with self.subTest(map=map_id, npc=npc.get("npc_id", "unknown")):
                    if 0 <= ny < len(ground) and 0 <= nx < len(ground[0]):
                        tile_id = ground[ny][nx]
                        self.assertTrue(_is_walkable(self.tiles_config, tile_id),
                                        f"地图 {map_id}: NPC {npc.get('npc_id')} 在 ({nx},{ny}) 瓦片 {tile_id} 不可行走")

    # ---- MAP-05: 所有传送门在可行走格子上 ----

    def test_map_05_portals_walkable(self):
        for map_id, map_data in self.maps.items():
            ground = map_data.get("layers", {}).get("ground", [])
            for obj in map_data.get("objects", []):
                if obj.get("type") == "portal":
                    ox, oy = obj.get("x", -1), obj.get("y", -1)
                    with self.subTest(map=map_id, portal=obj.get("id", "unknown")):
                        if 0 <= oy < len(ground) and 0 <= ox < len(ground[0]):
                            tile_id = ground[oy][ox]
                            self.assertTrue(_is_walkable(self.tiles_config, tile_id),
                                            f"地图 {map_id}: 传送门 {obj.get('id')} 在 ({ox},{oy}) 瓦片 {tile_id} 不可行走")

    # ---- MAP-06: 所有采集点在可行走格子上 ----

    def test_map_06_gather_points_walkable(self):
        for map_id, map_data in self.maps.items():
            ground = map_data.get("layers", {}).get("ground", [])
            for obj in map_data.get("objects", []):
                if obj.get("type") == "gather":
                    ox, oy = obj.get("x", -1), obj.get("y", -1)
                    with self.subTest(map=map_id, gather=obj.get("id", "unknown")):
                        if 0 <= oy < len(ground) and 0 <= ox < len(ground[0]):
                            tile_id = ground[oy][ox]
                            self.assertTrue(_is_walkable(self.tiles_config, tile_id),
                                            f"地图 {map_id}: 采集点 {obj.get('id')} 在 ({ox},{oy}) 瓦片 {tile_id} 不可行走")

    # ---- MAP-07: 无四面封闭区域 ----

    def test_map_07_no_enclosed_areas(self):
        for map_id, map_data in self.maps.items():
            ground = map_data.get("layers", {}).get("ground", [])
            if not ground:
                continue
            height = len(ground)
            width = len(ground[0])
            spawn = map_data.get("player_spawn", {})
            start_x, start_y = spawn.get("x", width // 2), spawn.get("y", height // 2)

            reachable = set()
            queue = deque([(start_x, start_y)])
            reachable.add((start_x, start_y))

            while queue:
                cx, cy = queue.popleft()
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in reachable:
                        if _is_walkable(self.tiles_config, ground[ny][nx]):
                            reachable.add((nx, ny))
                            queue.append((nx, ny))

            enclosed_count = 0
            for y in range(height):
                for x in range(width):
                    if (x, y) not in reachable and _is_walkable(self.tiles_config, ground[y][x]):
                        enclosed_count += 1

            with self.subTest(map=map_id):
                self.assertEqual(enclosed_count, 0,
                                 f"地图 {map_id} 有 {enclosed_count} 个不可达的可行走格子（封闭区域）")

    # ---- MAP-08: 传送门不重叠 ----

    def test_map_08_portals_no_overlap(self):
        for map_id, map_data in self.maps.items():
            portal_positions = {}
            for obj in map_data.get("objects", []):
                if obj.get("type") == "portal":
                    pos = (obj.get("x"), obj.get("y"))
                    if pos in portal_positions:
                        with self.subTest(map=map_id, pos=pos):
                            self.fail(f"地图 {map_id}: 传送门 {obj.get('id')} 与 {portal_positions[pos]} 在同一位置 {pos}")
                    portal_positions[pos] = obj.get("id")

    # ---- MAP-09: 传送门之间距离 >= 3 ----

    def test_map_09_portal_distance(self):
        min_distance = 3
        for map_id, map_data in self.maps.items():
            portals = [obj for obj in map_data.get("objects", []) if obj.get("type") == "portal"]
            for i in range(len(portals)):
                for j in range(i + 1, len(portals)):
                    p1, p2 = portals[i], portals[j]
                    dist = abs(p1.get("x", 0) - p2.get("x", 0)) + abs(p1.get("y", 0) - p2.get("y", 0))
                    with self.subTest(map=map_id, p1=p1.get("id"), p2=p2.get("id")):
                        self.assertGreaterEqual(dist, min_distance,
                                                f"地图 {map_id}: 传送门 {p1.get('id')} 和 {p2.get('id')} 距离 {dist} < {min_distance}")

    # ---- MAP-10: 地图连通性 ----

    def test_map_10_map_connectivity(self):
        map_graph = {}
        for map_id, map_data in self.maps.items():
            map_graph[map_id] = set()
            for obj in map_data.get("objects", []):
                if obj.get("type") == "portal":
                    target = obj.get("properties", {}).get("target_map", "")
                    if target:
                        map_graph[map_id].add(target)

        if not map_graph:
            return

        start_map = next(iter(map_graph))
        visited = set()
        queue = deque([start_map])
        visited.add(start_map)
        while queue:
            current = queue.popleft()
            for neighbor in map_graph.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        unreachable = set(map_graph.keys()) - visited
        self.assertEqual(len(unreachable), 0,
                         f"以下地图无法从 {start_map} 到达: {unreachable}")

    # ---- MAP-11: 传送门目标地图存在 ----

    def test_map_11_portal_target_exists(self):
        for map_id, map_data in self.maps.items():
            for obj in map_data.get("objects", []):
                if obj.get("type") == "portal":
                    target = obj.get("properties", {}).get("target_map", "")
                    with self.subTest(map=map_id, portal=obj.get("id")):
                        self.assertIn(target, self.maps,
                                      f"地图 {map_id}: 传送门 {obj.get('id')} 目标地图 '{target}' 不存在")

    # ---- MAP-12: 传送门目标位置可行走 ----

    def test_map_12_portal_target_walkable(self):
        for map_id, map_data in self.maps.items():
            for obj in map_data.get("objects", []):
                if obj.get("type") == "portal":
                    target_map = obj.get("properties", {}).get("target_map", "")
                    target_x = obj.get("properties", {}).get("target_x", -1)
                    target_y = obj.get("properties", {}).get("target_y", -1)
                    target_data = self.maps.get(target_map)
                    if not target_data:
                        continue
                    ground = target_data.get("layers", {}).get("ground", [])
                    with self.subTest(map=map_id, portal=obj.get("id")):
                        if 0 <= target_y < len(ground) and 0 <= target_x < len(ground[0]):
                            tile_id = ground[target_y][target_x]
                            self.assertTrue(_is_walkable(self.tiles_config, tile_id),
                                            f"地图 {map_id}: 传送门 {obj.get('id')} 目标位置 ({target_x},{target_y}) 瓦片 {tile_id} 不可行走")

    # ---- MAP-13: 宝箱在可行走格子上 ----

    def test_map_13_chests_walkable(self):
        for map_id, map_data in self.maps.items():
            ground = map_data.get("layers", {}).get("ground", [])
            for obj in map_data.get("objects", []):
                if obj.get("type") == "chest":
                    ox, oy = obj.get("x", -1), obj.get("y", -1)
                    with self.subTest(map=map_id, chest=obj.get("id", "unknown")):
                        if 0 <= oy < len(ground) and 0 <= ox < len(ground[0]):
                            tile_id = ground[oy][ox]
                            self.assertTrue(_is_walkable(self.tiles_config, tile_id),
                                            f"地图 {map_id}: 宝箱 {obj.get('id')} 在 ({ox},{oy}) 瓦片 {tile_id} 不可行走")

    # ---- MAP-14: 怪物在可行走格子上 ----

    def test_map_14_monsters_walkable(self):
        for map_id, map_data in self.maps.items():
            ground = map_data.get("layers", {}).get("ground", [])
            for monster in map_data.get("monsters", []):
                mx, my = monster.get("x", -1), monster.get("y", -1)
                with self.subTest(map=map_id, monster=monster.get("monster_id", "unknown")):
                    if 0 <= my < len(ground) and 0 <= mx < len(ground[0]):
                        tile_id = ground[my][mx]
                        self.assertTrue(_is_walkable(self.tiles_config, tile_id),
                                        f"地图 {map_id}: 怪物 {monster.get('monster_id')} 在 ({mx},{my}) 瓦片 {tile_id} 不可行走")


if __name__ == "__main__":
    unittest.main()
