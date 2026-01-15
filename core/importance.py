"""Importance Calculator for Mirage Memory System."""

import re
from typing import Dict, List, Set


# Intention words that boost importance
INTENTION_WORDS: Set[str] = {
	"build", "create", "plan", "want", "need", "will", "going",
	"project", "future", "goal", "dream", "hope", "promise",
	"focus", "important", "must", "should",
}

# Emotion words that boost importance
EMOTION_BOOST_WORDS: Set[str] = {
	"love", "hate", "amazing", "terrible", "best", "worst",
	"excited", "angry", "sad", "happy", "crazy", "incredible",
}


def calculate_importance(
	text: str,
	concepts: List[str],
	emotions: List[str],
	concept_history: Dict[str, int],
	context_concepts: List[str]
) -> float:
	"""
	Calculate importance score (0.0 - 1.0).
	
	Factors:
	- Novelty: New concepts = higher
	- Relevance: Overlap with context = higher
	- Intention: Future plans, goals = higher
	- Emotion: Strong emotions = higher
	"""
	
	# 1. Novelty (new concepts = high)
	if concepts:
		novelty_scores = []
		for c in concepts:
			freq = concept_history.get(c, 0)
			novelty_scores.append(1.0 / (1 + freq))
		novelty = sum(novelty_scores) / len(novelty_scores)
	else:
		novelty = 0.2
	
	# 2. Relevance (overlap with context)
	if concepts and context_concepts:
		overlap = len(set(concepts) & set(context_concepts))
		relevance = min(1.0, overlap * 0.3 + 0.2)
	else:
		relevance = 0.2
	
	# 3. Intention (future plans, goals)
	text_lower = text.lower()
	words = set(re.findall(r'\b\w+\b', text_lower))
	intention_count = len(words & INTENTION_WORDS)
	intention = min(1.0, intention_count * 0.25)
	
	# 4. Emotion boost
	emotion_count = len(words & EMOTION_BOOST_WORDS)
	emotion_boost = min(0.5, emotion_count * 0.15)
	
	# Non-neutral emotions also boost
	if emotions and "neutral" not in emotions:
		emotion_boost += 0.2
	
	# Weighted sum
	raw = (
		0.25 * novelty +
		0.20 * relevance +
		0.30 * intention +
		0.25 * emotion_boost
	)
	
	# Base + scaled
	importance = 0.1 + raw * 0.8
	
	return round(max(0.05, min(1.0, importance)), 2)
