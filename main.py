import json
import time
import os
from pathlib import Path
import multiprocessing

from core.listener import listen
from core.speaker import speak, initialize_speaker, set_azure_availability
from core.intent_parser import classify_intent
from automation.actions import execute_action

from core.conversation import generate_reply
from core.prompt_composer import PromptComposer

from core.memory import ActiveMemory, PassiveMemory, MemoryEvaluator
from core.system_diagnostics import SystemDiagnostics
from speech.azure import AzureSpeech

from config import logger, trace_logger, passive_logger


# ======================================================
# MEMORY CONFIG
# ======================================================

MAX_PASSIVE_MEMORIES = 50

# Get absolute storage path for memory JSON files
MEMORY_FOLDER = Path(__file__).parent / "memory"
MEMORY_FOLDER.mkdir(exist_ok=True)
MIRAGE_MEMORY_PATH = str(MEMORY_FOLDER / "mirage_memory.json")
ACTIVE_MEMORY_PATH = str(MEMORY_FOLDER / "active_memory.json")
PASSIVE_MEMORY_PATH = str(MEMORY_FOLDER / "passive_memory.json")


# ======================================================
# MAIN NOVA PROCESS
# ======================================================

def main():
    trace_logger.info("NOVA starting up")
    
    # ============================================================
    # SYSTEM DIAGNOSTICS & INITIALIZATION
    # ============================================================
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*12 + "HackSync_SKI SYSTEM STARTUP" + " "*20 + "║")
    print("╚" + "="*58 + "╝\n")
    
    # Run comprehensive system diagnostics
    diagnostics = SystemDiagnostics()
    system_ready = diagnostics.run_all_tests()
    
    # Initialize core components with diagnostics results
    azure_speech_available = diagnostics.is_azure_speech_available()
    emotion_enabled = diagnostics.is_emotion_enabled()
    
    # Initialize Azure Speech and Emotion Detector
    try:
        azure_speech = AzureSpeech()
        trace_logger.info("[INIT] Azure Speech initialized")
    except Exception as e:
        logger.error(f"[INIT] Failed to initialize Azure Speech: {e}")
        azure_speech = None
        azure_speech_available = False
    
    # User emotion detection disabled; use default output emotion only
    emotion_detector = None
    emotion_enabled = False

    # Initialize speaker with components and Azure status
    initialize_speaker(azure_speech, emotion_detector, azure_available=azure_speech_available)
    trace_logger.info("[INIT] Speaker initialized")
    
    print(f"\n╔" + "="*58 + "╗")
    print(f"║ 💭 Emotion Mode: {'DISABLED (Output uses default style)'}{'':<12} ║")
    print(f"║ 🔊 Audio Output: {'Azure Speech' if azure_speech_available else 'pyttsx3 fallback':<43} ║")
    print(f"╚" + "="*58 + "╝\n")
    
    if not system_ready:
        logger.warning("[WARN] System diagnostics indicate potential issues - proceeding with fallbacks")
        print("[⚠️  WARNING] System not fully ready - running with fallbacks\n")

    # ---------- INIT CORE COMPONENTS ----------
    active_memory = ActiveMemory(max_turns=5, storage_path=MIRAGE_MEMORY_PATH)
    passive_memory = PassiveMemory(storage_path=MIRAGE_MEMORY_PATH)
    memory_evaluator = MemoryEvaluator(passive_memory)

    prompt_composer = PromptComposer()

    trace_logger.info(f"Memory paths configured | mirage={MIRAGE_MEMORY_PATH}")
    speak("NOVA online.")

    # ---------- MAIN LOOP ----------
    while True:
        text = listen()
        if not text:
            continue

        trace_logger.info("User input received")

        intent_data = classify_intent(text)
        intent = intent_data.get("intent", "unknown")

        logger.info(f"User: {text} | Intent: {intent}")
        trace_logger.info(f"Final intent received: {intent}")

        reply = None

        if intent == "conversation":
            active_context = active_memory.get_context()
            relevant_passive = passive_memory.search(text, limit=3)

            prompt = prompt_composer.compose(
                user_text=text,
                active_context=active_context,
                passive_memories=relevant_passive
            )

            reply_data = generate_reply(prompt)
            if isinstance(reply_data, dict):
                reply_text = reply_data.get("reply", "")
                reply_emotion = reply_data.get("reply_emotion", "calm")
            else:
                reply_text = str(reply_data)
                reply_emotion = "calm"

            # Add to active memory
            active_memory.add(text, reply_text)
            
            # Recall related memories without promoting (for context files)
            recalled_nodes = passive_memory.recall_without_promoting(text, limit=10)
            
            # 🔥 EVALUATE MEMORY SYNCHRONOUSLY AFTER EVERY REPLY
            try:
                memory_evaluator.evaluate(user_text=text, nova_reply=reply_text)
                passive_logger.info("Memory evaluated and stored for turn")
            except Exception as e:
                trace_logger.error(f"Memory evaluation error: {e}")
            
            # 📝 WRITE MEMORY TEXT FILES (active.txt, passive.txt, super_passive.txt)
            try:
                active_memory.write_memory_files(MEMORY_FOLDER, recalled_nodes)
                trace_logger.info("Memory text files updated")
            except Exception as e:
                trace_logger.error(f"Failed to write memory files: {e}")
            
            # Enforce passive memory capacity
            if passive_memory.count() >= MAX_PASSIVE_MEMORIES:
                trace_logger.info("Passive memory at capacity, pruning lowest")
                lows = passive_memory.get_by_confidence("low")
                for mem in lows:
                    score = passive_memory.compute_priority(mem)
                    if score >= 0.7:
                        passive_memory.promote(mem, "high")
                    elif score >= 0.4:
                        passive_memory.promote(mem, "medium")
                passive_memory.discard_lowest_low()
                
        elif intent in ("open_app", "search_web", "system_control"):
            trace_logger.info(
                f"Action detected: {intent_data.get('action', intent)}"
            )
            reply_text = execute_action(intent_data)
            reply_emotion = "calm"
        else:
            print(intent)
            reply_text = "I'm not sure what to do with that yet."
            reply_emotion = "calm"

        trace_logger.info("Speech synthesis started")
        speak(reply_text, reply_emotion)
        trace_logger.info("Speech synthesis completed")


# ======================================================
# ENTRY POINT (WINDOWS SAFE)
# ======================================================

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
