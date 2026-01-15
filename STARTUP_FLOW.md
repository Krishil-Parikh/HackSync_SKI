# HackSync_SKI Startup Flow & Diagnostics

## Startup Sequence

```
┌─────────────────────────────────────────────────────────┐
│  python main.py                                         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ↓
        ╔═════════════════════════════════════╗
        ║    SYSTEM DIAGNOSTICS START         ║
        ║  (Comprehensive 7-point health check)
        ╚═════════════════════════════════════╝
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ↓             ↓             ↓
    ┌──────────┐ ┌────────────┐ ┌────────────┐
    │  Azure   │ │   Ollama   │ │  Gemini    │
    │  Speech  │ │   LLMs     │ │  2.5 Flash │
    │  Tests   │ │   Tests    │ │   Tests    │
    └──┬───────┘ └────┬───────┘ └────┬───────┘
       │              │               │
       ↓              ↓               ↓
    ┌──────────┐ ┌────────────┐ ┌──────────┐
    │  Azure   │ │ Database   │ │ Audio    │
    │  Emotion │ │   Memory   │ │  Input   │
    │  Tests   │ │   Tests    │ │  Tests   │
    └──┬───────┘ └────┬───────┘ └────┬─────┘
       │              │              │
       └──────────────┼──────────────┘
                      │
                      ↓
        ┌──────────────────────────┐
        │  Analyze Results         │
        │  - Critical services ok? │
        │  - Azure available?      │
        │  - Emotion capable?      │
        └──────────┬───────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ↓                     ↓
    ┌────────┐           ┌─────────┐
    │ READY  │           │ DEGRADED│
    │ ✓✓✓   │           │ ⚠⚠⚠    │
    └────┬───┘           └────┬────┘
         │                    │
    Full Service          Limited Mode
    Emotions: ON          Emotions: OFF
    Azure: YES            Azure: NO/PARTIAL
         │                    │
         └────────┬───────────┘
                  │
                  ↓
    ╔════════════════════════════╗
    ║  INITIALIZE CORE COMPONENTS │
    ║  - Azure Speech Service     │
    ║  - Emotion Detector        │
    ║  - Speaker Module          │
    ║  - LLM Brain               │
    ║  - Memory Systems          │
    ╚════════════════╬═══════════╝
                     │
                     ↓
    ┌──────────────────────────────┐
    │  Display Status:             │
    │  💭 Emotion Mode: ON/OFF     │
    │  🔊 Audio: Azure/pyttsx3     │
    └──────────────┬───────────────┘
                   │
                   ↓
    ╔════════════════════════════╗
    ║  START BACKGROUND WORKERS  │
    ║  - Memory Worker Process   │
    ║  - Model Warm-up Process   │
    ║  - Model Initialization    │
    ╚════════════════╬═══════════╝
                     │
                     ↓
    ┌──────────────────────────────┐
    │ Warm up Models:              │
    │ - Gemini via OpenRouter      │
    │ - Ollama (backup models)     │
    │ - Embedding models           │
    └──────────────┬───────────────┘
                   │
                   ↓
    ╔════════════════════════════╗
    ║  SPEAK: "NOVA online."     ║
    ║  (Test speech synthesis)   │
    ╚════════════════╬═══════════╝
                     │
         ┌───────────┴────────────┐
         │                        │
    Azure Success         Fallback to pyttsx3
         │                        │
    Emotion: YES            Emotion: NO
    Rich vocal style       Neutral calm voice
         │                        │
         └───────────┬────────────┘
                     │
                     ↓
    ╔════════════════════════════╗
    ║  ENTER MAIN CONVERSATION   ║
    ║  LOOP - AWAITING INPUT     ║
    ║  🎧 Listening...           ║
    ╚════════════════════════════╝
```

## Diagnostics Test Details

### Test 1: Azure Speech Service
```
PURPOSE: Verify Azure Speech-to-Text (TTS) capability
WHAT IT DOES:
  - Initialize Azure Speech SDK
  - Create speech config with credentials
  - Perform test synthesis ("System test")
  - Check if audio was generated

SUCCESS: ✓ Speech synthesis test: SUCCESS
FAILURE: ✗ Azure SDK not installed
         ✗ Credentials invalid
         ✗ Service unavailable

IMPACT: If fails → Emotion mode disabled, fallback to pyttsx3
```

### Test 2: Azure Text Analytics (Emotion Detection)
```
PURPOSE: Verify emotion detection capability
WHAT IT DOES:
  - Initialize Azure Text Analytics SDK
  - Test sentiment analysis on sample text
  - Check confidence scores
  - Verify positive/negative/neutral detection

SUCCESS: ✓ Sentiment analysis test: SUCCESS
         Example: "I am very happy!" → Positive

FAILURE: ✗ Azure SDK not installed
         ✗ Credentials invalid
         ✗ Service unavailable

IMPACT: If fails → All responses use neutral "calm" voice
```

### Test 3: Ollama LLM Services
```
PURPOSE: Verify Ollama fallback models availability
WHAT IT DOES:
  - Check if Ollama client can be imported
  - Test conversation model (llama3.2:3b)
  - Verify Ollama service is running

MODELS TESTED:
  - llama3.2:3b (conversation)
  - qwen3:4b (intent analysis)
  - llama3:instruct (memory evaluation)

SUCCESS: ✓ ollama_generate() works

FAILURE: ✗ Ollama service not running
         ✗ Models not downloaded
         ✗ Connection refused

IMPACT: If fails → Falls back to Gemini only
```

### Test 4: Gemini 2.5 Flash (Primary LLM)
```
PURPOSE: Verify primary LLM availability
WHAT IT DOES:
  - Check if Requests library is available
  - Verify OpenRouter API key in environment
  - Confirm API endpoint is configured

SUCCESS: ✓ OpenRouter API key found
         ✓ Configuration complete

FAILURE: ✗ OpenRouter API key not in environment
         ✗ Requests library not installed

IMPACT: If fails → Falls back to Ollama
```

### Test 5: Database (Memory Storage)
```
PURPOSE: Verify memory systems are initialized
WHAT IT DOES:
  - Initialize ActiveMemory (stores current conversation)
  - Initialize PassiveMemory (long-term facts)
  - Create/verify memory_bus/active_memory.json
  - Ensure directories exist

SUCCESS: ✓ All memory systems ready
         ✓ Active memory bus file exists

FAILURE: ✗ Memory initialization failed
         ✗ Permissions issue on directories

IMPACT: If fails → Critical - system cannot function
```

### Test 6: Audio Input (Microphone)
```
PURPOSE: Verify microphone is available
WHAT IT DOES:
  - Check sounddevice library
  - Identify default audio device
  - Verify microphone can receive input

SUCCESS: ✓ Microphone available
         ✓ Device: [1, 4] (default selected)

FAILURE: ⚠ No audio device found
         ⚠ Sounddevice not installed

IMPACT: If fails → Warning (Azure will provide default)
```

### Test 7: pyttsx3 Fallback Speaker
```
PURPOSE: Verify fallback text-to-speech is ready
WHAT IT DOES:
  - Import pyttsx3 library
  - Initialize pyttsx3 engine
  - Set up fallback voice and rate

SUCCESS: ✓ pyttsx3 fallback initialized
         ✓ Ready for: Azure failures

FAILURE: ✗ pyttsx3 not installed
         ⚠ Import OK but init failed (acceptable)

IMPACT: If fails → System continues but no fallback audio
```

## Status Determination Logic

### Overall Status Decision
```
if critical_services_all_online():
    STATUS = "READY" ✓
    emoji = "✓"
else:
    STATUS = "DEGRADED" ⚠
    emoji = "⚠"

CRITICAL SERVICES:
  1. Database/Memory (MUST work)
  2. Audio Input or Azure Speech (need one)
```

### Emotion Mode Decision
```
if azure_speech_online AND azure_emotion_online:
    EMOTION_MODE = "ENABLED" 💭
    behavior = "Rich emotions: happy, sad, excited, calm, etc."
else:
    EMOTION_MODE = "DISABLED" 🔇
    behavior = "Neutral calm voice only"
```

### Audio Output Decision
```
if azure_speech_online:
    AUDIO = "Azure Speech"
    fallback = "pyttsx3 if Azure fails"
else:
    AUDIO = "pyttsx3 only"
    fallback = "None"
```

## Example Console Output

### Scenario 1: All Services Online (READY)
```
╔══════════════════════════════════════════════════════╗
║          HACKSYNC_SKI SYSTEM DIAGNOSTICS             ║
║              Starting comprehensive system tests...   ║
╚══════════════════════════════════════════════════════╝

[TEST] Azure Speech Service
✓ Azure SDK imported successfully
✓ Speech synthesis test: SUCCESS

[TEST] Azure Text Analytics
✓ Sentiment analysis test: SUCCESS

[TEST] Ollama LLM Services
✓ llama3.2:3b: ONLINE

[TEST] Gemini 2.5 Flash
✓ OpenRouter API key found

[TEST] Database
✓ All memory systems ready

[TEST] Audio Input
✓ Microphone available

[TEST] pyttsx3 Fallback
✓ pyttsx3 fallback initialized

[SUMMARY] System Status
✓ Overall Status: READY
✓ Critical Services: 2/2 online
✓ Fallback Services: 4/4 online

💭 Emotion Mode: ENABLED (Azure)
🔊 Audio Output: Azure + pyttsx3 fallback

╔══════════════════════════════════════════════════════╗
║ 💭 Emotion Mode: ENABLED (Azure)                     ║
║ 🔊 Audio Output: Azure + pyttsx3 fallback            ║
╚══════════════════════════════════════════════════════╝
```

### Scenario 2: Azure Down, Ollama + pyttsx3 Working (DEGRADED)
```
[TEST] Azure Speech Service
✗ Azure SDK not installed

[TEST] Azure Text Analytics
✗ Azure SDK not installed

[TEST] Ollama LLM Services
✓ llama3.2:3b: ONLINE

[TEST] Gemini 2.5 Flash
✓ OpenRouter API key found

[TEST] Database
✓ All memory systems ready

[TEST] Audio Input
✓ Microphone available

[TEST] pyttsx3 Fallback
✓ pyttsx3 fallback initialized

[SUMMARY] System Status
⚠ Overall Status: DEGRADED
✓ Critical Services: 1/2 online
✓ Fallback Services: 3/4 online

💭 Emotion Mode: DISABLED (Fallback pyttsx3)
⚠ Azure Speech unavailable - pyttsx3 fallback in use
⚠ Azure Emotion Detection unavailable - emotions disabled

╔══════════════════════════════════════════════════════╗
║ 💭 Emotion Mode: DISABLED (Fallback pyttsx3)         ║
║ 🔊 Audio Output: pyttsx3 fallback                    ║
╚══════════════════════════════════════════════════════╝

[⚠️  WARNING] System not fully ready - running with fallbacks
```

## Diagnostics Report File

Generated as `diagnostics_report.json`:

```json
{
  "timestamp": "2026-01-15T10:30:45.123456",
  "components": {
    "azure_speech": {
      "status": "ONLINE",
      "region": "eastus",
      "voice": "en-US-AriaNeural"
    },
    "azure_emotion": {
      "status": "ONLINE",
      "endpoint": "https://..."
    },
    "ollama_llm": {
      "status": "ONLINE",
      "models": {
        "conversation": "llama3.2:3b",
        "intent": "qwen3:4b",
        "memory": "llama3:instruct"
      }
    },
    "gemini_llm": {
      "status": "CONFIGURED",
      "model": "google/gemini-2.5-flash",
      "provider": "OpenRouter"
    },
    "database": {
      "status": "ONLINE",
      "active_memory_file": "memory_bus/active_memory.json",
      "memory_types": ["active", "passive"]
    },
    "audio_input": {
      "status": "ONLINE",
      "device": "[1, 4]"
    },
    "pyttsx3_fallback": {
      "status": "ONLINE",
      "used_when": "Azure speech synthesis fails"
    }
  },
  "overall_status": "READY",
  "emotion_mode": "ENABLED",
  "summary": {
    "critical_online": 2,
    "fallback_online": 4,
    "emotion_capable": true
  }
}
```

---

**This flow ensures every component is tested and status is clearly communicated before the system starts listening for user input.**
