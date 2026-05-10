#!/usr/bin/env python3
"""重构青石村和幽暗森林地图"""
import json
from pathlib import Path

# 瓦片常量
WALL = 4       # 边界墙
GRASS = 0      # 草地
DIRT = 1       # 泥土路
WATER = 2      # 水面
BRIDGE = 17    # 木桥
TREE = 5       # 树木
STONE = 6      # 石头
FLOWER = 7     # 花朵
FENCE = 8      # 栅栏
FOREST_G = 9   # 森林地面
CAVE_F = 10    # 洞穴地面
LAVA = 11      # 熔岩
SAND = 12      # 沙地
SNOW = 13      # 雪地
WOOD_F = 14    # 木地板
FLOWER_G = 15  # 花丛草地
RIVER = 16     # 小河
BUSH = 18      # 灌木丛
DEAD_TREE = 19 # 枯树
FLOWER_P = 20  # 花朵
DEEP_G = 21    # 深草地
STONE_T = 22   # 石板

def create_village():
    """重构青石村 50x40"""
    W, H = 50, 40
    
    # 初始化全草地
    ground = [[GRASS for _ in range(W)] for _ in range(H)]
    
    # 边界墙 (只有一层)
    for r in range(H):
        for c in range(W):
            if r == 0 or r == H - 1 or c == 0 or c == W - 1:
                ground[r][c] = WALL
    
    # ===== 道路系统 =====
    # 主干道 - 横向 (row 20)
    for c in range(1, W - 1):
        ground[20][c] = DIRT
    
    # 主干道 - 纵向 (col 25)
    for r in range(1, H - 1):
        ground[r][25] = DIRT
    
    # 次要道路 - 连接各建筑
    # 上方横向路 (row 12)
    for c in range(1, W - 1):
        ground[12][c] = DIRT
    
    # 下方横向路 (row 30)
    for c in range(1, W - 1):
        ground[30][c] = DIRT
    
    # 左侧纵向路 (col 12)
    for r in range(1, H - 1):
        ground[r][12] = DIRT
    
    # 右侧纵向路 (col 38)
    for r in range(1, H - 1):
        ground[r][38] = DIRT
    
    # ===== 建筑 (放在道路围成的区域中心) =====
    # 铁匠铺 (左上区域) 6x5
    bx, by = 4, 4
    for r in range(by, by + 5):
        for c in range(bx, bx + 6):
            if r == by or r == by + 4 or c == bx or c == bx + 5:
                ground[r][c] = WALL
            else:
                ground[r][c] = WOOD_F
    
    # 商店 (右上区域) 6x5
    bx, by = 40, 4
    for r in range(by, by + 5):
        for c in range(bx, bx + 6):
            if r == by or r == by + 4 or c == bx or c == bx + 5:
                ground[r][c] = WALL
            else:
                ground[r][c] = WOOD_F
    
    # 神殿 (左下区域) 6x5
    bx, by = 4, 33
    for r in range(by, by + 5):
        for c in range(bx, bx + 6):
            if r == by or r == by + 4 or c == bx or c == bx + 5:
                ground[r][c] = WALL
            else:
                ground[r][c] = STONE_T
    
    # 学院 (右下区域) 6x5
    bx, by = 40, 33
    for r in range(by, by + 5):
        for c in range(bx, bx + 6):
            if r == by or r == by + 4 or c == bx or c == bx + 5:
                ground[r][c] = WALL
            else:
                ground[r][c] = STONE_T
    
    # ===== 水井 (中心广场) =====
    wx, wy = 25, 15
    for r in range(wy - 1, wy + 2):
        for c in range(wx - 1, wx + 2):
            if r == wy - 1 or r == wy + 1 or c == wx - 1 or c == wx + 1:
                ground[r][c] = FENCE
            else:
                ground[r][c] = WATER
    
    # ===== 装饰 =====
    # 花坛 (左上区域)
    for i in range(3):
        ground[8][18 + i] = FLOWER_P
        ground[9][18 + i] = FLOWER_P
    
    # 花坛 (右上区域)
    for i in range(3):
        ground[8][30 + i] = FLOWER_P
        ground[9][30 + i] = FLOWER_P
    
    # 灌木丛 (左下区域)
    for i in range(2):
        for j in range(2):
            ground[25 + i][15 + j] = BUSH
    
    # 灌木丛 (右下区域)
    for i in range(2):
        for j in range(2):
            ground[25 + i][32 + j] = BUSH
    
    # 花朵散布
    flower_positions = [
        (4, 15), (4, 35), (7, 20), (7, 30),
        (14, 8), (14, 40), (16, 18), (16, 32),
        (23, 10), (23, 38), (27, 20), (27, 30),
        (32, 15), (32, 35), (35, 22), (35, 28),
    ]
    for r, c in flower_positions:
        if ground[r][c] == GRASS:
            ground[r][c] = FLOWER
    
    # 栅栏围栏 (村庄边缘装饰)
    for c in range(4, 10):
        if ground[4][c] == GRASS:
            ground[4][c] = FENCE
    for c in range(40, 46):
        if ground[4][c] == GRASS:
            ground[4][c] = FENCE
    
    # 石头装饰
    stone_positions = [(6, 20), (6, 30), (34, 20), (34, 30)]
    for r, c in stone_positions:
        if ground[r][c] == GRASS:
            ground[r][c] = STONE
    
    # 花丛草地散布
    for r, c in [(5, 18), (5, 32), (10, 8), (10, 40), (33, 18), (33, 32)]:
        if ground[r][c] == GRASS:
            ground[r][c] = FLOWER_G
    
    # 传送门位置 (主干道交叉口)
    portal_x, portal_y = 25, 19
    
    # 玩家出生点
    spawn_x, spawn_y = 25, 21
    
    # NPC位置 (建筑门口附近)
    npcs = [
        {"npc_id": "blacksmith", "x": 10, "y": 11},   # 铁匠铺门口
        {"npc_id": "merchant", "x": 38, "y": 10},     # 商店门口
        {"npc_id": "priest", "x": 10, "y": 27},       # 神殿门口
        {"npc_id": "skill_master", "x": 39, "y": 27}, # 学院门口
    ]
    
    # 物件
    objects = [
        {
            "id": "portal_to_forest",
            "type": "portal",
            "x": portal_x,
            "y": portal_y,
            "properties": {
                "target_map": "forest",
                "target_x": 30,
                "target_y": 26
            }
        }
    ]
    
    map_data = {
        "id": "village",
        "name": "青石村",
        "width": W,
        "height": H,
        "tile_size": 32,
        "layers": {"ground": ground},
        "monsters": [],
        "objects": objects,
        "npcs": npcs,
        "player_spawn": {"x": spawn_x, "y": spawn_y}
    }
    
    return map_data


def create_forest():
    """重构幽暗森林 60x50"""
    W, H = 60, 50
    
    # 初始化全森林地面
    ground = [[FOREST_G for _ in range(W)] for _ in range(H)]
    
    # 边界墙 (只有一层)
    for r in range(H):
        for c in range(W):
            if r == 0 or r == H - 1 or c == 0 or c == W - 1:
                ground[r][c] = WALL
    
    # ===== 道路系统 =====
    # 纵向主路 (col 30) - 连接传送门
    for r in range(1, H - 1):
        ground[r][30] = DIRT
    
    # 横向主路 (row 25)
    for c in range(1, W - 1):
        ground[25][c] = DIRT
    
    # 次要道路
    # 横向路 (row 12)
    for c in range(1, W - 1):
        ground[12][c] = DIRT
    
    # 横向路 (row 38)
    for c in range(1, W - 1):
        ground[38][c] = DIRT
    
    # 纵向路 (col 15)
    for r in range(1, H - 1):
        ground[r][15] = DIRT
    
    # 纵向路 (col 45)
    for r in range(1, H - 1):
        ground[r][45] = DIRT
    
    # ===== 河流 (从左上到右下) =====
    # 水平河流段 (row 18)
    for c in range(5, 25):
        if ground[18][c] == FOREST_G:
            ground[18][c] = RIVER
    
    # 垂直河流段 (col 40)
    for r in range(18, 42):
        if ground[r][40] == FOREST_G:
            ground[r][40] = RIVER
    
    # 桥梁
    # 主路跨河桥
    ground[18][30] = BRIDGE
    
    ground[25][40] = BRIDGE
    
    # ===== 树木区域 =====
    # 左上密林区
    for r in range(4, 11):
        for c in range(4, 12):
            if ground[r][c] == FOREST_G:
                if (r + c) % 3 == 0:
                    ground[r][c] = TREE
                elif (r * c) % 7 == 0:
                    ground[r][c] = BUSH
    
    # 右上林区
    for r in range(4, 11):
        for c in range(35, 43):
            if ground[r][c] == FOREST_G:
                if (r + c) % 4 == 0:
                    ground[r][c] = TREE
                elif (r * c) % 11 == 0:
                    ground[r][c] = BUSH
    
    # 左下林区
    for r in range(30, 37):
        for c in range(4, 12):
            if ground[r][c] == FOREST_G:
                if (r + c) % 3 == 0:
                    ground[r][c] = TREE
                elif (r * c) % 9 == 0:
                    ground[r][c] = BUSH
    
    # 右下密林区 (危险区)
    for r in range(30, 37):
        for c in range(35, 43):
            if ground[r][c] == FOREST_G:
                if (r + c) % 2 == 0:
                    ground[r][c] = TREE
                elif (r * c) % 5 == 0:
                    ground[r][c] = BUSH
    
    # ===== 池塘 =====
    # 左上池塘
    px, py = 8, 6
    for r in range(py, py + 3):
        for c in range(px, px + 4):
            if r == py or r == py + 2 or c == px or c == px + 3:
                pass  # 保持边缘
            else:
                ground[r][c] = WATER
    
    # 右下池塘
    px, py = 42, 34
    for r in range(py, py + 3):
        for c in range(px, px + 4):
            if r == py or r == py + 2 or c == px or c == px + 3:
                pass
            else:
                ground[r][c] = WATER
    
    # ===== 装饰 =====
    # 花朵散布
    import random
    random.seed(42)  # 固定种子保证一致性
    for _ in range(40):
        r = random.randint(4, H - 5)
        c = random.randint(4, W - 5)
        if ground[r][c] == FOREST_G:
            ground[r][c] = FLOWER
    
    # 石头散布
    for _ in range(25):
        r = random.randint(4, H - 5)
        c = random.randint(4, W - 5)
        if ground[r][c] == FOREST_G:
            ground[r][c] = STONE
    
    # 枯树散布
    for _ in range(15):
        r = random.randint(4, H - 5)
        c = random.randint(4, W - 5)
        if ground[r][c] == FOREST_G:
            ground[r][c] = DEAD_TREE
    
    # 深草地散布
    for _ in range(50):
        r = random.randint(4, H - 5)
        c = random.randint(4, W - 5)
        if ground[r][c] == FOREST_G:
            ground[r][c] = DEEP_G
    
    # 花丛草地散布
    for _ in range(30):
        r = random.randint(4, H - 5)
        c = random.randint(4, W - 5)
        if ground[r][c] == FOREST_G:
            ground[r][c] = FLOWER_G
    
    # 灌木丛散布
    for _ in range(20):
        r = random.randint(4, H - 5)
        c = random.randint(4, W - 5)
        if ground[r][c] == FOREST_G:
            ground[r][c] = BUSH
    
    # 传送门位置
    portal_x, portal_y = 30, 26
    
    # 玩家出生点
    spawn_x, spawn_y = 30, 24
    
    # NPC位置 (靠近道路)
    npcs = [
        {"npc_id": "herbalist", "x": 20, "y": 18},  # 森林中部，靠近道路
    ]
    
    # 物件
    objects = [
        {
            "id": "portal_to_village",
            "type": "portal",
            "x": portal_x,
            "y": portal_y,
            "properties": {
                "target_map": "village",
                "target_x": 25,
                "target_y": 21
            }
        },
        {
            "id": "chest_forest_01",
            "type": "chest",
            "x": 42,
            "y": 38,
            "properties": {
                "items": [{"item_id": "health_potion", "quantity": 2}],
                "opened": False
            }
        },
        {
            "id": "herb_01",
            "type": "gather",
            "x": 12,
            "y": 20,
            "properties": {
                "item_id": "herb",
                "respawn_time": 60
            }
        },
        {
            "id": "herb_02",
            "type": "gather",
            "x": 48,
            "y": 35,
            "properties": {
                "item_id": "herb",
                "respawn_time": 60
            }
        }
    ]
    
    # 怪物位置
    monsters = [
        {"monster_id": "slime", "x": 15, "y": 10},
        {"monster_id": "slime", "x": 22, "y": 8},
        {"monster_id": "wild_wolf", "x": 40, "y": 20, "patrol": [{"x": 38, "y": 20}, {"x": 42, "y": 20}, {"x": 42, "y": 24}]},
        {"monster_id": "wild_wolf", "x": 10, "y": 35, "patrol": [{"x": 8, "y": 35}, {"x": 14, "y": 35}]},
        {"monster_id": "forest_spider", "x": 48, "y": 30},
        {"monster_id": "goblin", "x": 35, "y": 40},
        {"monster_id": "dark_bear", "x": 50, "y": 15}
    ]
    
    map_data = {
        "id": "forest",
        "name": "幽暗森林",
        "width": W,
        "height": H,
        "tile_size": 32,
        "layers": {"ground": ground},
        "monsters": monsters,
        "objects": objects,
        "npcs": npcs,
        "player_spawn": {"x": spawn_x, "y": spawn_y}
    }
    
    return map_data


if __name__ == "__main__":
    maps_dir = Path("config/maps")
    maps_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成青石村
    village = create_village()
    with open(maps_dir / "village.json", "w", encoding="utf-8") as f:
        json.dump(village, f, ensure_ascii=False, indent=2)
    print(f"青石村地图已生成: {village['width']}x{village['height']}")
    
    # 生成幽暗森林
    forest = create_forest()
    with open(maps_dir / "forest.json", "w", encoding="utf-8") as f:
        json.dump(forest, f, ensure_ascii=False, indent=2)
    print(f"幽暗森林地图已生成: {forest['width']}x{forest['height']}")
    
    print("地图重构完成！")
