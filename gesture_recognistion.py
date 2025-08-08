import cv2
import mediapipe as mp
import pyautogui
import webbrowser
import time
import numpy as np
import os

# === MediaPipe Init ===
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1)

# === Webcam ===
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Error: Could not open webcam.")
    exit()

last_gesture = ""
last_time = 0
cooldown = 2  # seconds

# === Omen HUD Overlay ===
def apply_overlay(background, overlay_path):
    if not os.path.exists(overlay_path):
        print("❌ Overlay file not found.")
        return background

    overlay_img = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
    if overlay_img is None:
        print("❌ Failed to load overlay image.")
        return background

    if overlay_img.shape[2] < 4:
        print("❌ No alpha channel in overlay.")
        return background

    overlay_img = cv2.resize(overlay_img, (background.shape[1], background.shape[0]))
    alpha = overlay_img[:, :, 3] / 255.0

    for c in range(3):
        background[:, :, c] = background[:, :, c] * (1 - alpha) + overlay_img[:, :, c] * alpha

    return background

# === Trigger Actions for Gestures ===
def perform_action(gesture):
    global last_gesture, last_time
    if gesture == last_gesture and time.time() - last_time < cooldown:
        return
    last_gesture = gesture
    last_time = time.time()

    if gesture == "Rock!":
        webbrowser.open("https://www.youtube.com")
    elif gesture == "Peace!":
        pyautogui.press('space')
    elif gesture == "Thumbs Down!":
        pyautogui.press('right')
    elif gesture == "Thumbs Up!":
        pyautogui.press('left')

# === Recognize Gestures ===
def get_gesture(landmarks):
    def is_finger_up(tip, pip):
        return landmarks[tip].y < landmarks[pip].y

    THUMB_TIP, THUMB_IP, THUMB_MCP = 4, 3, 2
    INDEX_TIP, INDEX_PIP = 8, 6
    MIDDLE_TIP, MIDDLE_PIP = 12, 10
    RING_TIP, RING_PIP = 16, 14
    PINKY_TIP, PINKY_PIP = 20, 18

    thumb_up = landmarks[THUMB_TIP].y < landmarks[THUMB_IP].y
    thumb_down = landmarks[THUMB_TIP].y > landmarks[THUMB_IP].y and landmarks[THUMB_TIP].y > landmarks[THUMB_MCP].y
    index_up = is_finger_up(INDEX_TIP, INDEX_PIP)
    middle_up = is_finger_up(MIDDLE_TIP, MIDDLE_PIP)
    ring_up = is_finger_up(RING_TIP, RING_PIP)
    pinky_up = is_finger_up(PINKY_TIP, PINKY_PIP)

    if thumb_up and not (index_up or middle_up or ring_up or pinky_up):
        return "Thumbs Up!"
    elif thumb_down and not (index_up or middle_up or ring_up or pinky_up):
        return "Thumbs Down!"
    elif index_up and middle_up and not (ring_up or pinky_up or thumb_up):
        return "Peace!"
    elif all([thumb_up, index_up, middle_up, ring_up, pinky_up]):
        return "Palm!"
    elif index_up and pinky_up and not (middle_up or ring_up or thumb_up):
        return "Rock!"
    else:
        return "Unrecognized"

# === MAIN LOOP ===
omen_overlay_path = "omen_hud.png"
print("🧪 Checking overlay:", omen_overlay_path, "Exists:", os.path.exists(omen_overlay_path))

while True:
    success, img = cap.read()
    if not success:
        print("⚠️ Warning: Empty frame received.")
        continue

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)

    gesture = "Unrecognized"

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            gesture = get_gesture(hand_landmarks.landmark)
            if gesture != "Unrecognized":
                perform_action(gesture)

    # Display Gesture Text
    if int(time.time() * 10) % 2 == 0:
        cv2.putText(img, f'Gesture: {gesture}', (20, 50),
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 0, 255), 3)

    # Apply HUD
    img = apply_overlay(img, omen_overlay_path)

    cv2.imshow("🕶️ VoidTrace: Gesture Control", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
