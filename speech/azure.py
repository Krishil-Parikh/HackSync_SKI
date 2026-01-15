import azure.cognitiveservices.speech as speechsdk
from configuration.settings import settings
import logging
import os
import time
import threading

logger = logging.getLogger(__name__)

# Import fallback speaker
try:
    from speech.pyttsx3_fallback import PyTTSX3Fallback
    fallback_speaker = PyTTSX3Fallback()
except Exception as e:
    logger.warning(f"[INIT] Could not initialize pyttsx3 fallback: {e}")
    fallback_speaker = None

class AzureSpeech:
    # Emotion to Azure style mapping
    EMOTION_STYLES = {
        "calm": "calm",
        "sad": "sad",
        "cheerful": "cheerful",
        "curious": "curious",
        "empathetic": "empathetic",
        "excited": "excited",
        "default": "neutral"
    }

    def __init__(self):
        try:
            self.config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY,
                region=settings.AZURE_SPEECH_REGION
            )
            self.config.speech_synthesis_voice_name = settings.VOICE
            self.config.speech_recognition_language = "en-US"
            
            # Use PCM WAV so winsound can play the file directly on Windows
            self.config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
            )
            
            logger.info(f"[INIT] Azure Speech initialized: region={settings.AZURE_SPEECH_REGION}, voice={settings.VOICE}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Speech: {e}")
            raise

    def listen(self):
        """Speech to Text - Listen to user input"""
        audio = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = speechsdk.SpeechRecognizer(self.config, audio)

        print("\n[Listening...]")
        result = recognizer.recognize_once()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            heard_text = result.text
            print(f"[System Heard]: '{heard_text}'")
            return heard_text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("[No speech detected]")
            return ""
        elif result.reason == speechsdk.ResultReason.Canceled:
            error_details = result.cancellation_details
            print(f"[Speech Recognition Canceled]: {error_details.reason}")
            if error_details.error_details:
                print(f"   Error details: {error_details.error_details}")
            return ""
        
        return ""

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters in text"""
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&apos;"
        }
        for char, escaped in replacements.items():
            text = text.replace(char, escaped)
        return text

    def _create_ssml(self, text: str, emotion: str) -> str:
        """Create SSML markup with proper formatting"""
        # Map emotion to closest Azure style
        style = self.EMOTION_STYLES.get(emotion, self.EMOTION_STYLES["default"])
        
        # Escape XML special characters
        safe_text = self._escape_xml(text)
        
        ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
    <voice name="{settings.VOICE}">
        <mstts:viseme type="FacialExpression"/>
        <mstts:express-as style="{style}" styledegree="1.0">
            {safe_text}
        </mstts:express-as>
    </voice>
</speak>'''
        return ssml

    def speak(self, text: str, emotion: str):
        """Text to Speech - Speak response with visemes and emotion
        
        Pipeline: Azure -> Fallback (pyttsx3)
        """
        print(f"\n[System Speaking - emotion: {emotion}]: '{text}'")
        
        # Initialize visemes list at the start
        visemes = []

        def on_viseme(evt):
            """Callback for viseme events during synthesis"""
            try:
                viseme_info = {
                    "time_ms": evt.audio_offset / 10000,  # Convert to milliseconds
                    "viseme_id": evt.viseme_id
                }
                visemes.append(viseme_info)
                print(f"  [Viseme ID={evt.viseme_id}, Time={viseme_info['time_ms']:.0f}ms]")
            except Exception as e:
                logger.error(f"Error in viseme callback: {e}")

        def on_synthesizing(evt):
            """Callback for synthesis progress"""
            try:
                if evt.result.reason == speechsdk.ResultReason.SynthesizingAudio:
                    pass  # Synthesis in progress
            except Exception as e:
                logger.error(f"Error in synthesizing callback: {e}")

        # ============================================================
        # ATTEMPT PRIMARY: AZURE SPEECH SYNTHESIS
        # ============================================================
        try:
            # Output directly to default speaker (no file)
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.config,
                audio_config=audio_config
            )
            
            # Connect callbacks
            synthesizer.viseme_received.connect(on_viseme)
            synthesizer.synthesizing.connect(on_synthesizing)
            
            # Create SSML
            ssml = self._create_ssml(text, emotion)
            logger.debug(f"SSML: {ssml}")
            
            # Perform speech synthesis asynchronously and wait for completion
            result = synthesizer.speak_ssml_async(ssml).get()
            
            # Check result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print(f"[Synthesis Complete] Total visemes: {len(visemes)}")
                logger.info(f"[AZURE] Speech synthesis successful: text_length={len(text)}, viseme_count={len(visemes)}")
                print(f"[Audio playback completed]")
                return visemes  # Success, exit early
                
            elif result.reason == speechsdk.ResultReason.Canceled:
                error_details = result.cancellation_details
                error_msg = f"{error_details.reason}"
                if error_details.error_details:
                    error_msg += f": {error_details.error_details}"
                print(f"[Azure Synthesis Failed]: {error_msg}")
                logger.warning(f"[AZURE] Speech synthesis failed: {error_msg}")
                # Fall through to fallback
                
            else:
                print(f"[Unexpected Result]: {result.reason}")
                logger.warning(f"[AZURE] Unexpected synthesis result: {result.reason}")
                # Fall through to fallback
        
        except Exception as e:
            logger.warning(f"[AZURE] Speech synthesis error, falling back to pyttsx3: {e}")
            print(f"[Azure failed, using fallback]")
            
        # ============================================================
        # FALLBACK: PYTTSX3
        # ============================================================
        if fallback_speaker:
            try:
                fallback_speaker.speak(text, emotion)
                logger.info("[FALLBACK] Successfully used pyttsx3 for speech")
                return visemes
            except Exception as e2:
                logger.error(f"[FALLBACK] pyttsx3 also failed: {e2}")
                print(f"[Critical Error]: Both Azure and fallback failed: {e2}")
                return visemes
        else:
            logger.error("[FALLBACK] pyttsx3 fallback not available")
            print("[Critical Error]: Azure failed and pyttsx3 fallback not initialized")
            return visemes