#!/usr/bin/env python3
"""自动修复地图封闭问题并恢复交互数据"""
import json
import copy
from pathlib import Path
from collections import deque

PROJECT_DIR = Path(__file__).parent.parent
MAPS_DIR = PROJECT_DIR / "config" / "maps"
TILES_FILE = PROJECT_DIR / "config" / "tiles.json"
OLD_MAPS = {
    "village": Path("/tmp/old_village.json"),
    "forest": Path("/tmp/old_forest.json"),
    "dark_cave": Path("/tmp/old_dark_cave.json"),
    "desert_oasis": Path("/tmp/old_desert_oasis.json"),
    "royal_city": Path("/tmp/old_royal_city.json"),
}

with open(TILES_FILE, "r", encoding="utf-8") as f:
    tile_config = json.load(f)

ROAD_TILE = 1

def is_walkable(tile_id):
    t = tile_config.get(str(tile_id), {})
    return t.get("walkable", False)

def find_connected_components(ground, width, height, spawn_x, spawn_y):
    reachable = set()
    q = deque([(spawn_x, spawn_y)])
    reachable.add((spawn_x, spawn_y))
    
    while q:
        x, y = q.popleft()
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in reachable:
                if is_walkable(ground[ny][nx]):
                    reachable.add((nx, ny))
                    q.append((nx, ny))
    
    visited = set()
    enclosed_areas = []
    for y in range(height):
        for x in range(width):
            if (x,y) not in visited and (x,y) not in reachable and is_walkable(ground[y][x]):
                area = set()
                aq = deque([(x,y)])
                area.add((x,y))
                visited.add((x,y))
                while aq:
                    ax, ay = aq.popleft()
                    for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                        nx, ny = ax+dx, ay+dy
                        if 0 <= nx < width and 0 <= ny < height and (nx,ny) not in visited and (nx,ny) not in reachable:
                            if is_walkable(ground[ny][nx]):
                                area.add((nx,ny))
                                visited.add((nx,ny))
                                aq.append((nx,ny))
                if len(area) >= 4:
                    enclosed_areas.append(area)
    
    return reachable, enclosed_areas

def find_border_to_punch(ground, width, height, enclosed_area, reachable):
    """找到打通封闭区域的最佳位置
    
    寻找封闭区域边缘的不可行走瓦片，该瓦片一侧是封闭区域内的可行走瓦片，
    另一侧是可达区域内的可行走瓦片（或靠近可达区域）。
    """
    best_candidate = None
    best_reachable_neighbors = 0
    
    for x, y in enclosed_area:
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height:
                if not is_walkable(ground[ny][nx]) and (nx, ny) not in enclosed_area:
                    reachable_neighbor_count = 0
                    for ddx, ddy in [(0,1),(0,-1),(1,0),(-1,0)]:
                        nnx, nny = nx+ddx, ny+ddy
                        if 0 <= nnx < width and 0 <= nny < height:
                            if (nnx, nny) in reachable:
                                reachable_neighbor_count += 1
                    
                    if reachable_neighbor_count > best_reachable_neighbors:
                        best_reachable_neighbors = reachable_neighbor_count
                        best_candidate = (nx, ny)
    
    if best_candidate:
        return best_candidate
    
    for x, y in enclosed_area:
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height:
                if not is_walkable(ground[ny][nx]) and (nx, ny) not in enclosed_area:
                    return (nx, ny)
    
    return None

def make_map_open(ground, width, height, target_ratio=0.75):
    import random
    random.seed(42)
    
    total = width * height
    walkable = sum(1 for r in ground for t in r if is_walkable(t))
    current_ratio = walkable / total
    
    if current_ratio >= target_ratio:
        return 0
    
    blocked = [(x, y) for y in range(height) for x in range(width) if not is_walkable(ground[y][x])]
    
    needed = int(total * target_ratio) - walkable
    random.shuffle(blocked)
    
    made_open = 0
    for x, y in blocked:
        if made_open >= needed:
            break
        has_neighbor = False
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height and is_walkable(ground[ny][nx]):
                has_neighbor = True
                break
        if has_neighbor:
            ground[y][x] = ROAD_TILE
            made_open += 1
    
    return made_open

def fix_enclosed_areas(ground, width, height, spawn_x, spawn_y):
    fixed = 0
    max_iterations = 50
    
    for _ in range(max_iterations):
        reachable, enclosed_areas = find_connected_components(ground, width, height, spawn_x, spawn_y)
        if not enclosed_areas:
            break
        
        for area in enclosed_areas:
            target = find_border_to_punch(ground, width, height, area, reachable)
            if target:
                tx, ty = target
                if not is_walkable(ground[ty][tx]):
                    ground[ty][tx] = ROAD_TILE
                    fixed += 1
    
    return fixed

def scale_coord(old_x, old_y, old_w, old_h, new_w, new_h, margin=2):
    ratio_x = (new_w - 2*margin) / max(old_w - 2*margin, 1)
    ratio_y = (new_h - 2*margin) / max(old_h - 2*margin, 1)
    new_x = margin + int((old_x - margin) * ratio_x)
    new_y = margin + int((old_y - margin) * ratio_y)
    new_x = max(margin, min(new_x, new_w - margin - 1))
    new_y = max(margin, min(new_y, new_h - margin - 1))
    return new_x, new_y

def find_walkable_near(ground, x, y, width, height, max_r=5):
    if 0 <= y < height and 0 <= x < width and is_walkable(ground[y][x]):
        return x, y
    for r in range(1, max_r+1):
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                nx, ny = x+dx, y+dy
                if 0 <= nx < width and 0 <= ny < height and is_walkable(ground[ny][nx]):
                    return nx, ny
    return x, y

def restore_interactive_data(map_data, old_data):
    old_w, old_h = old_data["width"], old_data["height"]
    new_w, new_h = map_data["width"], map_data["height"]
    ground = map_data["layers"]["ground"]
    
    old_portals = [o for o in old_data.get("objects", []) if o.get("type") == "portal"]
    restored_portals = 0
    for portal in old_portals:
        px, py = scale_coord(portal["x"], portal["y"], old_w, old_h, new_w, new_h)
        px, py = find_walkable_near(ground, px, py, new_w, new_h)
        
        new_portal = copy.deepcopy(portal)
        new_portal["x"] = px
        new_portal["y"] = py
        map_data["objects"].append(new_portal)
        restored_portals += 1
    
    old_items = [o for o in old_data.get("objects", []) if o.get("type") in ("chest", "gather")]
    for item in old_items:
        ix, iy = scale_coord(item["x"], item["y"], old_w, old_h, new_w, new_h)
        ix, iy = find_walkable_near(ground, ix, iy, new_w, new_h)
        
        new_item = copy.deepcopy(item)
        new_item["x"] = ix
        new_item["y"] = iy
        map_data["objects"].append(new_item)
    
    for npc in old_data.get("npcs", []):
        nx, ny = scale_coord(npc["x"], npc["y"], old_w, old_h, new_w, new_h)
        nx, ny = find_walkable_near(ground, nx, ny, new_w, new_h)
        new_npc = copy.deepcopy(npc)
        new_npc["x"] = nx
        new_npc["y"] = ny
        map_data["npcs"].append(new_npc)
    
    for mg in old_data.get("monster_groups", []):
        mx, my = scale_coord(mg["x"], mg["y"], old_w, old_h, new_w, new_h)
        mx, my = find_walkable_near(ground, mx, my, new_w, new_h)
        new_mg = copy.deepcopy(mg)
        new_mg["x"] = mx
        new_mg["y"] = my
        map_data["monster_groups"].append(new_mg)

def fix_map(map_name):
    map_file = MAPS_DIR / f"{map_name}.json"
    old_file = OLD_MAPS.get(map_name)
    
    if not map_file.exists():
        print(f"  ⚠ 地图文件不存在: {map_file}")
        return
    
    with open(map_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    w, h = data["width"], data["height"]
    ground = data["layers"]["ground"]
    spawn = data.get("player_spawn", {"x": w//2, "y": h//2})
    sx, sy = spawn["x"], spawn["y"]
    
    print(f"\n修复地图: {map_name} ({w}x{h})")
    
    open_count = make_map_open(ground, w, h, target_ratio=0.85)
    print(f"  开放瓦片: {open_count}")
    
    fixed_count = fix_enclosed_areas(ground, w, h, sx, sy)
    print(f"  打通封闭: {fixed_count}")
    
    if old_file and old_file.exists():
        with open(old_file, "r", encoding="utf-8") as f:
            old_data = json.load(f)
        restore_interactive_data(data, old_data)
        print(f"  恢复 objects: {len(data['objects'])}")
        print(f"  恢复 npcs: {len(data['npcs'])}")
        print(f"  恢复 monsters: {len(data['monster_groups'])}")
    
    with open(map_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {map_file}")

if __name__ == "__main__":
    maps = sorted(mf.stem for mf in MAPS_DIR.glob("*.json"))
    if not maps:
        print("未找到地图文件")
    else:
        for m in maps:
            fix_map(m)
        print("\n所有地图修复完成!")
