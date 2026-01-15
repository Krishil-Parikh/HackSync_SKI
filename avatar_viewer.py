"""
Avatar Viewer - HUMANIZED version with micro-movements and randomness
NO CAMERA NEEDED - uses YOUR calibrated expression data

Controls:
  1 = Neutral
  2 = Blink
  3 = Smile
  4 = Sad
  5 = Surprise
  B = Toggle auto-blink
  ESC = Exit
"""

import cv2
import numpy as np
import mediapipe as mp
import json
import os
import time
import random
import math

# ============ Setup ============

mp_face = mp.solutions.face_mesh
CYAN = (255, 255, 0)
DARK_CYAN = (180, 180, 0)

WIDTH = 900
HEIGHT = 800

CALIBRATION_PATH = os.path.join(os.path.dirname(__file__), "avatar_calibration.json")

# ============ Load Calibration ============

def load_calibration():
    with open(CALIBRATION_PATH, 'r') as f:
        data = json.load(f)
    
    expressions = {}
    for expr_name, expr_data in data['expressions'].items():
        expressions[expr_name] = expr_data['landmarks']
    
    return expressions

try:
    expressions = load_calibration()
    print(f"✓ Loaded expressions: {list(expressions.keys())}")
except FileNotFoundError:
    print("✗ No calibration found! Run calibrate_face.py first.")
    exit(1)

# ============ HUMANIZATION SETTINGS ============

# Micro-movement (natural face tremor)
MICRO_MOVEMENT_AMOUNT = 0.0008  # How much landmarks jitter
MICRO_MOVEMENT_SPEED = 0.15     # How fast the jitter changes

# Expression variation (randomness when switching expressions)
EXPRESSION_VARIATION = 0.002   # Random offset per landmark

# Breathing animation
BREATHING_AMOUNT = 0.003       # How much face moves up/down
BREATHING_SPEED = 0.8          # Breathing rate (cycles per second)

# Transition smoothing
TRANSITION_SPEED = 0.12        # How fast to transition between expressions

# ============ State ============

current_expression = "neutral"
target_landmarks = [lm[:] for lm in expressions["neutral"]]  # Deep copy
display_landmarks = [lm[:] for lm in expressions["neutral"]]

# Micro-movement noise offsets (Perlin-like using sin waves)
noise_phases = [[random.random() * 100 for _ in range(3)] for _ in range(478)]

# Auto-blink
auto_blink = True
last_blink_time = time.time()
blink_interval = random.uniform(2.5, 4.5)  # Random interval
blink_phase = 0
is_blinking = False

# Animation time
start_time = time.time()

# ============ Humanization Functions ============

def add_micro_movement(landmarks, t):
    """Add subtle natural jitter to all landmarks"""
    result = []
    for i, lm in enumerate(landmarks):
        # Use multiple sine waves for organic movement
        jitter_x = math.sin(t * 3.7 + noise_phases[i][0]) * MICRO_MOVEMENT_AMOUNT
        jitter_y = math.sin(t * 4.3 + noise_phases[i][1]) * MICRO_MOVEMENT_AMOUNT * 1.2
        jitter_z = math.sin(t * 2.9 + noise_phases[i][2]) * MICRO_MOVEMENT_AMOUNT * 0.5
        
        # Add some randomness to the jitter
        jitter_x += math.sin(t * 7.1 + i * 0.1) * MICRO_MOVEMENT_AMOUNT * 0.3
        jitter_y += math.sin(t * 5.3 + i * 0.15) * MICRO_MOVEMENT_AMOUNT * 0.3
        
        result.append([
            lm[0] + jitter_x,
            lm[1] + jitter_y,
            lm[2] + jitter_z
        ])
    return result

def add_breathing(landmarks, t):
    """Add subtle breathing movement"""
    breath = math.sin(t * BREATHING_SPEED * 2 * math.pi) * BREATHING_AMOUNT
    
    result = []
    for lm in landmarks:
        result.append([
            lm[0],
            lm[1] + breath,  # Move whole face up/down slightly
            lm[2]
        ])
    return result

def add_expression_variation(landmarks):
    """Add random variation to expression (called once per expression change)"""
    result = []
    for lm in landmarks:
        result.append([
            lm[0] + random.uniform(-EXPRESSION_VARIATION, EXPRESSION_VARIATION),
            lm[1] + random.uniform(-EXPRESSION_VARIATION, EXPRESSION_VARIATION),
            lm[2] + random.uniform(-EXPRESSION_VARIATION * 0.5, EXPRESSION_VARIATION * 0.5)
        ])
    return result

def smooth_transition(current, target, speed):
    """Smoothly interpolate current landmarks towards target"""
    result = []
    for i in range(len(current)):
        result.append([
            current[i][0] + (target[i][0] - current[i][0]) * speed,
            current[i][1] + (target[i][1] - current[i][1]) * speed,
            current[i][2] + (target[i][2] - current[i][2]) * speed
        ])
    return result

def interpolate_landmarks(lm1, lm2, t):
    """Linear interpolation between landmarks"""
    result = []
    for i in range(len(lm1)):
        result.append([
            lm1[i][0] + (lm2[i][0] - lm1[i][0]) * t,
            lm1[i][1] + (lm2[i][1] - lm1[i][1]) * t,
            lm1[i][2] + (lm2[i][2] - lm1[i][2]) * t
        ])
    return result

# ============ Drawing ============

def landmarks_to_pixels(landmarks, w, h, scale=1.8, offset_y=80):
    pixels = []
    center_x = sum(lm[0] for lm in landmarks) / len(landmarks)
    center_y = sum(lm[1] for lm in landmarks) / len(landmarks)
    
    for lm in landmarks:
        x = int((lm[0] - center_x) * w * scale + w/2)
        y = int((lm[1] - center_y) * h * scale + h/2 + offset_y)
        pixels.append((x, y))
    
    return pixels

def draw_face(canvas, landmarks, w, h):
    pixels = landmarks_to_pixels(landmarks, w, h)
    
    # Mesh
    for edge in mp_face.FACEMESH_TESSELATION:
        p1 = pixels[edge[0]]
        p2 = pixels[edge[1]]
        cv2.line(canvas, p1, p2, DARK_CYAN, 1)
    
    # Face oval
    for edge in mp_face.FACEMESH_FACE_OVAL:
        p1 = pixels[edge[0]]
        p2 = pixels[edge[1]]
        cv2.line(canvas, p1, p2, CYAN, 2)
    
    # Points
    for p in pixels:
        cv2.circle(canvas, p, 1, CYAN, -1)

# ============ Main Loop ============

print("\n" + "="*50)
print("  HUMANIZED AVATAR VIEWER")
print("="*50)
print("\n1=Neutral 2=Blink 3=Smile 4=Sad 5=Surprise")
print("B=Toggle auto-blink  ESC=Exit\n")

while True:
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    
    current_time = time.time()
    elapsed = current_time - start_time
    
    # === Smooth transition to target expression ===
    display_landmarks = smooth_transition(display_landmarks, target_landmarks, TRANSITION_SPEED)
    
    # === Auto-blink ===
    blink_overlay = None
    
    if auto_blink and "blink" in expressions:
        if not is_blinking and (current_time - last_blink_time) > blink_interval:
            is_blinking = True
            blink_phase = 0
            blink_interval = random.uniform(2.5, 4.5)  # Randomize next interval
        
        if is_blinking:
            blink_phase += 1
            
            if blink_phase <= 4:
                t = blink_phase / 4.0
            else:
                t = (8 - blink_phase) / 4.0
            
            t = max(0, min(1, t))
            blink_overlay = interpolate_landmarks(display_landmarks, expressions["blink"], t)
            
            if blink_phase >= 8:
                is_blinking = False
                last_blink_time = current_time
    
    # === Apply humanization ===
    final_landmarks = blink_overlay if blink_overlay else display_landmarks
    
    # Add breathing
    final_landmarks = add_breathing(final_landmarks, elapsed)
    
    # Add micro-movements
    final_landmarks = add_micro_movement(final_landmarks, elapsed)
    
    # === Draw ===
    draw_face(canvas, final_landmarks, WIDTH, HEIGHT)
    
    # UI
    cv2.putText(canvas, f"Expression: {current_expression.upper()}", 
               (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, CYAN, 2)
    
    blink_status = "ON" if auto_blink else "OFF"
    cv2.putText(canvas, f"Auto-blink: {blink_status} | Humanized: ON", 
               (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    cv2.putText(canvas, "1=Neutral 2=Blink 3=Smile 4=Sad 5=Surprise | B=Blink | ESC=Exit", 
               (20, HEIGHT - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)
    
    # Glow
    canvas = cv2.GaussianBlur(canvas, (3, 3), 0)
    
    cv2.imshow("Humanized Avatar", canvas)
    
    # === Input ===
    key = cv2.waitKey(16) & 0xFF  # ~60 FPS
    
    if key == 27:
        break
    elif key == ord('1') and "neutral" in expressions:
        current_expression = "neutral"
        target_landmarks = add_expression_variation(expressions["neutral"])
    elif key == ord('2') and "blink" in expressions:
        current_expression = "blink"
        target_landmarks = add_expression_variation(expressions["blink"])
    elif key == ord('3') and "smile" in expressions:
        current_expression = "smile"
        target_landmarks = add_expression_variation(expressions["smile"])
    elif key == ord('4') and "sad" in expressions:
        current_expression = "sad"
        target_landmarks = add_expression_variation(expressions["sad"])
    elif key == ord('5') and "surprise" in expressions:
        current_expression = "surprise"
        target_landmarks = add_expression_variation(expressions["surprise"])
    elif key == ord('b') or key == ord('B'):
        auto_blink = not auto_blink
        print(f"Auto-blink: {'ON' if auto_blink else 'OFF'}")

cv2.destroyAllWindows()
print("Viewer closed.")
