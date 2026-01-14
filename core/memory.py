import json
import time
import uuid
import re
from collections import deque

from config import trace_logger, passive_logger
from ollama.client import ollama_generate, ollama_embed
from ollama.prompts import MEMORY_EVALUATOR_PROMPT, MEMORY_REEVALUATION_PROMPT
from core.db import passive_memory_collection
from pymongo.errors import DuplicateKeyError


def _preview(text: str, limit: int = 150) -> str:
    try:
        return (text or "")[:limit].replace("\n", " ")
    except Exception:
        return "<unavailable>"


def _fact_key(text: str) -> str:
    # Normalize for deduplication: lowercase and collapse whitespace
    try:
        base = (text or "").strip().lower()
        # Collapse multiple whitespace into single space
        return " ".join(base.split())
    except Exception:
        return (text or "").lower()


def _find_json_block(text: str) -> str | None:
    if not text:
        return None

    # Prefer fenced code block content if present
    try:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
        if m:
            text = m.group(1).strip()
    except Exception:
        pass

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]

    return None


# ======================================================
# ACTIVE MEMORY (MAIN PROCESS ONLY)
# ======================================================

class ActiveMemory:
    """
    Short-term working memory (used only for prompt context).
    """

    def __init__(self, max_turns: int = 5):
        self.buffer = deque(maxlen=max_turns)
        trace_logger.info(f"ActiveMemory initialized | max_turns={max_turns}")

    def add(self, user_text: str, nova_reply: str):
        self.buffer.append(
            f"User: {user_text}\nNOVA: {nova_reply}"
        )

    def get_context(self) -> str:
        return "\n".join(self.buffer)

    def clear(self):
        self.buffer.clear()


# ======================================================
# PASSIVE MEMORY ITEM (INTERNAL MODEL)
# ======================================================

class PassiveMemoryItem:
    """
    Atomic passive memory fact (user or NOVA).
    """

    def __init__(
        self,
        fact: str,
        topic: str,
        relevance_tags: list,
        confidence: str = "low",
        origin: str = "user"   # user | nova
    ):
        self.id = str(uuid.uuid4())
        self.origin = origin
        self.fact = fact
        self.topic = topic
        self.relevance_tags = relevance_tags
        self.confidence = confidence
        self.timestamp = time.time()
        self.last_reinforced = self.timestamp
        self.status = "active"


# ======================================================
# PASSIVE MEMORY (MONGODB BACKEND)
# ======================================================

class PassiveMemory:
    """
    MongoDB-backed passive memory store.
    """

    # ---------- INSERT ----------

    def add(self, item: PassiveMemoryItem):
        passive_logger.info(
            f"Insert start | origin={item.origin} | topic={item.topic} | confidence={item.confidence}"
        )

        # Embedding generation with error logging
        try:
            embedding = ollama_embed(item.fact)
            emb_len = len(embedding) if hasattr(embedding, "__len__") else 0
            passive_logger.info(f"Embedding generated | len={emb_len}")
        except Exception as e:
            passive_logger.error(f"Embedding error | error={e}")
            embedding = None

        try:
            result = passive_memory_collection.insert_one({
            "origin": item.origin,
            "fact": item.fact,
                "fact_key": _fact_key(item.fact),
            "topic": item.topic,
            "relevance_tags": item.relevance_tags,
            "confidence": item.confidence,
            "status": item.status,
            "timestamp": item.timestamp,
            "last_reinforced": item.last_reinforced,
            "embedding": embedding
            })
            try:
                inserted_id = str(result.inserted_id)
            except Exception:
                inserted_id = "<unknown>"
            passive_logger.info(
                f"Inserted passive memory | id={inserted_id} | len(fact)={len(item.fact)}"
            )
        except DuplicateKeyError:
            passive_logger.info(
                f"Duplicate fact ignored | key={_fact_key(item.fact)}"
            )
            return
        except Exception as e:
            passive_logger.error(f"Insert error | topic={item.topic} | error={e}")
            return

    # ---------- QUERY HELPERS (USED BY WORKER) ----------

    def count(self):
        return passive_memory_collection.count_documents(
            {"status": "active"}
        )

    def get_by_confidence(self, level: str):
        return list(
            passive_memory_collection.find({
                "confidence": level,
                "status": "active"
            })
        )

    def promote(self, mem, new_level: str):
        passive_memory_collection.update_one(
            {"_id": mem["_id"]},
            {
                "$set": {
                    "confidence": new_level,
                    "last_reinforced": time.time()
                }
            }
        )
        passive_logger.info(
            f"Promoted memory | id={mem['_id']} | confidence={new_level}"
        )

    def discard_lowest_low(self):
        low = passive_memory_collection.find_one(
            {"confidence": "low", "status": "active"},
            sort=[("timestamp", 1)]
        )

        if low:
            passive_memory_collection.delete_one(
                {"_id": low["_id"]}
            )
            passive_logger.info(
                f"Discarded LOW memory | id={low['_id']}"
            )

    # ---------- PRIORITY SCORING (DETERMINISTIC) ----------

    def compute_priority(self, mem) -> float:
        """
        Deterministic relevance score.
        No LLMs involved.
        """

        now = time.time()

        recency = max(
            0.0,
            1.0 - ((now - mem["last_reinforced"]) / 3600)
        )

        identity_weight = 1.0 if mem["topic"] == "identity" else 0.0
        length_weight = min(len(mem["fact"].split()) / 10, 1.0)

        score = (
            0.5 * recency +
            0.3 * length_weight +
            0.2 * identity_weight
        )

        return score

    def update_confidence(self, mem_id, new_confidence: str):
        passive_memory_collection.update_one(
            {"_id": mem_id},
            {
                "$set": {
                    "confidence": new_confidence,
                    "last_reinforced": time.time()
                }
            }
        )
        passive_logger.info(
            f"Updated confidence | id={mem_id} | confidence={new_confidence}"
        )

    def update_topic(self, mem_id, new_topic: str):
        passive_memory_collection.update_one(
            {"_id": mem_id},
            {
                "$set": {
                    "topic": new_topic,
                    "last_reinforced": time.time()
                }
            }
        )
        passive_logger.info(
            f"Updated topic | id={mem_id} | topic={new_topic}"
        )

    def update_tags(self, mem_id, new_tags: list):
        passive_memory_collection.update_one(
            {"_id": mem_id},
            {
                "$set": {
                    "relevance_tags": new_tags,
                    "last_reinforced": time.time()
                }
            }
        )
        passive_logger.info(
            f"Updated tags | id={mem_id}"
        )


# ======================================================
# MEMORY EVALUATOR (WORKER PROCESS ONLY)
# ======================================================

import json
import re
import time

from config import trace_logger
from ollama.client import ollama_generate
from core.memory import PassiveMemoryItem

ALLOWED_TOPICS = {
    "identity", "preference", "habit", "project", "tool",
    "goal", "plan", "decision", "skill", "background", "other"
}

ALLOWED_CONFIDENCE = {"low", "medium", "high"}

# Control switches
EXTRACT_FROM_NOVA = False  # reduce noise: only extract from user by default


class MemoryEvaluator:
    """
    Worker-only memory evaluator.
    Extraction + re-evaluation logic.
    """

    def __init__(self, passive_memory):
        self.passive_memory = passive_memory
        trace_logger.info("MemoryEvaluator initialized")
        passive_logger.info("MemoryEvaluator initialized")

    # ==================================================
    # ENTRY POINT (CALLED BY WORKER)
    # ==================================================

    def evaluate(self, user_text: str, nova_reply: str):
        passive_logger.info(
            f"Evaluate turn | user_len={len(user_text)} | nova_len={len(nova_reply)}"
        )

        self._extract_and_store(user_text, origin="user")
        if EXTRACT_FROM_NOVA:
            self._extract_and_store(nova_reply, origin="nova")
        else:
            passive_logger.info("Extraction skipped for nova origin (disabled)")

        # 🔴 Capacity control
        if self.passive_memory.count() >= 50:
            self._re_evaluate_low_confidence()

    # ==================================================
    # EXTRACTION
    # ==================================================

    def _extract_and_store(self, text: str, origin: str):
        if not self._should_attempt_extraction(text, origin):
            passive_logger.info(f"Extraction gated | origin={origin}")
            return
        items = self._llm_extract(text, origin)
        if not items:
            passive_logger.info(f"No items extracted | origin={origin}")
            return

        for item in items:
            self.passive_memory.add(item)
        passive_logger.info(
            f"Extracted {len(items)} items | origin={origin}"
        )

    def _llm_extract(self, text: str, origin: str):
        # Log request preview
        try:
            preview = (text or "")[:200].replace("\n", " ")
        except Exception:
            preview = "<unavailable>"
        passive_logger.info(
            f"LLM extract request | origin={origin} | text_preview={preview}"
        )

        response = ollama_generate(
            model="llama3:instruct",
            prompt=MEMORY_EVALUATOR_PROMPT.replace("{user_input}", text)
        )

        # Log raw response preview
        try:
            resp_preview = (response or "")[:400].replace("\n", " ")
            passive_logger.info(
                f"LLM extract response | len={len(response or '')} | preview={resp_preview}"
            )
        except Exception:
            passive_logger.warning("LLM extract: failed to preview response")

        if not response:
            passive_logger.warning("LLM extract: empty response")
            return None

        json_str = _find_json_block(response)
        if not json_str:
            passive_logger.warning("LLM extract: no JSON object matched in response")
            return None

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            snippet = _preview(json_str, 200)
            passive_logger.error(f"LLM extract: JSON decode error | error={e} | snippet={snippet}")
            return None

        facts = data.get("facts", [])
        if not isinstance(facts, list):
            passive_logger.warning("LLM extract: 'facts' not a list")
            return None

        items = []

        for f in facts:
            if not isinstance(f, dict):
                continue

            fact = f.get("fact")
            topic = f.get("topic")
            confidence = f.get("confidence")
            tags = f.get("relevance_tags", [])

            if (
                not isinstance(fact, str)
                or topic not in ALLOWED_TOPICS
                or confidence not in ALLOWED_CONFIDENCE
                or not isinstance(tags, list)
            ):
                continue

            if not self._is_store_worthy(fact):
                passive_logger.info("LLM extract: fact filtered out by store-worthiness check")
                continue

            items.append(
                PassiveMemoryItem(
                    fact=fact.strip(),
                    topic=topic,
                    relevance_tags=tags[:5],
                    confidence=confidence,
                    origin=origin
                )
            )

        for it in items:
            passive_logger.info(
                f"LLM extract: parsed item | origin={origin} | topic={it.topic} | conf={it.confidence} | fact_preview={_preview(it.fact, 150)}"
            )
        return items or None

    # ==================================================
    # RE-EVALUATION WHEN CAPACITY EXCEEDED
    # ==================================================

    def _re_evaluate_low_confidence(self):
        lows = self.passive_memory.get_by_confidence("low")
        passive_logger.info(f"Re-evaluate low-confidence | count={len(lows)}")
        now = time.time()

        for mem in lows:
            age_seconds = int(now - mem["last_reinforced"])

            # Log request preview
            passive_logger.info(
                f"Re-eval request | id={mem['_id']} | topic={mem.get('topic')} | conf={mem.get('confidence')} | age={age_seconds}s | fact_preview={_preview(mem.get('fact',''), 120)}"
            )

            response = ollama_generate(
                model="llama3:instruct",
                prompt=MEMORY_REEVALUATION_PROMPT.format(
                    fact=mem["fact"],
                    topic=mem["topic"],
                    confidence=mem["confidence"],
                    age_seconds=age_seconds
                )
            )

            # Log response preview
            try:
                resp_preview = (response or "")[:300].replace("\n", " ")
                passive_logger.info(
                    f"Re-eval response | id={mem['_id']} | preview={resp_preview}"
                )
            except Exception:
                passive_logger.warning(f"Re-eval: failed to preview response | id={mem['_id']}")

            json_str = _find_json_block(response or "")
            if not json_str:
                passive_logger.warning(f"Re-eval: no JSON object matched | id={mem['_id']}")
                continue

            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                snippet = _preview(json_str, 200)
                passive_logger.error(f"Re-eval: JSON decode error | id={mem['_id']} | error={e} | snippet={snippet}")
                continue

            new_conf = data.get("confidence")
            new_topic = data.get("topic")
            new_tags = data.get("relevance_tags")

            passive_logger.info(
                f"Re-eval parsed | id={mem['_id']} | conf={new_conf} | topic={new_topic} | tags_count={(len(new_tags) if isinstance(new_tags,list) else 0)}"
            )

            if new_conf in ALLOWED_CONFIDENCE:
                self.passive_memory.update_confidence(mem["_id"], new_conf)
                passive_logger.info(
                    f"Updated confidence | id={mem['_id']} | -> {new_conf}"
                )

            if new_topic in ALLOWED_TOPICS:
                self.passive_memory.update_topic(mem["_id"], new_topic)
                passive_logger.info(
                    f"Updated topic | id={mem['_id']} | -> {new_topic}"
                )

            if isinstance(new_tags, list):
                self.passive_memory.update_tags(mem["_id"], new_tags[:5])
                passive_logger.info(
                    f"Updated tags | id={mem['_id']} | count={len(new_tags[:5])}"
                )

    # ==================================================
    # FILTER
    # ==================================================

    def _is_store_worthy(self, fact: str) -> bool:
        fact_l = fact.lower()

        banned = [
            "here are", "extracted", "does not have", "doesn't have",
            "is being addressed", "no information", "unknown",
            "the person", "no user name is mentioned", "user name is unknown",
            "there is no mentioned user name", "the text does not contain any explicit facts",
            "name is not explicitly stated", "not explicitly stated", "no explicit",
        ]

        if any(b in fact_l for b in banned):
            return False

        if len(fact.split()) < 3:
            return False

        return True

    def _should_attempt_extraction(self, text: str, origin: str) -> bool:
        if not text or len(text.strip()) < 3:
            return False

        # Simple keyword triggers; cheap pre-filter before hitting LLM
        triggers = [
            "my name is", "call me", "remember", "i like", "i prefer",
            "from now on", "i'm from", "i am from", "birthday", "project",
            "you will be called", "your name is", "refer to you as"
        ]

        text_l = text.lower()
        if any(t in text_l for t in triggers):
            return True

        # For now, only auto-extract on user side when no trigger if text is long enough
        return origin == "user" and len(text.split()) >= 6
