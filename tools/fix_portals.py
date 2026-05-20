#!/usr/bin/env python3
"""修复传送门位置（确保周围可行走）和中文命名"""
import json
from pathlib import Path
from collections import deque

MAPS_DIR = Path(__file__).parent.parent / "config" / "maps"
TILES_FILE = Path(__file__).parent.parent / "config" / "tiles.json"

with open(TILES_FILE, "r", encoding="utf-8") as f:
    tile_config = json.load(f)

def is_walkable(tile_id):
    return tile_config.get(str(tile_id), {}).get("walkable", False)

PORTAL_NAMES = {
    "village": "村庄",
    "forest": "森林",
    "dark_cave": "黑暗洞穴",
    "desert_oasis": "沙漠绿洲",
    "royal_city": "王城",
}

def get_portal_cn_name(target_map, map_data=None):
    if map_data and "metadata" in map_data:
        map_names = map_data["metadata"].get("map_names", {})
        if target_map in map_names:
            return map_names[target_map]
    return PORTAL_NAMES.get(target_map, target_map)

def find_safe_spot(ground, x, y, width, height, max_r=10):
    if 0 <= y < height and 0 <= x < width and is_walkable(ground[y][x]):
        neighbors_ok = all(
            is_walkable(ground[y+dy][x+dx])
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]
            if 0 <= x+dx < width and 0 <= y+dy < height
        )
        if neighbors_ok:
            return x, y
    
    for r in range(1, max_r+1):
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                nx, ny = x+dx, y+dy
                if 0 <= nx < width and 0 <= ny < height and is_walkable(ground[ny][nx]):
                    all_ok = True
                    for ddx, ddy in [(0,1),(0,-1),(1,0),(-1,0)]:
                        nnx, nny = nx+ddx, ny+ddy
                        if 0 <= nnx < width and 0 <= nny < height:
                            if not is_walkable(ground[nny][nnx]):
                                all_ok = False
                                break
                        else:
                            all_ok = False
                            break
                    if all_ok:
                        return nx, ny
    return x, y

def fix_map(map_name, map_data_cache=None):
    map_file = MAPS_DIR / f"{map_name}.json"
    if not map_file.exists():
        print(f"  ⚠ 地图文件不存在: {map_file}")
        return
    
    with open(map_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    w, h = data["width"], data["height"]
    ground = data["layers"]["ground"]
    portals = data.get("objects", [])
    
    fixed = []
    name_fixed = []
    
    for p in portals:
        if p.get("type") != "portal":
            continue
        
        px, py = p["x"], p["y"]
        target = p.get("properties", {}).get("target_map", "")
        
        needs_move = False
        if not (0 <= py < h and 0 <= px < w) or not is_walkable(ground[py][px]):
            needs_move = True
        else:
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = px+dx, py+dy
                if 0 <= nx < w and 0 <= ny < h:
                    if not is_walkable(ground[ny][nx]):
                        needs_move = True
                        break
        
        if needs_move:
            new_x, new_y = find_safe_spot(ground, px, py, w, h)
            old_pos = (px, py)
            p["x"], p["y"] = new_x, new_y
            fixed.append((p["id"], old_pos, (new_x, new_y)))
        
        target_cn = get_portal_cn_name(target, data)
        expected_name = f"传送门（前往{target_cn}）"
        
        props = p.get("properties", {})
        current_name = props.get("name", "")
        if current_name != expected_name:
            old_name = current_name
            props["name"] = expected_name
            name_fixed.append((p["id"], old_name, expected_name))
    
    if fixed or name_fixed:
        print(f"=== {map_name} ===")
        for pid, old, new in fixed:
            print(f"  位置修复: {pid}: {old} -> {new}")
        for pid, old_name, new_name in name_fixed:
            print(f"  名称修复: {pid}: '{old_name}' -> '{new_name}'")
        print()
    
    with open(map_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    map_files = sorted(MAPS_DIR.glob("*.json"))
    if not map_files:
        print("未找到地图文件")
    else:
        for mf in map_files:
            fix_map(mf.stem)
        print("传送门修复完成!")
