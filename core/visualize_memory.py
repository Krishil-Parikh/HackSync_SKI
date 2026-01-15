"""Memory Graph Visualizer - Visualize the complete memory structure.

Shows all nodes, their connections, and concepts.
Generates an interactive HTML visualization.
"""

import json
from pathlib import Path
from core.mirage_memory import MirageMemory

def generate_html_graph(memory: MirageMemory, speakers: dict, output_file: str = "memory_graph.html"):
    """Generate an interactive HTML visualization of the memory graph."""
    
    # Collect all nodes and edges
    nodes_data = []
    edges_data = []
    
    all_nodes = list(memory.active) + memory.passive + memory.super_passive
    
    # Color scheme for tiers
    tier_colors = {
        "active": "#4CAF50",      # Green
        "passive": "#FFC107",     # Yellow
        "super_passive": "#F44336" # Red
    }
    
    for node in all_nodes:
        speaker = speakers.get(str(node.id), speakers.get(node.id, "Unknown"))
        text_short = node.text[:50] + "..." if len(node.text) > 50 else node.text
        
        nodes_data.append({
            "id": node.id,
            "label": f"[{node.id}] {speaker}",
            "title": f"{speaker}: {node.text}<br>Concepts: {', '.join(node.concepts)}<br>Tier: {node.tier}",
            "color": tier_colors.get(node.tier, "#999999"),
            "tier": node.tier,
            "concepts": node.concepts,
        })
        
        # Add edges for links
        for link_id in node.links:
            edges_data.append({
                "from": node.id,
                "to": link_id,
            })
    
    # Generate HTML with vis.js
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>Mirage Memory Graph</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }}
        h1 {{
            text-align: center;
            color: #00d9ff;
        }}
        #graph {{
            width: 100%;
            height: 80vh;
            border: 2px solid #333;
            border-radius: 10px;
            background: #16213e;
        }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
        }}
        .stats {{
            text-align: center;
            margin: 20px 0;
            color: #aaa;
        }}
    </style>
</head>
<body>
    <h1>Mirage Memory Graph</h1>
    
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background: #4CAF50;"></div>
            <span>Active ({len([n for n in all_nodes if n.tier == 'active'])})</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #FFC107;"></div>
            <span>Passive ({len([n for n in all_nodes if n.tier == 'passive'])})</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #F44336;"></div>
            <span>Super Passive ({len([n for n in all_nodes if n.tier == 'super_passive'])})</span>
        </div>
    </div>
    
    <div class="stats">
        Total Nodes: {len(all_nodes)} | Total Links: {len(edges_data)}
    </div>
    
    <div id="graph"></div>
    
    <script>
        var nodes = new vis.DataSet({json.dumps(nodes_data)});
        var edges = new vis.DataSet({json.dumps(edges_data)});
        
        var container = document.getElementById('graph');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            nodes: {{
                shape: 'dot',
                size: 16,
                font: {{
                    size: 12,
                    color: '#ffffff'
                }},
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                width: 1,
                color: {{
                    color: '#555555',
                    highlight: '#00d9ff'
                }},
                arrows: {{
                    to: {{ enabled: true, scaleFactor: 0.5 }}
                }},
                smooth: {{
                    type: 'continuous'
                }}
            }},
            physics: {{
                stabilization: {{ iterations: 200 }},
                barnesHut: {{
                    gravitationalConstant: -3000,
                    springLength: 150,
                    springConstant: 0.02
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100
            }}
        }};
        
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file


def generate_text_report(memory: MirageMemory, speakers: dict):
    """Generate a text report of the memory graph."""
    
    print("=" * 70)
    print("MIRAGE MEMORY GRAPH - Complete Visualization")
    print("=" * 70)
    
    all_nodes = list(memory.active) + memory.passive + memory.super_passive
    
    # Stats
    print(f"\n📊 STATISTICS")
    print(f"  Total Nodes: {len(all_nodes)}")
    print(f"  Active: {len(memory.active)} / {memory.ACTIVE_SIZE}")
    print(f"  Passive: {len(memory.passive)} / {memory.PASSIVE_SIZE}")
    print(f"  Super Passive: {len(memory.super_passive)}")
    
    total_links = sum(len(n.links) for n in all_nodes)
    print(f"  Total Links: {total_links}")
    
    # Concept frequency
    concept_count = {}
    for node in all_nodes:
        for concept in node.concepts:
            concept_count[concept] = concept_count.get(concept, 0) + 1
    
    print(f"\n🏷️ TOP CONCEPTS (most frequent)")
    sorted_concepts = sorted(concept_count.items(), key=lambda x: -x[1])[:15]
    for concept, count in sorted_concepts:
        bar = "█" * min(count, 20)
        print(f"  {concept:20s} {bar} ({count})")
    
    # Most connected nodes
    print(f"\n🔗 MOST CONNECTED NODES")
    sorted_by_links = sorted(all_nodes, key=lambda n: len(n.links), reverse=True)[:10]
    for node in sorted_by_links:
        speaker = speakers.get(str(node.id), speakers.get(node.id, "?"))
        text = node.text[:40] + "..." if len(node.text) > 40 else node.text
        print(f"  [{node.id:3d}] {speaker:10s} → {len(node.links)} links | {text}")
    
    # Tier breakdown
    for tier_name, tier_nodes in [("ACTIVE", memory.active), ("PASSIVE", memory.passive), ("SUPER PASSIVE", memory.super_passive)]:
        if not tier_nodes:
            continue
        print(f"\n📦 {tier_name} ({len(tier_nodes)} nodes)")
        print("-" * 60)
        for node in tier_nodes[:20]:  # Show max 20 per tier
            speaker = speakers.get(str(node.id), speakers.get(node.id, "?"))
            text = node.text[:45] + "..." if len(node.text) > 45 else node.text
            links_str = f"→ {node.links}" if node.links else ""
            print(f"  [{node.id:3d}] {speaker:10s}: {text}")
            if node.concepts:
                print(f"        concepts: {node.concepts[:5]}")
            if node.links:
                print(f"        links: {node.links}")
        if len(tier_nodes) > 20:
            print(f"  ... and {len(tier_nodes) - 20} more nodes")


def main():
    print("Loading memory...")
    memory = MirageMemory(storage_path="chatbot_memory.json")
    
    # Load speakers
    speakers = {}
    if Path("speakers.json").exists():
        with open("speakers.json", 'r', encoding='utf-8') as f:
            speakers = json.load(f)
    
    # Generate text report
    generate_text_report(memory, speakers)
    
    # Generate HTML graph
    output_file = generate_html_graph(memory, speakers)
    print(f"\n✓ HTML Graph saved to: {output_file}")
    print("  Open in browser to see interactive visualization!")


if __name__ == "__main__":
    main()
