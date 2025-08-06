# Hand Gesture Control System

A real-time hand gesture recognition system using MediaPipe, OpenCV, and PyAutoGUI. This project allows you to control your system using only your "right-hand gestures" via webcam.

## Features

- Move mouse with your index finger
- Right-click using thumb + index finger pinch
- Swipe right (Index + Middle) → Previous (← key)
- Swipe left (Index + Middle) → Next (→ key)
- Scroll with 3 fingers (Index + Middle + Ring)
- Volume up/down by moving 4 joined fingers vertically
- Mute/Unmute with thumbs up
- Drag with closed fist
- Pause/Play with double tap (customizable)

## Tech Stack

- Python 3
- OpenCV
- MediaPipe
- PyAutoGUI
- NumPy

## How to Run

1. **Install dependencies**
   ```bash
   pip install opencv-python mediapipe pyautogui numpy

2. python gesture_control.py

