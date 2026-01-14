import json
import time
import multiprocessing
import os

from core.listener import listen
from core.speaker import speak
from core.intent_parser import classify_intent
from automation.actions import execute_action
from gestures.hand_gesture_worker import gesture_worker

from core.conversation import generate_reply
from core.prompt_composer import PromptComposer
from core.memory_relevance import PassiveMemoryRelevanceMatcher

from core.memory import ActiveMemory, PassiveMemory, MemoryEvaluator
from core.active_memory_writer import append_turn

from config import logger, trace_logger, passive_logger


# ======================================================
# MEMORY WORKER CONFIG
# ======================================================

ACTIVE_MEMORY_FILE = "memory_bus/active_memory.json"
CHECK_INTERVAL = 3
MAX_PASSIVE_MEMORIES = 50


# ======================================================
# MEMORY WORKER PROCESS
# ======================================================

def memory_worker_loop():
    trace_logger.info("Memory Worker process started")

    passive_memory = PassiveMemory()
    memory_evaluator = MemoryEvaluator(passive_memory)

    last_processed_ts = 0

    def load_active_memory():
        if not os.path.exists(ACTIVE_MEMORY_FILE):
            return {"turns": []}

        with open(ACTIVE_MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_new_turns(data):
        nonlocal last_processed_ts
        new = []

        for turn in data.get("turns", []):
            if turn["timestamp"] > last_processed_ts:
                new.append(turn)

        if new:
            last_processed_ts = new[-1]["timestamp"]

        return new

    def re_evaluate_low_priority():
        lows = passive_memory.get_by_confidence("low")

        for mem in lows:
            score = passive_memory.compute_priority(mem)

            if score >= 0.7:
                passive_memory.promote(mem, "high")
            elif score >= 0.4:
                passive_memory.promote(mem, "medium")

    def enforce_capacity():
        count = passive_memory.count()
        if count <= MAX_PASSIVE_MEMORIES:
            return

        trace_logger.info("Passive memory capacity exceeded")
        passive_logger.info(f"Capacity exceeded | count={count} | max={MAX_PASSIVE_MEMORIES}")

        # 🔴 YOUR RULE (LOCKED)
        re_evaluate_low_priority()
        passive_memory.discard_lowest_low()

    while True:
        try:
            data = load_active_memory()
            new_turns = get_new_turns(data)

            for turn in new_turns:
                memory_evaluator.evaluate(
                    user_text=turn["user"],
                    nova_reply=turn["nova"]
                )
                passive_logger.info("Evaluated and stored passive memories for new turn")

            enforce_capacity()

        except Exception as e:
            trace_logger.error(f"Memory Worker error: {e}")

        time.sleep(CHECK_INTERVAL)

# ======================================================
# MODEL WARM-UP WORKER (NEW)
# ======================================================

def model_warmup_loop():
    from ollama.client import ollama_generate, ollama_embed

    trace_logger.info("Model warm-up worker started")

    while True:
        try:
            # 🔥 Conversation model
            ollama_generate(
                model="llama3.2:3b",
                prompt="Hello",
            )

            # 🔥 Memory evaluator model
            ollama_generate(
                model="llama3:instruct",
                prompt="Extract facts.",
            )

            # 🔥 Intent model
            ollama_generate(
                model="qwen3:4b",
                prompt="Classify intent.",
            )

            # 🔥 Embedding model
            ollama_embed("warmup")

            trace_logger.info("Model warm-up cycle completed")

        except Exception as e:
            trace_logger.error(f"Model warm-up error: {e}")

        # 🔁 Every 30 seconds
        time.sleep(30)


# ======================================================
# MAIN NOVA PROCESS
# ======================================================

def main():
    trace_logger.info("NOVA starting up")

    # 🔥 START MEMORY WORKER AS BACKGROUND PROCESS
    memory_process = multiprocessing.Process(
        target=memory_worker_loop,
        daemon=True
    )
    memory_process.start()

    trace_logger.info(
        f"Memory Worker started | PID={memory_process.pid}"
    )
        # 🔥 START MODEL WARM-UP PROCESS
    warmup_process = multiprocessing.Process(
        target=model_warmup_loop,
        daemon=True
    )
    warmup_process.start()

    trace_logger.info(
        f"Model warm-up worker started | PID={warmup_process.pid}"
    )

    # 🔥 PERFORM INITIAL WARM-UP BEFORE STARTING
    trace_logger.info("Performing initial model warm-up...")
    from ollama.client import ollama_generate, ollama_embed
    
    try:
        ollama_generate(model="llama3.2:3b", prompt="Hello")
        ollama_generate(model="llama3:instruct", prompt="Extract facts.")
        ollama_generate(model="qwen3:4b", prompt="Classify intent.")
        ollama_embed("warmup")
        trace_logger.info("Initial warm-up completed")
    except Exception as e:
        trace_logger.error(f"Initial warm-up error: {e}")

    # ---------- INIT CORE COMPONENTS ----------
    active_memory = ActiveMemory(max_turns=5)

    relevance_matcher = PassiveMemoryRelevanceMatcher(
        max_results=3,
        threshold=0.75
    )

    prompt_composer = PromptComposer()

    speak("NOVA online.")

    # ---------- GESTURE CONTROL PROCESS ----------
    gesture_process = None

    # ---------- MAIN LOOP ----------
    while True:
        text = listen()
        if not text:
            continue

        trace_logger.info("User input received")

        # ----- DIRECT GESTURE CONTROL (BYPASS INTENT) -----
        if "gesture control" in text.lower():
            trace_logger.info("Direct gesture control request detected; bypassing intent analysis")
            if gesture_process is None or not gesture_process.is_alive():
                gesture_process = multiprocessing.Process(
                    target=gesture_worker,
                    daemon=True
                )
                gesture_process.start()
                trace_logger.info(f"Gesture control started | PID={gesture_process.pid}")
                reply = "Gesture control activated. Make a fist with both hands to stop."
            else:
                reply = "Gesture control is already running."

            speak(reply)
            continue

        intent_data = classify_intent(text)
        intent = intent_data.get("intent", "unknown")

        logger.info(f"User: {text} | Intent: {intent}")
        trace_logger.info(f"Final intent received: {intent}")

        reply = None

        if intent == "conversation":
            active_context = active_memory.get_context()
            relevant_passive = relevance_matcher.find_relevant(text)

            prompt = prompt_composer.compose(
                user_text=text,
                active_context=active_context,
                passive_memories=relevant_passive
            )

            reply = generate_reply(prompt)

            active_memory.add(text, reply)

            # 🔥 WRITE TO ACTIVE MEMORY BUS (JSON)
            append_turn(text, reply)
        elif intent in ("open_app", "search_web", "system_control"):
            trace_logger.info(
                f"Action detected: {intent_data.get('action', intent)}"
            )
            reply = execute_action(intent_data)
        elif intent == "gesture_control":
            trace_logger.info("Gesture control requested")
            
            # Start gesture control in a separate process
            if gesture_process is None or not gesture_process.is_alive():
                gesture_process = multiprocessing.Process(
                    target=gesture_worker,
                    daemon=True
                )
                gesture_process.start()
                trace_logger.info(f"Gesture control started | PID={gesture_process.pid}")
                reply = "Gesture control activated. Make a fist with both hands to stop."
            else:
                reply = "Gesture control is already running."
        else:
            reply = "I'm not sure what to do with that yet."

        trace_logger.info("Speech synthesis started")
        speak(reply)
        trace_logger.info("Speech synthesis completed")


# ======================================================
# ENTRY POINT (WINDOWS SAFE)
# ======================================================

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
