from config import trace_logger, passive_logger
from ollama.prompts import CONVERSATION_SYSTEM_PROMPT


class PromptComposer:
    def compose(
        self,
        user_text: str,
        active_context,
        passive_memories: list
    ) -> str:

        trace_logger.info("PromptComposer: composing prompt")

        prompt = CONVERSATION_SYSTEM_PROMPT.strip() + "\n\n"

        if active_context:
            prompt += "RECENT CONTEXT:\n"
            # Convert active_context to string if it's a list
            if isinstance(active_context, list):
                for ctx in active_context:
                    if isinstance(ctx, dict):
                        prompt += f"- {ctx.get('text', '')}\n"
                    else:
                        prompt += f"- {str(ctx)}\n"
            else:
                prompt += str(active_context) + "\n"
            prompt += "\n"

        if passive_memories:
            prompt += "BACKGROUND CONTEXT (USE SILENTLY):\n"
            for mem in passive_memories:
                # Handle both dict and object formats
                mem_text = mem.get('text', '') if isinstance(mem, dict) else getattr(mem, 'text', str(mem))
                if mem_text:
                    prompt += f"- {mem_text}\n"
            prompt += "\n"

        # Log what we're injecting for observability
        try:
            count = len(passive_memories or [])
            previews = [
                ((mem.get('text', '')[:80]).replace('\n',' ') if isinstance(mem, dict) else str(mem)[:80])
                for mem in (passive_memories or [])
            ]
            passive_logger.info(
                f"Prompt injection | passive_count={count} | previews={previews}"
            )
        except Exception:
            passive_logger.info("Prompt injection | passive_count=0")

        prompt += f"User: {user_text}\nNOVA:"

        return prompt
