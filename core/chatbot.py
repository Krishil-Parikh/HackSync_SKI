"""Mirage Chatbot - AI with Human-Like Memory.

Each message (user and bot) becomes a node in memory.
Context for AI = Active memory (7 nodes) + Recalled nodes (up to memory strength)
Total context can be 7 + 10 = 17 nodes maximum.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

from mirage_memory import MirageMemory

# Load environment variables
load_dotenv()

# ANSI Colors
class C:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


class MirageChatbot:
    """AI Chatbot with human-like memory integration."""
    
    def __init__(self):
        # Initialize OpenRouter client
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in .env")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        # Model to use
        self.model = "meta-llama/llama-3.3-70b-instruct:free"
        
        # Initialize memory system
        self.memory = MirageMemory(storage_path="chatbot_memory.json")
        
        # Memory text files
        self.active_file = "active.txt"
        self.passive_file = "passive.txt"
        self.super_passive_file = "super_passive.txt"
        
        # System prompt
        self.system_prompt = """You are Mirage. you give answers completely human like in one sentence - not too short, not too long. Max is 10 words minimum is 4 words."""
        
        # Track speakers: node_id -> speaker name (Dev, Mirage, Aditya, etc.)
        self.speakers = {}
        
        # Load speakers from file if available (created by seed_memory.py)
        self._load_speakers()
        
        # Update text files on startup
        self._update_memory_files()
    
    def _load_speakers(self):
        """Load speaker names from speakers.json if it exists."""
        import json
        from pathlib import Path
        
        speakers_file = Path("speakers.json")
        if speakers_file.exists():
            try:
                with open(speakers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert string keys to int
                    self.speakers = {int(k): v for k, v in data.items()}
                print(f"Loaded {len(self.speakers)} speaker mappings")
            except Exception as e:
                print(f"Could not load speakers.json: {e}")
    
    def _update_memory_files(self):
        """Update the text files for each memory tier."""
        # Active memory only (7 nodes)
        active_nodes = self.memory.get_tier_nodes("active")
        self._write_tier_file(self.active_file, active_nodes, "ACTIVE MEMORY (7 nodes)")
        
        # Passive memory
        passive_nodes = self.memory.get_tier_nodes("passive")
        self._write_tier_file(self.passive_file, passive_nodes, "PASSIVE MEMORY")
        
        # Super passive memory
        super_nodes = self.memory.get_tier_nodes("super_passive")
        self._write_tier_file(self.super_passive_file, super_nodes, "SUPER PASSIVE MEMORY")
    
    def _write_tier_file(self, filename: str, nodes: list, title: str):
        """Write nodes to a text file in conversation format."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== {title} ===\n\n")
            
            for node in nodes:
                speaker = self.speakers.get(node.id, "Unknown")
                f.write(f"{speaker}: {node.text}\n")
            
            if not nodes:
                f.write("(empty)\n")
    
    def _write_full_context_file(self, active_nodes: list, recalled_nodes: list):
        """
        Write active.txt with FULL context: 7 active + recalled nodes.
        This is what gets sent to the LLM.
        """
        with open(self.active_file, 'w', encoding='utf-8') as f:
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
    
    def _recall_without_promoting(self, query: str) -> list:
        """
        Search for related memories WITHOUT promoting them.
        Returns nodes from passive and super_passive that match the query.
        """
        from concept_extraction import extract, semantic_similarity
        
        extraction = extract(query)
        query_concepts = extraction.concepts if extraction.concepts else [query.lower()]
        
        recalled = []
        
        # Search passive
        for node in self.memory.passive:
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
                recalled.append((node, score, "passive"))
        
        # Search super_passive
        for node in self.memory.super_passive:
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
                recalled.append((node, score, "super_passive"))
        
        # Sort by score and limit to memory strength
        recalled.sort(key=lambda x: -x[1])
        return [node for node, score, tier in recalled[:self.memory.DEFAULT_MEMORY_STRENGTH]]
    
    def chat(self, user_message: str) -> str:
        """
        Process user message and get AI response.
        
        Flow:
        1. Add user message to memory
        2. Get active memory (7 nodes)
        3. Recall related memories from passive/super (up to 10 nodes)
        4. Write active.txt with FULL context (7 + recalled)
        5. Send full context to LLM
        6. Add response to memory
        """
        # 1. Store user message as a node
        user_node = self.memory.add(f"{user_message}")
        self.speakers[user_node.id] = "User"  # Current user
        
        # 2. Get active memory (7 nodes)
        active_nodes = list(self.memory.get_tier_nodes("active"))
        
        # 3. Recall related memories WITHOUT promoting (keeps them in passive/super)
        recalled_nodes = self._recall_without_promoting(user_message)
        
        # 4. Write active.txt with FULL context BEFORE calling LLM
        self._write_full_context_file(active_nodes, recalled_nodes)
        
        # Update passive and super files
        passive_nodes = self.memory.get_tier_nodes("passive")
        self._write_tier_file(self.passive_file, passive_nodes, "PASSIVE MEMORY")
        super_nodes = self.memory.get_tier_nodes("super_passive")
        self._write_tier_file(self.super_passive_file, super_nodes, "SUPER PASSIVE MEMORY")
        
        # 5. Build context string for LLM (active + recalled)
        context_parts = []
        
        # Add active nodes
        for node in active_nodes:
            speaker = self.speakers.get(node.id, "Unknown")
            context_parts.append(f"{speaker}: {node.text}")
        
        # Add recalled nodes
        for node in recalled_nodes:
            speaker = self.speakers.get(node.id, "Unknown")
            context_parts.append(f"{speaker}: {node.text}")
        
        context = "\n".join(context_parts)
        
        # 6. Prepare messages for API
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        if context:
            messages.append({
                "role": "system",
                "content": f"Here is the conversation so far:\n{context}"
            })
        
        messages.append({"role": "user", "content": user_message})
        
        # 7. Call LLM
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://mirage-memory.local",
                    "X-Title": "Mirage Memory Chatbot",
                },
                model=self.model,
                messages=messages,
            )
            bot_response = completion.choices[0].message.content
        except Exception as e:
            bot_response = f"[Error: {str(e)}]"
        
        # 8. Store bot response as a node
        bot_node = self.memory.add(f"{bot_response}")
        self.speakers[bot_node.id] = "Mirage"
        
        # Save speakers to file
        self._save_speakers()
        
        # 9. Final update - get new active state after adding response
        active_nodes = list(self.memory.get_tier_nodes("active"))
        self._write_full_context_file(active_nodes, recalled_nodes)
        
        return bot_response
    
    def _save_speakers(self):
        """Save speakers mapping to file."""
        import json
        with open("speakers.json", "w", encoding="utf-8") as f:
            json.dump(self.speakers, f, indent=2)
    
    def get_stats(self):
        """Get memory statistics."""
        return self.memory.get_stats()
    
    def clear(self):
        """Clear all memories and files."""
        self.memory.clear()
        self.speakers.clear()
        self._update_memory_files()


def print_banner():
    print(f"""
{C.CYAN}+==============================================================+
|               {C.BOLD}MIRAGE - AI with Human Memory{C.RESET}{C.CYAN}                |
+==============================================================+
|  {C.RESET}Type a message to chat{C.CYAN}                                      |
|  {C.YELLOW}/status{C.CYAN}  - Memory statistics                               |
|  {C.YELLOW}/memory{C.CYAN}  - Show active memory                              |
|  {C.YELLOW}/clear{C.CYAN}   - Clear all memories                              |
|  {C.YELLOW}/quit{C.CYAN}    - Exit                                            |
+==============================================================+{C.RESET}

{C.DIM}Context = Active (7) + Recalled (up to 10) = max 17 nodes{C.RESET}
""")


def main():
    print_banner()
    
    try:
        chatbot = MirageChatbot()
    except ValueError as e:
        print(f"{C.RED}Error: {e}{C.RESET}")
        return
    
    # Show loaded memories
    stats = chatbot.get_stats()
    if stats['total_nodes'] > 0:
        print(f"{C.GREEN}Loaded {stats['total_nodes']} memories{C.RESET}")
        print(f"  Active: {stats['active_count']}, Passive: {stats['passive_count']}, Super: {stats['super_passive_count']}")
        print(f"{C.DIM}  Use /clear to start fresh{C.RESET}\n")
    
    while True:
        try:
            user_input = input(f"{C.BOLD}You >{C.RESET} ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.lower()
                
                if cmd in ("/quit", "/exit"):
                    print(f"\n{C.CYAN}Goodbye! Memories saved.{C.RESET}\n")
                    break
                
                elif cmd == "/clear":
                    chatbot.clear()
                    print(f"{C.GREEN}All memories cleared.{C.RESET}\n")
                
                elif cmd == "/status":
                    stats = chatbot.get_stats()
                    print(f"""
{C.BOLD}Memory Status:{C.RESET}
  {C.GREEN}Active:{C.RESET}        {stats['active_count']:3d} / {stats['active_max']}
  {C.YELLOW}Passive:{C.RESET}       {stats['passive_count']:3d} / {stats['passive_max']}
  {C.RED}Super Passive:{C.RESET} {stats['super_passive_count']:3d} / unlimited
  Total: {stats['total_nodes']} nodes
""")
                
                elif cmd == "/memory":
                    nodes = chatbot.memory.get_tier_nodes("active")
                    print(f"\n{C.BOLD}Active Memory ({len(nodes)}/7):{C.RESET}")
                    for node in nodes:
                        speaker = chatbot.speakers.get(node.id, "?")
                        text = node.text[:50] + "..." if len(node.text) > 50 else node.text
                        print(f"  [{node.id}] {speaker}: {text}")
                    print()
                
                else:
                    print(f"{C.RED}Unknown command: {cmd}{C.RESET}")
                
                continue
            
            # Chat with AI
            print(f"{C.DIM}Thinking...{C.RESET}")
            response = chatbot.chat(user_input)
            print(f"\n{C.MAGENTA}{C.BOLD}Mirage >{C.RESET} {response}\n")
            
        except KeyboardInterrupt:
            print(f"\n\n{C.CYAN}Goodbye! Memories saved.{C.RESET}\n")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
