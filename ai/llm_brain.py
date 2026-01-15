import logging
import os
import requests
from configuration.settings import settings
from config import trace_logger as logger

class LLMBrain:
    """Local LLM using Ollama for intelligent response generation"""
    
    def __init__(self):
        self.api_url = settings.OLLAMA_API_URL
        self.model = settings.OLLAMA_MODEL
        self.temperature = settings.OLLAMA_TEMPERATURE
        self.max_tokens = settings.OLLAMA_MAX_TOKENS
        # Ollama availability (local fallback)
        self.available = self._check_ollama_availability()

        # OpenRouter (remote) configuration - key must be provided via env var
        self.openrouter_key =  "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" # os.getenv("OPENROUTER_API_KEY")
        self.openrouter_url = getattr(settings, "OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
        self.openrouter_model = getattr(settings, "OPENROUTER_MODEL", "google/gemini-2.5-flash")
        self.openrouter_available = bool(self.openrouter_key)

        if self.openrouter_available:
            logger.info("[LLM] OpenRouter key found; OpenRouter will be used as primary LLM when available.")

        # Track last LLM used for diagnostics
        self.last_llm_used = None

        if self.available:
            logger.info(f"[LLM] Ollama initialized: model={self.model}, endpoint={self.api_url}")
        else:
            logger.warning("[LLM] Ollama not available. Make sure Ollama is running for fallback!")
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama server is available"""
        try:
            # Check both possible endpoints
            base_url = self.api_url.replace('/api', '')
            response = requests.get(f"{base_url}/api/tags", timeout=2)
            if response.status_code != 200:
                response = requests.get(f"{base_url}/tags", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"[LLM] Ollama unavailable: {e}")
            return False
    
    def generate(self, prompt: str) -> str:
        """Generate completion from raw prompt (for intent, memory, actions)"""
        # Try OpenRouter (Gemini) first
        if self.openrouter_available:
            try:
                logger.info(f"[LLM] Attempting OpenRouter request with model: {self.openrouter_model}")
                generated = self._openrouter_raw_prompt(prompt)
                if generated:
                    self.last_llm_used = "openrouter"
                    logger.info(f"[LLM] Used OpenRouter for prompt: {prompt[:50]}...")
                    return generated
                else:
                    logger.warning("[LLM] OpenRouter returned empty response")
            except Exception as e:
                logger.warning(f"[LLM] OpenRouter request failed: {e}")
        else:
            logger.warning("[LLM] OpenRouter not available (no API key), skipping to Ollama")

        # Fallback to Ollama
        if self.available:
            try:
                response = requests.post(
                    f"{self.api_url}/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    generated_text = result.get("response", "").strip()
                    if generated_text:
                        self.last_llm_used = "ollama"
                        logger.info(f"[LLM] Used Ollama for prompt: {prompt[:50]}...")
                        return generated_text
            except Exception as e:
                logger.error(f"[LLM] Ollama error: {e}")

        # Final fallback
        logger.warning("[LLM] Both OpenRouter and Ollama unavailable, using empty response")
        return ""

    def generate_response(self, user_input: str) -> str:
        """Generate response using local LLM"""
        # Try OpenRouter (remote Gemini) first when API key present
        if self.openrouter_available:
            try:
                generated = self._openrouter_generate(user_input)
                if generated:
                    self.last_llm_used = "openrouter"
                    return generated
            except Exception as e:
                logger.warning(f"[LLM] OpenRouter request failed: {e}")

        # Next try Ollama (local) if available
        if self.available:
            try:
                prompt = self._create_prompt(user_input)

                response = requests.post(
                    f"{self.api_url}/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    generated_text = result.get("response", "").strip()

                    if generated_text:
                        logger.info(f"[LLM] Generated response (Ollama): {generated_text[:60]}...")
                        self.last_llm_used = "ollama"
                        return generated_text
                else:
                    logger.error(f"[LLM] Ollama API error: {response.status_code}")
            except requests.exceptions.Timeout:
                logger.error("[LLM] Ollama request timeout")
            except Exception as e:
                logger.error(f"[LLM] Error generating response (Ollama): {e}")

        # Final fallback
        return self._fallback_response(user_input)

    def generate_structured_response(self, user_input: str) -> dict:
        """Ask the LLM to return a JSON object with keys: reply, emotions (list of {label,confidence}), llm."""
        instruction = (
            "Return STRICT JSON only with these keys: 'reply' (string), 'emotions' (array of {label:string, confidence:0-1}), "
            "and 'llm' (string indicating which model generated this). If unsure about an emotion, give low confidence. "
            "Example: {\"reply\":\"Hi\", \"emotions\": [{\"label\":\"happy\", \"confidence\":0.9}], \"llm\":\"google/gemini-2.5-flash\"}"
        )

        # Prefer OpenRouter for structured JSON
        if self.openrouter_available:
            try:
                headers = {
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": self.openrouter_model,
                    "messages": [
                        {"role": "system", "content": instruction},
                        {"role": "user", "content": user_input}
                    ],
                    "temperature": self.temperature,
                    "max_tokens": 2000
                }

                resp = requests.post(f"{self.openrouter_url}/chat/completions", json=payload, headers=headers, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    # Extract text content
                    choice = (data.get("choices") or [{}])[0]
                    msg = choice.get("message") or {}
                    content = ""
                    if isinstance(msg, dict):
                        content = msg.get("content") or ""
                    else:
                        content = choice.get("text") or ""

                    # Try parse JSON from model output
                    import json, re
                    try:
                        # attempt full JSON load
                        parsed = json.loads(content)
                    except Exception:
                        # attempt to extract first JSON object
                        m = re.search(r"\{.*\}", content, re.S)
                        if m:
                            try:
                                parsed = json.loads(m.group(0))
                            except Exception:
                                parsed = None
                        else:
                            parsed = None

                    if isinstance(parsed, dict):
                        parsed.setdefault("llm", self.openrouter_model)
                        self.last_llm_used = "openrouter"
                        return parsed
                else:
                    logger.error(f"[LLM] OpenRouter API error (structured): {resp.status_code} {resp.text}")
            except Exception as e:
                logger.warning(f"[LLM] OpenRouter structured request failed: {e}")

        # Fallback to Ollama for structured output via prompt
        if self.available:
            try:
                prompt = (
                    instruction + "\nUser: " + user_input + "\nAssistant: "
                )
                response = requests.post(
                    f"{self.api_url}/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    text = result.get("response", "").strip()
                    import json, re
                    try:
                        parsed = json.loads(text)
                    except Exception:
                        m = re.search(r"\{.*\}", text, re.S)
                        if m:
                            try:
                                parsed = json.loads(m.group(0))
                            except Exception:
                                parsed = None
                        else:
                            parsed = None

                    if isinstance(parsed, dict):
                        parsed.setdefault("llm", self.model)
                        self.last_llm_used = "ollama"
                        return parsed
            except Exception as e:
                logger.warning(f"[LLM] Ollama structured request failed: {e}")

        # Final fallback: construct a minimal JSON using the older fallback response and no emotions
        fallback_text = self._fallback_response(user_input)
        return {"reply": fallback_text, "emotions": [], "llm": "fallback"}

    def _openrouter_raw_prompt(self, prompt: str) -> str:
        """Generate completion from raw prompt using OpenRouter."""
        if not self.openrouter_key:
            logger.error("[LLM] OpenRouter key is missing!")
            return ""

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.openrouter_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": 2000  # Reasonable limit for OpenRouter
        }

        logger.info(f"[LLM] Sending request to {self.openrouter_url}/chat/completions")
        resp = requests.post(f"{self.openrouter_url}/chat/completions", json=payload, headers=headers, timeout=30)
        
        logger.info(f"[LLM] OpenRouter response status: {resp.status_code}")
        
        if resp.status_code != 200:
            logger.error(f"[LLM] OpenRouter API error: {resp.status_code} {resp.text}")
            return ""

        data = resp.json()
        logger.info(f"[LLM] OpenRouter response data keys: {data.keys()}")
        
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        if isinstance(message, dict):
            content = message.get("content") or ""
        else:
            content = choice.get("text") or ""

        result = (content or "").strip()
        logger.info(f"[LLM] OpenRouter extracted content length: {len(result)}")
        return result

    def _openrouter_generate(self, user_input: str) -> str:
        """Generate text using OpenRouter / Gemini chat completions endpoint."""
        if not self.openrouter_key:
            return ""

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.openrouter_model,
            "messages": [
                {"role": "system", "content": "You are a helpful, friendly AI assistant. Respond concisely."},
                {"role": "user", "content": user_input}
            ],
            "temperature": self.temperature,
            "max_tokens": 2000
        }

        resp = requests.post(f"{self.openrouter_url}/chat/completions", json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            logger.error(f"[LLM] OpenRouter API error: {resp.status_code} {resp.text}")
            return ""

        data = resp.json()
        # Parse robustly for content
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        if isinstance(message, dict):
            content = message.get("content") or message.get("content")
        else:
            content = choice.get("text") or message or ""

        generated = (content or "").strip()
        if generated:
            logger.info(f"[LLM] Generated response (OpenRouter): {generated[:60]}...")
        return generated
    
    def _create_prompt(self, user_input: str) -> str:
        """Create an optimized prompt for the LLM"""
        prompt = f"""You are a helpful, friendly AI assistant. Answer the user's input concisely and naturally in 1-2 sentences.

User: {user_input}
Assistant:"""
        return prompt
    
    def _fallback_response(self, user_input: str) -> str:
        """Fallback response when LLM is unavailable"""
        logger.warning("[LLM] Using fallback response")
        
        text_lower = user_input.lower()
        
        if "?" in text_lower:
            return "That's a great question! Let me think about that and provide you with a thoughtful answer."
        elif any(word in text_lower for word in ["hello", "hi", "hey", "greetings"]):
            return "Hello! It's wonderful to meet you. How can I help you today?"
        elif any(word in text_lower for word in ["thanks", "thank you", "appreciate"]):
            return "You're very welcome! I'm always happy to help you out."
        elif any(word in text_lower for word in ["sorry", "apologies", "my bad"]):
            return "No worries at all! Everyone makes mistakes. Let's move forward together."
        else:
            return "That's really interesting! Let me think about what you said and respond thoughtfully to you."
