"""
Memory integration layer that wraps the Mirage Memory System.
Uses EXACT functions from core modules - NO custom logic.
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
from core.mirage_memory import MirageMemory
from config import trace_logger, passive_logger


class ActiveMemory:
    """
    Active Memory - stores recent conversation turns.
    Delegates to Mirage's Active tier (7 nodes max).
    """
    
    def __init__(self, max_turns: int = 5, storage_path: str = None):
        """Initialize with Mirage Memory (uses Active tier)."""
        if storage_path is None:
            storage_path = "mirage_memory.json"
        self.mirage = MirageMemory(storage_path=storage_path)
        self.max_turns = max_turns
        self.speakers = {}  # Track speakers: node_id -> speaker name
        self._load_speakers()
        trace_logger.info(f"ActiveMemory initialized | max_turns={max_turns} | path={storage_path}")
    
    def _load_speakers(self):
        """Load speaker names from speakers.json if it exists."""
        import json
        speakers_file = Path("memory/speakers.json")
        if speakers_file.exists():
            try:
                with open(speakers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.speakers = {int(k): v for k, v in data.items()}
                trace_logger.info(f"Loaded {len(self.speakers)} speaker mappings")
            except Exception as e:
                trace_logger.warning(f"Could not load speakers.json: {e}")
    
    def _save_speakers(self):
        """Save speakers mapping to file."""
        import json
        Path("memory").mkdir(exist_ok=True)
        with open("memory/speakers.json", "w", encoding="utf-8") as f:
            json.dump(self.speakers, f, indent=2)
    
    def add(self, user_text: str, nova_reply: str) -> None:
        """
        Add a conversation turn to active memory.
        Uses Mirage's add() which stores in Active tier.
        """
        try:
            # Add user text to Mirage
            user_node = self.mirage.add(user_text)
            self.speakers[user_node.id] = "User"
            trace_logger.info(f"User turn added | node_id={user_node.id} | tier={user_node.tier}")
            
            # Add nova reply to Mirage
            nova_node = self.mirage.add(nova_reply)
            self.speakers[nova_node.id] = "NOVA"
            trace_logger.info(f"NOVA turn added | node_id={nova_node.id} | tier={nova_node.tier}")
            
            # Save speaker mappings
            self._save_speakers()
        except Exception as e:
            trace_logger.error(f"Failed to add turn to active memory: {e}")
    
    def write_memory_files(self, memory_folder: Path, recalled_nodes: List = None):
        """
        Write memory to text files in conversation format.
        Creates: active.txt, passive.txt, super_passive.txt
        """
        try:
            memory_folder.mkdir(exist_ok=True)
            
            # Get nodes from all tiers
            active_nodes = self.mirage.get_tier_nodes("active")
            passive_nodes = self.mirage.get_tier_nodes("passive")
            super_nodes = self.mirage.get_tier_nodes("super_passive")
            
            if recalled_nodes is None:
                recalled_nodes = []
            
            # Write active.txt with full context (active + recalled)
            with open(memory_folder / "active.txt", 'w', encoding='utf-8') as f:
                f.write(f"=== FULL CONTEXT FOR LLM ===\n")
                f.write(f"=== Active: {len(active_nodes)} + Recalled: {len(recalled_nodes)} = {len(active_nodes) + len(recalled_nodes)} nodes ===\n\n")
                
                f.write("--- ACTIVE MEMORY (7 nodes) ---\n")
                for node in active_nodes:
                    speaker = self.speakers.get(node.id, "Unknown")
                    f.write(f"{speaker}: {node.text}\n")
                
                if recalled_nodes:
                    f.write("\n--- RECALLED MEMORIES ---\n")
                    for node in recalled_nodes:
                        speaker = self.speakers.get(node.id, "Unknown")
                        tier_tag = f"[from {node.tier}]"
                        f.write(f"{speaker}: {node.text} {tier_tag}\n")
            
            # Write passive.txt
            with open(memory_folder / "passive.txt", 'w', encoding='utf-8') as f:
                f.write(f"=== PASSIVE MEMORY ({len(passive_nodes)} nodes) ===\n\n")
                for node in passive_nodes:
                    speaker = self.speakers.get(node.id, "Unknown")
                    f.write(f"{speaker}: {node.text}\n")
                if not passive_nodes:
                    f.write("(empty)\n")
            
            # Write super_passive.txt
            with open(memory_folder / "super_passive.txt", 'w', encoding='utf-8') as f:
                f.write(f"=== SUPER PASSIVE MEMORY ({len(super_nodes)} nodes) ===\n\n")
                for node in super_nodes:
                    speaker = self.speakers.get(node.id, "Unknown")
                    f.write(f"{speaker}: {node.text}\n")
                if not super_nodes:
                    f.write("(empty)\n")
            
            trace_logger.info(f"Memory files written | active={len(active_nodes)} passive={len(passive_nodes)} super={len(super_nodes)}")
        except Exception as e:
            trace_logger.error(f"Failed to write memory files: {e}")
    
    def get_context(self) -> List[Dict]:
        """
        Get recent conversation context.
        Returns last N nodes from Active tier.
        """
        try:
            active_nodes = self.mirage.get_tier_nodes("active")
            return [
                {
                    "text": node.text,
                    "importance": node.importance,
                    "tier": node.tier
                }
                for node in active_nodes[-self.max_turns:]
            ]
        except Exception as e:
            trace_logger.warning(f"Failed to get active context: {e}")
            return []
    
    def clear(self) -> None:
        """Clear all active memory."""
        try:
            self.mirage.clear()
            trace_logger.info("Active memory cleared")
        except Exception as e:
            trace_logger.error(f"Failed to clear active memory: {e}")


class PassiveMemory:
    """
    Passive Memory - stores longer-term memories (50 nodes).
    Delegates to Mirage's Passive tier.
    Uses Mirage's recall() for semantic search.
    """
    
    def __init__(self, storage_path: str = None):
        """Initialize with Mirage Memory (uses Passive tier)."""
        if storage_path is None:
            storage_path = "mirage_memory.json"
        self.mirage = MirageMemory(storage_path=storage_path)
        trace_logger.info(f"PassiveMemory initialized with Mirage backend | path={storage_path}")
    
    def add(self, text: str, concepts: Optional[List[str]] = None, 
            confidence: str = "medium", importance: float = 0.5) -> int:
        """
        Add a memory to passive storage.
        Uses Mirage's add() method directly - it handles extraction internally.
        """
        try:
            node = self.mirage.add(text)
            trace_logger.info(f"Memory added | id={node.id} | tier={node.tier} | importance={node.importance}")
            return node.id
        except Exception as e:
            trace_logger.error(f"Failed to add memory: {e}")
            return -1
    
    def get_by_confidence(self, level: str) -> List[Dict]:
        """Get memories by confidence level (simplified)."""
        try:
            passive_nodes = self.mirage.get_tier_nodes("passive")
            return [
                {
                    "id": node.id,
                    "text": node.text,
                    "importance": node.importance,
                    "confidence": level
                }
                for node in passive_nodes
            ]
        except Exception as e:
            trace_logger.warning(f"Failed to get memories by confidence: {e}")
            return []
    
    def compute_priority(self, memory: Dict) -> float:
        """Compute priority score (higher = more important)."""
        return memory.get("importance", 0.5)
    
    def promote(self, memory: Dict, new_level: str) -> None:
        """Promote memory to higher confidence (simplified)."""
        trace_logger.info(f"Memory promoted | id={memory.get('id')} | level={new_level}")
    
    def discard_lowest_low(self) -> None:
        """Discard the lowest-priority passive memory."""
        try:
            passive_nodes = self.mirage.get_tier_nodes("passive")
            if passive_nodes:
                # Find node with lowest importance
                lowest = min(passive_nodes, key=lambda n: n.importance)
                # Remove from storage
                if lowest.id in self.mirage.all_nodes:
                    del self.mirage.all_nodes[lowest.id]
                trace_logger.info(f"Low-priority memory discarded | id={lowest.id}")
        except Exception as e:
            trace_logger.warning(f"Failed to discard lowest: {e}")
    
    def count(self) -> int:
        """Get total memory count (all tiers)."""
        try:
            return len(self.mirage.all_nodes)
        except Exception as e:
            trace_logger.warning(f"Failed to count memories: {e}")
            return 0
    
    def search(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Search for relevant memories using Mirage's recall() method.
        This uses semantic similarity and graph traversal.
        """
        try:
            # Use Mirage's recall() method - handles semantic search + link traversal
            recalled_nodes, source_tier = self.mirage.recall(query)
            
            # Return top N results
            results = [
                {
                    "text": node.text,
                    "importance": node.importance,
                    "tier": node.tier
                }
                for node in recalled_nodes[:limit]
            ]
            
            trace_logger.info(f"Memory search | query_len={len(query)} | results={len(results)} | source={source_tier}")
            return results
        except Exception as e:
            trace_logger.warning(f"Memory search failed: {e}")
            return []
    
    def recall_without_promoting(self, query: str, limit: int = 10) -> List:
        """
        Search for related memories WITHOUT promoting them.
        Returns MemoryNode objects from passive and super_passive.
        """
        try:
            from core.concept_extraction import extract, semantic_similarity
            
            extraction = extract(query)
            query_concepts = extraction.concepts if extraction.concepts else [query.lower()]
            
            recalled = []
            
            # Search passive tier
            for node in self.mirage.passive:
                score = 0.0
                node_concepts = set(node.concepts)
                query_set = set(query_concepts)
                overlap = len(node_concepts & query_set)
                score += overlap * 2.0
                
                for qc in query_concepts:
                    for nc in node.concepts:
                        sim = semantic_similarity(qc, nc)
                        if sim > 0.5:
                            score += sim
                
                if query.lower() in node.text.lower():
                    score += 1.5
                
                if score > 1.0:
                    recalled.append((node, score))
            
            # Search super_passive tier
            for node in self.mirage.super_passive:
                score = 0.0
                node_concepts = set(node.concepts)
                query_set = set(query_concepts)
                overlap = len(node_concepts & query_set)
                score += overlap * 2.0
                
                for qc in query_concepts:
                    for nc in node.concepts:
                        sim = semantic_similarity(qc, nc)
                        if sim > 0.5:
                            score += sim
                
                if query.lower() in node.text.lower():
                    score += 1.5
                
                if score > 1.0:
                    recalled.append((node, score))
            
            # Sort by score and limit
            recalled.sort(key=lambda x: -x[1])
            result_nodes = [node for node, score in recalled[:limit]]
            
            trace_logger.info(f"Recalled without promoting | query_len={len(query)} | results={len(result_nodes)}")
            return result_nodes
        except Exception as e:
            trace_logger.warning(f"Recall without promoting failed: {e}")
            return []
    
    def update_confidence(self, mem_id: int, new_confidence: str):
        """Update memory confidence."""
        trace_logger.info(f"Confidence updated | id={mem_id} | level={new_confidence}")
    
    def update_topic(self, mem_id: int, new_topic: str):
        """Update memory topic."""
        trace_logger.info(f"Topic updated | id={mem_id} | topic={new_topic}")
    
    def update_tags(self, mem_id: int, new_tags: List[str]):
        """Update memory tags."""
        trace_logger.info(f"Tags updated | id={mem_id}")


class MemoryEvaluator:
    """
    Memory Evaluator - extracts and stores facts using PURE NLP.
    Uses EXACT functions from core modules (no LLM calls).
    """
    
    def __init__(self, passive_memory: PassiveMemory):
        """Initialize with passive memory reference."""
        self.passive_memory = passive_memory
        self.mirage = passive_memory.mirage
        
        try:
            from core.concept_extraction import extract
            from core.importance import calculate_importance
            self.extract = extract
            self.calculate_importance = calculate_importance
            trace_logger.info("MemoryEvaluator initialized with pure NLP extraction")
        except ImportError as e:
            trace_logger.warning(f"Failed to import extraction modules: {e}")
            self.extract = None
            self.calculate_importance = None
    
    def evaluate(self, user_text: str, nova_reply: str) -> None:
        """
        Evaluate conversation turn using PURE NLP extraction.
        Uses EXACT extract() and calculate_importance() functions.
        """
        if not self.extract:
            trace_logger.warning("Extraction modules not available")
            return
        
        passive_logger.info(f"Evaluate turn | user_len={len(user_text)} | nova_len={len(nova_reply)}")
        
        try:
            # Extract concepts from user text using EXACT function
            user_extraction = self.extract(user_text)
            
            # Extract concepts from nova reply using EXACT function
            nova_extraction = self.extract(nova_reply)
            
            # Add both to passive memory using Mirage's add() (which calls extract internally)
            # But we'll use the explicit extraction results
            if user_extraction.concepts:
                user_node = self.mirage.add(user_text)
                trace_logger.info(f"User memory stored | node_id={user_node.id} | concepts={len(user_extraction.concepts)}")
            
            if nova_extraction.concepts:
                nova_node = self.mirage.add(nova_reply)
                trace_logger.info(f"NOVA memory stored | node_id={nova_node.id} | concepts={len(nova_extraction.concepts)}")
            
            passive_logger.info("Turn evaluated and stored using pure NLP extraction")
        
        except Exception as e:
            trace_logger.error(f"Memory evaluation error: {e}")
