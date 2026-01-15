"""Memory Store v3 for Mirage Memory System.

Uses semantic similarity for linking instead of exact word matching.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from core.memory_node import MemoryNode, create_timestamp
from core.concept_extraction import extract_concepts_enhanced, ExtractionResult, semantic_similarity
from core.importance import calculate_importance


class MemoryStore:
	"""
	Central memory store for Mirage v3.
	Uses semantic similarity for intelligent linking.
	"""
	
	# Thresholds
	CONTEXT_WINDOW = 10
	MIN_SEMANTIC_SIMILARITY = 0.5  # Minimum similarity to consider linking
	MIN_LINK_SCORE = 2.0  # Minimum total score to create a link
	
	def __init__(self, storage_path: Optional[str] = None):
		"""Initialize the memory store."""
		self.nodes: Dict[int, MemoryNode] = {}
		self.concept_index: Dict[str, Set[int]] = {}
		self.concept_frequency: Dict[str, int] = {}
		self.topic_index: Dict[str, Set[int]] = {}
		self.people_index: Dict[str, Set[int]] = {}  # person -> node IDs
		self.next_id: int = 1
		self.storage_path = storage_path
		
		# Conversation context
		self.context_concepts: List[str] = []
		self.context_topics: List[str] = []
		self.context_people: List[str] = []
		
		# Cache for extraction results (for semantic similarity)
		self.node_extractions: Dict[int, ExtractionResult] = {}
		
		# Load existing memories
		if storage_path:
			self._load()
	
	def add(self, text: str) -> Tuple[MemoryNode, ExtractionResult]:
		"""Add a new memory from text."""
		# Extract concepts
		extraction = extract_concepts_enhanced(text)
		concepts = [c.text for c in extraction.concepts]
		topics = extraction.topics
		people = extraction.people
		
		# Calculate importance
		importance = calculate_importance(
			text=text,
			concepts=concepts,
			topics=topics,
			people=people,
			concept_history=self.concept_frequency,
			context_concepts=self.context_concepts,
			context_topics=self.context_topics
		)
		
		# Create node
		node = MemoryNode(
			id=self.next_id,
			text=text,
			timestamp=create_timestamp(),
			concepts=concepts,
			importance=importance,
			links=[]
		)
		
		# Calculate semantic links
		node.links = self._calculate_semantic_links(extraction, node.id)
		
		# Store node and extraction
		self.nodes[node.id] = node
		self.node_extractions[node.id] = extraction
		self.next_id += 1
		
		# Update indices
		self._update_indices(node, topics, people)
		
		# Update context
		self._update_context(concepts, topics, people)
		
		# Bidirectional links
		self._update_bidirectional_links(node)
		
		# Save
		if self.storage_path:
			self._save()
		
		return node, extraction
	
	def _calculate_semantic_links(
		self,
		current_extraction: ExtractionResult,
		current_id: int
	) -> List[int]:
		"""
		Calculate links using semantic similarity.
		
		Scoring:
		- Same topic: +3.0
		- Shared person: +4.0 (people are very important)
		- Semantic similarity of concepts: +similarity * 2.0
		- Recent node bonus: +0.5 (decaying)
		"""
		if not self.nodes:
			return []
		
		candidates: Dict[int, float] = {}
		current_topics = set(current_extraction.topics)
		current_people = set(current_extraction.people)
		current_concepts = [c.text for c in current_extraction.concepts]
		
		for node_id, node in self.nodes.items():
			if node_id == current_id:
				continue
			
			score = 0.0
			
			# 1. Topic overlap (+3.0 per topic)
			if node_id in self.node_extractions:
				other_topics = set(self.node_extractions[node_id].topics)
				topic_overlap = len(current_topics & other_topics)
				score += topic_overlap * 3.0
			else:
				# Check topic index
				for topic in current_topics:
					if topic in self.topic_index and node_id in self.topic_index[topic]:
						score += 3.0
			
			# 2. Shared people (+4.0 per person - most important!)
			for person in current_people:
				if person in self.people_index and node_id in self.people_index[person]:
					score += 4.0
			
			# 3. Semantic similarity of concepts
			for current_concept in current_concepts:
				for node_concept in node.concepts:
					# Use semantic similarity instead of exact matching
					sim = semantic_similarity(current_concept, node_concept)
					if sim >= self.MIN_SEMANTIC_SIMILARITY:
						score += sim * 2.0
			
			# 4. Recency bonus (recent nodes more likely to be connected)
			recency_order = sorted(self.nodes.keys(), reverse=True)
			try:
				recency_idx = recency_order.index(node_id)
				if recency_idx < self.CONTEXT_WINDOW:
					recency_bonus = 0.5 * (1 - recency_idx / self.CONTEXT_WINDOW)
					score += recency_bonus
			except ValueError:
				pass
			
			if score >= self.MIN_LINK_SCORE:
				candidates[node_id] = score
		
		# Sort by score, take top 5
		sorted_candidates = sorted(candidates.items(), key=lambda x: -x[1])
		return [nid for nid, _ in sorted_candidates[:5]]
	
	def _update_indices(
		self,
		node: MemoryNode,
		topics: List[str],
		people: List[str]
	) -> None:
		"""Update all indices."""
		# Concept index
		for concept in node.concepts:
			if concept not in self.concept_index:
				self.concept_index[concept] = set()
			self.concept_index[concept].add(node.id)
			self.concept_frequency[concept] = self.concept_frequency.get(concept, 0) + 1
		
		# Topic index
		for topic in topics:
			if topic not in self.topic_index:
				self.topic_index[topic] = set()
			self.topic_index[topic].add(node.id)
		
		# People index
		for person in people:
			if person not in self.people_index:
				self.people_index[person] = set()
			self.people_index[person].add(node.id)
	
	def _update_context(
		self,
		concepts: List[str],
		topics: List[str],
		people: List[str]
	) -> None:
		"""Update conversation context."""
		self.context_concepts = (concepts + self.context_concepts)[:20]
		self.context_topics = list(set(topics) | set(self.context_topics[:5]))[:5]
		self.context_people = list(set(people) | set(self.context_people[:10]))[:10]
	
	def _update_bidirectional_links(self, new_node: MemoryNode) -> None:
		"""Update linked nodes to link back."""
		for linked_id in new_node.links:
			if linked_id in self.nodes:
				linked_node = self.nodes[linked_id]
				if new_node.id not in linked_node.links:
					linked_node.links.append(new_node.id)
					if len(linked_node.links) > 5:
						linked_node.links = linked_node.links[-5:]
	
	def search(self, query: str) -> List[MemoryNode]:
		"""Search using semantic similarity."""
		results: List[Tuple[MemoryNode, float]] = []
		query_lower = query.lower().strip()
		
		for node in self.nodes.values():
			score = 0.0
			
			# Check topics
			if node.id in self.node_extractions:
				if query_lower in self.node_extractions[node.id].topics:
					score += 2.0
			
			# Check concepts with semantic similarity
			for concept in node.concepts:
				if query_lower in concept:
					score += 1.5  # Exact substring match
				else:
					sim = semantic_similarity(query_lower, concept)
					if sim >= 0.4:
						score += sim
			
			# Check people
			if query_lower in [p.lower() for p in self.context_people]:
				if node.id in self.people_index.get(query_lower, set()):
					score += 2.0
			
			# Text search
			if query_lower in node.text.lower():
				score += 0.5
			
			if score > 0:
				results.append((node, score))
		
		# Sort by score
		results.sort(key=lambda x: -x[1])
		return [node for node, _ in results]
	
	def get_node(self, node_id: int) -> Optional[MemoryNode]:
		"""Get a specific node."""
		return self.nodes.get(node_id)
	
	def get_all_nodes(self) -> List[MemoryNode]:
		"""Get all nodes sorted by ID."""
		return [self.nodes[i] for i in sorted(self.nodes.keys())]
	
	def get_stats(self) -> Dict:
		"""Get memory statistics."""
		return {
			"total_nodes": len(self.nodes),
			"total_concepts": len(self.concept_index),
			"total_topics": len(self.topic_index),
			"topics": list(self.topic_index.keys()),
			"people": list(self.people_index.keys()),
			"top_concepts": sorted(
				self.concept_frequency.items(),
				key=lambda x: -x[1]
			)[:10],
			"context_topics": self.context_topics,
		}
	
	def clear(self) -> None:
		"""Clear all memories."""
		self.nodes.clear()
		self.concept_index.clear()
		self.concept_frequency.clear()
		self.topic_index.clear()
		self.people_index.clear()
		self.node_extractions.clear()
		self.next_id = 1
		self.context_concepts = []
		self.context_topics = []
		self.context_people = []
		
		if self.storage_path and Path(self.storage_path).exists():
			Path(self.storage_path).unlink()
	
	def _save(self) -> None:
		"""Save to file."""
		if not self.storage_path:
			return
		
		data = {
			"next_id": self.next_id,
			"nodes": [node.to_dict() for node in self.nodes.values()],
			"concept_frequency": self.concept_frequency,
			"topic_index": {k: list(v) for k, v in self.topic_index.items()},
			"people_index": {k: list(v) for k, v in self.people_index.items()},
			"context_topics": self.context_topics,
			"context_people": self.context_people,
		}
		
		Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
		with open(self.storage_path, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent=2, ensure_ascii=False)
	
	def _load(self) -> None:
		"""Load from file."""
		if not self.storage_path or not Path(self.storage_path).exists():
			return
		
		try:
			with open(self.storage_path, 'r', encoding='utf-8') as f:
				data = json.load(f)
			
			self.next_id = data.get("next_id", 1)
			self.concept_frequency = data.get("concept_frequency", {})
			self.context_topics = data.get("context_topics", [])
			self.context_people = data.get("context_people", [])
			
			# Rebuild topic index
			for topic, nids in data.get("topic_index", {}).items():
				self.topic_index[topic] = set(nids)
			
			# Rebuild people index
			for person, nids in data.get("people_index", {}).items():
				self.people_index[person] = set(nids)
			
			# Load nodes
			for node_dict in data.get("nodes", []):
				node = MemoryNode.from_dict(node_dict)
				self.nodes[node.id] = node
				
				# Rebuild concept index
				for concept in node.concepts:
					if concept not in self.concept_index:
						self.concept_index[concept] = set()
					self.concept_index[concept].add(node.id)
					
		except Exception as e:
			print(f"Warning: Could not load memories: {e}")
