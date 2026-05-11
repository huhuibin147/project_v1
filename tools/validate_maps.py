#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地图校验和修复工具
检查并修复以下问题：
1. NPC/物件/传送门放置在不可行走的格子上
2. 围成一圈导致无法进入的区域
3. 传送门卡在无法走的格子上
4. 四面封闭的区域（被不可行走瓦片完全包围）
"""

import json
import os
import sys
from pathlib import Path
from collections import deque

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
MAPS_DIR = Path(__file__).parent.parent / "config" / "maps"
TILES_FILE = Path(__file__).parent.parent / "config" / "tiles.json"

# 加载瓦片配置
with open(TILES_FILE, "r", encoding="utf-8") as f:
    tile_config = json.load(f)

def is_walkable(tile_id, tile_config):
    """检查瓦片是否可行走"""
    tile_info = tile_config.get(str(tile_id))
    if not tile_info:
        return False
    return tile_info.get("walkable", False)

def check_map(map_file):
    """检查单个地图文件"""
    print(f"\n检查地图: {map_file.name}")
    
    with open(map_file, "r", encoding="utf-8") as f:
        map_data = json.load(f)
    
    map_id = map_data.get("id", "unknown")
    width = map_data.get("width", 0)
    height = map_data.get("height", 0)
    ground = map_data.get("layers", {}).get("ground", [])
    
    issues = []
    
    # 检查NPC位置
    for npc in map_data.get("npcs", []):
        x, y = npc.get("x", 0), npc.get("y", 0)
        if 0 <= x < width and 0 <= y < height:
            tile_id = ground[y][x] if y < len(ground) and x < len(ground[y]) else -1
            if not is_walkable(tile_id, tile_config):
                issues.append({
                    "type": "npc",
                    "id": npc.get("npc_id", "unknown"),
                    "x": x,
                    "y": y,
                    "tile_id": tile_id,
                    "tile_name": tile_config.get(str(tile_id), {}).get("name", "unknown")
                })
    
    # 检查物件位置
    for obj in map_data.get("objects", []):
        x, y = obj.get("x", 0), obj.get("y", 0)
        obj_type = obj.get("type", "unknown")
        if 0 <= x < width and 0 <= y < height:
            tile_id = ground[y][x] if y < len(ground) and x < len(ground[y]) else -1
            if not is_walkable(tile_id, tile_config):
                issues.append({
                    "type": obj_type,
                    "id": obj.get("id", "unknown"),
                    "x": x,
                    "y": y,
                    "tile_id": tile_id,
                    "tile_name": tile_config.get(str(tile_id), {}).get("name", "unknown")
                })
    
    # 检查物件重叠（同一位置有多个物件）
    position_map = {}
    for obj in map_data.get("objects", []):
        x, y = obj.get("x", 0), obj.get("y", 0)
        pos_key = f"{x},{y}"
        if pos_key not in position_map:
            position_map[pos_key] = []
        position_map[pos_key].append(obj)
    
    for pos_key, objects_at_pos in position_map.items():
        if len(objects_at_pos) > 1:
            # 检查是否有传送门重叠
            has_portal = any(obj.get("type") == "portal" for obj in objects_at_pos)
            if has_portal:
                x, y = map(int, pos_key.split(","))
                issues.append({
                    "type": "overlapping_objects",
                    "id": f"overlap_{pos_key}",
                    "x": x,
                    "y": y,
                    "objects": objects_at_pos
                })
    
    # 检查传送门之间的距离（确保传送门不会太近）
    portals = [obj for obj in map_data.get("objects", []) if obj.get("type") == "portal"]
    min_portal_distance = 5  # 传送门之间最小距离
    
    for i in range(len(portals)):
        for j in range(i + 1, len(portals)):
            p1 = portals[i]
            p2 = portals[j]
            x1, y1 = p1.get("x", 0), p1.get("y", 0)
            x2, y2 = p2.get("x", 0), p2.get("y", 0)
            distance = abs(x1 - x2) + abs(y1 - y2)  # 曼哈顿距离
            
            if distance < min_portal_distance:
                issues.append({
                    "type": "portal_too_close",
                    "id": f"portal_distance_{p1.get('id', 'unknown')}_{p2.get('id', 'unknown')}",
                    "x": (x1 + x2) // 2,
                    "y": (y1 + y2) // 2,
                    "portal1": p1,
                    "portal2": p2,
                    "distance": distance
                })
    
    # 检查玩家出生点
    spawn = map_data.get("player_spawn", {})
    spawn_x, spawn_y = spawn.get("x", 0), spawn.get("y", 0)
    if 0 <= spawn_x < width and 0 <= spawn_y < height:
        tile_id = ground[spawn_y][spawn_x] if spawn_y < len(ground) and spawn_x < len(ground[spawn_y]) else -1
        if not is_walkable(tile_id, tile_config):
            issues.append({
                "type": "player_spawn",
                "id": "player_spawn",
                "x": spawn_x,
                "y": spawn_y,
                "tile_id": tile_id,
                "tile_name": tile_config.get(str(tile_id), {}).get("name", "unknown")
            })
    
    # 检查封闭区域（只检测面积小于100格的小封闭区域）
    enclosed_areas = find_enclosed_areas(map_data, tile_config)
    if enclosed_areas:
        for i, area in enumerate(enclosed_areas):
            # 只关注小封闭区域（面积小于100格）
            if len(area) > 100:
                continue
                
            # 检查封闭区域内是否有物件
            enclosed_objects = []
            for obj in map_data.get("objects", []):
                obj_x, obj_y = obj.get("x", 0), obj.get("y", 0)
                if (obj_x, obj_y) in area:
                    enclosed_objects.append(obj)
            
            if enclosed_objects:
                issues.append({
                    "type": "enclosed_area",
                    "id": f"enclosed_area_{i+1}",
                    "area": area,
                    "objects": enclosed_objects,
                    "center": (sum(x for x, y in area) // len(area), sum(y for x, y in area) // len(area))
                })
    
    if issues:
        print(f"  发现 {len(issues)} 个问题:")
        for issue in issues:
            if issue["type"] == "enclosed_area":
                area = issue["area"]
                objects = issue["objects"]
                print(f"    - [封闭区域] {issue['id']} - {len(area)}个格子，包含 {len(objects)} 个物件:")
                for obj in objects:
                    print(f"      * [{obj.get('type', 'unknown')}] {obj.get('id', 'unknown')} 在 ({obj.get('x', 0)}, {obj.get('y', 0)})")
            elif issue["type"] == "overlapping_objects":
                objects = issue["objects"]
                print(f"    - [物件重叠] {issue['id']} 在 ({issue['x']}, {issue['y']}) - {len(objects)} 个物件重叠:")
                for obj in objects:
                    print(f"      * [{obj.get('type', 'unknown')}] {obj.get('id', 'unknown')}")
            elif issue["type"] == "portal_too_close":
                p1 = issue["portal1"]
                p2 = issue["portal2"]
                print(f"    - [传送门太近] {issue['id']} - 距离 {issue['distance']}:")
                print(f"      * [{p1.get('id', 'unknown')}] 在 ({p1.get('x', 0)}, {p1.get('y', 0)}) -> {p1.get('properties', {}).get('target_map', 'unknown')}")
                print(f"      * [{p2.get('id', 'unknown')}] 在 ({p2.get('x', 0)}, {p2.get('y', 0)}) -> {p2.get('properties', {}).get('target_map', 'unknown')}")
            else:
                print(f"    - [{issue['type']}] {issue['id']} 在 ({issue['x']}, {issue['y']}) - 瓦片: {issue['tile_name']} (ID: {issue['tile_id']})")
    else:
        print("  ✓ 所有位置都正确")
    
    return issues

def find_nearest_walkable(x, y, ground, width, height, tile_config, max_distance=10):
    """查找最近的可行走格子"""
    for distance in range(1, max_distance + 1):
        # 从内向外搜索
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                if abs(dx) == distance or abs(dy) == distance:  # 只检查边缘
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if ny < len(ground) and nx < len(ground[ny]):
                            tile_id = ground[ny][nx]
                            if is_walkable(tile_id, tile_config):
                                return nx, ny
    return None, None

def find_enclosed_areas(map_data, tile_config):
    """
    检测四面封闭的区域
    使用BFS从玩家出生点开始搜索，找出所有无法到达的小区域
    """
    width = map_data.get("width", 0)
    height = map_data.get("height", 0)
    ground = map_data.get("layers", {}).get("ground", [])
    
    if not ground:
        return []
    
    # 从玩家出生点开始BFS
    spawn = map_data.get("player_spawn", {})
    start_x, start_y = spawn.get("x", width // 2), spawn.get("y", height // 2)
    
    # 如果出生点不可行走，尝试找到最近的可行走格子
    if not is_walkable(ground[start_y][start_x], tile_config):
        start_x, start_y = find_nearest_walkable(start_x, start_y, ground, width, height, tile_config)
        if start_x is None:
            return []
    
    # BFS标记所有从出生点可达的格子
    reachable = set()
    queue = deque([(start_x, start_y)])
    reachable.add((start_x, start_y))
    
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    while queue:
        cx, cy = queue.popleft()
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in reachable and ny < len(ground) and nx < len(ground[ny]):
                    if is_walkable(ground[ny][nx], tile_config):
                        reachable.add((nx, ny))
                        queue.append((nx, ny))
    
    # 找出所有不可达的可行走格子（封闭区域）
    enclosed_areas = []
    visited = set()
    
    for y in range(height):
        for x in range(width):
            if (x, y) not in visited and (x, y) not in reachable:
                if y < len(ground) and x < len(ground[y]) and is_walkable(ground[y][x], tile_config):
                    # 发现一个新的封闭区域，使用BFS找出所有相连的格子
                    area = []
                    area_queue = deque([(x, y)])
                    visited.add((x, y))
                    
                    while area_queue:
                        ax, ay = area_queue.popleft()
                        area.append((ax, ay))
                        
                        for dx, dy in directions:
                            nx, ny = ax + dx, ay + dy
                            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited and (nx, ny) not in reachable:
                                if ny < len(ground) and nx < len(ground[ny]) and is_walkable(ground[ny][nx], tile_config):
                                    visited.add((nx, ny))
                                    area_queue.append((nx, ny))
                    
                    if area:
                        enclosed_areas.append(area)
    
    return enclosed_areas

def fix_map(map_file, issues):
    """修复地图问题"""
    if not issues:
        return
    
    print(f"\n修复地图: {map_file.name}")
    
    with open(map_file, "r", encoding="utf-8") as f:
        map_data = json.load(f)
    
    width = map_data.get("width", 0)
    height = map_data.get("height", 0)
    ground = map_data.get("layers", {}).get("ground", [])
    
    fixed_count = 0
    
    for issue in issues:
        issue_type = issue["type"]
        issue_id = issue["id"]
        
        if issue_type == "enclosed_area":
            # 处理封闭区域：将封闭区域内的物件移动到外部可行走格子
            area = issue["area"]
            objects = issue["objects"]
            
            for obj in objects:
                obj_x, obj_y = obj.get("x", 0), obj.get("y", 0)
                new_x, new_y = find_nearest_walkable_outside_enclosed(obj_x, obj_y, area, ground, width, height, tile_config)
                
                if new_x is not None:
                    print(f"  移动 [{obj.get('type', 'unknown')}] {obj.get('id', 'unknown')} 从封闭区域 ({obj_x}, {obj_y}) 到 ({new_x}, {new_y})")
                    
                    # 更新物件位置
                    for map_obj in map_data["objects"]:
                        if map_obj.get("id") == obj.get("id"):
                            map_obj["x"] = new_x
                            map_obj["y"] = new_y
                            fixed_count += 1
                            break
                    
                    # 将封闭区域的瓦片改为可行走瓦片（打开封闭区域）
                    open_enclosed_area(area, ground, tile_config)
                else:
                    print(f"  ⚠ 无法为 [{obj.get('type', 'unknown')}] {obj.get('id', 'unknown')} 找到合适的外部位置")
        elif issue_type == "portal_too_close":
            # 处理传送门太近：移动第二个传送门到更远的位置
            p1 = issue["portal1"]
            p2 = issue["portal2"]
            min_distance = 5
            
            # 移动第二个传送门
            p2_x, p2_y = p2.get("x", 0), p2.get("y", 0)
            new_x, new_y = find_nearest_walkable_far_from(p2_x, p2_y, p1.get("x", 0), p1.get("y", 0), map_data["objects"], ground, width, height, tile_config, min_distance)
            
            if new_x is not None:
                print(f"  移动传送门 [{p2.get('id', 'unknown')}] 从 ({p2_x}, {p2_y}) 到 ({new_x}, {new_y})（远离 {p1.get('id', 'unknown')}）")
                
                for map_obj in map_data["objects"]:
                    if map_obj.get("id") == p2.get("id"):
                        map_obj["x"] = new_x
                        map_obj["y"] = new_y
                        fixed_count += 1
                        break
            else:
                print(f"  ⚠ 无法为 [{p2.get('id', 'unknown')}] 找到合适的位置")
        elif issue_type == "overlapping_objects":
            # 处理重叠物件：移动非传送门物件到其他位置
            objects = issue["objects"]
            
            # 优先保留传送门，移动其他物件
            portal_objects = []
            other_objects = []
            for obj in objects:
                if obj.get("type") == "portal":
                    portal_objects.append(obj)
                else:
                    other_objects.append(obj)
            
            # 如果有多个传送门重叠，保留第一个，移动其他传送门
            if len(portal_objects) > 1:
                other_objects.extend(portal_objects[1:])
            
            # 如果没有传送门，保留第一个物件
            if not portal_objects and objects:
                other_objects = objects[1:]
            
            # 移动其他物件
            for obj in other_objects:
                obj_x, obj_y = obj.get("x", 0), obj.get("y", 0)
                new_x, new_y = find_nearest_walkable_not_occupied(obj_x, obj_y, map_data["objects"], ground, width, height, tile_config)
                
                if new_x is not None:
                    print(f"  移动重叠物件 [{obj.get('type', 'unknown')}] {obj.get('id', 'unknown')} 从 ({obj_x}, {obj_y}) 到 ({new_x}, {new_y})")
                    
                    for map_obj in map_data["objects"]:
                        if map_obj.get("id") == obj.get("id"):
                            map_obj["x"] = new_x
                            map_obj["y"] = new_y
                            fixed_count += 1
                            break
                else:
                    print(f"  ⚠ 无法为 [{obj.get('type', 'unknown')}] {obj.get('id', 'unknown')} 找到合适的空位置")
        else:
            old_x, old_y = issue["x"], issue["y"]
            new_x, new_y = find_nearest_walkable(old_x, old_y, ground, width, height, tile_config)
            
            if new_x is not None:
                print(f"  移动 [{issue_type}] {issue_id} 从 ({old_x}, {old_y}) 到 ({new_x}, {new_y})")
                
                if issue_type == "npc":
                    for npc in map_data["npcs"]:
                        if npc.get("npc_id") == issue_id:
                            npc["x"] = new_x
                            npc["y"] = new_y
                            fixed_count += 1
                            break
                elif issue_type in ["portal", "chest", "gather", "decoration"]:
                    for obj in map_data["objects"]:
                        if obj.get("id") == issue_id:
                            obj["x"] = new_x
                            obj["y"] = new_y
                            fixed_count += 1
                            break
                elif issue_type == "player_spawn":
                    map_data["player_spawn"]["x"] = new_x
                    map_data["player_spawn"]["y"] = new_y
                    fixed_count += 1
            else:
                print(f"  ⚠ 无法为 [{issue_type}] {issue_id} 找到合适的可行走位置")
    
    if fixed_count > 0:
        with open(map_file, "w", encoding="utf-8") as f:
            json.dump(map_data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 已修复 {fixed_count} 个问题")

def find_nearest_walkable_outside_enclosed(x, y, enclosed_area, ground, width, height, tile_config, max_distance=20):
    """查找封闭区域外的最近可行走格子"""
    enclosed_set = set(enclosed_area)
    
    for distance in range(1, max_distance + 1):
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                if abs(dx) == distance or abs(dy) == distance:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if (nx, ny) not in enclosed_set and ny < len(ground) and nx < len(ground[ny]):
                            tile_id = ground[ny][nx]
                            if is_walkable(tile_id, tile_config):
                                return nx, ny
    return None, None

def find_nearest_walkable_not_occupied(x, y, all_objects, ground, width, height, tile_config, max_distance=20):
    """查找最近的未被占用的可行走格子"""
    # 构建已占用位置集合
    occupied_positions = set()
    for obj in all_objects:
        occupied_positions.add((obj.get("x", 0), obj.get("y", 0)))
    
    for distance in range(1, max_distance + 1):
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                if abs(dx) == distance or abs(dy) == distance:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if (nx, ny) not in occupied_positions and ny < len(ground) and nx < len(ground[ny]):
                            tile_id = ground[ny][nx]
                            if is_walkable(tile_id, tile_config):
                                return nx, ny
    return None, None

def find_nearest_walkable_far_from(x, y, avoid_x, avoid_y, all_objects, ground, width, height, tile_config, min_distance, max_distance=30):
    """查找距离参考点至少min_distance远的可行走格子"""
    # 构建已占用位置集合
    occupied_positions = set()
    for obj in all_objects:
        occupied_positions.add((obj.get("x", 0), obj.get("y", 0)))
    
    for distance in range(1, max_distance + 1):
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                if abs(dx) == distance or abs(dy) == distance:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        # 检查距离参考点是否足够远
                        dist_from_avoid = abs(nx - avoid_x) + abs(ny - avoid_y)
                        if dist_from_avoid >= min_distance:
                            if (nx, ny) not in occupied_positions and ny < len(ground) and nx < len(ground[ny]):
                                tile_id = ground[ny][nx]
                                if is_walkable(tile_id, tile_config):
                                    return nx, ny
    return None, None

def open_enclosed_area(area, ground, tile_config):
    """
    打开封闭区域：将封闭区域边界的不可行走瓦片改为可行走瓦片
    策略：找到封闭区域边缘的不可行走瓦片，将其改为草地(0)
    """
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    area_set = set(area)
    
    # 找到封闭区域边缘的瓦片
    edge_tiles = []
    for x, y in area:
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in area_set:
                edge_tiles.append((x, y))
                break
    
    # 将边缘瓦片周围的不可行走瓦片改为草地
    modified = False
    for ex, ey in edge_tiles:
        for dx, dy in directions:
            nx, ny = ex + dx, ey + dy
            if 0 <= nx < len(ground[0]) and 0 <= ny < len(ground):
                tile_id = ground[ny][nx]
                if not is_walkable(tile_id, tile_config):
                    # 将不可行走瓦片改为草地
                    ground[ny][nx] = 0
                    modified = True
                    break
        if modified:
            break

def check_map_connectivity():
    """
    检查地图之间的连通性
    构建传送门图，检查是否所有地图都可以互相到达
    """
    print("\n" + "=" * 60)
    print("检查地图连通性...")
    print("=" * 60)
    
    # 构建地图图结构
    map_graph = {}  # {map_id: {target_map: [(portal_id, x, y), ...]}}
    
    for map_file in sorted(MAPS_DIR.glob("*.json")):
        with open(map_file, "r", encoding="utf-8") as f:
            map_data = json.load(f)
        
        map_id = map_data.get("id", "unknown")
        if map_id not in map_graph:
            map_graph[map_id] = {}
        
        for obj in map_data.get("objects", []):
            if obj.get("type") == "portal":
                target_map = obj.get("properties", {}).get("target_map", "")
                if target_map:
                    if target_map not in map_graph[map_id]:
                        map_graph[map_id][target_map] = []
                    map_graph[map_id][target_map].append({
                        "id": obj.get("id", "unknown"),
                        "x": obj.get("x", 0),
                        "y": obj.get("y", 0)
                    })
    
    # 打印地图连通性
    print("\n地图连通性:")
    for map_id, targets in sorted(map_graph.items()):
        print(f"\n  {map_id}:")
        for target_map, portals in sorted(targets.items()):
            for portal in portals:
                print(f"    -> {target_map} via [{portal['id']}] at ({portal['x']}, {portal['y']})")
    
    # 使用BFS检查从每个地图出发可以到达哪些地图
    print("\n" + "-" * 60)
    print("从每个地图出发的可达性:")
    
    all_map_ids = list(map_graph.keys())
    issues = []
    
    for start_map in sorted(all_map_ids):
        # BFS
        visited = set()
        queue = deque([start_map])
        visited.add(start_map)
        
        while queue:
            current = queue.popleft()
            if current in map_graph:
                for target_map in map_graph[current].keys():
                    if target_map not in visited:
                        visited.add(target_map)
                        queue.append(target_map)
        
        unreachable = set(all_map_ids) - visited
        if unreachable:
            print(f"\n  ⚠ {start_map} 无法到达: {', '.join(sorted(unreachable))}")
            issues.append({
                "type": "unreachable_maps",
                "from_map": start_map,
                "unreachable": sorted(unreachable)
            })
        else:
            print(f"  ✓ {start_map} 可以到达所有地图 ({len(visited)} 个)")
    
    return issues

def main():
    print("=" * 60)
    print("地图校验和修复工具")
    print("=" * 60)
    
    all_issues = {}
    
    # 检查所有地图
    for map_file in sorted(MAPS_DIR.glob("*.json")):
        issues = check_map(map_file)
        if issues:
            all_issues[map_file] = issues
    
    # 自动修复所有问题
    if all_issues:
        print("\n" + "=" * 60)
        print("自动修复所有问题...")
        for map_file, issues in all_issues.items():
            fix_map(map_file, issues)
        print("\n✓ 所有地图已修复！")
    else:
        print("\n✓ 所有地图都没有问题！")
    
    # 检查地图连通性
    connectivity_issues = check_map_connectivity()
    
    if connectivity_issues:
        print("\n" + "=" * 60)
        print("发现连通性问题:")
        for issue in connectivity_issues:
            print(f"  ⚠ {issue['from_map']} 无法到达: {', '.join(issue['unreachable'])}")
    else:
        print("\n✓ 所有地图都可以互相到达！")

if __name__ == "__main__":
    main()
