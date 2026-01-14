import speech_recognition as sr
import time
from http.client import RemoteDisconnected
from urllib.error import URLError
from config import trace_logger

recognizer = sr.Recognizer()
mic = sr.Microphone()

def listen():
    t0 = time.perf_counter()
    trace_logger.info("Listening started")
    print("🎧 Listening...")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    t1 = time.perf_counter()
    trace_logger.info(
        f"Speech captured | duration={(t1 - t0):.3f}s"
    )

    print("🧠 Recognizing...")
    trace_logger.info("Speech recognition started")

    try:
        text = recognizer.recognize_google(audio)
        t2 = time.perf_counter()

        trace_logger.info(
            f"Speech recognition successful | duration={(t2 - t1):.3f}s"
        )

        print("You:", text)
        return text.lower()

    except sr.UnknownValueError:
        trace_logger.warning("Speech recognition failed")
        print("❌ Sorry, couldn't hear that")
        return None
    
    except (RemoteDisconnected, URLError, OSError, ConnectionError) as e:
        trace_logger.error(f"Network error during speech recognition: {type(e).__name__}")
        print("🌐 Network error - please check your connection and try again")
        return None
    
    except sr.RequestError as e:
        trace_logger.error(f"Speech recognition service error: {e}")
        print("⚠️  Speech recognition service unavailable")
        return None
    
    except Exception as e:
        trace_logger.error(f"Unexpected error during speech recognition: {type(e).__name__}: {e}")
        print("❌ An unexpected error occurred")
        return None