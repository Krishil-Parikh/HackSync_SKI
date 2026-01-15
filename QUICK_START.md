# HackSync_SKI - Quick Reference Guide

## What Was Implemented

### ✅ Ditto Pipeline Architecture
- **Speech**: Azure TTS (primary) → pyttsx3 (fallback)
- **LLM**: Gemini 2.5 Flash (primary) → Ollama (fallback)
- **Emotions**: Azure sentiment analysis (if available) → Disabled (if not)
- **Diagnostics**: Full 7-point system health check on startup

### ✅ Emotion Mode Behavior
```
Azure Services ONLINE:
  ✓ Emotions ENABLED
  ✓ Rich vocal styles (happy, sad, excited, calm, empathetic, curious, cheerful)
  ✓ Sentiment-aware responses

Azure Services OFFLINE:
  ✓ Emotions DISABLED
  ✓ Neutral "calm" voice for all responses
  ✓ System continues working with pyttsx3
```

### ✅ Gestures Removed
- All gesture control code deleted
- Hand gesture worker disabled
- System is now focused on pure conversation and LLM-based actions

---

## Key Files

| File | Purpose | Status |
|------|---------|--------|
| [`main.py`](main.py) | Entry point with diagnostics | ✓ Updated |
| [`core/speaker.py`](core/speaker.py) | Speech synthesis coordinator | ✓ Refactored |
| [`core/system_diagnostics.py`](core/system_diagnostics.py) | Health check system | ✓ New |
| [`speech/azure.py`](speech/azure.py) | Azure TTS with fallback | ✓ Working |
| [`speech/pyttsx3_fallback.py`](speech/pyttsx3_fallback.py) | Fallback speaker | ✓ Integrated |
| [`ai/emotion_detector.py`](ai/emotion_detector.py) | Emotion detection | ✓ Updated |
| [`ai/llm_brain.py`](ai/llm_brain.py) | Gemini + Ollama LLM | ✓ Already correct |
| [`config.py`](config.py) | Logger configuration | ✓ Unchanged |
| [`config/settings.py`](configuration/settings.py) | API settings | ✓ Unchanged |

---

## Startup Sequence

1. **Python starts main.py**
2. **System Diagnostics Runs** (7 tests):
   - Azure Speech Service ✓
   - Azure Text Analytics ✓
   - Ollama LLM ✓
   - Gemini 2.5 Flash ✓
   - Database/Memory ✓
   - Audio Input ✓
   - pyttsx3 Fallback ✓
3. **Determines System Status**: READY or DEGRADED
4. **Determines Emotion Mode**: ENABLED or DISABLED
5. **Initializes Components**:
   - Azure Speech Service
   - Emotion Detector
   - Speaker Module
6. **Starts Background Workers**:
   - Memory Worker Process
   - Model Warm-up Process
7. **Speaks**: "NOVA online."
8. **Enters Loop**: 🎧 Listening...

---

## Running the System

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
set OPENROUTER_API_KEY=your_key
set AZURE_SPEECH_KEY=your_key
set AZURE_SPEECH_REGION=eastus
set AZURE_TEXT_KEY=your_key
set AZURE_TEXT_ENDPOINT=https://...
```

### Start the System
```bash
python main.py
```

### Expected Output
```
╔══════════════════════════════════════════════╗
║    HACKSYNC_SKI SYSTEM DIAGNOSTICS           ║
║      Starting comprehensive tests...         ║
╚══════════════════════════════════════════════╝

[TEST] Azure Speech Service
✓ Azure SDK imported successfully

[TEST] Azure Text Analytics
✓ Sentiment analysis test: SUCCESS

... (5 more tests)

[SUMMARY] System Status
✓ Overall Status: READY
✓ Critical Services: 2/2 online

💭 Emotion Mode: ENABLED (Azure)
🔊 Audio Output: Azure + pyttsx3 fallback

[NOVA]: NOVA online.
🎧 Listening...
```

---

## Architecture Flowchart

```
USER INPUT (text via listen())
        ↓
EMOTION DETECTION
  Azure Sentiment? → YES → emotional response
  Azure Sentiment? → NO  → calm response
        ↓
LLM GENERATION
  Gemini 2.5 Flash? → YES → use Gemini
  Gemini fails?     → FALLBACK to Ollama
        ↓
SPEECH SYNTHESIS
  Azure TTS? → YES → Azure voice with emotion
  Azure TTS? → NO  → pyttsx3 calm voice
        ↓
AUDIO PLAYBACK (pygame or system player)
        ↓
MEMORY UPDATE (active + passive)
        ↓
BACK TO LISTENING
```

---

## Configuration

### Azure Settings (config/settings.py)
```python
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "eastus")
AZURE_TEXT_KEY = os.getenv("AZURE_TEXT_KEY")
AZURE_TEXT_ENDPOINT = os.getenv("AZURE_TEXT_ENDPOINT")
VOICE = "en-US-AriaNeural"  # Azure voice
```

### LLM Models
```python
# Primary
GEMINI_MODEL = "google/gemini-2.5-flash"  # via OpenRouter
GEMINI_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Fallback
OLLAMA_MODELS = {
    "conversation": "llama3.2:3b",
    "intent": "qwen3:4b",
    "memory": "llama3:instruct"
}
```

### Emotion Styles (for Azure voice)
```python
EMOTION_STYLES = {
    "calm": "calm",
    "happy": "cheerful",
    "excited": "excited",
    "sad": "sad",
    "empathetic": "empathetic",
    "curious": "curious",
    "cheerful": "cheerful"
}
```

---

## Diagnostics Report

On every startup, a file `diagnostics_report.json` is generated:

```json
{
  "timestamp": "ISO-8601 timestamp",
  "components": {
    "azure_speech": {"status": "ONLINE|OFFLINE|UNAVAILABLE"},
    "azure_emotion": {"status": "ONLINE|OFFLINE|UNAVAILABLE"},
    "ollama_llm": {"status": "ONLINE|OFFLINE|UNAVAILABLE"},
    "gemini_llm": {"status": "CONFIGURED|UNCONFIGURED"},
    "database": {"status": "ONLINE|OFFLINE"},
    "audio_input": {"status": "ONLINE|WARNING"},
    "pyttsx3_fallback": {"status": "ONLINE|UNAVAILABLE"}
  },
  "overall_status": "READY|DEGRADED",
  "emotion_mode": "ENABLED|DISABLED",
  "summary": {
    "critical_online": 0-2,
    "fallback_online": 0-4,
    "emotion_capable": true|false
  }
}
```

---

## Troubleshooting

### "Azure SDK not installed"
```
✗ Azure SDK not installed

SOLUTION: pip install azure-cognitiveservices-speech
          pip install azure-ai-textanalytics
```

### "ollama_generate() got an unexpected keyword argument 'stream'"
```
Already fixed in latest diagnostics. If you see this error:

SOLUTION: Check ollama/client.py - don't pass 'stream' parameter
```

### "No module named 'config.settings'"
```
Already fixed. config/settings.py must be imported inside functions,
not at module level to avoid shadowing issues with config.py

SOLUTION: from config.settings import settings  (inside function)
```

### "Emotion Mode: DISABLED (Fallback pyttsx3)"
```
This is NORMAL when:
- Azure Text Analytics SDK not installed
- Azure credentials invalid
- Azure service unavailable

EXPECTED BEHAVIOR:
- All responses use neutral "calm" voice
- No sentiment analysis performed
- System continues working
```

### Audio playback not working
```
✓ Audio file created but playback failed

CHECK:
1. pygame installed? → pip install pygame
2. Speakers connected?
3. Volume turned on?

FALLBACK: Audio file saved to output/audio/speech_output.wav
```

---

## Development Notes

### How Emotion Mode Works

**When ENABLED (Azure working):**
```python
# In core/speaker.py
emotion = emotion_detector.detect_emotion(text)  # Azure sentiment
azure_speech.speak(text, emotion)                # Azure TTS with emotion
```

**When DISABLED (Azure down):**
```python
# In core/emotion_detector.py
if not self.emotion_enabled:
    return "calm"  # Always return neutral

# In core/speaker.py
emotion = "calm"  # No emotion detection
fallback_speaker.speak(text, "calm")  # pyttsx3 neutral
```

### How Fallback Works

**LLM Fallback:**
```python
try:
    response = call_gemini_2_5_flash()  # Primary
except:
    response = call_ollama()  # Fallback
```

**Speech Fallback:**
```python
try:
    azure_speech.speak(text, emotion)  # Primary
except:
    pyttsx3_fallback.speak(text, "calm")  # Fallback (emotions off)
```

### Memory System

- **ActiveMemory**: Current conversation (5 turns)
- **PassiveMemory**: Long-term facts learned
- **Memory Bus**: JSON file for inter-process communication

```python
from core.memory import ActiveMemory, PassiveMemory
from core.active_memory_writer import append_turn

active = ActiveMemory(max_turns=5)
active.add(user_text, nova_reply)
append_turn(user_text, nova_reply)  # Save to JSON
```

---

## Status Summary

| Feature | Status | Details |
|---------|--------|---------|
| Speech Synthesis | ✓ Complete | Azure + pyttsx3 fallback |
| Emotion Detection | ✓ Complete | Auto-disables when Azure down |
| LLM Integration | ✓ Complete | Gemini + Ollama pipeline |
| Gestures | ✓ Removed | No longer in system |
| Diagnostics | ✓ Complete | 7-point health check |
| Memory System | ✓ Complete | Active + Passive working |
| Intent Parsing | ✓ Complete | Using LLM brain |
| Main Loop | ✓ Clean | No gesture code |

---

## Files to Know

**Core Logic:**
- `main.py` - Entry point and main loop
- `core/speaker.py` - Speech synthesis coordinator
- `ai/emotion_detector.py` - Emotion detection
- `ai/llm_brain.py` - LLM calls (Gemini + Ollama)

**Infrastructure:**
- `core/system_diagnostics.py` - Health checks
- `core/memory.py` - Memory management
- `core/conversation.py` - Reply generation
- `core/intent_parser.py` - Intent classification

**I/O:**
- `speech/azure.py` - Azure TTS primary
- `speech/pyttsx3_fallback.py` - pyttsx3 fallback
- `core/listener.py` - Speech recognition

**Configuration:**
- `config.py` - Logging setup
- `config/settings.py` - API keys and settings
- `requirements.txt` - Dependencies
- `diagnostics_report.json` - System status (generated)

---

## Next Steps

1. ✓ Verify environment variables are set
2. ✓ Run `python main.py` to see diagnostics
3. ✓ Check `diagnostics_report.json` for details
4. ✓ Interact with the system to test conversation
5. ✓ Monitor logs in `nova_trace.log` for issues

---

**Ditto Pipeline - Multi-Level Fallback Architecture**  
**Status**: ✓ Implemented, Tested, Ready for Use  
**Date**: January 15, 2026
