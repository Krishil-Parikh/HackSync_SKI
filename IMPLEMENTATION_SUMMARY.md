# Ditto Pipeline Implementation Summary

## What's Changed

### 1. **New Files**
- `speech/pyttsx3_fallback.py` - Fallback text-to-speech using pyttsx3
- `DITTO_PIPELINE.md` - Comprehensive architecture documentation

### 2. **Modified Files**

#### `speech/azure.py`
- Added pyttsx3 fallback import
- Updated `speak()` method with try-except pipeline:
  - **PRIMARY**: Azure Speech TTS with SSML and visemes
  - **FALLBACK**: pyttsx3 with emotion-based rate/volume adjustment
- Clear logging showing which service is used (`[AZURE]` vs `[FALLBACK]`)

#### `config/settings.py`
- Added comments documenting LLM pipeline
- Confirmed Gemini 2.5 Flash as primary model
- Noted Ollama as fallback

#### `requirements.txt`
- Added `pyttsx3` for speech fallback
- Added Azure libraries: `azure-cognitiveservices-speech`, `azure-ai-textanalytics`, `azure-identity`
- Added `pygame` for audio playback

### 3. **Existing Code (No Changes Needed)**

#### `ai/llm_brain.py`
✅ **Already implements ditto pipeline!**
- PRIMARY: OpenRouter Gemini 2.5 Flash
- FALLBACK: Ollama local model
- FINAL FALLBACK: Hardcoded responses

#### `ai/brain.py`
✅ **Already orchestrates emotion detection + LLM**
- Emotion detection with Azure/keyword fallback
- Response generation via LLM brain

---

## Architecture: The Ditto Pipeline

```
INPUT (Speech)
    ↓
┌──────────────────────────────────┐
│ SPEECH LAYER                     │
├──────────────────────────────────┤
│ PRIMARY: Azure Speech-to-Text    │
│ FALLBACK: (SpeechRecognition)    │
└──────────────┬───────────────────┘
               ↓
┌──────────────────────────────────┐
│ EMOTION DETECTION LAYER          │
├──────────────────────────────────┤
│ PRIMARY: Azure Text Analytics    │
│ FALLBACK: Keyword Matching       │
└──────────────┬───────────────────┘
               ↓
┌──────────────────────────────────┐
│ LLM LAYER                        │
├──────────────────────────────────┤
│ PRIMARY: Gemini 2.5 Flash        │
│ FALLBACK: Ollama (local)         │
│ FALLBACK2: Hardcoded responses   │
└──────────────┬───────────────────┘
               ↓
┌──────────────────────────────────┐
│ SPEECH OUTPUT LAYER              │
├──────────────────────────────────┤
│ PRIMARY: Azure Text-to-Speech    │
│ FALLBACK: pyttsx3                │
└──────────────┬───────────────────┘
               ↓
         OUTPUT (Audio)
```

---

## Key Features

### ✅ Graceful Degradation
If Azure services fail → Automatic fallback to free/local solutions
- No manual intervention needed
- Users won't know a service failed (seamless experience)

### ✅ Transparent Logging
Every log message indicates which service is used:
```
[AZURE] Speech synthesis successful
[FALLBACK] Using pyttsx3 for speech
[LLM] Generated response (OpenRouter)
[LLM] Ollama not available, using fallback response
```

### ✅ Cost Optimization
- Uses expensive services (Azure, Gemini) as primary
- Falls back to free services (pyttsx3, Ollama) automatically
- Only pays for API calls when needed

### ✅ Privacy First
If APIs fail, Ollama runs locally with no data sent to cloud
- All processing on local machine
- Perfect for sensitive data

---

## Setup Instructions

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# Azure Services
export AZURE_SPEECH_KEY="your-azure-key"
export AZURE_SPEECH_REGION="centralindia"

# Gemini 2.5 Flash (via OpenRouter)
export OPENROUTER_API_KEY="your-openrouter-key"
```

### 3. Start Ollama (Optional but Recommended for Fallback)
```bash
# Install from https://ollama.ai
ollama serve
```

### 4. Run the Application
```bash
python main.py
```

---

## Testing the Pipeline

### Test Gemini LLM
```python
from ai.llm_brain import LLMBrain

brain = LLMBrain()
response = brain.generate_response("Hello!")
print(f"Response: {response}")
print(f"Used: {brain.last_llm_used}")  # Should show "openrouter" or "ollama"
```

### Test Speech Output
```python
from speech.azure import AzureSpeech

speaker = AzureSpeech()
speaker.speak("Hello world!", "happy")
# Uses Azure if available, falls back to pyttsx3 automatically
```

### Test Full Pipeline
```python
from ai.brain import think

response, emotion = think("Tell me a joke!")
print(f"Response: {response}")
print(f"Emotion: {emotion}")
```

### Check Pipeline Health
```python
from ai.brain import run_startup_tests

diagnostics = run_startup_tests()
print(diagnostics)
# Shows which services are available and working
```

---

## Logging

View logs to see which services are being used:

```bash
# Main application logs
tail -f mirage.log

# Search for specific service
grep -i "openrouter\|ollama\|azure\|fallback" mirage.log

# Search for errors
grep -i "error\|failed\|warning" mirage.log
```

---

## Troubleshooting

### Gemini Not Used (Falls Back to Ollama)
```bash
# Check if API key is set
echo $OPENROUTER_API_KEY

# Check logs
grep "OpenRouter" mirage.log
```

### Ollama Not Available
```bash
# Start Ollama
ollama serve

# Verify model
ollama list
```

### Azure Speech Not Working
```bash
# Check logs for [AZURE] messages
grep "\[AZURE\]" mirage.log

# Verify API key
echo $AZURE_SPEECH_KEY
```

### pyttsx3 Not Working
```bash
# Install or reinstall
pip install --upgrade pyttsx3

# On Linux, may need espeak
sudo apt-get install espeak
```

---

## File Changes Summary

| File | Change | Reason |
|------|--------|--------|
| `speech/pyttsx3_fallback.py` | NEW | Implements pyttsx3 fallback for speech |
| `speech/azure.py` | UPDATED | Added fallback logic to `speak()` |
| `config/settings.py` | UPDATED | Added documentation, confirmed Gemini |
| `requirements.txt` | UPDATED | Added pyttsx3, Azure libs |
| `DITTO_PIPELINE.md` | NEW | Full architecture documentation |
| `ai/llm_brain.py` | UNCHANGED | Already had ditto pattern! |
| `ai/brain.py` | UNCHANGED | Already orchestrates correctly! |
| `core/` | UNCHANGED | Intent parser and conversation intact |

---

## Performance Notes

- **Gemini 2.5 Flash**: ~1-2 seconds for response
- **Ollama (llama3.2:3b)**: ~3-5 seconds for response  
- **Azure TTS**: ~0.5-1 second for synthesis
- **pyttsx3**: ~0.1-0.5 seconds for synthesis

Total end-to-end latency: **2-7 seconds** depending on services used

---

## References

- **Ditto Pattern**: Graceful degradation with fallback chains
- **OpenRouter API**: https://openrouter.ai
- **Gemini 2.5 Flash**: https://ai.google.dev
- **Ollama**: https://ollama.ai
- **Azure Cognitive Services**: https://azure.microsoft.com/services/cognitive-services/
- **pyttsx3**: https://pypi.org/project/pyttsx3/

