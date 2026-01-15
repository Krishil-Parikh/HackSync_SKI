"""Simplified Concept Extraction for Mirage Memory System.

Pure NLP - no hardcoded lists.
Uses spaCy for:
- Named entities (any type)
- Noun phrases (cleaned)
- Emotions (keyword-based)

Requires: pip install spacy && python -m spacy download en_core_web_sm
"""

import re
from typing import Dict, List, Set
from dataclasses import dataclass

import spacy

# Load spaCy
try:
	_nlp = spacy.load("en_core_web_sm")
except OSError:
	raise OSError(
		"spaCy model not found. Run: python -m spacy download en_core_web_sm"
	)


# ─────────────────────────────────────────────────────────────────────────────
# Emotion Detection (Simple Keyword-Based)
# ─────────────────────────────────────────────────────────────────────────────

EMOTION_KEYWORDS: Dict[str, List[str]] = {
	"excitement": ["amazing", "awesome", "crazy", "incredible", "wow", "!"],
	"happiness": ["happy", "love", "great", "best", "wonderful", "glad"],
	"sadness": ["sad", "sorry", "unfortunately", "miss", "lost", "down"],
	"anger": ["angry", "hate", "frustrated", "annoyed", "mad"],
	"surprise": ["surprised", "shocked", "unexpected", "suddenly"],
	"focus": ["focus", "concentrate", "important", "need", "must", "should"],
}


def detect_emotions(text: str) -> List[str]:
	"""Detect emotions from text using keywords."""
	text_lower = text.lower()
	detected = []
	
	for emotion, keywords in EMOTION_KEYWORDS.items():
		for keyword in keywords:
			if keyword in text_lower:
				detected.append(emotion)
				break
	
	return detected if detected else ["neutral"]


# ─────────────────────────────────────────────────────────────────────────────
# Garbage Filters (Minimal)
# ─────────────────────────────────────────────────────────────────────────────

STOP_WORDS: Set[str] = {
	# Greetings
	"hi", "hii", "hello", "hey", "bye", "ok", "okay", "yeah", "yup", "nah",
	# Fillers
	"bro", "dude", "like", "just", "basically", "actually", "um", "uh",
	# Function words
	"the", "a", "an", "is", "are", "was", "were", "be", "been",
	"i", "you", "he", "she", "it", "we", "they", "my", "your",
	"what", "who", "where", "when", "why", "how",
	"and", "but", "or", "so", "to", "for", "of", "with", "in", "on",
}


def is_meaningful(text: str) -> bool:
	"""Check if text is meaningful (not just stop words)."""
	words = text.lower().split()
	meaningful_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
	return len(meaningful_words) > 0


def clean_phrase(phrase: str) -> str:
	"""Clean a phrase by removing leading/trailing stop words."""
	words = phrase.lower().split()
	
	# Strip from front
	while words and words[0] in STOP_WORDS:
		words.pop(0)
	
	# Strip from back
	while words and words[-1] in STOP_WORDS:
		words.pop()
	
	return " ".join(words)


# ─────────────────────────────────────────────────────────────────────────────
# Main Extraction
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ExtractionResult:
	"""Result of concept extraction."""
	concepts: List[str]
	emotions: List[str]
	people: List[str]


def extract(text: str) -> ExtractionResult:
	"""
	Extract concepts, emotions, and people from text.
	Uses pure NLP - no hardcoded lists.
	"""
	doc = _nlp(text)
	
	concepts: List[str] = []
	people: List[str] = []
	seen: Set[str] = set()
	
	# 1. Named Entities (spaCy detects them automatically)
	for ent in doc.ents:
		cleaned = ent.text.lower().strip()
		if cleaned not in seen and is_meaningful(cleaned):
			concepts.append(cleaned)
			seen.add(cleaned)
			
			# Track people separately
			if ent.label_ == "PERSON":
				people.append(cleaned)
	
	# 2. Noun Phrases
	for chunk in doc.noun_chunks:
		cleaned = clean_phrase(chunk.text)
		if cleaned and cleaned not in seen and is_meaningful(cleaned):
			concepts.append(cleaned)
			seen.add(cleaned)
	
	# 3. Proper nouns that might be names (not caught by NER)
	for token in doc:
		if token.pos_ == "PROPN":
			word = token.text.lower()
			if word not in seen and len(word) > 2 and word not in STOP_WORDS:
				concepts.append(word)
				people.append(word)
				seen.add(word)
	
	# 4. Emotions
	emotions = detect_emotions(text)
	
	return ExtractionResult(
		concepts=concepts,
		emotions=emotions,
		people=people
	)


def semantic_similarity(text1: str, text2: str) -> float:
	"""Calculate semantic similarity between two texts."""
	doc1 = _nlp(text1)
	doc2 = _nlp(text2)
	
	if doc1.has_vector and doc2.has_vector:
		return doc1.similarity(doc2)
	return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
	examples = [
		"Hello Jainam!",
		"The hackathon is crazy bro",
		"Hey did you see yesterday's match? Madrid won!",
		"I love Virat Kohli, he's the best cricket player",
		"Liverpool is down this season, so sad",
		"Let's focus on the project guys",
	]
	
	print("=" * 50)
	print("SIMPLIFIED CONCEPT EXTRACTION")
	print("=" * 50)
	
	for text in examples:
		result = extract(text)
		print(f"\n📝 \"{text}\"")
		print(f"   Concepts: {result.concepts}")
		print(f"   Emotions: {result.emotions}")
		if result.people:
			print(f"   People: {result.people}")