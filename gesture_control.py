import cv2
import numpy as np
import mediapipe as mp
import pyautogui
import time
import math
import subprocess

# Initialize mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Gesture label display time
gesture_display_time = 1.5
last_gesture_time = 0
last_gesture_label = ""

# PyAutoGUI config
pyautogui.FAILSAFE = False
screen_width, screen_height = pyautogui.size()

# Distance between two landmarks
def calculate_distance(lm1, lm2):
    return math.hypot(lm2.x - lm1.x, lm2.y - lm1.y)

# Detect swipe direction
def detect_swipe_direction(start_x, end_x):
    diff = end_x - start_x
    if abs(diff) > 0.2:
        return "right" if diff > 0 else "left"
    return None

# Scroll
def scroll(direction):
    pyautogui.scroll(100 if direction == "up" else -100)

# Launch apps
def launch_app(app):
    apps = {
        "spotify": "spotify",
        "vlc": "vlc",
        "youtube": "https://www.youtube.com"
    }
    if app == "youtube":
        subprocess.Popen(['start', 'chrome', apps[app]], shell=True)
    else:
        subprocess.Popen(apps[app], shell=True)

# Mouse helpers
def control_mouse(x, y):
    pyautogui.moveTo(x * screen_width, y * screen_height)

def start_drag():
    pyautogui.mouseDown()

def end_drag():
    pyautogui.mouseUp()

# Check if tips are close
def are_fingers_joined(lms, tips):
    for i in range(len(tips) - 1):
        if calculate_distance(lms[tips[i]], lms[tips[i + 1]]) > 0.05:
            return False
    return True

# Main
cap = cv2.VideoCapture(0)
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

gesture_start_x = None
scrolling = False
mouse_dragging = False
last_cy = None

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    current_time = time.time()

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            landmarks = hand_landmarks.landmark
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            fingers = {
                "thumb": landmarks[4].x < landmarks[3].x,
                "index": landmarks[8].y < landmarks[6].y,
                "middle": landmarks[12].y < landmarks[10].y,
                "ring": landmarks[16].y < landmarks[14].y,
                "pinky": landmarks[20].y < landmarks[18].y,
            }

            cx = landmarks[9].x
            cy = landmarks[9].y

            # Swipe
            if fingers["index"] and fingers["middle"] and not fingers["ring"]:
                if gesture_start_x is None:
                    gesture_start_x = landmarks[8].x
                else:
                    direction = detect_swipe_direction(gesture_start_x, landmarks[8].x)
                    if direction == "left":
                        last_gesture_label = "Go Next"
                        pyautogui.press('right')
                        gesture_start_x = None
                        last_gesture_time = current_time
                    elif direction == "right":
                        last_gesture_label = "Go Back"
                        pyautogui.press('left')
                        gesture_start_x = None
                        last_gesture_time = current_time
            else:
                gesture_start_x = None

            # Double tap index for play/pause
            if fingers["index"] and not fingers["middle"]:
                distance = calculate_distance(landmarks[8], landmarks[12])
                if distance < 0.03 and current_time - last_gesture_time > 1:
                    pyautogui.press('space')
                    last_gesture_label = "Play/Pause"
                    last_gesture_time = current_time

            # Thumbs up = mute/unmute
            if fingers["thumb"] and not any(fingers[f] for f in ["index", "middle", "ring", "pinky"]):
                pyautogui.press('m')
                last_gesture_label = "Mute/Unmute"
                last_gesture_time = current_time

            # Three finger scroll
            if fingers["index"] and fingers["middle"] and fingers["ring"]:
                scroll_dir = "up" if landmarks[8].y < 0.5 else "down"
                scroll(scroll_dir)
                last_gesture_label = f"Scroll {scroll_dir}"
                last_gesture_time = current_time

            # Volume control
            if (fingers["index"] and fingers["middle"] and fingers["ring"] and fingers["pinky"]
                and not fingers["thumb"]
                and are_fingers_joined(landmarks, [8, 12, 16, 20])):
                if last_cy is None:
                    last_cy = cy
                else:
                    delta = last_cy - cy
                    if abs(delta) > 0.03:
                        vol_dir = "up" if delta > 0 else "down"
                        pyautogui.press("volumeup" if vol_dir == "up" else "volumedown")
                        last_gesture_label = f"Volume {vol_dir}"
                        last_gesture_time = current_time
                        last_cy = cy
            else:
                last_cy = None

            # Move mouse with index finger only
            if fingers["index"] and not any([fingers["middle"], fingers["ring"], fingers["pinky"], fingers["thumb"]]):
                ix, iy = landmarks[8].x, landmarks[8].y
                screen_x = np.interp(ix, [0, 1], [0, screen_width])
                screen_y = np.interp(iy, [0, 1], [0, screen_height])
                pyautogui.moveTo(screen_x, screen_y)
                last_gesture_label = "Mouse Move"
                last_gesture_time = current_time

            # 👉 New Right Click: Index + Middle Pinch
            if (calculate_distance(landmarks[8], landmarks[12]) < 0.03 and
                not fingers["ring"] and not fingers["pinky"] and
                current_time - last_gesture_time > 0.5):
                pyautogui.rightClick()
                last_gesture_label = "Right Click"
                last_gesture_time = current_time

            # Drag with fist
            if not any(fingers.values()):
                if not mouse_dragging:
                    start_drag()
                    mouse_dragging = True
                    last_gesture_label = "Drag Start"
                    last_gesture_time = current_time
            elif mouse_dragging:
                end_drag()
                mouse_dragging = False
                last_gesture_label = "Drag End"
                last_gesture_time = current_time

            # Launch Spotify
            if all(fingers.values()) and cy < 0.2:
                launch_app("spotify")
                last_gesture_label = "Launch Spotify"
                last_gesture_time = current_time

    # Display gesture label
    if current_time - last_gesture_time < gesture_display_time:
        cv2.putText(frame, last_gesture_label, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

    cv2.imshow("Gesture Controller", frame)
    if cv2.waitKey(5) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
