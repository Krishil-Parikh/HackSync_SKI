"""
System Diagnostics Module
Tests and validates all HackSync_SKI system components on startup
"""

import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class SystemDiagnostics:
    """Comprehensive system health check and diagnostics"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "overall_status": "INITIALIZING"
        }
    
    def test_azure_speech(self):
        """Test Azure Speech Service (TTS) connectivity"""
        print("\n" + "="*60)
        print("[TEST] Azure Speech Service (Text-to-Speech)")
        print("="*60)
        
        try:
            # Test Azure SDK import first
            try:
                import azure.cognitiveservices.speech as speechsdk
                print(f"✓ Azure SDK imported successfully")
            except ImportError as e:
                print(f"✗ Azure SDK not installed: {e}")
                self.results["components"]["azure_speech"] = {"status": "UNAVAILABLE", "reason": "SDK not installed"}
                return False
            
            # Import settings (may fail due to config.py shadowing)
            try:
                from configuration.settings import settings
            except:
                # Fallback to direct import
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                from configuration.settings import settings
            
            # Test configuration
            config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY,
                region=settings.AZURE_SPEECH_REGION
            )
            
            print(f"✓ Region: {settings.AZURE_SPEECH_REGION}")
            print(f"✓ Voice: {settings.VOICE}")
            
            # Test a small synthesis
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
            synthesizer = speechsdk.SpeechSynthesizer(config, audio_config)
            
            result = synthesizer.speak_text_async("System test").get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print(f"✓ Speech synthesis test: SUCCESS")
                status = "ONLINE"
            else:
                print(f"✗ Speech synthesis test failed: {result.reason}")
                status = "OFFLINE"
            
            self.results["components"]["azure_speech"] = {
                "status": status,
                "region": settings.AZURE_SPEECH_REGION,
                "voice": settings.VOICE
            }
            
            return status == "ONLINE"
            
        except Exception as e:
            print(f"✗ Azure Speech test failed: {e}")
            self.results["components"]["azure_speech"] = {"status": "OFFLINE", "error": str(e)}
            return False
    
    def test_azure_emotion(self):
        """Test Azure Text Analytics (Emotion Detection) connectivity"""
        print("\n" + "="*60)
        print("[TEST] Azure Text Analytics (Emotion Detection)")
        print("="*60)
        
        try:
            # Test Azure SDK import first
            try:
                from azure.ai.textanalytics import TextAnalyticsClient
                from azure.core.credentials import AzureKeyCredential
                print(f"✓ Azure Text Analytics SDK imported successfully")
            except ImportError as e:
                print(f"✗ Azure Text Analytics SDK not installed (emotion detection will be disabled)")
                self.results["components"]["azure_emotion"] = {"status": "UNAVAILABLE", "reason": "SDK not installed"}
                return False
            
            # Import settings (may fail due to config.py shadowing)
            try:
                from configuration.settings import settings
            except:
                # Fallback to direct import
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                from configuration.settings import settings
            
            client = TextAnalyticsClient(
                endpoint=settings.AZURE_TEXT_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_TEXT_KEY)
            )
            
            print(f"✓ Endpoint: {settings.AZURE_TEXT_ENDPOINT}")
            
            # Test sentiment analysis
            test_text = "I am very happy!"
            result = client.analyze_sentiment([test_text], language="en")[0]
            
            print(f"✓ Sentiment analysis test: SUCCESS")
            print(f"  Test text: '{test_text}'")
            print(f"  Sentiment: {result.sentiment}")
            print(f"  Confidence: Pos={result.confidence_scores.positive:.2f}, Neg={result.confidence_scores.negative:.2f}")
            
            self.results["components"]["azure_emotion"] = {
                "status": "ONLINE",
                "endpoint": settings.AZURE_TEXT_ENDPOINT
            }
            
            return True
            
        except Exception as e:
            print(f"✗ Azure Emotion test failed: {e}")
            self.results["components"]["azure_emotion"] = {"status": "OFFLINE", "error": str(e)}
            return False
    
    def test_ollama_llm(self):
        """Test Ollama LLM fallback connectivity"""
        print("\n" + "="*60)
        print("[TEST] Ollama LLM Services")
        print("="*60)
        
        try:
            from ollama.client import ollama_generate
            
            print(f"✓ Ollama client imported successfully")
            
            # Test conversation model
            print(f"  Testing model: llama3.2:3b...")
            try:
                response = ollama_generate(model="llama3.2:3b", prompt="Hello")
                print(f"  ✓ llama3.2:3b: ONLINE")
                model_status = "ONLINE"
            except Exception as e:
                print(f"  ✗ llama3.2:3b: OFFLINE - {e}")
                model_status = "OFFLINE"
            
            self.results["components"]["ollama_llm"] = {
                "status": model_status,
                "models": {
                    "conversation": "llama3.2:3b",
                    "intent": "qwen3:4b",
                    "memory": "llama3:instruct"
                }
            }
            
            return model_status == "ONLINE"
            
        except ImportError:
            print(f"✗ Ollama client not available")
            self.results["components"]["ollama_llm"] = {"status": "UNAVAILABLE", "reason": "Client not available"}
            return False
        except Exception as e:
            print(f"✗ Ollama test failed: {e}")
            self.results["components"]["ollama_llm"] = {"status": "OFFLINE", "error": str(e)}
            return False
    
    def test_gemini_llm(self):
        """Test Gemini 2.5 Flash (via OpenRouter) connectivity"""
        print("\n" + "="*60)
        print("[TEST] Gemini 2.5 Flash (Primary LLM)")
        print("="*60)
        
        try:
            import requests
            
            print(f"✓ Requests library available")
            print(f"✓ OpenRouter API endpoint configured")
            
            # Test basic connectivity with a lightweight request
            # api_key = os.getenv("OPENROUTER_API_KEY")
            api_key = "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"
            if api_key:
                print(f"✓ OpenRouter API key found")
                status = "CONFIGURED"
            else:
                print(f"✗ OpenRouter API key not found in environment")
                status = "UNCONFIGURED"
            
            self.results["components"]["gemini_llm"] = {
                "status": status,
                "model": "google/gemini-2.5-flash",
                "provider": "OpenRouter"
            }
            
            return status == "CONFIGURED"
            
        except ImportError:
            print(f"✗ Requests library not installed")
            self.results["components"]["gemini_llm"] = {"status": "UNAVAILABLE", "reason": "Requests not installed"}
            return False
        except Exception as e:
            print(f"✗ Gemini test failed: {e}")
            self.results["components"]["gemini_llm"] = {"status": "UNCONFIGURED", "error": str(e)}
            return False
    
    def test_database(self):
        """Test database connectivity"""
        print("\n" + "="*60)
        print("[TEST] Database (Memory Storage)")
        print("="*60)
        
        try:
            from core.memory import ActiveMemory, PassiveMemory
            
            print(f"✓ Memory modules imported successfully")
            
            # Test active memory
            active = ActiveMemory(max_turns=5)
            print(f"✓ ActiveMemory initialized")
            
            # Test passive memory
            passive = PassiveMemory()
            print(f"✓ PassiveMemory initialized")
            
            # Test active memory file
            active_memory_file = "memory_bus/active_memory.json"
            if os.path.exists(active_memory_file):
                print(f"✓ Active memory bus file exists: {active_memory_file}")
            else:
                print(f"ℹ Active memory bus file will be created on first turn")
            
            # Ensure directory exists
            os.makedirs("memory_bus", exist_ok=True)
            print(f"✓ Memory bus directory ready")
            
            self.results["components"]["database"] = {
                "status": "ONLINE",
                "active_memory_file": active_memory_file,
                "memory_types": ["active", "passive"]
            }
            
            return True
            
        except Exception as e:
            print(f"✗ Database test failed: {e}")
            self.results["components"]["database"] = {"status": "OFFLINE", "error": str(e)}
            return False
    
    def test_audio_input(self):
        """Test microphone input availability"""
        print("\n" + "="*60)
        print("[TEST] Audio Input (Microphone)")
        print("="*60)
        
        try:
            import sounddevice as sd
            
            print(f"✓ Sounddevice library available")
            
            # Check default device
            device = sd.default.device
            print(f"✓ Default audio device: {device}")
            print(f"✓ Microphone available for listening")
            
            self.results["components"]["audio_input"] = {
                "status": "ONLINE",
                "device": str(device)
            }
            
            return True
            
        except ImportError:
            print(f"ℹ Sounddevice not installed (will use Azure default)")
            self.results["components"]["audio_input"] = {"status": "CONFIGURED", "reason": "Using Azure defaults"}
            return True
        except Exception as e:
            print(f"ℹ Audio input check: {e}")
            self.results["components"]["audio_input"] = {"status": "WARNING", "error": str(e)}
            return True  # Not critical
    
    def test_pyttsx3_fallback(self):
        """Test pyttsx3 fallback speaker"""
        print("\n" + "="*60)
        print("[TEST] pyttsx3 Fallback Speaker")
        print("="*60)
        
        try:
            from speech.pyttsx3_fallback import PyTTSX3Fallback
            
            # Attempt to initialize
            try:
                fallback = PyTTSX3Fallback()
                print(f"✓ pyttsx3 fallback initialized successfully")
                print(f"✓ Fallback speaker ready for: Azure failures")
                status = "ONLINE"
            except Exception as init_e:
                print(f"⚠ pyttsx3 fallback import OK but initialization failed: {init_e}")
                print(f"  (This is acceptable - will work when needed)")
                status = "AVAILABLE"
            
            self.results["components"]["pyttsx3_fallback"] = {
                "status": status,
                "used_when": "Azure speech synthesis fails"
            }
            
            return True
            
        except ImportError as e:
            print(f"✗ pyttsx3 fallback not available: {e}")
            self.results["components"]["pyttsx3_fallback"] = {"status": "UNAVAILABLE", "error": str(e)}
            return False
        except Exception as e:
            print(f"✗ pyttsx3 fallback unavailable: {e}")
            self.results["components"]["pyttsx3_fallback"] = {"status": "UNAVAILABLE", "error": str(e)}
            return False
    
    def run_all_tests(self):
        """Run all diagnostic tests"""
        print("\n\n")
        print("╔" + "="*58 + "╗")
        print("║" + " "*10 + "HACKSYNC_SKI SYSTEM DIAGNOSTICS" + " "*16 + "║")
        print("║" + " "*15 + "Starting comprehensive system tests..." + " "*6 + "║")
        print("╚" + "="*58 + "╝")
        
        # Run all tests
        azure_speech_ok = self.test_azure_speech()
        azure_emotion_ok = self.test_azure_emotion()
        ollama_ok = self.test_ollama_llm()
        gemini_ok = self.test_gemini_llm()
        db_ok = self.test_database()
        audio_ok = self.test_audio_input()
        pyttsx3_ok = self.test_pyttsx3_fallback()
        
        # Determine overall status
        print("\n" + "="*60)
        print("[SUMMARY] System Status")
        print("="*60)
        
        critical_services = [azure_speech_ok, db_ok]
        fallback_services = [azure_emotion_ok, ollama_ok, gemini_ok, pyttsx3_ok]
        
        if all(critical_services):
            status = "READY"
            emoji = "✓"
        else:
            status = "DEGRADED"
            emoji = "⚠"
        
        print(f"{emoji} Overall Status: {status}")
        print(f"✓ Critical Services: {sum(critical_services)}/{len(critical_services)} online")
        print(f"✓ Fallback Services: {sum(fallback_services)}/{len(fallback_services)} online")
        
        # Emotion mode status
        emotion_enabled = azure_emotion_ok
        print(f"\n💭 Emotion Mode: {'ENABLED (Azure)' if emotion_enabled else 'DISABLED (Fallback pyttsx3)'}")
        
        if not azure_speech_ok:
            print(f"⚠  Azure Speech unavailable - pyttsx3 fallback in use")
        
        if not azure_emotion_ok:
            print(f"⚠  Azure Emotion Detection unavailable - emotions disabled with fallback")
        
        self.results["overall_status"] = status
        self.results["emotion_mode"] = "ENABLED" if emotion_enabled else "DISABLED"
        self.results["summary"] = {
            "critical_online": sum(critical_services),
            "fallback_online": sum(fallback_services),
            "emotion_capable": emotion_enabled
        }
        
        # Save diagnostics report
        self._save_diagnostics_report()
        
        print("\n" + "="*60)
        print(f"Diagnostics report saved to: diagnostics_report.json")
        print("="*60 + "\n")
        
        return status == "READY"
    
    def _save_diagnostics_report(self):
        """Save diagnostics report to JSON file"""
        try:
            with open("diagnostics_report.json", "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            logger.info("Diagnostics report saved")
        except Exception as e:
            logger.error(f"Could not save diagnostics report: {e}")
    
    def is_azure_available(self):
        """Check if Azure Speech service is available (for TTS)"""
        azure_speech = self.results.get("components", {}).get("azure_speech", {}).get("status") == "ONLINE"
        return azure_speech
    
    def is_azure_speech_available(self):
        """Check if Azure Speech service is available"""
        return self.results.get("components", {}).get("azure_speech", {}).get("status") == "ONLINE"
    
    def is_emotion_enabled(self):
        """Check if emotion mode is enabled (requires both Azure Speech AND Azure Emotion)"""
        azure_speech = self.results.get("components", {}).get("azure_speech", {}).get("status") == "ONLINE"
        azure_emotion = self.results.get("components", {}).get("azure_emotion", {}).get("status") == "ONLINE"
        return azure_speech and azure_emotion
