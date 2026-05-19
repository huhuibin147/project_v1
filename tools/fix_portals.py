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

# 传送门中文名称映射
PORTAL_NAMES = {
    "village": "村庄",
    "forest": "森林",
    "dark_cave": "黑暗洞穴",
    "desert_oasis": "沙漠绿洲",
    "royal_city": "王城",
}

def find_safe_spot(ground, x, y, width, height, max_r=10):
    """在 (x,y) 附近寻找一个四周都可行走的位置"""
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
                    # 检查四周
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
    return x, y  # 找不到就返回原位置

def fix_map(map_name):
    map_file = MAPS_DIR / f"{map_name}.json"
    with open(map_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    w, h = data["width"], data["height"]
    ground = data["layers"]["ground"]
    portals = data.get("objects", [])
    
    fixed = []
    for p in portals:
        if p.get("type") != "portal":
            continue
        
        px, py = p["x"], p["y"]
        target = p.get("properties", {}).get("target_map", "")
        
        # 检查是否需要移动
        needs_move = False
        if not is_walkable(ground[py][px]):
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
        
        # 更新中文名称
        target_cn = PORTAL_NAMES.get(target, target)
        p["name"] = f"传送门（前往{target_cn}）"
    
    if fixed:
        print(f"=== {map_name} ===")
        for pid, old, new in fixed:
            print(f"  {pid}: {old} -> {new}")
        print()
    
    with open(map_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    for m in ["village", "forest", "dark_cave", "desert_oasis", "royal_city"]:
        fix_map(m)
    print("传送门修复完成!")
