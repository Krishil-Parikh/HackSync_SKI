import pyttsx3
import logging

logger = logging.getLogger(__name__)

class PyTTSX3Fallback:
    """Fallback Text-to-Speech using pyttsx3 when Azure services are unavailable"""
    
    # Map emotions to speech rates and volumes
    EMOTION_SETTINGS = {
        "calm": {"rate": 150, "volume": 0.8},
        "happy": {"rate": 180, "volume": 1.0},
        "excited": {"rate": 200, "volume": 1.0},
        "sad": {"rate": 120, "volume": 0.7},
        "empathetic": {"rate": 140, "volume": 0.9},
        "curious": {"rate": 160, "volume": 0.9},
        "cheerful": {"rate": 180, "volume": 0.95},
        "default": {"rate": 150, "volume": 0.85}
    }
    
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)  # Default speech rate
            self.engine.setProperty('volume', 0.85)  # Default volume
            
            # Try to set voice (varies by OS)
            try:
                voices = self.engine.getProperty('voices')
                if len(voices) > 0:
                    self.engine.setProperty('voice', voices[0].id)
            except Exception as e:
                logger.warning(f"[FALLBACK] Could not set voice: {e}")
            
            logger.info("[INIT] PyTTSX3 Fallback initialized successfully")
        except Exception as e:
            logger.error(f"[INIT] Failed to initialize PyTTSX3: {e}")
            raise
    
    def speak(self, text: str, emotion: str = "calm"):
        """Speak text with emotion-based adjustments"""
        if not text.strip():
            logger.warning("[FALLBACK] Empty text provided to speak()")
            return
        
        try:
            # Get emotion settings
            emotion_lower = emotion.lower() if emotion else "calm"
            settings_dict = self.EMOTION_SETTINGS.get(emotion_lower, self.EMOTION_SETTINGS["default"])
            
            # Apply settings
            self.engine.setProperty('rate', settings_dict['rate'])
            self.engine.setProperty('volume', settings_dict['volume'])
            
            print(f"\n[FALLBACK Speaking - emotion: {emotion}]: '{text}'")
            logger.info(f"[FALLBACK] Speaking (emotion={emotion}, rate={settings_dict['rate']}, volume={settings_dict['volume']}): {text[:60]}...")
            
            # Speak synchronously
            self.engine.say(text)
            self.engine.runAndWait()
            
            print(f"[Fallback playback completed]")
            logger.info("[FALLBACK] Speech synthesis and playback completed")
            
        except Exception as e:
            logger.error(f"[FALLBACK] Error during speech synthesis: {e}")
            print(f"[Error]: {e}")
    
    def listen(self):
        """
        Note: pyttsx3 is text-to-speech only and doesn't support speech recognition.
        This method is a stub for the fallback pipeline.
        Speech recognition should still use Azure or SpeechRecognition library.
        """
        logger.error("[FALLBACK] listen() not supported by pyttsx3. Use Azure or SpeechRecognition for input.")
        return ""
