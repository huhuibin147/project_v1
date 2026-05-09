import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
ITEMS_FILE = ROOT / "config" / "items.json"

# 等级段映射：tier -> 使用上限
tier_max = {
    "tier1": 4,
    "tier2": 9,
    "tier3": 15,
}

def main():
    with open(ITEMS_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    changed = 0
    for item_id, item in items.items():
        tier = item.get("tier")
        if tier and tier in tier_max:
            # 统一改为使用上限值（整数）
            item["level_range"] = tier_max[tier]
            changed += 1

    with open(ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"已更新 {changed} 个物品的 level_range 为使用上限值")

if __name__ == "__main__":
    main()
