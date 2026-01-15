"""Mirage Memory - Human-Like 3-Tier Memory System.

Architecture:
- Active Memory: 7 nodes (current working memory)
- Passive Memory: 50 nodes (short-term memory)
- Super Passive: Unlimited (long-term permanent storage)

Key Features:
- Interaction-based demotion (least-used nodes demote first)
- Memory strength traversal with randomness
- Graph-based link following for associative recall
- Nodes promoted from deeper tiers gain importance boost
"""

import json
import random
import warnings
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime

from core.memory_node import MemoryNode, create_timestamp
from core.concept_extraction import extract, semantic_similarity
from core.importance import calculate_importance

# Suppress spaCy warnings about word vectors
warnings.filterwarnings("ignore", message=".*W007.*")


class MirageMemory:
    """
    Human-Like 3-Tier Memory System.
    
    Active → Passive → Super Passive
    
    Demotion: Least interacted nodes move down first.
    Recall: Memory strength traversal with graph walking.
    """
    
    # Tier sizes
    ACTIVE_SIZE = 7
    PASSIVE_SIZE = 50
    
    # Memory strength defaults
    DEFAULT_MEMORY_STRENGTH = 10
    RANDOMNESS_VARIANCE = 0.25  # ±25% variance for human-like behavior
    
    # Link traversal
    MAX_LINK_DEPTH = 2
    
    def __init__(self, storage_path: str = "mirage_memory.json"):
        # Memory tiers (using list for Active to allow removal from middle)
        self.active: List[MemoryNode] = []
        self.passive: List[MemoryNode] = []
        self.super_passive: List[MemoryNode] = []
        
        # Indices for fast lookup
        self.all_nodes: Dict[int, MemoryNode] = {}
        self.concept_index: Dict[str, Set[int]] = {}
        self.concept_frequency: Dict[str, int] = {}
        
        # Interaction tracking (stored separately to not modify node structure)
        # Maps node_id -> interaction data
        self.interactions: Dict[int, Dict] = {}
        
        # Context
        self.context_concepts: List[str] = []
        self.next_id = 1
        self.storage_path = storage_path
        
        # Load existing memories
        self._load()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Interaction Tracking
    # ─────────────────────────────────────────────────────────────────────────
    
    def _init_interaction(self, node_id: int) -> None:
        """Initialize interaction data for a node."""
        if node_id not in self.interactions:
            self.interactions[node_id] = {
                "count": 0,
                "last_time": create_timestamp(),
                "promotion_count": 0,
            }
    
    def _record_interaction(self, node_id: int) -> None:
        """Record an interaction with a node."""
        self._init_interaction(node_id)
        self.interactions[node_id]["count"] += 1
        self.interactions[node_id]["last_time"] = create_timestamp()
    
    def _record_promotion(self, node_id: int) -> None:
        """Record that a node was promoted from a deeper tier."""
        self._init_interaction(node_id)
        self.interactions[node_id]["promotion_count"] += 1
        self.interactions[node_id]["count"] += 2  # Promotion is a strong interaction
    
    def _get_interaction_score(self, node: MemoryNode) -> float:
        """
        Calculate interaction score for demotion ranking.
        Lower score = more likely to be demoted.
        
        Fixes:
        - Link bonus is capped at 1.0 (prevents permanent stickiness)
        - Recency bonus for newer nodes (based on node ID)
        """
        self._init_interaction(node.id)
        data = self.interactions[node.id]
        
        score = data["count"]
        score += data["promotion_count"] * 2  # Promoted nodes are valuable
        score += node.importance * 2  # Importance matters
        
        # Link bonus - CAPPED at max 1.0 to prevent permanent stickiness
        link_bonus = min(len(node.links) * 0.3, 1.0)
        score += link_bonus
        
        # Recency bonus - newer nodes (higher ID) get slight advantage
        recency = node.id / self.next_id if self.next_id > 0 else 0
        score += recency * 0.5
        
        return score
    
    # ─────────────────────────────────────────────────────────────────────────
    # Core Operations
    # ─────────────────────────────────────────────────────────────────────────
    
    def add(self, text: str) -> MemoryNode:
        """Add a new memory. Goes to Active first."""
        
        # Extract concepts and emotions
        extraction = extract(text)
        
        # Calculate importance
        importance = calculate_importance(
            text=text,
            concepts=extraction.concepts,
            emotions=extraction.emotions,
            concept_history=self.concept_frequency,
            context_concepts=self.context_concepts
        )
        
        # Create node
        node = MemoryNode(
            id=self.next_id,
            text=text,
            timestamp=create_timestamp(),
            concepts=extraction.concepts,
            emotions=extraction.emotions,
            importance=importance,
            links=[],
            tier="active"
        )
        
        # Calculate links
        node.links = self._calculate_links(node)
        
        # Handle Active overflow - demote LEAST USED
        while len(self.active) >= self.ACTIVE_SIZE:
            self._demote_least_used_active()
        
        # Add to Active
        self.active.append(node)
        self.all_nodes[node.id] = node
        self._init_interaction(node.id)
        self.next_id += 1
        
        # Update indices
        self._update_indices(node)
        
        # Update context
        self.context_concepts = (extraction.concepts + self.context_concepts)[:20]
        
        # Save
        self._save()
        
        return node
    
    def recall(self, query: str, memory_strength: Optional[int] = None) -> Tuple[List[MemoryNode], str]:
        """
        Search for memories using memory strength traversal.
        
        The memory strength determines how deeply we can search:
        - Active costs 1 strength per node checked
        - Passive costs 2 strength per node  
        - Super Passive costs 3 strength per node
        
        Returns (found_nodes, tier_name where first found).
        Promotes found nodes to Active with importance boost.
        """
        if memory_strength is None:
            memory_strength = self.DEFAULT_MEMORY_STRENGTH
        
        # Add randomness for human-like behavior
        variance = random.uniform(1 - self.RANDOMNESS_VARIANCE, 1 + self.RANDOMNESS_VARIANCE)
        effective_strength = int(memory_strength * variance)
        
        # Extract concepts from query
        extraction = extract(query)
        query_concepts = extraction.concepts if extraction.concepts else [query.lower()]
        
        found_tier = "none"
        all_results: List[Tuple[MemoryNode, float, str]] = []  # (node, score, tier)
        
        # Phase 1: Search Active (cost = 1 per node)
        active_budget = min(effective_strength, len(self.active))
        active_results = self._search_tier_with_budget(
            self.active, query_concepts, query, active_budget
        )
        effective_strength -= len(active_results)
        
        if active_results:
            found_tier = "active"
            for node, score in active_results:
                all_results.append((node, score, "active"))
                self._record_interaction(node.id)
        
        # Phase 2: Search Passive (cost = 2 per node)
        if effective_strength >= 2:
            passive_budget = effective_strength // 2
            passive_results = self._search_tier_with_budget(
                self.passive, query_concepts, query, passive_budget
            )
            effective_strength -= len(passive_results) * 2
            
            if passive_results:
                if found_tier == "none":
                    found_tier = "passive"
                for node, score in passive_results:
                    all_results.append((node, score, "passive"))
        
        # Phase 3: Search Super Passive (cost = 3 per node)
        if effective_strength >= 3:
            super_budget = effective_strength // 3
            super_results = self._search_tier_with_budget(
                self.super_passive, query_concepts, query, super_budget
            )
            
            if super_results:
                if found_tier == "none":
                    found_tier = "super_passive"
                for node, score in super_results:
                    all_results.append((node, score, "super_passive"))
        
        if not all_results:
            return [], "none"
        
        # Sort all results by score
        all_results.sort(key=lambda x: -x[1])
        
        # Follow links from top results to find associated memories
        linked_nodes = []
        for node, _, _ in all_results[:3]:
            linked = self._follow_links(node)
            for ln in linked:
                if ln.id not in {n.id for n, _, _ in all_results}:
                    linked_nodes.append(ln)
        
        # Promote non-active nodes to Active
        nodes_to_promote = [
            (node, tier) for node, score, tier in all_results 
            if tier != "active"
        ][:3]  # Max 3 promotions
        
        for node, source_tier in nodes_to_promote:
            self._promote_to_active(node, source_tier)
        
        # Return all found nodes
        result_nodes = [node for node, _, _ in all_results]
        
        self._save()
        return result_nodes, found_tier
    
    # ─────────────────────────────────────────────────────────────────────────
    # Tier Management - Interaction Based
    # ─────────────────────────────────────────────────────────────────────────
    
    def _demote_least_used_active(self) -> None:
        """Move LEAST INTERACTED node from Active to Passive."""
        if not self.active:
            return
        
        # Find node with lowest interaction score
        least_used = min(self.active, key=lambda n: self._get_interaction_score(n))
        
        self.active.remove(least_used)
        least_used.tier = "passive"
        self.passive.append(least_used)
        
        # Check Passive overflow
        while len(self.passive) > self.PASSIVE_SIZE:
            self._demote_least_used_passive()
    
    def _demote_least_used_passive(self) -> None:
        """Move LEAST INTERACTED node from Passive to Super Passive."""
        if not self.passive:
            return
        
        # Find node with lowest interaction score
        least_used = min(self.passive, key=lambda n: self._get_interaction_score(n))
        
        self.passive.remove(least_used)
        least_used.tier = "super_passive"
        self.super_passive.append(least_used)
        # Super Passive is permanent - no further demotion
    
    def _promote_to_active(self, node: MemoryNode, source_tier: str) -> None:
        """
        Promote a node to Active memory.
        Nodes from deeper tiers get importance boost.
        """
        # Remove from current tier
        if node in self.passive:
            self.passive.remove(node)
        elif node in self.super_passive:
            self.super_passive.remove(node)
        else:
            return  # Already in active or not found
        
        # Importance boost based on source tier
        if source_tier == "passive":
            node.importance = min(1.0, node.importance + 0.1)
        elif source_tier == "super_passive":
            node.importance = min(1.0, node.importance + 0.2)
        
        # Record promotion
        self._record_promotion(node.id)
        
        # Handle Active overflow
        while len(self.active) >= self.ACTIVE_SIZE:
            self._demote_least_used_active()
        
        # Add to Active
        node.tier = "active"
        self.active.append(node)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Search & Linking
    # ─────────────────────────────────────────────────────────────────────────
    
    def _search_tier_with_budget(
        self,
        tier: List[MemoryNode],
        query_concepts: List[str],
        raw_query: str,
        budget: int
    ) -> List[Tuple[MemoryNode, float]]:
        """
        Search a tier with a limited budget.
        Returns list of (node, score) pairs.
        """
        results: List[Tuple[MemoryNode, float]] = []
        nodes_checked = 0
        
        # Sort tier by interaction score (most interacted first - more likely to be relevant)
        sorted_tier = sorted(
            tier, 
            key=lambda n: self._get_interaction_score(n), 
            reverse=True
        )
        
        for node in sorted_tier:
            if nodes_checked >= budget:
                break
            
            score = 0.0
            
            # Concept overlap
            node_concepts = set(node.concepts)
            query_set = set(query_concepts)
            overlap = len(node_concepts & query_set)
            score += overlap * 2.0
            
            # Semantic similarity with query
            for qc in query_concepts:
                for nc in node.concepts:
                    sim = semantic_similarity(qc, nc)
                    if sim > 0.5:
                        score += sim
            
            # Text match (fallback)
            if raw_query.lower() in node.text.lower():
                score += 1.5
            
            # Importance boost
            score += node.importance * 0.5
            
            # Interaction boost (frequently accessed = likely relevant)
            interaction_score = self._get_interaction_score(node)
            score += min(interaction_score * 0.1, 1.0)
            
            nodes_checked += 1
            
            if score > 1.0:
                results.append((node, score))
        
        # Sort by score
        results.sort(key=lambda x: -x[1])
        return results[:5]  # Max 5 per tier
    
    def _follow_links(self, start_node: MemoryNode, depth: int = None) -> List[MemoryNode]:
        """
        Traverse the memory graph following links.
        Returns connected nodes up to specified depth.
        This enables associative recall - remembering related things.
        """
        if depth is None:
            depth = self.MAX_LINK_DEPTH
        
        visited = {start_node.id}
        to_visit = [(start_node, 0)]
        results = []
        
        while to_visit:
            node, current_depth = to_visit.pop(0)
            
            if current_depth >= depth:
                continue
            
            for link_id in node.links:
                if link_id not in visited and link_id in self.all_nodes:
                    linked_node = self.all_nodes[link_id]
                    visited.add(link_id)
                    results.append(linked_node)
                    to_visit.append((linked_node, current_depth + 1))
                    
                    # Record that this linked node was accessed
                    self._record_interaction(link_id)
        
        return results
    
    def _calculate_links(self, new_node: MemoryNode) -> List[int]:
        """Calculate links based on shared concepts and semantic similarity."""
        candidates: Dict[int, float] = {}
        
        for node_id, node in self.all_nodes.items():
            if node_id == new_node.id:
                continue
            
            score = 0.0
            
            # Shared concepts
            shared = set(new_node.concepts) & set(node.concepts)
            score += len(shared) * 2.0
            
            # Semantic similarity
            for nc in new_node.concepts:
                for oc in node.concepts:
                    sim = semantic_similarity(nc, oc)
                    if sim > 0.5:
                        score += sim
            
            # Shared emotions
            shared_emotions = set(new_node.emotions) & set(node.emotions)
            if shared_emotions and "neutral" not in shared_emotions:
                score += len(shared_emotions)
            
            # Tier bonus (linking to active nodes is more relevant)
            if node.tier == "active":
                score += 0.5
            
            if score > 1.5:
                candidates[node_id] = score
        
        # Top 5 links
        sorted_links = sorted(candidates.items(), key=lambda x: -x[1])
        return [nid for nid, _ in sorted_links[:5]]
    
    def _update_indices(self, node: MemoryNode) -> None:
        """Update concept index."""
        for concept in node.concepts:
            if concept not in self.concept_index:
                self.concept_index[concept] = set()
            self.concept_index[concept].add(node.id)
            self.concept_frequency[concept] = self.concept_frequency.get(concept, 0) + 1
    
    # ─────────────────────────────────────────────────────────────────────────
    # Graph Visualization
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_graph_data(self) -> Dict:
        """Get data for graph visualization."""
        nodes = []
        edges = []
        
        # Collect all nodes with tier info
        for node in self.active + self.passive + self.super_passive:
            interaction_data = self.interactions.get(node.id, {"count": 0, "promotion_count": 0})
            nodes.append({
                "id": node.id,
                "text": node.text[:30] + "..." if len(node.text) > 30 else node.text,
                "concepts": node.concepts,
                "tier": node.tier,
                "importance": node.importance,
                "interactions": interaction_data["count"],
                "promotions": interaction_data["promotion_count"],
            })
            
            # Collect edges
            for link_id in node.links:
                if link_id in self.all_nodes:
                    linked_node = self.all_nodes[link_id]
                    shared = set(node.concepts) & set(linked_node.concepts)
                    edges.append({
                        "from": node.id,
                        "to": link_id,
                        "reason": list(shared) if shared else ["semantic"],
                    })
        
        return {"nodes": nodes, "edges": edges}
    
    def visualize_graph_text(self) -> str:
        """Generate ASCII visualization of the memory graph."""
        lines = []
        lines.append("=" * 60)
        lines.append("MIRAGE MEMORY GRAPH - Human-Like Memory System")
        lines.append("=" * 60)
        
        # Group by tier
        tiers = {
            "ACTIVE": self.active,
            "PASSIVE": self.passive,
            "SUPER_PASSIVE": self.super_passive,
        }
        
        for tier_name, nodes in tiers.items():
            if not nodes:
                continue
            
            max_size = self.ACTIVE_SIZE if tier_name == "ACTIVE" else (
                self.PASSIVE_SIZE if tier_name == "PASSIVE" else "∞"
            )
            lines.append(f"\n📦 {tier_name} ({len(nodes)}/{max_size} nodes)")
            lines.append("-" * 40)
            
            for node in nodes:
                # Node info
                text_short = node.text[:35] + "..." if len(node.text) > 35 else node.text
                interaction_data = self.interactions.get(node.id, {"count": 0})
                lines.append(f"  [{node.id}] {text_short}")
                lines.append(f"      concepts: {node.concepts}")
                lines.append(f"      imp: {node.importance:.2f} | interactions: {interaction_data['count']}")
                
                # Links
                if node.links:
                    for link_id in node.links:
                        if link_id in self.all_nodes:
                            linked = self.all_nodes[link_id]
                            shared = set(node.concepts) & set(linked.concepts)
                            reason = list(shared)[:2] if shared else ["similar"]
                            lines.append(f"      └─→ [{link_id}] (via {reason})")
        
        return "\n".join(lines)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Stats & Utilities
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        return {
            "active_count": len(self.active),
            "passive_count": len(self.passive),
            "super_passive_count": len(self.super_passive),
            "total_nodes": len(self.all_nodes),
            "total_concepts": len(self.concept_index),
            "active_max": self.ACTIVE_SIZE,
            "passive_max": self.PASSIVE_SIZE,
        }
    
    def get_tier_nodes(self, tier: str) -> List[MemoryNode]:
        """Get nodes from a specific tier."""
        if tier == "active":
            return list(self.active)
        elif tier == "passive":
            return list(self.passive)
        elif tier == "super_passive":
            return list(self.super_passive)
        return []
    
    def clear(self) -> None:
        """Clear all memories."""
        self.active.clear()
        self.passive.clear()
        self.super_passive.clear()
        self.all_nodes.clear()
        self.concept_index.clear()
        self.concept_frequency.clear()
        self.interactions.clear()
        self.context_concepts = []
        self.next_id = 1
        
        if Path(self.storage_path).exists():
            Path(self.storage_path).unlink()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────────────────────────────────────
    
    def _save(self) -> None:
        """Save all tiers to file."""
        data = {
            "next_id": self.next_id,
            "active": [n.to_dict() for n in self.active],
            "passive": [n.to_dict() for n in self.passive],
            "super_passive": [n.to_dict() for n in self.super_passive],
            "concept_frequency": self.concept_frequency,
            "context_concepts": self.context_concepts,
            "interactions": self.interactions,  # NEW: Save interaction data
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load(self) -> None:
        """Load memories from file."""
        if not Path(self.storage_path).exists():
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.next_id = data.get("next_id", 1)
            self.concept_frequency = data.get("concept_frequency", {})
            self.context_concepts = data.get("context_concepts", [])
            self.interactions = data.get("interactions", {})
            
            # Convert string keys back to int (JSON converts int keys to strings)
            self.interactions = {int(k): v for k, v in self.interactions.items()}
            
            # Load nodes into tiers
            for node_dict in data.get("active", []):
                node = MemoryNode.from_dict(node_dict)
                self.active.append(node)
                self.all_nodes[node.id] = node
                self._rebuild_index(node)
            
            for node_dict in data.get("passive", []):
                node = MemoryNode.from_dict(node_dict)
                self.passive.append(node)
                self.all_nodes[node.id] = node
                self._rebuild_index(node)
            
            for node_dict in data.get("super_passive", []):
                node = MemoryNode.from_dict(node_dict)
                self.super_passive.append(node)
                self.all_nodes[node.id] = node
                self._rebuild_index(node)
                
        except Exception as e:
            print(f"Warning: Could not load memories: {e}")
    
    def _rebuild_index(self, node: MemoryNode) -> None:
        """Rebuild concept index for a node."""
        for concept in node.concepts:
            if concept not in self.concept_index:
                self.concept_index[concept] = set()
            self.concept_index[concept].add(node.id)
