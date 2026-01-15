import logging
import os
import sys

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mirage.log', encoding='utf-8')
    ]
)

class Settings:
    AZURE_SPEECH_KEY = "7JbMTmjAkBkm1J1biQ4Vc5fFWp7BP1DHDQXla5a28xRrASR5gha7JQQJ99CAACGhslBXJ3w3AAAYACOG42qn"
    AZURE_SPEECH_REGION = "centralindia"
    
    # Azure Text Analytics for emotion detection
    AZURE_TEXT_ENDPOINT = "https://centralindia.api.cognitive.microsoft.com/"
    AZURE_TEXT_KEY = "7JbMTmjAkBkm1J1biQ4Vc5fFWp7BP1DHDQXla5a28xRrASR5gha7JQQJ99CAACGhslBXJ3w3AAAYACOG42qn"  # Using same key, if needed use different one
    
    VOICE = "en-US-JennyNeural"
    
    # Supported Azure voices
    SUPPORTED_VOICES = [
        "en-US-AriaNeural",
        "en-US-JennyNeural",
        "en-US-GuyNeural",
        "en-US-AmberNeural",
        "en-US-AshleyNeural"
    ]
    
    # Azure emotion styles
    EMOTION_STYLES = {
        "happy": "cheerful",
        "sad": "sad",
        "angry": "empathetic",
        "neutral": "calm",
        "excited": "excited",
        "anxious": "empathetic",
        "default": "calm"
    }
    
    # Ollama LLM Configuration (FALLBACK)
    OLLAMA_API_URL = "http://localhost:11434/api"
    OLLAMA_MODEL = "llama3.2:3b"  # Fast model: llama3.2:3b (2.0GB), qwen3:4b (2.5GB), deepseek-coder:6.7b (3.8GB)
    OLLAMA_TEMPERATURE = 0.7
    OLLAMA_MAX_TOKENS = 100  # Reduced for faster generation
    
    # OpenRouter (PRIMARY) - Google Gemini 2.5 Flash
    # Configuration for remote LLM - do NOT store API keys here
    # Provide your OpenRouter API key via the environment variable: OPENROUTER_API_KEY
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL = "google/gemini-2.5-flash"  # PRIMARY: Gemini 2.5 Flash
    
    # LLM Pipeline:
    # 1. Primary: Gemini 2.5 Flash via OpenRouter (requires OPENROUTER_API_KEY env var)
    # 2. Fallback: Ollama local model (requires Ollama running locally)

settings = Settings()
