import time
from ai.llm_brain import LLMBrain
from config import trace_logger
import re
from core.ec5 import (
    text_to_plutchik_vector,
    apply_polar_filtering,
    generate_response_spectrum,
    spectrum_to_prompt,
    ALL_EMOTIONS,
)

# Initialize LLM brain (will use Gemini -> Ollama fallback)
llm_brain = LLMBrain()

ALLOWED_REPLY_EMOTIONS = [
    "calm", "cheerful", "empathetic", "excited", "sad", "curious"
]

# Plutchik → System emotion mapping
PLUTCHIK_TO_SYSTEM = {
    "joy": "cheerful",
    "trust": "empathetic",
    "anger": "calm",        # calm = controlled anger
    "fear": "empathetic",
    "sadness": "sad",
    "disgust": "calm",
    "surprise": "curious",
    "anticipation": "excited"
}


def spectrum_to_single_emotion(emotion_spectrum: dict) -> str:
    """Collapse spectrum to ONE dominant emotion for TTS."""
    if not emotion_spectrum:
        return "calm"
    
    try:
        dominant_emotion, intensity = max(emotion_spectrum.items(), key=lambda x: x[1])
        trace_logger.info(f"[EMOTION] Dominant: {dominant_emotion} (intensity={intensity:.2f})")
    except (ValueError, AttributeError):
        return "calm"
    
    mapped = PLUTCHIK_TO_SYSTEM.get(dominant_emotion, "calm")
    trace_logger.info(f"[EMOTION] Mapped to: {mapped}")
    return mapped


def _extract_json(text: str):
    match = re.search(r"\{[\s\S]*?\}", text)
    return match.group() if match else None


def generate_reply(prompt: str):
    """Generate a reply with EC5 emotion spectrum system.

    Returns a dict: {"reply": str, "reply_emotion": one-of ALLOWED_REPLY_EMOTIONS}
    """
    trace_logger.info("Conversation generation started")
    start = time.perf_counter()

    # Step 1: Extract user emotions from the prompt
    user_emotions_raw = text_to_plutchik_vector(prompt)
    trace_logger.info(f"[USER EMOTIONS RAW] {user_emotions_raw}")
    
    # Step 2: Apply polar filtering
    user_emotions = apply_polar_filtering(user_emotions_raw)
    trace_logger.info(f"[USER EMOTIONS FILTERED] {user_emotions}")
    
    # Step 3: Generate AI response spectrum
    ai_spectrum = generate_response_spectrum(user_emotions)
    trace_logger.info(f"[AI SPECTRUM] {ai_spectrum}")
    
    # Step 4: Convert spectrum to prompt instruction
    spectrum_instruction = spectrum_to_prompt(ai_spectrum)
    
    # Step 5: Generate response with this emotional context
    structured_prompt = f"""You are NOVA, an emotionally expressive AI friend.

CURRENT EMOTIONAL STATE:
{spectrum_instruction}

GUIDELINES:
- Respond with genuine emotion matching your state
- You can disagree, push back, or express concern
- Be authentic, not performative
- Keep responses short and natural (1-2 sentences)

Conversation:
{prompt}

Respond naturally as a friend would."""

    raw_response = llm_brain.generate(structured_prompt)

    duration = time.perf_counter() - start
    trace_logger.info(
        f"Conversation reply received | duration={duration:.3f}s | model={llm_brain.last_llm_used}"
    )

    if not raw_response:
        trace_logger.warning("Conversation model returned empty response")
        return "I'm not sure what to say right now."

    # Collapse spectrum to single emotion for TTS
    reply_emotion = spectrum_to_single_emotion(ai_spectrum)
    
    return {"reply": raw_response.strip(), "reply_emotion": reply_emotion}