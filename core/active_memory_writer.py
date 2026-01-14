import json
import time
import os
from config import trace_logger

ACTIVE_MEMORY_FILE = "memory_bus/active_memory.json"
MAX_TURNS_FILE = int(os.getenv("ACTIVE_MEMORY_MAX_TURNS", "5"))


def append_turn(user_text: str, nova_reply: str):
    os.makedirs("memory_bus", exist_ok=True)

    # Initialize file if it doesn't exist or is empty
    if not os.path.exists(ACTIVE_MEMORY_FILE) or os.path.getsize(ACTIVE_MEMORY_FILE) == 0:
        with open(ACTIVE_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"turns": [], "last_updated": time.time()}, f, indent=2)

    with open(ACTIVE_MEMORY_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)

        turn = {
            "timestamp": time.time(),
            "user": user_text,
            "nova": nova_reply
        }

        data["turns"].append(turn)

        # Keep only the last N turns
        if len(data["turns"]) > MAX_TURNS_FILE:
            before = len(data["turns"])
            data["turns"] = data["turns"][-MAX_TURNS_FILE:]
            trace_logger.info(
                f"Active memory trimmed | before={before} | kept={MAX_TURNS_FILE}"
            )
        data["last_updated"] = time.time()

        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

    trace_logger.info("Active memory turn appended")
