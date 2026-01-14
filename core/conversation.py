import time
from ollama.client import ollama_generate
from config import trace_logger

CONVERSATION_MODEL = "llama3:instruct"

def generate_reply(prompt: str) -> str:
    """Generate a reply from a fully composed prompt.

    The caller is responsible for composing the final prompt including
    any conversation history and user input.
    """
    trace_logger.info("Conversation generation started")
    start = time.perf_counter()

    reply = ollama_generate(
        model=CONVERSATION_MODEL,
        prompt=prompt
    )

    duration = time.perf_counter() - start
    trace_logger.info(
        f"Conversation reply received | duration={duration:.3f}s"
    )

    return reply.strip()