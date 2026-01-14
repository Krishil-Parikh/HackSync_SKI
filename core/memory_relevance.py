import numpy as np
from ollama.client import ollama_embed
from core.db import passive_memory_collection
from config import trace_logger, passive_logger


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0

    return float(
        np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    )


class PassiveMemoryRelevanceMatcher:
    """
    Finds relevant passive memories using cosine similarity.
    """

    def __init__(self, max_results=3, threshold=0.75):
        self.max_results = max_results
        self.threshold = threshold

    def find_relevant(self, query_text: str):
        trace_logger.info("Finding relevant passive memory")

        query_embedding = ollama_embed(query_text)

        cursor = passive_memory_collection.find(
            {"status": "active"}
        )

        scored = []

        for mem in cursor:
            emb = mem.get("embedding")
            if not emb:
                continue

            score = cosine_similarity(query_embedding, emb)

            if score >= self.threshold:
                scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = [mem for _, mem in scored[:self.max_results]]

        trace_logger.info(
            f"Relevant passive memories found | count={len(results)}"
        )

        try:
            previews = [
                (round(s, 3), m.get("topic", "unknown"), (m.get("fact", "")[:80]).replace("\n", " "))
                for s, m in scored[:self.max_results]
            ]
            passive_logger.info(
                f"Relevance results | threshold={self.threshold} | selected={len(results)} | top={previews}"
            )
        except Exception:
            pass

        return results
