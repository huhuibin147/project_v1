import json
import logging
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from config import load_config

_config = load_config()
_client = OpenAI(api_key=_config["api_key"], base_url=_config["base_url"])
_model = _config["model"]

# 日志配置
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "llm_calls.log"

logger = logging.getLogger("llm")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
fh.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(fh)


def chat_completion(messages: list[dict], temperature: float = 0.7) -> str:
    """调用 OpenAI 兼容接口，返回助手回复文本。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    resp = _client.chat.completions.create(
        model=_model,
        messages=messages,
        temperature=temperature,
    )
    content = resp.choices[0].message.content

    # 记录完整调用日志
    log_entry = {
        "time": timestamp,
        "model": _model,
        "temperature": temperature,
        "messages": messages,
        "response": content,
    }
    logger.info(json.dumps(log_entry, ensure_ascii=False, indent=2))
    logger.info("=" * 80)

    return content
