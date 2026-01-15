import logging
from ai.emotion_detector import EmotionDetector
from ai.llm_brain import LLMBrain

logger = logging.getLogger(__name__)

emotion_detector = EmotionDetector()
llm_brain = LLMBrain()

def think(user_text: str) -> tuple:
    """
    Process user input using LLM, generate response and detect emotion using Azure.
    Returns: (response_text, emotion_style)
    """
    if not user_text.strip():
        return "I didn't catch that. Could you repeat?", "calm"

    # First try Azure emotion detection if the Azure client initialized
    azure_available = getattr(emotion_detector, "client", None) is not None

    if azure_available:
        # Use Azure detector to get a single high-level style
        try:
            emotion_style = emotion_detector.detect_emotion(user_text)
            # Use LLM to generate text reply
            response = llm_brain.generate_response(user_text)
            logger.info(f"[BRAIN] (Azure) Input: '{user_text[:50]}...' | Emotion: {emotion_style} | Response: '{str(response)[:50]}...'")
            return response, emotion_style
        except Exception as e:
            logger.warning(f"[BRAIN] Azure detection failed at runtime: {e}")

    # If Azure is unavailable or failed, ask the LLM to produce structured JSON including emotions
    structured = llm_brain.generate_structured_response(user_text)

    # structured should be dict with keys: reply, emotions (list), llm
    reply = structured.get("reply", "")
    emotions = structured.get("emotions", [])
    used = structured.get("llm") or llm_brain.last_llm_used

    # Create a compact emotion string for backward compatibility
    if emotions:
        # join labels with confidences
        emotion_summary = ", ".join([f"{e.get('label')}({e.get('confidence',0):.2f})" for e in emotions])
    else:
        emotion_summary = "calm"

    logger.info(f"[BRAIN] (LLM) Input: '{user_text[:50]}...' | Emotions: {emotion_summary} | LLM: {used} | Reply: '{reply[:50]}...'")
    # Return reply and the structured emotions blob (so caller may render richly)
    return reply, {"emotions": emotions, "llm": used}


def run_startup_tests() -> dict:
    """Run a set of quick checks for Azure emotion detector and LLM availability.
    Returns a diagnostic dict."""
    diagnostics = {"azure_text": {}, "llm": {}}

    # Test Azure Text Analytics presence
    try:
        azure_client = getattr(emotion_detector, "client", None)
        diagnostics["azure_text"]["available"] = azure_client is not None
        if azure_client:
            # quick sample
            sample = "I am very happy and excited about today!"
            try:
                style = emotion_detector.detect_emotion(sample)
                diagnostics["azure_text"]["sample_result"] = style
            except Exception as e:
                diagnostics["azure_text"]["error"] = str(e)
    except Exception as e:
        diagnostics["azure_text"]["error_init"] = str(e)

    # Test LLMs: structured generation
    try:
        test_prompt = "System check. Say hello and provide one likely emotion with confidence in JSON."
        structured = llm_brain.generate_structured_response(test_prompt)
        diagnostics["llm"]["structured_sample"] = structured
        diagnostics["llm"]["last_llm_used"] = llm_brain.last_llm_used
    except Exception as e:
        diagnostics["llm"]["error"] = str(e)

    return diagnostics
