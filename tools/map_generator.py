#!/usr/bin/env python3
"""
地图生成器 - 用于创建和管理游戏地图

功能：
1. 生成新地图（支持村庄、森林、洞穴、城镇等模板）
2. 格式化现有地图JSON（紧凑数组格式）
3. 扩展现有地图尺寸
4. 修复地图边界问题
5. 验证地图（检查封闭区域、可达性等）
6. 可视化预览地图布局
7. 批量操作

使用方法：
  python map_generator.py generate village my_village    # 生成新村庄地图
  python map_generator.py generate forest my_forest      # 生成新森林地图
  python map_generator.py generate cave my_cave          # 生成新洞穴地图
  python map_generator.py format                         # 格式化所有地图JSON
  python map_generator.py expand village 60 50           # 扩展地图尺寸
  python map_generator.py fix village                    # 修复地图边界
  python map_generator.py fix all                        # 修复所有地图
  python map_generator.py validate village               # 验证地图
  python map_generator.py preview village                # 预览地图布局
  python map_generator.py list                           # 列出所有地图
"""

import json
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from collections import deque

# 瓦片类型定义
TILES = {
    0: {"name": "草地", "symbol": ".", "color": "\033[32m", "walkable": True},
    1: {"name": "泥土路", "symbol": "·", "color": "\033[33m", "walkable": True},
    2: {"name": "水面", "symbol": "~", "color": "\033[34m", "walkable": False},
    3: {"name": "木桥", "symbol": "=", "color": "\033[33m", "walkable": True},
    4: {"name": "墙/边界", "symbol": "#", "color": "\033[37m", "walkable": False},
    5: {"name": "树木", "symbol": "T", "color": "\033[32m", "walkable": False},
    6: {"name": "石头", "symbol": "S", "color": "\033[37m", "walkable": False},
    7: {"name": "花朵", "symbol": "*", "color": "\033[35m", "walkable": True},
    8: {"name": "栅栏", "symbol": "+", "color": "\033[33m", "walkable": False},
    9: {"name": "森林地面", "symbol": ",", "color": "\033[32m", "walkable": True},
    10: {"name": "洞穴地面", "symbol": "_", "color": "\033[90m", "walkable": True},
    11: {"name": "熔岩", "symbol": "!", "color": "\033[31m", "walkable": False},
    12: {"name": "沙地", "symbol": "s", "color": "\033[93m", "walkable": True},
    13: {"name": "雪地", "symbol": "S", "color": "\033[97m", "walkable": True},
    14: {"name": "室内地板", "symbol": "F", "color": "\033[90m", "walkable": True},
    15: {"name": "花丛草地", "symbol": "f", "color": "\033[32m", "walkable": True},
    16: {"name": "小河", "symbol": "r", "color": "\033[34m", "walkable": False},
    17: {"name": "木桥", "symbol": "B", "color": "\033[33m", "walkable": True},
    18: {"name": "灌木丛", "symbol": "b", "color": "\033[32m", "walkable": False},
    19: {"name": "枯树", "symbol": "D", "color": "\033[33m", "walkable": False},
    20: {"name": "花朵", "symbol": "F", "color": "\033[35m", "walkable": True},
    21: {"name": "深草地", "symbol": "g", "color": "\033[32m", "walkable": True},
    22: {"name": "石板", "symbol": "P", "color": "\033[37m", "walkable": True},
    23: {"name": "熔岩", "symbol": "L", "color": "\033[31m", "walkable": False},
    24: {"name": "冰面", "symbol": "I", "color": "\033[96m", "walkable": True},
}

# 结构定义（可放置在地图上的建筑/装饰）
STRUCTURES = {
    "house_small": {
        "name": "小型房屋",
        "width": 5,
        "height": 5,
        "tiles": [
            [4, 4, 4, 4, 4],
            [4, 14, 14, 14, 4],
            [4, 14, 14, 14, 4],
            [4, 14, 14, 14, 4],
            [4, 4, 1, 4, 4],
        ],
        "door": (2, 4),
    },
    "house_medium": {
        "name": "中型房屋",
        "width": 7,
        "height": 6,
        "tiles": [
            [4, 4, 4, 4, 4, 4, 4],
            [4, 14, 14, 14, 14, 14, 4],
            [4, 14, 14, 14, 14, 14, 4],
            [4, 14, 14, 14, 14, 14, 4],
            [4, 14, 14, 14, 14, 14, 4],
            [4, 4, 4, 1, 4, 4, 4],
        ],
        "door": (3, 5),
    },
    "blacksmith": {
        "name": "铁匠铺",
        "width": 8,
        "height": 6,
        "tiles": [
            [4, 4, 4, 4, 4, 4, 4, 4],
            [4, 14, 14, 14, 14, 14, 14, 4],
            [4, 14, 14, 14, 14, 14, 14, 4],
            [4, 14, 14, 14, 14, 14, 14, 4],
            [4, 14, 14, 14, 14, 14, 14, 4],
            [4, 4, 4, 4, 1, 4, 4, 4],
        ],
        "door": (4, 5),
    },
    "shop": {
        "name": "商店",
        "width": 7,
        "height": 5,
        "tiles": [
            [4, 4, 4, 4, 4, 4, 4],
            [4, 14, 14, 14, 14, 14, 4],
            [4, 14, 14, 14, 14, 14, 4],
            [4, 14, 14, 14, 14, 14, 4],
            [4, 4, 1, 4, 4, 4, 4],
        ],
        "door": (2, 4),
    },
    "temple": {
        "name": "神殿",
        "width": 7,
        "height": 7,
        "tiles": [
            [4, 4, 4, 4, 4, 4, 4],
            [4, 22, 22, 22, 22, 22, 4],
            [4, 22, 22, 22, 22, 22, 4],
            [4, 22, 22, 22, 22, 22, 4],
            [4, 22, 22, 22, 22, 22, 4],
            [4, 22, 22, 22, 22, 22, 4],
            [4, 4, 4, 1, 4, 4, 4],
        ],
        "door": (3, 6),
    },
    "academy": {
        "name": "学院",
        "width": 8,
        "height": 7,
        "tiles": [
            [4, 4, 4, 4, 4, 4, 4, 4],
            [4, 22, 22, 22, 22, 22, 22, 4],
            [4, 22, 22, 22, 22, 22, 22, 4],
            [4, 22, 22, 22, 22, 22, 22, 4],
            [4, 22, 22, 22, 22, 22, 22, 4],
            [4, 22, 22, 22, 22, 22, 22, 4],
            [4, 4, 4, 4, 1, 4, 4, 4],
        ],
        "door": (4, 6),
    },
    "tavern": {
        "name": "酒馆",
        "width": 7,
        "height": 6,
        "tiles": [
            [4, 4, 4, 4, 4, 4, 4],
            [4, 14, 14, 14, 14, 14, 4],
            [4, 14, 14, 14, 14, 14, 4],
            [4, 14, 14, 14, 14, 14, 4],
            [4, 14, 14, 14, 14, 14, 4],
            [4, 4, 4, 1, 4, 4, 4],
        ],
        "door": (3, 5),
    },
    "well": {
        "name": "水井",
        "width": 3,
        "height": 3,
        "tiles": [
            [8, 8, 8],
            [8, 2, 8],
            [8, 8, 8],
        ],
    },
    "tree_cluster": {
        "name": "树丛",
        "width": 3,
        "height": 3,
        "tiles": [
            [0, 5, 0],
            [5, 0, 5],
            [0, 5, 0],
        ],
    },
    "pond": {
        "name": "池塘",
        "width": 5,
        "height": 4,
        "tiles": [
            [0, 0, 0, 0, 0],
            [0, 2, 2, 2, 0],
            [0, 2, 2, 2, 0],
            [0, 0, 0, 0, 0],
        ],
    },
    "river_h": {
        "name": "横向河流",
        "width": 5,
        "height": 2,
        "tiles": [
            [16, 16, 16, 16, 16],
            [16, 16, 16, 16, 16],
        ],
    },
    "river_v": {
        "name": "纵向河流",
        "width": 2,
        "height": 5,
        "tiles": [
            [16, 16],
            [16, 16],
            [16, 16],
            [16, 16],
            [16, 16],
        ],
    },
    "bridge_h": {
        "name": "横向桥",
        "width": 5,
        "height": 1,
        "tiles": [[17, 17, 17, 17, 17]],
    },
    "bridge_v": {
        "name": "纵向桥",
        "width": 1,
        "height": 5,
        "tiles": [[17], [17], [17], [17], [17]],
    },
    "fence_h": {
        "name": "横向栅栏",
        "width": 5,
        "height": 1,
        "tiles": [[8, 8, 8, 8, 8]],
    },
    "fence_v": {
        "name": "纵向栅栏",
        "width": 1,
        "height": 5,
        "tiles": [[8], [8], [8], [8], [8]],
    },
    "road_h": {
        "name": "横向道路",
        "width": 5,
        "height": 1,
        "tiles": [[1, 1, 1, 1, 1]],
    },
    "road_v": {
        "name": "纵向道路",
        "width": 1,
        "height": 5,
        "tiles": [[1], [1], [1], [1], [1]],
    },
    "bush_cluster": {
        "name": "灌木丛",
        "width": 3,
        "height": 3,
        "tiles": [
            [0, 18, 0],
            [18, 0, 18],
            [0, 18, 0],
        ],
    },
    "flower_garden": {
        "name": "花坛",
        "width": 3,
        "height": 3,
        "tiles": [
            [0, 20, 0],
            [20, 0, 20],
            [0, 20, 0],
        ],
    },
}

# 地图模板
TEMPLATES = {
    "village": {
        "description": "村庄地图 - 有房屋、道路和NPC",
        "default_size": (50, 40),
        "border_tile": 4,
        "ground_tile": 0,
        "structures": ["house_small", "house_medium", "blacksmith", "shop", "well"],
        "roads": True,
        "decorations": ["pond", "fence_h", "fence_v"],
    },
    "forest": {
        "description": "森林地图 - 有树木、道路和采集点",
        "default_size": (60, 50),
        "border_tile": 4,
        "ground_tile": 9,
        "structures": [],
        "roads": True,
        "decorations": ["tree_cluster", "pond"],
    },
    "cave": {
        "description": "洞穴地图 - 有石头、熔岩和宝箱",
        "default_size": (40, 30),
        "border_tile": 4,
        "ground_tile": 10,
        "structures": [],
        "roads": False,
        "decorations": [],
        "hazards": [11],
    },
    "town": {
        "description": "城镇地图 - 大型村庄，有更多建筑",
        "default_size": (80, 60),
        "border_tile": 4,
        "ground_tile": 0,
        "structures": ["house_small", "house_medium", "blacksmith", "shop", "well"],
        "roads": True,
        "decorations": ["pond", "fence_h", "fence_v"],
    },
    "desert": {
        "description": "沙漠地图 - 有沙地和绿洲",
        "default_size": (50, 50),
        "border_tile": 4,
        "ground_tile": 12,
        "structures": ["well"],
        "roads": True,
        "decorations": ["pond"],
    },
}

MAPS_DIR = Path("config/maps")


class MapGenerator:
    """地图生成器类"""
    
    def __init__(self, maps_dir: Path = None):
        self.maps_dir = maps_dir or MAPS_DIR
        self.maps_dir.mkdir(parents=True, exist_ok=True)
    
    def create_empty_map(self, width: int, height: int, border_tile: int = 4, 
                         ground_tile: int = 0) -> List[List[int]]:
        """创建空白地图"""
        ground = []
        for r in range(height):
            row = []
            for c in range(width):
                if r < 2 or r >= height - 2 or c < 2 or c >= width - 2:
                    row.append(border_tile)
                else:
                    row.append(ground_tile)
            ground.append(row)
        return ground
    
    def place_structure(self, ground: List[List[int]], structure_id: str, 
                        x: int, y: int) -> bool:
        """在地图上放置结构"""
        if structure_id not in STRUCTURES:
            print(f"警告: 未知结构 '{structure_id}'")
            return False
        
        struct = STRUCTURES[structure_id]
        struct_tiles = struct["tiles"]
        struct_height = len(struct_tiles)
        struct_width = len(struct_tiles[0])
        
        height = len(ground)
        width = len(ground[0])
        
        # 检查边界
        if y + struct_height > height - 2 or x + struct_width > width - 2:
            return False
        if y < 2 or x < 2:
            return False
        
        # 放置结构
        for r in range(struct_height):
            for c in range(struct_width):
                ground[y + r][x + c] = struct_tiles[r][c]
        
        return True
    
    def add_road(self, ground: List[List[int]], start: Tuple[int, int], 
                 end: Tuple[int, int], width: int = 1) -> None:
        """添加道路（直线）"""
        x1, y1 = start
        x2, y2 = end
        
        if x1 == x2:
            # 垂直道路
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for w in range(width):
                    if 2 <= x1 + w < len(ground[0]) - 2:
                        ground[y][x1 + w] = 1
        elif y1 == y2:
            # 水平道路
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for w in range(width):
                    if 2 <= y1 + w < len(ground) - 2:
                        ground[y1 + w][x] = 1
    
    def add_random_trees(self, ground: List[List[int]], count: int, 
                         border_tile: int = 4) -> None:
        """随机添加树木"""
        height = len(ground)
        width = len(ground[0])
        
        placed = 0
        attempts = 0
        max_attempts = count * 10
        
        while placed < count and attempts < max_attempts:
            x = random.randint(3, width - 4)
            y = random.randint(3, height - 4)
            
            if ground[y][x] != border_tile and ground[y][x] != 5:
                ground[y][x] = 5
                placed += 1
            
            attempts += 1
    
    def add_random_decorations(self, ground: List[List[int]], 
                               decorations: List[str], count: int) -> None:
        """随机添加装饰物"""
        height = len(ground)
        width = len(ground[0])
        
        for _ in range(count):
            deco = random.choice(decorations)
            if deco not in STRUCTURES:
                continue
            
            struct = STRUCTURES[deco]
            struct_width = struct["width"]
            struct_height = struct["height"]
            
            x = random.randint(3, width - struct_width - 3)
            y = random.randint(3, height - struct_height - 3)
            
            self.place_structure(ground, deco, x, y)
    
    def generate_map(self, map_type: str, map_id: str, 
                     width: int = None, height: int = None,
                     name: str = None) -> Dict:
        """生成完整地图"""
        if map_type not in TEMPLATES:
            raise ValueError(f"未知的地图类型: {map_type}")
        
        template = TEMPLATES[map_type]
        width = width or template["default_size"][0]
        height = height or template["default_size"][1]
        
        border_tile = template["border_tile"]
        ground_tile = template["ground_tile"]
        
        # 创建基础地图
        ground = self.create_empty_map(width, height, border_tile, ground_tile)
        
        # 根据类型添加内容
        if map_type == "village":
            self._generate_village_content(ground, template)
        elif map_type == "forest":
            self._generate_forest_content(ground, template)
        elif map_type == "cave":
            self._generate_cave_content(ground, template)
        elif map_type == "town":
            self._generate_town_content(ground, template)
        elif map_type == "desert":
            self._generate_desert_content(ground, template)
        
        # 创建地图数据
        map_data = {
            "id": map_id,
            "name": name or map_id,
            "width": width,
            "height": height,
            "tile_size": 32,
            "layers": {
                "ground": ground
            },
            "objects": [],
            "npcs": [],
            "player_spawn": {
                "x": width // 2,
                "y": height // 2
            }
        }
        
        return map_data
    
    def _generate_village_content(self, ground: List[List[int]], 
                                   template: Dict) -> None:
        """生成村庄内容"""
        height = len(ground)
        width = len(ground[0])
        
        # 添加建筑（更合理的布局）
        self.place_structure(ground, "blacksmith", 10, 5)
        self.place_structure(ground, "shop", width - 17, 5)
        self.place_structure(ground, "house_small", 8, height - 10)
        self.place_structure(ground, "house_medium", width - 19, height - 11)
        self.place_structure(ground, "temple", width // 2 - 3, 5)
        
        # 添加主要道路（十字路口）
        road_y = height // 2
        self.add_road(ground, (2, road_y), (width - 3, road_y), width=2)
        self.add_road(ground, (width // 2, 2), (width // 2, height - 3), width=2)
        
        # 添加次要道路
        self.add_road(ground, (10, 10), (10, road_y), width=1)
        self.add_road(ground, (width - 13, 10), (width - 13, road_y), width=1)
        
        # 添加装饰物
        self.place_structure(ground, "well", width // 2 - 1, height // 2 + 5)
        self.place_structure(ground, "pond", 5, height // 2 - 3)
        
        # 添加花朵装饰
        for _ in range(20):
            x = random.randint(3, width - 4)
            y = random.randint(3, height - 4)
            if ground[y][x] == 0:  # 只在草地上放置
                ground[y][x] = random.choice([7, 15, 20])  # 花朵/花丛/花朵
        
        # 添加栅栏围栏
        self.place_structure(ground, "fence_h", 15, height // 2 + 8)
        self.place_structure(ground, "fence_v", 3, height // 2 - 5)
        
        # 添加灌木丛
        for _ in range(8):
            x = random.randint(3, width - 6)
            y = random.randint(3, height - 6)
            if ground[y][x] == 0:
                self.place_structure(ground, "bush_cluster", x, y)
    
    def _generate_forest_content(self, ground: List[List[int]], 
                                  template: Dict) -> None:
        """生成森林内容"""
        height = len(ground)
        width = len(ground[0])
        
        # 添加密集树木（分组放置）
        for _ in range(80):
            x = random.randint(3, width - 4)
            y = random.randint(3, height - 4)
            if ground[y][x] == 9:  # 只在森林地面上放置
                # 创建小树丛
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        if 3 <= nx < width - 3 and 3 <= ny < height - 3:
                            if ground[ny][nx] == 9 and random.random() < 0.6:
                                ground[ny][nx] = 5
        
        # 添加主要道路（十字路口）
        self.add_road(ground, (width // 2, 2), (width // 2, height - 3), width=2)
        self.add_road(ground, (2, height // 2), (width - 3, height // 2), width=2)
        
        # 添加蜿蜒小径
        path_x = width // 4
        for y in range(5, height - 5):
            if random.random() < 0.3:
                path_x += random.choice([-1, 0, 1])
                path_x = max(3, min(width - 4, path_x))
            if ground[y][path_x] == 9:
                ground[y][path_x] = 1
        
        # 添加河流
        river_y = height // 3
        for x in range(3, width - 3):
            if ground[river_y][x] == 9:
                ground[river_y][x] = 16
                if river_y + 1 < height - 3 and ground[river_y + 1][x] == 9:
                    ground[river_y + 1][x] = 16
        
        # 添加桥梁跨越河流
        bridge_x = width // 2
        for dy in range(-1, 2):
            if ground[river_y + dy][bridge_x] == 16:
                ground[river_y + dy][bridge_x] = 17
        
        # 添加池塘和装饰
        self.add_random_decorations(ground, ["pond"], 3)
        
        # 添加花朵、石头和灌木
        for _ in range(30):
            x = random.randint(3, width - 4)
            y = random.randint(3, height - 4)
            if ground[y][x] == 9:
                ground[y][x] = random.choice([7, 6, 18, 19])  # 花朵/石头/灌木/枯树
        
        # 添加深草地
        for _ in range(20):
            x = random.randint(3, width - 4)
            y = random.randint(3, height - 4)
            if ground[y][x] == 9:
                ground[y][x] = 21
    
    def _generate_cave_content(self, ground: List[List[int]], 
                                template: Dict) -> None:
        """生成洞穴内容"""
        height = len(ground)
        width = len(ground[0])
        
        # 添加石头
        for _ in range(20):
            x = random.randint(3, width - 4)
            y = random.randint(3, height - 4)
            ground[y][x] = 6
        
        # 添加熔岩
        for _ in range(10):
            x = random.randint(3, width - 4)
            y = random.randint(3, height - 4)
            if ground[y][x] == 10:
                ground[y][x] = 11
    
    def _generate_town_content(self, ground: List[List[int]], 
                                template: Dict) -> None:
        """生成城镇内容"""
        height = len(ground)
        width = len(ground[0])
        
        # 添加多个建筑
        buildings = ["house_small", "house_medium", "blacksmith", "shop"]
        
        # 左侧建筑
        self.place_structure(ground, "blacksmith", 5, 5)
        self.place_structure(ground, "shop", 5, 15)
        self.place_structure(ground, "house_small", 5, 25)
        
        # 右侧建筑
        self.place_structure(ground, "house_medium", width - 19, 5)
        self.place_structure(ground, "house_small", width - 17, 15)
        self.place_structure(ground, "shop", width - 19, 25)
        
        # 添加道路网格
        self.add_road(ground, (2, 12), (width - 3, 12), width=2)
        self.add_road(ground, (2, 22), (width - 3, 22), width=2)
        self.add_road(ground, (2, 32), (width - 3, 32), width=2)
        self.add_road(ground, (width // 3, 2), (width // 3, height - 3), width=2)
        self.add_road(ground, (2 * width // 3, 2), (2 * width // 3, height - 3), width=2)
        
        # 添加装饰
        self.place_structure(ground, "well", width // 2 - 1, height // 2 - 1)
    
    def _generate_desert_content(self, ground: List[List[int]], 
                                  template: Dict) -> None:
        """生成沙漠内容"""
        height = len(ground)
        width = len(ground[0])
        
        # 添加绿洲
        self.place_structure(ground, "pond", width // 2 - 2, height // 2 - 2)
        
        # 添加水井
        self.place_structure(ground, "well", width // 4, height // 4)
        self.place_structure(ground, "well", 3 * width // 4, 3 * height // 4)
        
        # 添加道路
        self.add_road(ground, (width // 2, 2), (width // 2, height - 3), width=2)
    
    def format_map_json(self, data: Dict) -> str:
        """格式化地图JSON，ground数组每行一个"""
        output = "{\n"
        
        keys = list(data.keys())
        for i, key in enumerate(keys):
            value = data[key]
            comma = "," if i < len(keys) - 1 else ""
            
            if key == 'layers':
                output += '  "layers": {\n'
                layer_keys = list(value.keys())
                for j, layer_key in enumerate(layer_keys):
                    layer_value = value[layer_key]
                    layer_comma = "," if j < len(layer_keys) - 1 else ""
                    
                    if layer_key == 'ground':
                        output += '    "ground": [\n'
                        for k, row in enumerate(layer_value):
                            row_str = ", ".join(str(x) for x in row)
                            row_comma = "," if k < len(layer_value) - 1 else ""
                            output += f"      [{row_str}]{row_comma}\n"
                        output += '    ]\n'
                    else:
                        output += f'    "{layer_key}": {json.dumps(layer_value)}{layer_comma}\n'
                output += f'  }}{comma}\n'
            else:
                output += f'  "{key}": {json.dumps(value, ensure_ascii=False)}{comma}\n'
        
        output += "}"
        return output
    
    def save_map(self, map_data: Dict, filepath: Path = None) -> Path:
        """保存地图到文件"""
        map_id = map_data["id"]
        filepath = filepath or self.maps_dir / f"{map_id}.json"
        
        output = self.format_map_json(map_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(output)
        
        return filepath
    
    def load_map(self, map_id: str) -> Optional[Dict]:
        """加载地图"""
        filepath = self.maps_dir / f"{map_id}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_maps(self) -> List[Dict]:
        """列出所有地图"""
        maps = []
        
        for filepath in self.maps_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    maps.append({
                        "id": data.get("id", filepath.stem),
                        "name": data.get("name", filepath.stem),
                        "width": data.get("width", 0),
                        "height": data.get("height", 0),
                        "filepath": str(filepath)
                    })
            except Exception as e:
                print(f"警告: 无法读取 {filepath}: {e}")
        
        return maps
    
    def remove_border(self, ground: List[List[int]]) -> Tuple[List[List[int]], int]:
        """移除地图边界墙"""
        height = len(ground)
        width = len(ground[0])
        
        border_tile = ground[0][0]
        
        top = 0
        bottom = height
        left = 0
        right = width
        
        while top < height and all(t == border_tile for t in ground[top]):
            top += 1
        while bottom > top and all(t == border_tile for t in ground[bottom - 1]):
            bottom -= 1
        
        if top < bottom:
            while left < width:
                if all(ground[r][left] == border_tile for r in range(top, bottom)):
                    left += 1
                else:
                    break
            while right > left:
                if all(ground[r][right - 1] == border_tile for r in range(top, bottom)):
                    right -= 1
                else:
                    break
        
        inner = []
        for r in range(top, bottom):
            inner.append(ground[r][left:right])
        
        return inner, border_tile
    
    def fix_map(self, map_id: str) -> bool:
        """修复地图边界问题"""
        data = self.load_map(map_id)
        if not data:
            print(f"错误: 地图 '{map_id}' 不存在")
            return False
        
        old_ground = data['layers']['ground']
        old_height = len(old_ground)
        old_width = len(old_ground[0])
        
        inner_ground, border_tile = self.remove_border(old_ground)
        inner_height = len(inner_ground)
        inner_width = len(inner_ground[0]) if inner_height > 0 else 0
        
        ground_tile = 0
        for r in inner_ground:
            for tile in r:
                if tile != border_tile:
                    ground_tile = tile
                    break
            if ground_tile != border_tile:
                break
        
        old_offset_y = (old_height - inner_height) // 2
        old_offset_x = (old_width - inner_width) // 2
        
        new_ground = []
        for r in range(old_height):
            row = []
            for c in range(old_width):
                if r < 2 or r >= old_height - 2 or c < 2 or c >= old_width - 2:
                    row.append(border_tile)
                else:
                    inner_r = r - 2
                    inner_c = c - 2
                    if 0 <= inner_r < inner_height and 0 <= inner_c < inner_width:
                        row.append(inner_ground[inner_r][inner_c])
                    else:
                        row.append(ground_tile)
            new_ground.append(row)
        
        data['layers']['ground'] = new_ground
        
        coord_offset_x = 2 - old_offset_x
        coord_offset_y = 2 - old_offset_y
        
        for obj in data.get('objects', []):
            obj['x'] += coord_offset_x
            obj['y'] += coord_offset_y
            if 'target_x' in obj.get('properties', {}):
                obj['properties']['target_x'] += coord_offset_x
                obj['properties']['target_y'] += coord_offset_y
        
        for npc in data.get('npcs', []):
            npc['x'] += coord_offset_x
            npc['y'] += coord_offset_y
        
        if 'player_spawn' in data:
            data['player_spawn']['x'] += coord_offset_x
            data['player_spawn']['y'] += coord_offset_y
        
        self.save_map(data)
        
        print(f"地图 '{map_id}' 已修复")
        print(f"移除边界: {old_offset_x}x{old_offset_y}")
        print(f"坐标偏移: ({coord_offset_x}, {coord_offset_y})")
        return True
    
    def expand_map(self, map_id: str, new_width: int, new_height: int) -> bool:
        """扩展地图尺寸"""
        data = self.load_map(map_id)
        if not data:
            print(f"错误: 地图 '{map_id}' 不存在")
            return False
        
        old_ground = data['layers']['ground']
        old_height = len(old_ground)
        old_width = len(old_ground[0])
        
        inner_ground, border_tile = self.remove_border(old_ground)
        inner_height = len(inner_ground)
        inner_width = len(inner_ground[0]) if inner_height > 0 else 0
        
        ground_tile = 0
        for r in inner_ground:
            for tile in r:
                if tile != border_tile:
                    ground_tile = tile
                    break
            if ground_tile != border_tile:
                break
        
        offset_y = (new_height - inner_height) // 2
        offset_x = (new_width - inner_width) // 2
        
        old_offset_y = (old_height - inner_height) // 2
        old_offset_x = (old_width - inner_width) // 2
        
        new_ground = []
        for r in range(new_height):
            row = []
            for c in range(new_width):
                if r < 2 or r >= new_height - 2 or c < 2 or c >= new_width - 2:
                    row.append(border_tile)
                else:
                    inner_r = r - offset_y
                    inner_c = c - offset_x
                    if 0 <= inner_r < inner_height and 0 <= inner_c < inner_width:
                        row.append(inner_ground[inner_r][inner_c])
                    else:
                        row.append(ground_tile)
            new_ground.append(row)
        
        data['layers']['ground'] = new_ground
        data['width'] = new_width
        data['height'] = new_height
        
        coord_offset_x = offset_x - old_offset_x
        coord_offset_y = offset_y - old_offset_y
        
        for obj in data.get('objects', []):
            obj['x'] += coord_offset_x
            obj['y'] += coord_offset_y
            if 'target_x' in obj.get('properties', {}):
                obj['properties']['target_x'] += coord_offset_x
                obj['properties']['target_y'] += coord_offset_y
        
        for npc in data.get('npcs', []):
            npc['x'] += coord_offset_x
            npc['y'] += coord_offset_y
        
        if 'player_spawn' in data:
            data['player_spawn']['x'] += coord_offset_x
            data['player_spawn']['y'] += coord_offset_y
        
        self.save_map(data)
        
        print(f"地图 '{map_id}' 已扩展: {old_width}x{old_height} -> {new_width}x{new_height}")
        print(f"内部区域: {inner_width}x{inner_height}")
        print(f"坐标偏移: ({coord_offset_x}, {coord_offset_y})")
        return True
    
    def validate_map(self, map_id: str) -> Dict:
        """验证地图"""
        data = self.load_map(map_id)
        if not data:
            return {"valid": False, "error": f"地图 '{map_id}' 不存在"}
        
        ground = data['layers']['ground']
        width = data['width']
        height = data['height']
        
        issues = []
        
        # 检查尺寸匹配
        if len(ground) != height:
            issues.append(f"地图高度不匹配: 声明{height}, 实际{len(ground)}")
        if ground and len(ground[0]) != width:
            issues.append(f"地图宽度不匹配: 声明{width}, 实际{len(ground[0])}")
        
        # 检查玩家出生点
        spawn = data.get('player_spawn', {})
        spawn_x = spawn.get('x', 0)
        spawn_y = spawn.get('y', 0)
        
        if not (0 <= spawn_x < width and 0 <= spawn_y < height):
            issues.append(f"玩家出生点超出地图范围: ({spawn_x}, {spawn_y})")
        elif ground and not TILES.get(ground[spawn_y][spawn_x], {}).get('walkable', True):
            issues.append(f"玩家出生点在不可通行区域: ({spawn_x}, {spawn_y})")
        
        # 检查NPC位置
        for npc in data.get('npcs', []):
            npc_x = npc.get('x', 0)
            npc_y = npc.get('y', 0)
            if not (0 <= npc_x < width and 0 <= npc_y < height):
                issues.append(f"NPC '{npc.get('npc_id')}' 超出地图范围: ({npc_x}, {npc_y})")
        
        # 检查对象位置
        for obj in data.get('objects', []):
            obj_x = obj.get('x', 0)
            obj_y = obj.get('y', 0)
            if not (0 <= obj_x < width and 0 <= obj_y < height):
                issues.append(f"对象 '{obj.get('id')}' 超出地图范围: ({obj_x}, {obj_y})")
        
        # 检查可达性（从玩家出生点开始）
        if ground:
            reachable = self._check_reachability(ground, spawn_x, spawn_y)
            total_walkable = sum(1 for r in ground for t in r if TILES.get(t, {}).get('walkable', True))
            if reachable < total_walkable * 0.5:
                issues.append(f"可达区域过小: {reachable}/{total_walkable} ({reachable*100//total_walkable}%)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "stats": {
                "width": width,
                "height": height,
                "total_tiles": width * height,
                "walkable_tiles": sum(1 for r in ground for t in r if TILES.get(t, {}).get('walkable', True)),
                "npcs": len(data.get('npcs', [])),
                "objects": len(data.get('objects', []))
            }
        }
    
    def _check_reachability(self, ground: List[List[int]], 
                            start_x: int, start_y: int) -> int:
        """检查可达区域"""
        height = len(ground)
        width = len(ground[0])
        
        visited = set()
        queue = deque([(start_x, start_y)])
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in visited:
                continue
            if not (0 <= x < width and 0 <= y < height):
                continue
            if not TILES.get(ground[y][x], {}).get('walkable', True):
                continue
            
            visited.add((x, y))
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                queue.append((x + dx, y + dy))
        
        return len(visited)
    
    def preview_map(self, map_id: str) -> None:
        """预览地图"""
        data = self.load_map(map_id)
        if not data:
            print(f"错误: 地图 '{map_id}' 不存在")
            return
        
        ground = data['layers']['ground']
        width = data['width']
        height = data['height']
        
        print(f"\n地图: {data.get('name', map_id)} ({width}x{height})\n")
        
        max_display_width = 80
        max_display_height = 40
        
        step_x = max(1, width // max_display_width)
        step_y = max(1, height // max_display_height)
        
        RESET = "\033[0m"
        
        for r in range(0, height, step_y):
            line = ""
            for c in range(0, width, step_x):
                tile = ground[r][c]
                tile_info = TILES.get(tile, {"symbol": "?", "color": "\033[37m"})
                line += f"{tile_info['color']}{tile_info['symbol']}{RESET}"
            print(line)
        
        print(f"\n图例:")
        for tile_id, info in TILES.items():
            print(f"  {info['color']}{info['symbol']}{RESET} = {info['name']} ({tile_id})")


def main():
    generator = MapGenerator()
    
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    
    if command == "generate":
        if len(sys.argv) < 4:
            print("用法: python map_generator.py generate <type> <id> [width] [height] [name]")
            print(f"\n可用类型: {', '.join(TEMPLATES.keys())}")
            return
        
        map_type = sys.argv[2]
        map_id = sys.argv[3]
        width = int(sys.argv[4]) if len(sys.argv) > 4 else None
        height = int(sys.argv[5]) if len(sys.argv) > 5 else None
        name = sys.argv[6] if len(sys.argv) > 6 else None
        
        try:
            map_data = generator.generate_map(map_type, map_id, width, height, name)
            filepath = generator.save_map(map_data)
            print(f"已生成地图: {filepath} ({map_data['width']}x{map_data['height']})")
        except Exception as e:
            print(f"错误: {e}")
    
    elif command == "format":
        for map_info in generator.list_maps():
            data = generator.load_map(map_info["id"])
            if data:
                generator.save_map(data)
                print(f"已格式化: {map_info['filepath']}")
    
    elif command == "expand":
        if len(sys.argv) < 5:
            print("用法: python map_generator.py expand <id> <width> <height>")
            return
        
        map_id = sys.argv[2]
        width = int(sys.argv[3])
        height = int(sys.argv[4])
        
        generator.expand_map(map_id, width, height)
    
    elif command == "fix":
        if len(sys.argv) < 3:
            print("用法: python map_generator.py fix <id>")
            print("      python map_generator.py fix all")
            return
        
        if sys.argv[2] == "all":
            for map_info in generator.list_maps():
                generator.fix_map(map_info["id"])
        else:
            generator.fix_map(sys.argv[2])
    
    elif command == "validate":
        if len(sys.argv) < 3:
            print("用法: python map_generator.py validate <id>")
            return
        
        result = generator.validate_map(sys.argv[2])
        
        if result["valid"]:
            print(f"地图 '{sys.argv[2]}' 验证通过")
            print(f"统计: {result['stats']}")
        else:
            print(f"地图 '{sys.argv[2]}' 验证失败:")
            for issue in result.get("issues", []):
                print(f"  - {issue}")
    
    elif command == "preview":
        if len(sys.argv) < 3:
            print("用法: python map_generator.py preview <id>")
            return
        
        generator.preview_map(sys.argv[2])
    
    elif command == "list":
        maps = generator.list_maps()
        print(f"\n共 {len(maps)} 个地图:\n")
        for m in maps:
            print(f"  {m['id']}: {m['name']} ({m['width']}x{m['height']})")
    
    else:
        print(f"未知命令: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
