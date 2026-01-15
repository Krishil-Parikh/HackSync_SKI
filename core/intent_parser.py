import json
import re
import time
from ai.llm_brain import LLMBrain
from config import trace_logger

# Initialize LLM brain (will use Gemini -> Ollama fallback)
llm_brain = LLMBrain()

def extract_json(text: str):
    match = re.search(r"\{[\s\S]*?\}", text)
    return match.group() if match else None


def classify_intent(text: str) -> dict:
    trace_logger.info("Intent classification started")
    start = time.perf_counter()

    # Use LLM brain for intent classification (Gemini -> Ollama fallback)
    intent_prompt = f"""You are a precise intent classifier. Analyze the user's input and return ONLY a JSON object with the intent and relevant details.

User input: "{text}"

Return a JSON object in this exact format:
{{
  "intent": "conversation" | "open_app" | "search_web" | "system_control",
  "action": "specific_action_if_applicable",
  "target": "target_entity_if_applicable"
}}

Examples:
- "hello" -> {{"intent": "conversation"}}
- "open chrome" -> {{"intent": "open_app", "action": "open", "target": "chrome"}}
- "search for cats" -> {{"intent": "search_web", "action": "search", "target": "cats"}}
- "increase volume" -> {{"intent": "system_control", "action": "volume_up"}}

Respond with ONLY the JSON object, no other text."""

    raw_response = llm_brain.generate(intent_prompt)
    print(f"The response is : {raw_response}")
    duration = time.perf_counter() - start
    trace_logger.info(
        f"Intent model responded | duration={duration:.3f}s | response={raw_response[:200] if raw_response else 'EMPTY'}"
    )

    if not raw_response:
        trace_logger.warning("Intent classifier returned empty response - falling back to unknown")
        return {"intent": "unknown"}

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
