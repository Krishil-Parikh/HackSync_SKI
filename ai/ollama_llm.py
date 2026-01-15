import requests
import logging
from configuration.settings import settings

logger = logging.getLogger(__name__)

class OllamaLLM:
    """Local LLM generation using Ollama with Qwen/Mistral models"""
    
    def __init__(self):
        self.api_url = settings.OLLAMA_API_URL
        self.model = settings.OLLAMA_MODEL
        self.temperature = settings.OLLAMA_TEMPERATURE
        self.max_tokens = settings.OLLAMA_MAX_TOKENS
        
        logger.info(f"[INIT] Ollama LLM initialized: model={self.model}, url={self.api_url}")
        self._warm_up_model()
    
    def _warm_up_model(self):
        """Load model into memory for faster first response"""
        try:
            logger.info(f"[WARMUP] Warming up Ollama model: {self.model}")
            response = requests.post(
                f"{self.api_url}/generate",
                json={
                    "model": self.model,
                    "prompt": "Hi",
                    "stream": False
                },
                timeout=120
            )
            logger.info(f"[WARMUP] Model loaded successfully")
        except Exception as e:
            logger.warning(f"[WARMUP] Could not warm up model: {e}")
    
    def generate(self, prompt: str) -> str:
        """Generate response from Ollama LLM"""
        try:
            logger.info(f"[LLM] Generating response for prompt: '{prompt[:50]}...'")
            
            response = requests.post(
                f"{self.api_url}/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()["response"].strip()
                logger.info(f"[LLM] Generated: '{result[:80]}...'")
                return result
            else:
                logger.error(f"[LLM] Request failed: {response.status_code}")
                return self._fallback_response(prompt)
        
        except requests.exceptions.ConnectionError:
            logger.error("[LLM] Ollama not running on localhost:11434")
            return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"[LLM] Generation error: {e}")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, user_input: str) -> str:
        """Fallback response if Ollama is not available"""
        logger.warning("[LLM] Using fallback response")
        
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ["hello", "hi", "hey"]):
            return "Hello! It's great to meet you. How can I assist you today?"
        elif "?" in user_input:
            return "That's a great question! Let me think about that carefully for you."
        elif any(word in user_lower for word in ["thank", "thanks", "appreciate"]):
            return "You're very welcome! I'm always happy to help."
        else:
            return "That's interesting. I appreciate you sharing that with me. Can you tell me more?"


# Global instance
_ollama_instance = None

def get_ollama_llm() -> OllamaLLM:
    """Get or create Ollama LLM instance"""
    global _ollama_instance
    if _ollama_instance is None:
        _ollama_instance = OllamaLLM()
    return _ollama_instance
