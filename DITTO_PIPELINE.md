# HackSync SKI - Ditto Pipeline Architecture

## Overview

The **Ditto Pipeline** implements a graceful fallback architecture with primary and secondary services at each layer. This ensures the system remains operational even when primary services fail.

```
┌─────────────────────────────────────────────────────────────────┐
│                     DITTO PIPELINE                               │
│                                                                   │
│  ┌─────────────────┐         ┌─────────────────┐                │
│  │   SPEECH I/O    │         │      LLM        │                │
│  ├─────────────────┤         ├─────────────────┤                │
│  │ PRIMARY: Azure  │         │ PRIMARY: Gemini │                │
│  │   ↓ (fails)     │         │  2.5 Flash      │                │
│  │ FALLBACK:       │         │   ↓ (fails)     │                │
│  │ pyttsx3         │         │ FALLBACK:       │                │
│  │                 │         │ Ollama Local    │                │
│  └─────────────────┘         └─────────────────┘                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Speech Input/Output

### Primary: Azure Cognitive Services

**Location:** `speech/azure.py`

**Features:**
- Speech Recognition (STT) via Azure Speech-to-Text
- Speech Synthesis (TTS) via Azure Text-to-Speech
- Emotion-aware SSML (Scalable Speech Markup Language)
- Viseme support for facial animation
- Multiple neural voices

**Setup:**
```python
AZURE_SPEECH_KEY = "your-key"
AZURE_SPEECH_REGION = "centralindia"
VOICE = "en-US-JennyNeural"
```

**Emotion Styles Mapping:**
- `happy` → `cheerful`
- `sad` → `sad`
- `angry` → `empathetic`
- `excited` → `excited`
- `anxious` → `empathetic`
- `neutral` → `calm`

### Fallback: PyTTSX3

**Location:** `speech/pyttsx3_fallback.py`

**Features:**
- Cross-platform text-to-speech
- Emotion-based rate & volume adjustment
- No external API keys required
- Lightweight and fast

**Emotion Settings:**
```python
{
    "calm": {"rate": 150, "volume": 0.8},
    "happy": {"rate": 180, "volume": 1.0},
    "excited": {"rate": 200, "volume": 1.0},
    "sad": {"rate": 120, "volume": 0.7},
}
```

**Pipeline Flow:**

```python
# speech/azure.py
def speak(self, text: str, emotion: str):
    try:
        # ATTEMPT PRIMARY: AZURE SPEECH SYNTHESIS
        # ... Azure implementation ...
        return  # Success, exit early
    except Exception as e:
        # FALLBACK: PYTTSX3
        if fallback_speaker:
            fallback_speaker.speak(text, emotion)
```

---

## Layer 2: LLM (Large Language Model)

### Primary: Gemini 2.5 Flash (via OpenRouter)

**Location:** `ai/llm_brain.py`

**Features:**
- State-of-the-art Gemini 2.5 Flash model
- Structured JSON output with emotions
- Chat completions endpoint
- High quality responses with low latency

**Configuration:**
```python
OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "google/gemini-2.5-flash"
```

**Setup:**
```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

**Methods:**
- `generate_response(user_input)` - Simple text response
- `generate_structured_response(user_input)` - JSON with emotions

**JSON Response Format:**
```json
{
  "reply": "Your response here",
  "emotions": [
    {"label": "happy", "confidence": 0.9},
    {"label": "excited", "confidence": 0.7}
  ],
  "llm": "google/gemini-2.5-flash"
}
```

### Fallback: Ollama (Local)

**Location:** `ai/llm_brain.py`

**Features:**
- Runs locally without API keys
- Privacy-first (no cloud uploads)
- Instant fallback if Gemini unavailable
- Multiple model options

**Configuration:**
```python
OLLAMA_API_URL = "http://localhost:11434/api"
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_TEMPERATURE = 0.7
OLLAMA_MAX_TOKENS = 100
```

**Setup:**
```bash
# Install Ollama: https://ollama.ai
ollama pull llama3.2:3b
ollama serve
```

**Pipeline Flow:**

```python
# ai/llm_brain.py
def generate_response(self, user_input: str) -> str:
    # Try PRIMARY: Gemini 2.5 Flash
    if self.openrouter_available:
        try:
            generated = self._openrouter_generate(user_input)
            if generated:
                self.last_llm_used = "openrouter"
                return generated
        except Exception as e:
            logger.warning(f"OpenRouter request failed: {e}")
    
    # Fallback: Ollama Local
    if self.available:
        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json={...}
            )
            # ... process response ...
            self.last_llm_used = "ollama"
            return generated_text
        except Exception as e:
            logger.error(f"Ollama error: {e}")
    
    # Final fallback: hardcoded response
    return self._fallback_response(user_input)
```

---

## Layer 3: Emotion Detection

**Location:** `ai/emotion_detector.py`

### Primary: Azure Text Analytics

- Sentiment analysis via Azure
- Maps to emotion styles
- Used in brain.py

### Fallback: Keyword Matching

- Keyword-based sentiment analysis
- No external API required
- Fast and reliable

---

## Layer 4: Intent Parsing & Conversation

**Location:** `core/intent_parser.py`, `core/conversation.py`

These components maintain the original architecture and use the Ollama backend, which is fine since they're internal processing:

```python
# core/intent_parser.py - Extracts user intent
classify_intent(text: str) -> dict

# core/conversation.py - Generates replies
generate_reply(prompt: str) -> str
```

The brain.py wraps these with the ditto pipeline.

---

## Flow Diagram

```
User Input
    ↓
┌─────────────────────────────────────┐
│ speech/azure.py: listen()           │
│ └─ Azure STT                        │
│ └─ (speech recognition)             │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ ai/brain.py: think()                │
│ ├─ ai/emotion_detector.py           │
│ │  └─ PRIMARY: Azure Text Analytics │
│ │  └─ FALLBACK: Keyword matching    │
│ └─ ai/llm_brain.py                  │
│    ├─ PRIMARY: Gemini 2.5 Flash     │
│    └─ FALLBACK: Ollama              │
└──────────┬──────────────────────────┘
           ↓ (response, emotion)
┌─────────────────────────────────────┐
│ speech/azure.py: speak()            │
│ ├─ PRIMARY: Azure TTS with SSML     │
│ └─ FALLBACK: pyttsx3                │
└─────────────────────────────────────┘
           ↓
    User Output (Audio)
```

---

## Environment Setup

### Required Environment Variables

```bash
# Azure Speech Services
AZURE_SPEECH_KEY=your-key
AZURE_SPEECH_REGION=centralindia

# OpenRouter (Gemini 2.5 Flash)
OPENROUTER_API_KEY=your-openrouter-key
```

### Or use config/settings.py

```python
class Settings:
    AZURE_SPEECH_KEY = "..."
    AZURE_SPEECH_REGION = "centralindia"
    
    OPENROUTER_API_KEY = "..."  # via environment variable
```

### Dependencies

```bash
pip install -r requirements.txt

# Azure
pip install azure-cognitiveservices-speech
pip install azure-ai-textanalytics
pip install azure-identity

# Speech fallback
pip install pyttsx3

# Audio playback
pip install pygame

# Other
pip install requests opencv-python mediapipe pyautogui
```

---

## Testing the Pipeline

### Test Gemini + Ollama Pipeline

```python
from ai.llm_brain import LLMBrain

brain = LLMBrain()

# Test simple response
response = brain.generate_response("Hello!")
print(f"Response: {response}")
print(f"LLM Used: {brain.last_llm_used}")

# Test structured response (with emotions)
structured = brain.generate_structured_response("I'm very excited!")
print(f"Structured: {structured}")
```

### Test Azure + pyttsx3 Pipeline

```python
from speech.azure import AzureSpeech

speaker = AzureSpeech()
speaker.speak("Hello world!", "happy")
# Falls back to pyttsx3 if Azure fails
```

### Test Full Brain Pipeline

```python
from ai.brain import think

response, emotion = think("Tell me a joke")
print(f"Response: {response}")
print(f"Emotion: {emotion}")
```

---

## Diagnostics

### Check Pipeline Status

```python
from ai.brain import run_startup_tests

diagnostics = run_startup_tests()
print(diagnostics)

# Output structure:
# {
#     "azure_text": {"available": true, "sample_result": "..."},
#     "llm": {
#         "structured_sample": {...},
#         "last_llm_used": "openrouter"
#     }
# }
```

### View Logs

```bash
# Main app logs
tail -f mirage.log

# Intent parsing logs
tail -f nova_intents.log

# Trace logs
tail -f nova_trace.log

# Memory logs
tail -f passive_memory.log
```

---

## Troubleshooting

### Gemini Not Working (Falls Back to Ollama)

**Symptom:** `last_llm_used: "ollama"` when expecting Gemini

**Solutions:**
1. Check `OPENROUTER_API_KEY` is set: `echo $OPENROUTER_API_KEY`
2. Verify API key is valid: https://openrouter.ai
3. Check internet connection
4. Review logs: `grep "OpenRouter" mirage.log`

### Ollama Not Working

**Symptom:** Responses use fallback hardcoded text

**Solutions:**
1. Start Ollama: `ollama serve`
2. Verify model is installed: `ollama list`
3. Pull model: `ollama pull llama3.2:3b`
4. Check endpoint: `curl http://localhost:11434/api/tags`

### Azure Speech Not Working (Falls Back to pyttsx3)

**Symptom:** Output uses pyttsx3 voice instead of Azure

**Solutions:**
1. Check `AZURE_SPEECH_KEY` is set and valid
2. Verify region: `AZURE_SPEECH_REGION=centralindia`
3. Check internet connection
4. Review logs: `grep "AZURE" mirage.log`

### pyttsx3 Not Working

**Symptom:** No audio output and errors about pyttsx3

**Solutions:**
1. Install pyttsx3: `pip install pyttsx3`
2. On Linux, may need espeak: `sudo apt-get install espeak`
3. On macOS: usually works out of the box
4. On Windows: usually works out of the box

---

## Architecture Principles

### 1. Graceful Degradation
Each layer has a primary and fallback. If primary fails, secondary is automatically used.

### 2. Transparency
Logs and diagnostics show which service was used (`last_llm_used`, logs with `[AZURE]`, `[FALLBACK]`, etc.)

### 3. No Single Point of Failure
- Speech I/O: Azure → pyttsx3
- LLM: Gemini → Ollama
- Emotions: Azure Text Analytics → Keyword matching

### 4. Performance Optimization
- Gemini is fast (primary)
- Ollama is local (fast fallback)
- Both are orders of magnitude faster than older approaches

### 5. Cost Efficiency
- pyttsx3 and Ollama require no API calls
- Azure and Gemini are paid but high quality
- Automatic fallback minimizes API usage

---

## File Structure

```
HackSync_SKI/
├── ai/
│   ├── brain.py                    # DITTO: Orchestrates emotion + LLM
│   ├── emotion_detector.py         # Azure → Keyword matching
│   ├── llm_brain.py               # DITTO: Gemini 2.5 Flash → Ollama
│   ├── ollama_llm.py
│   └── __pycache__/
├── speech/
│   ├── azure.py                    # DITTO: Azure TTS → pyttsx3
│   ├── pyttsx3_fallback.py        # NEW: pyttsx3 implementation
│   └── __pycache__/
├── config/
│   ├── settings.py                 # Configuration with DITTO comments
│   └── __pycache__/
├── core/
│   ├── brain.py                    # (keep existing structure)
│   ├── conversation.py
│   ├── intent_parser.py
│   └── ...
├── requirements.txt                # Updated with pyttsx3, azure libs
└── README.md
```

---

## Future Enhancements

1. **Caching Layer**: Cache Gemini responses to reduce API calls
2. **Custom Models**: Add more Ollama models for different tasks
3. **Real-time Monitoring**: Dashboard showing which service is used
4. **Load Balancing**: Distribute requests across multiple models
5. **Fine-tuning**: Train Ollama models on custom intents
6. **Latency Metrics**: Track response times for optimization

---

## References

- **OpenRouter API**: https://openrouter.ai/docs
- **Gemini 2.5 Flash**: https://ai.google.dev/
- **Ollama**: https://ollama.ai
- **Azure Cognitive Services**: https://azure.microsoft.com/services/cognitive-services/
- **pyttsx3**: https://pypi.org/project/pyttsx3/

