import traceback

print("Direct import test:")
try:
    import azure.cognitiveservices.speech as speechsdk
    print("✓ Azure Speech SDK imported successfully")
    print(f"✓ Version: {speechsdk.__version__ if hasattr(speechsdk, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"✗ ImportError: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"✗ Other error: {e}")
    traceback.print_exc()

print("\n" + "="*60)
print("Config.settings import test:")
try:
    from config.settings import settings
    print("✓ Settings imported")
    print(f"✓ Azure Speech Key present: {bool(settings.AZURE_SPEECH_KEY)}")
    print(f"✓ Azure Speech Region: {settings.AZURE_SPEECH_REGION}")
except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()
