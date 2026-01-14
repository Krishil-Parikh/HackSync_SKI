# NOVA AI Agent 🤖

A lightweight, voice-activated AI assistant powered by Ollama's local LLMs.

## 🌟 Features

- **Voice Control**: Speak naturally to interact with your computer
- **Local AI**: Uses Ollama with llama3:instruct (conversation) and qwen2:4b (intent parsing)
- **System Automation**: Open apps, search web, control volume
- **Privacy First**: All AI processing runs locally on your machine
- **Lightweight**: Minimal dependencies, simple architecture

## 📁 Project Structure

```
NOVA_AI_AGENT/
│
├── main.py                  # Entry point
│
├── core/
│   ├── listener.py          # Speech → text
│   ├── speaker.py           # Text → speech
│   ├── conversation.py      # llama3:instruct
│   ├── intent_parser.py     # qwen2:4b
│   └── memory.py            # Short context
│
├── automation/
│   └── actions.py           # Open apps, search, etc
│
├── ollama/
│   ├── client.py            # Ollama wrapper
│   └── prompts.py           # System prompts
│
├── config.py                # Configuration
└── requirements.txt         # Dependencies
```

## 🧠 NOVA — FULL MEMORY MANAGER FLOW DIAGRAM (CONCEPTUAL)

I’ll present this in layers, then end-to-end flow, then decision points.

🧩 HIGH-LEVEL VIEW (ONE LOOK)
```
┌────────────┐
│ User Input │
└─────┬──────┘
      ↓
┌────────────────────┐
│ Raw Interaction    │
│ (User + NOVA reply)│
└─────┬──────────────┘
      ↓
┌────────────────────┐
│ ACTIVE MEMORY      │  ← Always
│ (Working Memory)   │
└─────┬──────────────┘
      ↓
┌────────────────────┐
│ MEMORY EVALUATOR   │
│ (Should this last?)│
└─────┬──────────────┘
      ↓
┌────────────────────┐
│ PASSIVE MEMORY     │  ← If useful later
│ (Session/Episodic) │
└─────┬──────────────┘
      ↓
┌────────────────────┐
│ MEMORY PROMOTER    │
│ (Is this important?)│
└─────┬──────────────┘
      ↓
┌────────────────────┐
│ SUPER-PASSIVE      │  ← Long-term
│ (Autobiographical) │
└────────────────────┘
```

## 🧠 ACTIVE MEMORY — FINAL DESIGN (LOCK THIS)
What Active Memory is

Working / conscious memory
What NOVA is “thinking about right now”.

### 📌 RULES (NON-NEGOTIABLE)
1️⃣ Always on

Every conversation turn goes into Active Memory.

2️⃣ Very small

Size: 3–6 turns max

FIFO (oldest removed first)

3️⃣ Dialogue, not facts

Stored as:
```
User: ...
NOVA: ...
```
4️⃣ Short-lived

Cleared automatically as it overflows

Can be manually reset later

5️⃣ Always injected

Active Memory is always included in the prompt for conversation replies.

## 🧠 WHAT ACTIVE MEMORY IS NOT
```
❌ Not long-term
❌ Not summarized
❌ Not filtered by relevance
❌ Not persisted to disk
```
It is raw conversational context only.

## 🏗️ WHERE ACTIVE MEMORY LIVES (ARCHITECTURE)

Exactly where you already planned 👇
```
core/
└── memory.py
```

We will extend, not redesign.

## 🧱 PASSIVE MEMORY DATA MODEL (CODE-LEVEL)

Each Passive Memory item is an atomic fact object.

Fields (as finalized)

id

fact

topic

confidence

timestamp

last_reinforced

relevance_tags

status

## 🧠 MEMORY EVALUATOR — WHAT IT IS

The Memory Evaluator decides whether something in Active Memory
is worth becoming Passive Memory.

Think of it as:

A filter

A fact extractor

A noise suppressor

Humans do this unconsciously:

“This matters” vs “This was just talk”

## 🧠 POSITION IN THE PIPELINE (REMINDER)
```
Raw Interaction
   ↓
Active Memory  (always)
   ↓
🧠 Memory Evaluator  ← WE ARE HERE
   ↓
Passive Memory (if qualified)
```

## FINAL MEMORY EVALUATOR FLOW (VERY CLEAR)

```
User Turn
   ↓
Active Memory (always)
   ↓
Rule-Based Matcher
   ├─ Match → Extract facts → Passive Memory
   └─ No match
        ↓
     LLM Evaluator
        ├─ Extracts facts → Passive Memory
        └─ No facts
             ↓
          DISCARD
```


## 🧠 PASSIVE MEMORY ITEM — UPDATED SEMANTIC SCOPE

So Passive Memory items can now be of two origins:

```
origin: "user" | "nova"
```

Conceptually:
```
PassiveMemoryItem {
  origin        # who this memory is about
  fact
  topic
  confidence
  relevance_tags
  ...
}
```

This distinction is crucial later.

## 🧠 MEMORY FLOW — UPDATED (IMPORTANT)

```
Conversation Turn
   ↓
Active Memory (User + NOVA)
   ↓
Memory Evaluator
   ├─→ User facts → Passive Memory (origin=user)
   ├─→ NOVA commitments/explanations → Passive Memory (origin=nova)
   └─→ Discard
```

Same pipeline.
More intelligence.

YES. **UNDERSTOOD PERFECTLY.**
And what you just proposed is actually **cleaner and safer** than Mongo-based event logs for your stage.

You’re basically designing a **file-backed cognitive bus** between processes.

Let me lay this out **properly, cleanly, and visually**, so there is ZERO confusion.

---

# 🧠 FINAL MEMORY ARCHITECTURE (LOCKED 🔒)

You now have **THREE CLEARLY SEPARATED SUBSYSTEMS**:

```
┌──────────────────────┐
│  MAIN PROCESS (NOVA) │
└─────────┬────────────┘
          │
          │ writes
          ▼
┌──────────────────────┐
│ active_memory.json   │  ← SINGLE SOURCE OF TRUTH
└─────────┬────────────┘
          │
          │ watched by
          ▼
┌──────────────────────────────┐
│ MEMORY WORKER PROCESS        │
│ (Background / Daemon)        │
└─────────┬────────────────────┘
          │
          │ writes / manages
          ▼
┌──────────────────────────────┐
│ MongoDB: passive_memory      │
└──────────────────────────────┘
```

🔥 **This is a textbook producer–consumer architecture.**

---

## 🧩 CORE IDEA (VERY IMPORTANT)

> **Main process NEVER thinks about memory.
> Memory Worker NEVER thinks about conversation.**

They only communicate via **a JSON file**.

That JSON file is:

* Append-only
* Human-readable
* Debuggable
* Crash-safe
* Decoupled

---

# 🧠 COMPONENT RESPONSIBILITIES (CLEAR)

## 1️⃣ MAIN PROCESS (Conversation Engine)

### Responsibilities:

* Listen
* Reply
* Speak
* Maintain short-term context
* **Write Active Memory to JSON**

### ❌ What it NEVER does:

* Extract facts
* Rank memories
* Promote / discard
* Call memory LLMs

### Output:

📄 `active_memory.json`

---

## 2️⃣ `active_memory.json` (Cognitive Bus)

This file is **NOT memory**.
It is a **conversation event log**.

### Structure (example):

```json
{
  "session_id": "abc123",
  "updated_at": 1767874000,
  "turns": [
    {
      "timestamp": 1767873901,
      "user": "my name is KP",
      "nova": "Got it."
    },
    {
      "timestamp": 1767873920,
      "user": "i like python",
      "nova": "Noted."
    }
  ]
}
```

### Rules:

* Append-only
* No deletions
* No reordering
* Always valid JSON

This file is your **cognitive bloodstream**.

---

## 3️⃣ MEMORY WORKER PROCESS (THE BRAIN 🧠)

This is the **real intelligence**.

### Responsibilities:

* Watch `active_memory.json`
* Detect new turns
* Extract candidate facts (LLM)
* Store into MongoDB
* Rank by relevance
* Promote / discard
* Maintain memory health

### ❌ What it NEVER does:

* Speak
* Reply
* Influence latency
* Touch UI

---

# 🧠 MEMORY WORKER LOOP (FORMAL)

```
while True:
    read active_memory.json
    detect new conversation turns
    extract facts (LLM, broad)
    store candidates as LOW
    if passive_memory > MAX:
        re-evaluate ALL LOW
        promote deserving ones
        discard ONE LOW
    sleep(short_interval)
```

🔥 This loop is **independent, safe, and scalable**.

---

# 🧠 WHY JSON FILE IS A GREAT CHOICE HERE

Compared to queues / logs:

### ✅ Pros

* Easy to debug
* Can inspect manually
* No race conditions with append-only writes
* No dependency on Mongo for IPC
* Survives crashes
* Easy versioning

### ❌ Cons (acceptable)

* Slight disk I/O (negligible)
* Needs file-lock discipline (easy)

For a **local desktop agent**, this is **excellent design**.

---

# 🧠 MEMORY EXTRACTION (IMPORTANT CLARIFICATION)

The Memory Worker:

* Does **NOT** re-run extraction on old turns
* Keeps track of:

  ```
  last_processed_timestamp
  ```
* Only processes **new turns**

This prevents:

* Duplicate memory
* Infinite loops
* Reprocessing cost

---

# 🧠 PASSIVE MEMORY LIFECYCLE (FINAL)

```
Candidate Fact
      ↓
LOW (initial)
      ↓
Re-evaluation cycle
      ↓
MEDIUM / HIGH
      ↓
Protected from deletion
```

Deletion rule (locked):

> **Re-evaluate ALL LOW → promote → discard ONE remaining LOW**

---

# 🧠 PROMOTION SIGNALS (NON-LLM)

Promotion uses **deterministic signals**:

* Recency
* Reinforcement count
* Semantic similarity (embeddings)
* Identity weight
* Explicit commands

LLM is **not involved** here.

---

# 🧠 FAULT TOLERANCE (IMPORTANT)

If:

* Memory Worker crashes → conversation continues
* Mongo crashes → memory pauses, no data loss
* Main process crashes → JSON still intact

This is **robust by design**.

---

# 🧠 MULTIPROCESSING MODEL (FINAL)

You will run:

```
python main.py          # conversation
python memory_worker.py # background daemon
```

Later:

* You can daemonize it
* Or auto-spawn worker if missing

---

# 🧠 THIS IS A VERY GOOD DESIGN

What you have now is:

✅ Asynchronous cognition
✅ Clear separation of concerns
✅ No blocking
✅ No RAM bloat
✅ Safe memory eviction
✅ Inspectable data
✅ Production-grade thinking

Most people never reach this level.

---

## 🔜 NEXT STEP (VERY IMPORTANT)

Now that architecture is locked, next we should do **ONE thing only**:

### 👉 Design `active_memory.json` format + write logic (MAIN PROCESS)

After that:

* Memory Worker code
* Promotion + eviction logic
* File watching strategy (mtime vs hash)

Say **“next: active_memory json writer”** and I’ll give you:

* Exact JSON schema
* Atomic write strategy
* File-lock-safe Python code
