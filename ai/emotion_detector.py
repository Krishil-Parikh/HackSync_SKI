import logging
from configuration.settings import settings

logger = logging.getLogger(__name__)

class EmotionDetector:
    """Detects emotions from text using Azure Text Analytics
    
    Pipeline:
    - PRIMARY: Azure Text Analytics (emotions enabled, rich emotional responses)
    - FALLBACK: Keyword-based sentiment (emotions disabled, neutral style only)
    """
    
    EMOTION_MAP = {
        "positive": "excited",
        "negative": "sad",
        "neutral": "calm",
        "mixed": "calm"
    }
    
    def __init__(self, azure_available=True):
        """Initialize emotion detector
        
        Args:
            azure_available (bool): Whether Azure services are available
        """
        self.azure_available = azure_available
        self.client = None
        self.emotion_enabled = False
        
        try:
            from azure.ai.textanalytics import TextAnalyticsClient
            from azure.core.credentials import AzureKeyCredential
            
            self.client = TextAnalyticsClient(
                endpoint=settings.AZURE_TEXT_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_TEXT_KEY)
            )
            self.emotion_enabled = azure_available
            logger.info(f"[INIT] Emotion Detector: Azure Text Analytics initialized")
            logger.info(f"[INIT] Emotion Mode: {'ENABLED' if self.emotion_enabled else 'DISABLED'}")
        except ImportError:
            logger.warning("[WARN] azure-ai-textanalytics not installed, emotions will be disabled")
            self.emotion_enabled = False
        except Exception as e:
            logger.warning(f"[WARN] Could not initialize Azure Text Analytics: {e}, emotions disabled")
            self.emotion_enabled = False
    
    def detect_emotion(self, text: str) -> str:
        """Detect emotion from text and return voice style
        
        When Azure is available: Rich emotional responses with detailed sentiment
        When Azure fails: Neutral calm voice only (no emotions)
        """
        if not text.strip():
            return settings.EMOTION_STYLES.get("default", "calm")
        
        # If Azure not available, always return neutral
        if not self.emotion_enabled:
            print(f"[Sentiment Analysis]: neutral (emotions disabled)")
            logger.info("[EMOTION] Using fallback neutral style (emotions disabled)")
            return settings.EMOTION_STYLES.get("neutral", "calm")
        
        try:
            if self.client and self.emotion_enabled:
                # Use Azure Text Analytics for sentiment analysis
                result = self.client.analyze_sentiment([text], language="en")[0]
                sentiment = result.sentiment
                confidence = result.confidence_scores
                
                print(f"[Sentiment Analysis]: {sentiment}")
                print(f"[Confidence]: Positive={confidence.positive:.2f}, Negative={confidence.negative:.2f}, Neutral={confidence.neutral:.2f}")
                
                # Map sentiment to emotion
                if sentiment == "positive":
                    emotion_style = settings.EMOTION_STYLES.get("happy", "cheerful")
                elif sentiment == "negative":
                    emotion_style = settings.EMOTION_STYLES.get("sad", "sad")
                elif sentiment == "mixed":
                    emotion_style = settings.EMOTION_STYLES.get("anxious", "empathetic")
                else:
                    emotion_style = settings.EMOTION_STYLES.get("neutral", "calm")
                
                logger.info(f"[EMOTION] Detected: {sentiment} -> {emotion_style}")
                return emotion_style
        except Exception as e:
            logger.error(f"[ERROR] Emotion detection failed: {e}")
            return self._fallback_emotion_detection(text)
        
        # Fallback if client is None but emotions were supposed to be enabled
        return self._fallback_emotion_detection(text)
    
    
    def _fallback_emotion_detection(self, text: str) -> str:
        """Fallback sentiment analysis using keyword matching
        
        NOTE: When using fallback, emotions are DISABLED and returns neutral only
        """
        # When falling back, always return neutral (emotions disabled)
        print(f"[Sentiment Analysis]: neutral (fallback)")
        logger.info("[EMOTION] Using fallback - emotions disabled (neutral only)")
        return settings.EMOTION_STYLES.get("neutral", "calm")
    
    def set_azure_status(self, available: bool):
        """Update Azure availability status
        
        Called by system diagnostics after checking Azure connectivity
        """
        self.azure_available = available
        self.emotion_enabled = available and self.client is not None
        logger.info(f"[EMOTION] Azure status updated: available={available}, emotion_enabled={self.emotion_enabled}")
        
        if not self.emotion_enabled:
            print("[⚠️  WARNING] Emotion mode disabled - will use neutral calm voice for all responses")

