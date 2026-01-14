from config import trace_logger, passive_logger
from ollama.prompts import CONVERSATION_SYSTEM_PROMPT


class PromptComposer:
    def compose(
        self,
        user_text: str,
        active_context: str,
        passive_memories: list
    ) -> str:

        trace_logger.info("PromptComposer: composing prompt")

        prompt = CONVERSATION_SYSTEM_PROMPT.strip() + "\n\n"

        if active_context:
            prompt += "RECENT CONTEXT:\n"
            prompt += active_context + "\n\n"

        if passive_memories:
            prompt += "BACKGROUND CONTEXT (USE SILENTLY):\n"
            for mem in passive_memories:
                prompt += f"- {mem['fact']}\n"
            prompt += "\n"

        # Log what we're injecting for observability
        try:
            count = len(passive_memories or [])
            previews = [
                (mem.get('topic', 'unknown'), (mem.get('fact','')[:80]).replace('\n',' '))
                for mem in (passive_memories or [])
            ]
            passive_logger.info(
                f"Prompt injection | passive_count={count} | previews={previews}"
            )
        except Exception:
            passive_logger.info("Prompt injection | passive_count=0")

        prompt += f"User: {user_text}\nNOVA:"

        return prompt
