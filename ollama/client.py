import requests
from config import trace_logger

OLLAMA_URL = "http://localhost:11434/api/generate"

def ollama_generate(model, prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        },
        timeout=60
    )
    return response.json()["response"].strip()


def warm_up_model(model_name: str):
    """
    Sends a tiny dummy prompt to force model load into memory.
    """
    trace_logger.info(f"Warming up model: {model_name}")

    try:
        requests.post(
            OLLAMA_URL,
            json={
                "model": model_name,
                "prompt": "Hello",
                "stream": False
            },
            timeout=120
        )
        trace_logger.info(f"Model warmed successfully: {model_name}")
    except Exception as e:
        trace_logger.error(f"Failed to warm model {model_name}: {e}")
        
def ollama_embed(text: str):
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={
            "model": "nomic-embed-text",
            "prompt": text
        }
    )
    return response.json()["embedding"]
