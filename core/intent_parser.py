import json
import re
import time
from ollama.client import ollama_generate
from ollama.prompts import INTENT_PROMPT
from config import trace_logger

INTENT_MODEL = "qwen3:4b"

def extract_json(text: str):
    match = re.search(r"\{[\s\S]*?\}", text)
    return match.group() if match else None


def classify_intent(text: str) -> dict:
    trace_logger.info("Intent classification started")
    start = time.perf_counter()

    raw_response = ollama_generate(
        model=INTENT_MODEL,
        prompt=INTENT_PROMPT.replace("{user_input}",text)
    )

    duration = time.perf_counter() - start
    trace_logger.info(
        f"Intent model responded | duration={duration:.3f}s"
    )

    json_str = extract_json(raw_response)
    if not json_str:
        return {"intent": "unknown"}

    try:
        intent_data = json.loads(json_str)
        trace_logger.info(
            f"Intent parsed successfully: {intent_data.get('intent')}"
        )
        return intent_data
    except:
        return {"intent": "unknown"}
