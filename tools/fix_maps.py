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

# 从 tiles.json 加载配置
with open(TILES_FILE, "r", encoding="utf-8") as f:
    tile_config = json.load(f)

# 道路瓦片ID（用于打通封闭区域）
ROAD_TILE = 1

def is_walkable(tile_id):
    """判断瓦片是否可行走"""
    t = tile_config.get(str(tile_id), {})
    return t.get("walkable", False)

def find_connected_components(ground, width, height, spawn_x, spawn_y):
    """BFS 找出所有连通分量"""
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
    
    # 找出所有不可达的连通区域
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
                if len(area) >= 4:  # 至少4格才算封闭区域
                    enclosed_areas.append(area)
    
    return reachable, enclosed_areas

def find_boundary_tile(ground, width, height, enclosed_area, reachable):
    """找到封闭区域边界上相邻可达区域的不可行走瓦片"""
    for x, y in enclosed_area:
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height:
                # 如果相邻格子是可达区域的可行走瓦片，当前位置是封闭区边界
                if (nx, ny) in reachable and is_walkable(ground[ny][nx]):
                    return (x, y)  # 返回封闭区内的边界点
    return None

def find_border_to_punch(ground, width, height, enclosed_area, reachable):
    """找到打通封闭区域的最佳位置（将不可行走瓦片改为道路）"""
    for x, y in enclosed_area:
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height:
                if not is_walkable(ground[ny][nx]) and (nx, ny) in reachable:
                    # 找到一个相邻的不可行走但可达区域的格子
                    # 检查它的邻居是否还有更多可达区域（确保打通有意义）
                    return (nx, ny)  # 打通这个格子
    # 备选：打通封闭区域边缘的不可行走瓦片
    for x, y in enclosed_area:
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height:
                if not is_walkable(ground[ny][nx]):
                    return (nx, ny)
    return None

def make_map_open(ground, width, height, target_ratio=0.75):
    """让地图更开放：随机将部分不可行走瓦片改为可行走"""
    import random
    random.seed(42)  # 固定种子确保可重复
    
    total = width * height
    walkable = sum(1 for r in ground for t in r if is_walkable(t))
    current_ratio = walkable / total
    
    if current_ratio >= target_ratio:
        return 0
    
    # 收集所有不可行走的瓦片位置
    blocked = [(x, y) for y in range(height) for x in range(width) if not is_walkable(ground[y][x])]
    
    # 计算需要打通的数量
    needed = int(total * target_ratio) - walkable
    random.shuffle(blocked)
    
    made_open = 0
    for x, y in blocked:
        if made_open >= needed:
            break
        # 只打通相邻有可行走瓦片的格子（避免制造孤岛）
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
    """自动修复所有封闭区域"""
    fixed = 0
    max_iterations = 50  # 防止无限循环
    
    for _ in range(max_iterations):
        reachable, enclosed_areas = find_connected_components(ground, width, height, spawn_x, spawn_y)
        if not enclosed_areas:
            break
        
        for area in enclosed_areas:
            target = find_border_to_punch(ground, width, height, area, reachable)
            if target:
                tx, ty = target
                # 打通：将不可行走瓦片改为道路
                if not is_walkable(ground[ty][tx]):
                    ground[ty][tx] = ROAD_TILE
                    fixed += 1
    
    return fixed

def scale_coord(old_x, old_y, old_w, old_h, new_w, new_h, margin=2):
    """将旧坐标按比例映射到新地图，确保不超出边界"""
    ratio_x = (new_w - 2*margin) / max(old_w - 2*margin, 1)
    ratio_y = (new_h - 2*margin) / max(old_h - 2*margin, 1)
    new_x = margin + int((old_x - margin) * ratio_x)
    new_y = margin + int((old_y - margin) * ratio_y)
    new_x = max(margin, min(new_x, new_w - margin - 1))
    new_y = max(margin, min(new_y, new_h - margin - 1))
    return new_x, new_y

def restore_interactive_data(map_data, old_data):
    """从旧地图恢复 objects、npcs、monster_groups"""
    old_w, old_h = old_data["width"], old_data["height"]
    new_w, new_h = map_data["width"], map_data["height"]
    ground = map_data["layers"]["ground"]
    
    # 恢复传送门（关键！）
    old_portals = [o for o in old_data.get("objects", []) if o.get("type") == "portal"]
    restored_portals = 0
    for portal in old_portals:
        px, py = scale_coord(portal["x"], portal["y"], old_w, old_h, new_w, new_h)
        # 确保传送门放在可行走位置
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                nx, ny = px+dx, py+dy
                if 0 <= nx < new_w and 0 <= ny < new_h and is_walkable(ground[ny][nx]):
                    px, py = nx, ny
                    break
        
        new_portal = copy.deepcopy(portal)
        new_portal["x"] = px
        new_portal["y"] = py
        map_data["objects"].append(new_portal)
        restored_portals += 1
    
    # 恢复宝箱和采集点
    old_items = [o for o in old_data.get("objects", []) if o.get("type") in ("chest", "gather")]
    for item in old_items:
        ix, iy = scale_coord(item["x"], item["y"], old_w, old_h, new_w, new_h)
        # 确保放在可行走位置
        placed = False
        for r in range(5):
            for dy in range(-r, r+1):
                for dx in range(-r, r+1):
                    nx, ny = ix+dx, iy+dy
                    if 0 <= nx < new_w and 0 <= ny < new_h and is_walkable(ground[ny][nx]):
                        new_item = copy.deepcopy(item)
                        new_item["x"] = nx
                        new_item["y"] = ny
                        map_data["objects"].append(new_item)
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break
    
    # 恢复 NPC
    for npc in old_data.get("npcs", []):
        nx, ny = scale_coord(npc["x"], npc["y"], old_w, old_h, new_w, new_h)
        # 确保 NPC 放在可行走位置
        for r in range(5):
            for dy in range(-r, r+1):
                for dx in range(-r, r+1):
                    nnx, nny = nx+dx, ny+dy
                    if 0 <= nnx < new_w and 0 <= nny < new_h and is_walkable(ground[nny][nnx]):
                        new_npc = copy.deepcopy(npc)
                        new_npc["x"] = nnx
                        new_npc["y"] = nny
                        map_data["npcs"].append(new_npc)
                        break
                else:
                    continue
                break
            else:
                continue
            break
    
    # 恢复怪物组
    for mg in old_data.get("monster_groups", []):
        mx, my = scale_coord(mg["x"], mg["y"], old_w, old_h, new_w, new_h)
        # 确保怪物组放在可行走位置
        for r in range(5):
            for dy in range(-r, r+1):
                for dx in range(-r, r+1):
                    mmx, mmy = mx+dx, my+dy
                    if 0 <= mmx < new_w and 0 <= mmy < new_h and is_walkable(ground[mmy][mmx]):
                        new_mg = copy.deepcopy(mg)
                        new_mg["x"] = mmx
                        new_mg["y"] = mmy
                        map_data["monster_groups"].append(new_mg)
                        break
                else:
                    continue
                break
            else:
                continue
            break

def fix_map(map_name):
    """修复单个地图"""
    map_file = MAPS_DIR / f"{map_name}.json"
    old_file = OLD_MAPS.get(map_name)
    
    with open(map_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    w, h = data["width"], data["height"]
    ground = data["layers"]["ground"]
    spawn = data.get("player_spawn", {"x": w//2, "y": h//2})
    sx, sy = spawn["x"], spawn["y"]
    
    print(f"\n修复地图: {map_name} ({w}x{h})")
    
    # 1. 先开放地图
    open_count = make_map_open(ground, w, h, target_ratio=0.85)
    print(f"  开放瓦片: {open_count}")
    
    # 2. 修复封闭区域
    fixed_count = fix_enclosed_areas(ground, w, h, sx, sy)
    print(f"  打通封闭: {fixed_count}")
    
    # 2. 从旧地图恢复数据
    if old_file and old_file.exists():
        with open(old_file, "r", encoding="utf-8") as f:
            old_data = json.load(f)
        restore_interactive_data(data, old_data)
        print(f"  恢复 objects: {len(data['objects'])}")
        print(f"  恢复 npcs: {len(data['npcs'])}")
        print(f"  恢复 monsters: {len(data['monster_groups'])}")
    
    # 保存
    with open(map_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {map_file}")

if __name__ == "__main__":
    maps = ["village", "forest", "dark_cave", "desert_oasis", "royal_city"]
    for m in maps:
        fix_map(m)
    print("\n所有地图修复完成!")
