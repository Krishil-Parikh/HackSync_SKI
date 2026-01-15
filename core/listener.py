import speech_recognition as sr
import time
from http.client import RemoteDisconnected
from urllib.error import URLError
from config import trace_logger
from configuration.settings import settings

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

    # Try Azure Speech Recognition first (primary)
    try:
        azure_key = settings.AZURE_SPEECH_KEY
        azure_region = settings.AZURE_SPEECH_REGION
        
        if azure_key and azure_region:
            result = recognizer.recognize_azure(audio, key=azure_key, location=azure_region)
            # Azure returns tuple (text, confidence) - extract text only
            if isinstance(result, tuple):
                text = result[0]
            else:
                text = result
            
            t2 = time.perf_counter()
            trace_logger.info(
                f"Azure speech recognition successful | duration={(t2 - t1):.3f}s"
            )
            print("You:", text)
            return text.lower()
    except sr.UnknownValueError:
        trace_logger.warning("Azure speech recognition: could not understand audio")
    except sr.RequestError as e:
        trace_logger.warning(f"Azure speech recognition unavailable: {e}")
    except Exception as e:
        trace_logger.warning(f"Azure speech recognition error: {e}")

    # Fallback to Google Speech Recognition
    try:
        text = recognizer.recognize_google(audio)
        t2 = time.perf_counter()

        trace_logger.info(
            f"Google speech recognition successful (fallback) | duration={(t2 - t1):.3f}s"
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