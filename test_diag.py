from core.system_diagnostics import SystemDiagnostics
import traceback

diag = SystemDiagnostics()

print("Testing Azure Speech...")
try:
    result = diag.test_azure_speech()
    print(f"Result: {result}")
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()

print("\n\nTesting Azure Emotion...")
try:
    result = diag.test_azure_emotion()
    print(f"Result: {result}")
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
