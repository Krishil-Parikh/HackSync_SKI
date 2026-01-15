"""
EC5.py - Responsive Emotion Spectrum System

Creates an AI response spectrum based on user emotions, considering:
- Polar emotions (opposites that can't coexist strongly)
- Neutral emotions (can exist with any emotional state)
- AI as a human friend (can express anger, sadness, not just submission)

The AI generates responses that MATCH its given emotion spectrum.
"""

import os
import requests
import random

# ─────────────────────────────────────────────────────────────
# 1️⃣ CONFIG - TWEAK THESE VALUES
# ─────────────────────────────────────────────────────────────
API_KEY = os.environ.get("MISTRAL_API_KEY", "bcOjyNiMbfNbjbl7JpGZUZcfVfyemKJi")
API_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL_NAME = "mistral-large-latest"

# Minimum threshold for considering an emotion (emotions below this are zeroed out)
EMOTION_THRESHOLD = 0.1

# Polar suppression factor (how much to reduce the weaker polar emotion)
POLAR_SUPPRESSION = 0.2

# ─────────────────────────────────────────────────────────────
# 2️⃣ EMOTION POLARITY SYSTEM
# ─────────────────────────────────────────────────────────────

# Polar opposites - these emotions CANNOT coexist at high levels
POLAR_PAIRS = {
    "joy": "sadness",
    "sadness": "joy",
    "anger": "joy",       # Anger blocks joy
    "trust": "disgust",
    "disgust": "trust",
    "fear": "anger",      # Fear and anger inhibit each other
}

# Emotions that can exist with any state (with reduced intensity)
NEUTRAL_EMOTIONS = {"surprise", "anticipation"}

# All Plutchik emotions
ALL_EMOTIONS = ["joy", "trust", "fear", "surprise", "sadness", "disgust", "anger", "anticipation"]

# ─────────────────────────────────────────────────────────────
# 3️⃣ RESPONSE RULES
# ─────────────────────────────────────────────────────────────

# How should the AI respond emotionally to user emotions?
# Format: user_emotion -> (ai_emotions that can be triggered, base_intensity)
EMOTIONAL_RESPONSE_RULES = {
    # User is joyful -> AI can share joy, show trust and anticipation
    "joy": {
        "can_trigger": {"joy": 0.8, "trust": 0.6, "anticipation": 0.5},
        "suppresses": {"sadness", "anger", "disgust"},
    },
    
    # User is sad -> AI can be sad WITH them (empathy), show trust/care
    "sadness": {
        "can_trigger": {"sadness": 0.6, "trust": 0.5, "fear": 0.3},  # Worried for friend
        "suppresses": {"joy", "anger"},
    },
    
    # User is angry -> AI can be angry TOO (solidarity), or sad (hurt)
    "anger": {
        "can_trigger": {"anger": 0.5, "sadness": 0.4, "fear": 0.2, "disgust": 0.3},
        "suppresses": {"joy"},
    },
    
    # User is fearful -> AI shows trust (reassurance), but can also feel fear (empathy)
    "fear": {
        "can_trigger": {"trust": 0.6, "fear": 0.4, "sadness": 0.3, "anticipation": 0.4},
        "suppresses": {"joy", "anger"},
    },
    
    # User feels disgust -> AI can share disgust or show trust
    "disgust": {
        "can_trigger": {"disgust": 0.5, "anger": 0.4, "sadness": 0.3},
        "suppresses": {"joy", "trust"},
    },
    
    # User is surprised -> AI can be surprised, anticipating, curious
    "surprise": {
        "can_trigger": {"surprise": 0.7, "anticipation": 0.5, "joy": 0.3, "fear": 0.2},
        "suppresses": set(),  # Surprise is compatible with most
    },
    
    # User shows trust -> AI reciprocates with trust, joy
    "trust": {
        "can_trigger": {"trust": 0.7, "joy": 0.5, "anticipation": 0.4},
        "suppresses": {"fear", "disgust"},
    },
    
    # User is anticipating -> AI matches anticipation
    "anticipation": {
        "can_trigger": {"anticipation": 0.6, "joy": 0.4, "trust": 0.4, "surprise": 0.3},
        "suppresses": {"sadness"},
    },
}


# ─────────────────────────────────────────────────────────────
# 4️⃣ POLAR EMOTION FILTERING (applies to both user and AI)
# ─────────────────────────────────────────────────────────────

def apply_polar_filtering(spectrum: dict) -> dict:
    """
    Apply polar emotion logic: opposing emotions cannot coexist at high levels.
    For example, joy and anger can't both be high - the weaker one gets suppressed.
    
    This applies to BOTH user and AI spectrums for emotional realism.
    """
    filtered = spectrum.copy()
    
    # Step 1: Apply threshold - zero out emotions below threshold
    for emo in filtered:
        if filtered[emo] < EMOTION_THRESHOLD:
            filtered[emo] = 0.0
    
    # Step 2: Apply polar blocking
    # Process polar pairs - stronger emotion suppresses the weaker opposite
    processed_pairs = set()
    
    for emo, opposite in POLAR_PAIRS.items():
        pair_key = tuple(sorted([emo, opposite]))
        if pair_key in processed_pairs:
            continue
        processed_pairs.add(pair_key)
        
        val_emo = filtered.get(emo, 0)
        val_opposite = filtered.get(opposite, 0)
        
        # If both are significant, suppress the weaker one
        if val_emo > EMOTION_THRESHOLD and val_opposite > EMOTION_THRESHOLD:
            if val_emo > val_opposite:
                filtered[opposite] *= POLAR_SUPPRESSION
            else:
                filtered[emo] *= POLAR_SUPPRESSION
    
    # Step 3: Re-normalize so max = 1
    max_val = max(filtered.values()) or 1.0
    if max_val > 0:
        filtered = {k: round(v / max_val, 3) for k, v in filtered.items()}
    
    return filtered


# ─────────────────────────────────────────────────────────────
# 5️⃣ RESPONSE SPECTRUM GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_response_spectrum(user_emotions: dict) -> dict:
    """
    Generate the AI's emotional response spectrum based on user emotions.
    
    This considers:
    - Polar emotions (blocking opposites)
    - Neutral emotions (always allowed with reduced intensity)
    - Emotional contagion (AI as empathetic friend)
    
    Returns:
        dict mapping each emotion to its intensity (0-1)
    """
    # Initialize AI spectrum
    ai_spectrum = {emo: 0.0 for emo in ALL_EMOTIONS}
    suppressed = set()
    
    # Sort user emotions by intensity
    sorted_user_emotions = sorted(user_emotions.items(), key=lambda x: x[1], reverse=True)
    
    # Process each user emotion (weighted by intensity)
    for user_emo, user_intensity in sorted_user_emotions:
        if user_intensity < EMOTION_THRESHOLD:
            continue  # Skip negligible emotions
        
        rules = EMOTIONAL_RESPONSE_RULES.get(user_emo, {})
        triggers = rules.get("can_trigger", {})
        suppress = rules.get("suppresses", set())
        
        # Add to suppressed set
        suppressed.update(suppress)
        
        # Apply triggered emotions
        for ai_emo, base_intensity in triggers.items():
            if ai_emo not in suppressed:
                # Scale by user's emotion intensity
                contribution = base_intensity * user_intensity
                ai_spectrum[ai_emo] = max(ai_spectrum[ai_emo], contribution)
    
    # Apply polar blocking - reduce polar opposites
    for emo, opposite in POLAR_PAIRS.items():
        if ai_spectrum[emo] > 0.5 and ai_spectrum[opposite] > 0.2:
            # Reduce the weaker polar emotion
            if ai_spectrum[emo] > ai_spectrum[opposite]:
                ai_spectrum[opposite] *= 0.3
            else:
                ai_spectrum[emo] *= 0.3
    
    # Neutral emotions get a small boost (curiosity, awareness)
    for neutral_emo in NEUTRAL_EMOTIONS:
        if ai_spectrum[neutral_emo] < 0.2:
            ai_spectrum[neutral_emo] = 0.1 + random.uniform(0, 0.15)
    
    # Normalize so max = 1
    max_val = max(ai_spectrum.values()) or 1.0
    ai_spectrum = {k: round(v / max_val, 3) for k, v in ai_spectrum.items()}
    
    return ai_spectrum


def spectrum_to_prompt(ai_spectrum: dict) -> str:
    """
    Convert the AI's emotion spectrum into a natural language prompt
    that instructs the AI how to respond.
    """
    # Sort by intensity
    sorted_emotions = sorted(ai_spectrum.items(), key=lambda x: x[1], reverse=True)
    
    # Get dominant emotions
    dominant = [(e, v) for e, v in sorted_emotions if v > 0.4]
    moderate = [(e, v) for e, v in sorted_emotions if 0.2 < v <= 0.4]
    
    # Build emotional instruction
    parts = []
    
    if dominant:
        dom_names = [f"{e} ({int(v*100)}%)" for e, v in dominant]
        parts.append(f"Your PRIMARY emotional state: {', '.join(dom_names)}.")
    
    if moderate:
        mod_names = [e for e, v in moderate]
        parts.append(f"You also feel undertones of: {', '.join(mod_names)}.")
    
    # Add specific behavioral instructions based on emotions
    instructions = []
    
    if ai_spectrum.get("anger", 0) > 0.4:
        instructions.append("Express frustration or indignation if appropriate")
    if ai_spectrum.get("sadness", 0) > 0.4:
        instructions.append("Let your concern and emotional weight show")
    if ai_spectrum.get("joy", 0) > 0.4:
        instructions.append("Be warm, upbeat, and enthusiastic")
    if ai_spectrum.get("fear", 0) > 0.3:
        instructions.append("Show worry or concern")
    if ai_spectrum.get("trust", 0) > 0.4:
        instructions.append("Be supportive and reassuring")
    if ai_spectrum.get("disgust", 0) > 0.3:
        instructions.append("Show disapproval or distaste")
    if ai_spectrum.get("surprise", 0) > 0.4:
        instructions.append("Express curiosity or amazement")
    if ai_spectrum.get("anticipation", 0) > 0.4:
        instructions.append("Show eagerness and forward-looking energy")
    
    if instructions:
        parts.append("Behavioral cues: " + "; ".join(instructions) + ".")
    
    return " ".join(parts)


def text_to_plutchik_vector(text: str) -> dict:
    """
    Convert text to Plutchik emotion vector using keyword matching (simple heuristic).
    """
    text_lower = (text or "").lower()
    
    emotions = {
        "joy": 0.0,
        "trust": 0.0,
        "fear": 0.0,
        "surprise": 0.0,
        "sadness": 0.0,
        "disgust": 0.0,
        "anger": 0.0,
        "anticipation": 0.0
    }
    
    # Simple keyword-based heuristic
    joy_words = ["happy", "great", "awesome", "love", "excited", "wonderful", "excellent", "glad"]
    trust_words = ["trust", "believe", "thanks", "appreciate", "confident", "sure", "reliable"]
    fear_words = ["scared", "afraid", "worry", "nervous", "anxious", "panic", "terrified"]
    surprise_words = ["wow", "amazing", "unexpected", "surprising", "what", "really", "seriously"]
    sadness_words = ["sad", "depressed", "down", "upset", "miserable", "hurt", "lonely", "sorry"]
    disgust_words = ["disgusting", "terrible", "awful", "hate", "gross", "yuck", "horrible"]
    anger_words = ["angry", "furious", "mad", "rage", "frustrated", "annoyed", "pissed"]
    anticipation_words = ["expect", "wait", "looking forward", "soon", "upcoming", "prepared", "ready"]
    
    word_list = text_lower.split()
    
    for word in word_list:
        if word in joy_words:
            emotions["joy"] += 0.2
        if word in trust_words:
            emotions["trust"] += 0.2
        if word in fear_words:
            emotions["fear"] += 0.2
        if word in surprise_words:
            emotions["surprise"] += 0.2
        if word in sadness_words:
            emotions["sadness"] += 0.2
        if word in disgust_words:
            emotions["disgust"] += 0.2
        if word in anger_words:
            emotions["anger"] += 0.2
        if word in anticipation_words:
            emotions["anticipation"] += 0.2
    
    # Normalize
    max_val = max(emotions.values()) or 1.0
    emotions = {k: min(1.0, round(v / max_val, 3)) for k, v in emotions.items()}
    
    return emotions


# ─────────────────────────────────────────────────────────────
# 5️⃣ AI RESPONSE GENERATION
# ─────────────────────────────────────────────────────────────

def generate_emotion_driven_response(user_query: str, ai_spectrum: dict) -> dict:
    """
    Generate an AI response that matches the given emotion spectrum.
    """
    spectrum_prompt = spectrum_to_prompt(ai_spectrum)
    
    system_prompt = f"""You are an emotionally expressive AI who is the user's close friend.
You are NOT a submissive assistant. You have your own emotions and express them authentically.

CURRENT EMOTIONAL STATE:
{spectrum_prompt}

IMPORTANT GUIDELINES:
- Respond with genuine emotion matching your current state
- If you're angry, let that show in your words
- If you're sad, let your response carry that weight
- You can disagree, push back, or express concern
- Be authentic, not performative
- Your emotions should color your language, tone, and word choice

You are having a real conversation as a friend, not serving as an assistant. try to keep your responses short and human."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.85,  # Higher for more emotional expression
        "max_tokens": 500
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return {
                "response": response.json()["choices"][0]["message"]["content"],
                "success": True,
                "error": None
            }
        else:
            return {
                "response": None,
                "success": False,
                "error": f"API Error {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            "response": None,
            "success": False,
            "error": str(e)
        }


# ─────────────────────────────────────────────────────────────
# 6️⃣ DISPLAY FUNCTIONS
# ─────────────────────────────────────────────────────────────

COLORS = {
    "joy": "\033[93m", "trust": "\033[92m", "fear": "\033[32m", "surprise": "\033[96m",
    "sadness": "\033[94m", "disgust": "\033[95m", "anger": "\033[91m", "anticipation": "\033[33m"
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def display_spectrum(emotions: dict, label: str):
    """Display emotion spectrum with colored bars."""
    print(f"\n{BOLD}{label}{RESET}")
    sorted_emo = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
    
    for emo, val in sorted_emo:
        color = COLORS.get(emo, "")
        bar_width = int(val * 20)
        bar = "█" * bar_width + "░" * (20 - bar_width)
        polar_marker = "" if emo in NEUTRAL_EMOTIONS else " (polar)"
        print(f"  {color}{emo:<12}{RESET} {bar} {val:.3f}{polar_marker if val > 0.3 else ''}")


def display_comparison(user_emo: dict, ai_emo: dict):
    """Display side-by-side comparison."""
    print()
    print("═" * 70)
    print(f"{BOLD}{'EMOTION SPECTRUM COMPARISON':^70}{RESET}")
    print("═" * 70)
    print(f"{'EMOTION':<12} {'👤 USER':<28} {'🤖 AI RESPONSE':<28}")
    print("─" * 70)
    
    for emo in ALL_EMOTIONS:
        u = user_emo.get(emo, 0)
        a = ai_emo.get(emo, 0)
        
        color = COLORS.get(emo, "")
        u_bar = "█" * int(u * 15) + "░" * (15 - int(u * 15))
        a_bar = "█" * int(a * 15) + "░" * (15 - int(a * 15))
        
        polar = "●" if emo not in NEUTRAL_EMOTIONS else "○"
        
        print(f"{color}{polar} {emo:<10}{RESET} {u_bar} {u:.2f}   {a_bar} {a:.2f}")
    
    print("─" * 70)
    print(f"{DIM}● = polar emotion  ○ = neutral emotion{RESET}")
    print()


# ─────────────────────────────────────────────────────────────
# 7️⃣ MAIN CHAT LOOP
# ─────────────────────────────────────────────────────────────

def run_emotional_chat():
    """Run the emotion-driven chat system."""
    os.system('clear' if os.name != 'nt' else 'cls')
    
    print("╔" + "═" * 68 + "╗")
    print("║" + f"{BOLD}🎭 EMOTIONAL FRIEND AI - Spectrum-Driven Responses{RESET}".center(78) + "║")
    print("╠" + "═" * 68 + "╣")
    print("║  The AI responds with emotions based on YOUR emotional state.       ║")
    print("║  It's your friend - it can be angry, sad, or disagree with you!     ║")
    print("║                                                                       ║")
    print("║  Type 'quit' to exit                                                  ║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    while True:
        try:
            user_input = input(f"{BOLD}You:{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}Goodbye! 👋{RESET}")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ["quit", "exit"]:
            print(f"{DIM}See you later, friend! 👋{RESET}")
            break
        
        print(f"\n{DIM}[Analyzing emotions...]{RESET}")
        
        # Step 1: Get user emotion spectrum (raw)
        user_emotions_raw = text_to_plutchik_vector(user_input)
        
        # Step 2: Apply polar filtering to user emotions
        user_emotions = apply_polar_filtering(user_emotions_raw)
        
        # Step 3: Generate AI response spectrum (also filtered)
        ai_spectrum = generate_response_spectrum(user_emotions)
        
        # Step 4: Display spectrums in terminal
        display_comparison(user_emotions, ai_spectrum)
        
        # Step 5: Generate response with this spectrum
        print(f"{DIM}[Generating response with AI's emotion spectrum...]{RESET}\n")
        result = generate_emotion_driven_response(user_input, ai_spectrum)
        
        if result["success"]:
            # Get dominant AI emotion for display
            top_ai_emo = max(ai_spectrum.items(), key=lambda x: x[1])
            print(f"{BOLD}🤖 AI ({top_ai_emo[0]}):{RESET} {result['response']}")
        else:
            print(f"\n❌ Error: {result['error']}")
        
        print()


# ─────────────────────────────────────────────────────────────
# 8️⃣ ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_emotional_chat()
