# Ditto Pipeline Quick Reference

## 🎯 What is the Ditto Pipeline?

A **graceful fallback architecture** where each component has a primary service and automatic fallback:

```
PRIMARY → FALLBACK → FINAL FALLBACK (if needed)
```

## 🔄 Pipeline Layers

### Layer 1: Speech I/O
```
Speech Recognition:  Azure Speech-to-Text
Speech Synthesis:    Azure TTS → pyttsx3 (if fails)
```

### Layer 2: Emotion Detection
```
Primary:    Azure Text Analytics
Fallback:   Keyword-based sentiment
```

### Layer 3: LLM (Language Model)
```
Primary:     Gemini 2.5 Flash (via OpenRouter)
Fallback:    Ollama (local, no API key)
Final:       Hardcoded fallback responses
```

## 🚀 Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Set API Keys
```bash
export OPENROUTER_API_KEY="your-key"
export AZURE_SPEECH_KEY="your-key"
export AZURE_SPEECH_REGION="centralindia"
```

### 3. Start Ollama (Optional)
```bash
ollama serve
```

### 4. Run
```bash
python main.py
```

## 📊 Service Status Examples

### Everything Works
```
[LLM] Generated response (OpenRouter)
[AZURE] Speech synthesis successful
→ Gemini + Azure
```

### Gemini Down → Uses Ollama
```
[LLM] OpenRouter request failed
[LLM] Generated response (Ollama)
[AZURE] Speech synthesis successful
→ Ollama + Azure
```

### Azure Down → Uses pyttsx3
```
[LLM] Generated response (OpenRouter)
[AZURE] Speech synthesis failed
[FALLBACK] Speaking (emotion=happy, rate=180)
→ Gemini + pyttsx3
```

### All Down → Uses All Fallbacks
```
[LLM] Ollama unavailable
[FALLBACK] Using fallback response
[FALLBACK] Speaking (emotion=calm, rate=150)
→ Hardcoded + pyttsx3
```

## 🔍 Check Status

```python
from ai.brain import run_startup_tests

diagnostics = run_startup_tests()
print(diagnostics)

# Shows:
# - Azure Text Analytics available?
# - Gemini accessible?
# - Ollama running?
# - Which LLM is primary?
```

## 📝 Logging

All services log with clear prefixes:
```
[AZURE]      - Azure services in use
[FALLBACK]   - Fallback services in use
[LLM]        - LLM operations
[EMOTION]    - Emotion detection
```

View logs:
```bash
tail -f mirage.log | grep "\[AZURE\]\|\[FALLBACK\]\|\[LLM\]"
```

## 📋 Files Changed

| File | What | Why |
|------|------|-----|
| `speech/pyttsx3_fallback.py` | ✨ NEW | Speech fallback |
| `speech/azure.py` | ✏️ MODIFIED | Added fallback |
| `config/settings.py` | ✏️ MODIFIED | Added docs |
| `requirements.txt` | ✏️ MODIFIED | Added deps |
| `ai/llm_brain.py` | ✓ UNCHANGED | Already had ditto! |
| `ai/brain.py` | ✓ UNCHANGED | Already orchestrates! |

## 🎮 Test Commands

### Test Gemini
```python
from ai.llm_brain import LLMBrain
brain = LLMBrain()
print(brain.generate_response("Hi!"))
print(brain.last_llm_used)  # "openrouter" or "ollama"
```

### Test Speech
```python
from speech.azure import AzureSpeech
speaker = AzureSpeaker()
speaker.speak("Hello!", "happy")
```

### Test Full Brain
```python
from ai.brain import think
response, emotion = think("Tell me a joke")
print(response, emotion)
```

## ⚙️ Configuration

**Primary Models:**
- LLM: `google/gemini-2.5-flash`
- Speech: Azure TTS + SSML
- Emotion: Azure Text Analytics

**Fallback Models:**
- LLM: `llama3.2:3b` (Ollama)
- Speech: pyttsx3
- Emotion: Keyword matching

Edit in `config/settings.py`

## 🔐 API Keys Needed

| Service | Key | Where | Optional? |
|---------|-----|-------|-----------|
| Gemini | `OPENROUTER_API_KEY` | OpenRouter | No (falls back to Ollama) |
| Azure Speech | `AZURE_SPEECH_KEY` | Azure Portal | No (falls back to pyttsx3) |
| Azure Region | `AZURE_SPEECH_REGION` | Azure Portal | No |

## 🐛 Troubleshooting

**Gemini not used?**
```bash
echo $OPENROUTER_API_KEY  # Should show key
grep "OpenRouter" mirage.log
```

**Ollama available?**
```bash
curl http://localhost:11434/api/tags
```

**pyttsx3 not working?**
```bash
pip install --upgrade pyttsx3
# On Linux: sudo apt-get install espeak
```

## 📚 Files to Read

1. **Quick Overview**: This file (you're reading it!)
2. **Full Architecture**: `DITTO_PIPELINE.md`
3. **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
4. **Code**: `speech/pyttsx3_fallback.py` and `speech/azure.py`

## 🎯 Key Principles

1. **Automatic Fallback** - No manual intervention
2. **Transparent Logging** - See which service is used
3. **Cost Efficient** - Uses free services when paid ones fail
4. **Privacy First** - Ollama has no cloud uploads
5. **Zero Downtime** - Always has a working solution

---

**Questions?** See `DITTO_PIPELINE.md` for full documentation.
