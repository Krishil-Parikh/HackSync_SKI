import cv2
import time
import math
import numpy as np
import pyautogui

import gestures.handTrackingModule as htm
from core.listener import listen
from core.speaker import speak

# ===========================
# CONFIG (UNCHANGED)
# ===========================
wCam, hCam = 640, 480
frameR = 100
smoothening = 5

CLICK_HOLD = 3
DRAG_HOLD = 6
STOP_HOLD = 5

PINCH_DIST = 35

pyautogui.FAILSAFE = False

# ===========================
# STATE (UNCHANGED)
# ===========================
plocX, plocY = 0, 0
dragging = False
gesture_active = True

gesture_start = {}

def hold(key, seconds):
    now = time.time()
    if key not in gesture_start:
        gesture_start[key] = now
        return False
    return (now - gesture_start[key]) >= seconds

def reset(key):
    gesture_start.pop(key, None)

# ===========================
# INIT (UNCHANGED)
# ===========================
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

detector = htm.handDetector(maxHands=1)
wScr, hScr = pyautogui.size()

print("NOVA: Gesture control activated. Make a fist with both hands to stop.")

# ===========================
# LOOP
# ===========================
while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img)

    if not gesture_active:
        cv2.imshow("Gestures", img)
        cv2.waitKey(1)
        continue

    if lmList:
        x1, y1 = lmList[8][1:]    # index
        x2, y2 = lmList[12][1:]   # middle
        x4, y4 = lmList[4][1:]    # thumb

        fingers = detector.findFingersUp(img)

        # ===========================
        # 1️⃣ MOVE CURSOR (EXACT COPY)
        # ===========================
        if fingers == [0,1,0,0,0]:
            x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
            y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))

            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening

            pyautogui.moveTo(wScr - clocX, clocY)

            plocX, plocY = clocX, clocY

        # ===========================
        # 2️⃣ CLICK (INDEX + MIDDLE)
        # ===========================
        if fingers[1] == 1 and fingers[2] == 1:
            if hold("click", CLICK_HOLD):
                pyautogui.click()
                reset("click")
        else:
            reset("click")

        # ===========================
        # 3️⃣ CLICK + DICTATE
        # ===========================
        if fingers == [0,1,1,0,0]:
            if hold("dictate", CLICK_HOLD):
                pyautogui.click()
                speak("Listening")
                text = listen()
                pyautogui.write(text)
                reset("dictate")
        else:
            reset("dictate")

        # ===========================
        # 4️⃣ SCROLL (FIST)
        # ===========================
        if fingers == [0,0,0,0,0]:
            pyautogui.scroll(-20)

        # ===========================
        # 5️⃣ DRAG (PINCH)
        # ===========================
        pinch_dist = math.hypot(x4 - x1, y4 - y1)

        if pinch_dist < PINCH_DIST:
            if hold("drag", DRAG_HOLD):
                if not dragging:
                    pyautogui.mouseDown()
                    dragging = True

                x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))
                pyautogui.moveTo(wScr - x3, y3)
        else:
            reset("drag")
            if dragging:
                pyautogui.mouseUp()
                dragging = False

    cv2.imshow("Gestures", img)
    cv2.waitKey(1)
