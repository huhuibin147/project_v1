import json
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print("错误：config.json 不存在，请先执行 python main.py 自动生成配置文件。")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 检查必填字段是否为空或为占位符
    placeholders = {"你的 API Key", "sk-xxx", ""}
    missing = []
    if not config.get("api_key") or config["api_key"] in placeholders:
        missing.append("api_key")
    if not config.get("base_url"):
        missing.append("base_url")
    if not config.get("model"):
        missing.append("model")

    if missing:
        print("=" * 50)
        print(f"错误：config.json 中以下字段未填写：{', '.join(missing)}")
        print(f"请编辑配置文件：{CONFIG_PATH}")
        print("=" * 50)
        sys.exit(1)

    return config
