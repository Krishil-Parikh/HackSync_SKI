"""
HackSync_SKI Speaker Module

Pipeline:
- PRIMARY: Azure Speech Synthesis (with emotion detection)
- FALLBACK: pyttsx3 (neutral voice, no emotions)

Emotions are enabled only when Azure services are fully operational.
If Azure fails, fallback to pyttsx3 with emotions disabled.
"""

import logging
from configuration.settings import settings

logger = logging.getLogger(__name__)

# Global references
_azure_speech = None
_azure_status = {"available": False}


def initialize_speaker(azure_speech_instance, emotion_detector_instance=None, azure_available=False):
    """Initialize speaker with Azure instance.
    Emotion detector is ignored (user emotion detection disabled)."""
    global _azure_speech, _azure_status
    
    _azure_speech = azure_speech_instance
    _azure_status["available"] = azure_available
    
    logger.info(f"[INIT] Speaker initialized with Azure available: {azure_available}")
    print(f"[Speaker] Azure {'enabled' if azure_available else 'disabled'} - Emotions disabled")


def set_azure_availability(available: bool):
    """Update Azure availability status at runtime"""
    global _azure_status
    _azure_status["available"] = available
    logger.info(f"[SPEAKER] Azure status changed: {available}")


def speak(text: str, emotion: str = None):
    """Speak response; accepts explicit reply emotion from conversation model."""
    global _azure_speech, _azure_status
    
    print(f"\n[NOVA]: {text}")

    # Use provided emotion if valid, else default to calm
    valid_styles = {
        "calm": "calm",
        "cheerful": "cheerful",
        "empathetic": "empathetic",
        "excited": "excited",
        "sad": "sad",
        "curious": "curious",
        "neutral": "calm"
    }

    style = valid_styles.get((emotion or "").lower(), valid_styles["calm"])

    if _azure_speech:
        try:
            _azure_speech.speak(text, style)
            logger.info(f"[SPEAKER] Speech synthesis successful (emotion: {style})")
        except Exception as e:
            logger.error(f"[SPEAKER] Azure speech failed: {e}")
            # Fallback is handled inside azure.py speak() method
    else:
        logger.error("[SPEAKER] Azure speech not initialized")
        print("[ERROR] Speaker not properly initialized")
