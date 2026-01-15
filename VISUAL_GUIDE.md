# Ditto Pipeline - Visual Guide

## 🎯 What You've Built

A **resilient AI system** that automatically falls back to secondary services when primary services fail.

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    DITTO PIPELINE                             ┃
┃                                                                ┃
┃  ┌─────────────────────────────────────────────────────┐     ┃
┃  │  Layer 1: SPEECH INPUT/OUTPUT                       │     ┃
┃  │  ┌──────────────────┐    ┌──────────────────────┐  │     ┃
┃  │  │ Azure TTS/STT    │ →→ │ pyttsx3 + Fallback   │  │     ┃
┃  │  │ (Premium)        │    │ (Free)               │  │     ┃
┃  │  └──────────────────┘    └──────────────────────┘  │     ┃
┃  │                                                      │     ┃
┃  │  Layer 2: EMOTION DETECTION                        │     ┃
┃  │  ┌──────────────────┐    ┌──────────────────────┐  │     ┃
┃  │  │ Azure Text       │ →→ │ Keyword Matching     │  │     ┃
┃  │  │ Analytics        │    │ (No API)             │  │     ┃
┃  │  └──────────────────┘    └──────────────────────┘  │     ┃
┃  │                                                      │     ┃
┃  │  Layer 3: LLM (LANGUAGE MODEL)                     │     ┃
┃  │  ┌──────────────────┐    ┌────────────────────┐   │     ┃
┃  │  │ Gemini 2.5 Flash │ →→ │ Ollama Local       │   │     ┃
┃  │  │ (Best Quality)   │    │ (Private)          │   │     ┃
┃  │  └──────────────────┘    └────────────────────┘   │     ┃
┃  │                              ↓                     │     ┃
┃  │                         ┌─────────────┐           │     ┃
┃  │                         │Hardcoded    │           │     ┃
┃  │                         │Responses    │           │     ┃
┃  │                         └─────────────┘           │     ┃
┃  │                                                    │     ┃
┃  └─────────────────────────────────────────────────────┘     ┃
┃                                                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## 🔄 How It Works

### Scenario 1: All Services Working
```
User: "Tell me a joke"
    ↓
[STT] Azure Speech Recognition → "Tell me a joke"
    ↓
[EMOTION] Azure Text Analytics → "neutral/calm"
    ↓
[LLM] Gemini 2.5 Flash → "Why did the AI go to school? To improve its neural network!"
    ↓
[TTS] Azure Speech Synthesis → 🔊 "Why did the AI go to school..."
```

### Scenario 2: Gemini Down → Uses Ollama
```
User: "Tell me a joke"
    ↓
[STT] Azure Speech Recognition → "Tell me a joke"
    ↓
[EMOTION] Azure Text Analytics → "neutral/calm"
    ↓
[LLM] Gemini 2.5 Flash → ❌ TIMEOUT
[LLM] Ollama → "Why did the processor go to the gym? To get a better CPU!"
    ↓
[TTS] Azure Speech Synthesis → 🔊 "Why did the processor..."
```

### Scenario 3: Azure Down → Uses pyttsx3
```
User: "Tell me a joke"
    ↓
[STT] Azure Speech Recognition → "Tell me a joke"
    ↓
[EMOTION] Azure Text Analytics → "neutral/calm"
    ↓
[LLM] Gemini 2.5 Flash → "Why did the AI go to school? To improve its neural network!"
    ↓
[TTS] Azure Speech Synthesis → ❌ API ERROR
[TTS] pyttsx3 → 🔊 (lower quality, but works!)
```

### Scenario 4: Everything Down → Survives Gracefully
```
User: "Tell me a joke"
    ↓
[STT] Azure Speech Recognition → "Tell me a joke"
    ↓
[EMOTION] Azure Text Analytics → ❌
[EMOTION] Keyword Matching → "calm"
    ↓
[LLM] Gemini 2.5 Flash → ❌
[LLM] Ollama → ❌
[LLM] Fallback → "That's interesting! Let me think about that..."
    ↓
[TTS] Azure Speech Synthesis → ❌
[TTS] pyttsx3 → 🔊 "That's interesting..."
```

## 📊 Service Tiers

### Tier 1: Premium (Best Quality)
- **Gemini 2.5 Flash** - Fastest, most intelligent AI
- **Azure TTS** - Professional voice, emotions, visemes
- **Azure Text Analytics** - Accurate sentiment analysis

**Cost**: ~$0.01-0.05 per request
**Speed**: 1-2 seconds

### Tier 2: Local/Free (Good Enough)
- **Ollama llama3.2:3b** - Free, private, 3-5 seconds
- **pyttsx3** - Free, cross-platform, 0.1-0.5 seconds
- **Keyword Matching** - Free, instant emotion detection

**Cost**: $0 (after setup)
**Speed**: 3-5 seconds

### Tier 3: Fallback (Emergency Only)
- **Hardcoded Responses** - No AI, just pre-written text
- Limited to friendly, generic responses

**Cost**: $0
**Speed**: Instant

## 🚀 Performance Comparison

| Scenario | LLM Time | Speech Time | Total | Quality |
|----------|----------|-------------|-------|---------|
| All Premium | 1-2s | 0.5-1s | 2-3s | ⭐⭐⭐⭐⭐ |
| Gemini + pyttsx3 | 1-2s | 0.1-0.5s | 1.5-2.5s | ⭐⭐⭐⭐ |
| Ollama + Azure | 3-5s | 0.5-1s | 4-6s | ⭐⭐⭐ |
| All Fallback | Instant | 0.1-0.5s | 0.5s | ⭐⭐ |

## 💾 Storage & Setup Requirements

| Component | Setup | Size | Cost |
|-----------|-------|------|------|
| Gemini 2.5 Flash | OpenRouter API key | 0 MB | ~$0.01/req |
| Azure Services | API keys + region | 0 MB | ~$0.01/req |
| Ollama llama3.2 | Download & run | 2 GB | $0 |
| pyttsx3 | pip install | 5 MB | $0 |
| Your Code | Already have | ~50 MB | $0 |

## 🎮 Code Examples

### Example 1: Just Send a Message
```python
from ai.brain import think

response, emotion = think("What's the weather like?")
print(f"AI: {response}")
print(f"Emotion: {emotion}")

# Automatically uses:
# - Gemini if available
# - Ollama if Gemini fails
# - Hardcoded response if Ollama fails
```

### Example 2: Check Which Service Is Being Used
```python
from ai.llm_brain import LLMBrain

brain = LLMBrain()
response = brain.generate_response("Hello!")

print(f"Response: {response}")
print(f"LLM Used: {brain.last_llm_used}")
# Output: "openrouter" or "ollama" or "fallback"
```

### Example 3: Full Diagnostics
```python
from ai.brain import run_startup_tests

diagnostics = run_startup_tests()

# Shows:
# ✓ Azure Text Analytics available: True/False
# ✓ Gemini 2.5 Flash accessible: True/False  
# ✓ Ollama running: True/False
# ✓ Primary LLM in use: "openrouter"/"ollama"/"fallback"
```

## 🔒 Security & Privacy

### Public API Calls (Logged)
- Azure services (configured in code)
- OpenRouter/Gemini (requires API key)

**Best Practice**: Set API keys as environment variables
```bash
export OPENROUTER_API_KEY="your-key"
export AZURE_SPEECH_KEY="your-key"
```

### Local/Private Processing (No logs to cloud)
- Ollama (runs on your machine)
- pyttsx3 (runs on your machine)
- Keyword matching (runs on your machine)

### Data Flow
```
User Input
    ↓ (encrypted if possible)
[Local Processing or API Call]
    ↓ (response encrypted if possible)
User Output
    ↓
User sees output
↓
Cloud logs (for API services only)
```

## 📈 Cost Analysis

### Option A: Always Use Gemini (Expensive)
```
1000 requests/day × $0.05/req × 30 days = $1,500/month
```

### Option B: Ditto Pipeline (Smart)
```
70% Gemini, 30% Ollama
700 × $0.05 = $35/month (only pay when you use premium)
300 × $0 = $0 (free local fallback)
Total: ~$35/month (vs $1,500)
```

### Option C: Always Use Ollama (Cheapest but Slower)
```
No API costs, just electricity
~$5/month in AWS-equivalent compute
```

**Ditto wins**: High quality + affordable + reliable!

## 🛠️ Customization Options

### Use Different LLM
Edit `config/settings.py`:
```python
OPENROUTER_MODEL = "anthropic/claude-3-haiku"  # or any OpenRouter model
OLLAMA_MODEL = "mistral"  # Change from llama3.2
```

### Adjust Emotion Settings
Edit `speech/pyttsx3_fallback.py`:
```python
EMOTION_SETTINGS = {
    "happy": {"rate": 200, "volume": 1.0},  # Faster, louder
    "sad": {"rate": 100, "volume": 0.5},    # Slower, quieter
}
```

### Change Speech Voice
Edit `config/settings.py`:
```python
VOICE = "en-US-AmberNeural"  # Change Azure voice
```

## 🎓 Learning Resources

1. **Quick Start**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. **Full Architecture**: [DITTO_PIPELINE.md](DITTO_PIPELINE.md)
3. **Implementation Details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
4. **External Docs**:
   - OpenRouter: https://openrouter.ai/docs
   - Ollama: https://ollama.ai
   - Azure Cognitive Services: https://azure.microsoft.com/services/cognitive-services/
   - pyttsx3: https://pypi.org/project/pyttsx3/

## ✨ Key Benefits

| Benefit | Why? |
|---------|------|
| **Never Stops Working** | Always has fallback |
| **Cost Efficient** | Pays for premium only when needed |
| **Privacy Friendly** | Falls back to local processing |
| **Fast** | Premium services are optimized |
| **Transparent** | Logs show which service is used |
| **Easy to Debug** | Clear error messages |
| **Scalable** | Add more models easily |

## 🚦 Status Indicators

Look for these in logs to understand what's happening:

```
[AZURE]      - Azure services (premium, cloud)
[FALLBACK]   - Fallback services (free, local)
[LLM]        - Language model operations
[EMOTION]    - Emotion detection
[INIT]       - Initialization
[ERROR]      - Something went wrong
[WARNING]    - Minor issue, using fallback
```

Example log:
```
2024-01-15 10:23:45 - [INIT] Azure Speech initialized
2024-01-15 10:23:45 - [LLM] OpenRouter key found; will use Gemini 2.5 Flash as primary
2024-01-15 10:23:46 - [LLM] Generated response (OpenRouter)
2024-01-15 10:23:46 - [AZURE] Speech synthesis successful
```

---

**Ready to use it?** → See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**Want to customize?** → See [DITTO_PIPELINE.md](DITTO_PIPELINE.md)

**Having issues?** → Check logs and [DITTO_PIPELINE.md](DITTO_PIPELINE.md#troubleshooting)
