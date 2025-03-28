import os
import sys
import cv2
import time
import pyaudio
import wave
import numpy as np
import mediapipe as mp
from groq import Groq

# ✅ API Keys (Replace with your own)
GROQ_API_KEY = "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"

# ✅ Initialize API Clients
groq_client = Groq(api_key=GROQ_API_KEY)

# ✅ Audio Streaming Configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)

# ✅ Function for Text-to-Speech (TTS) using built-in OS engine
def speak_text(text):
    if sys.platform == "win32":
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    elif sys.platform == "darwin":  # macOS
        os.system(f'say "{text}"')

# ✅ Function to detect hands using MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

# ✅ Function to track the location of a hand and get the hand's center position
def track_hand(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    
    hand_position = None
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # We track the position of the wrist (landmark 0)
            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
            hand_position = (int(wrist.x * frame.shape[1]), int(wrist.y * frame.shape[0]))  # in pixels
            cv2.circle(frame, hand_position, 10, (0, 255, 0), -1)  # Draw the wrist position on the frame
    
    return hand_position

# ✅ Function to handle the mouse click and set the target location
def set_target(event, x, y, flags, param):
    global target_position, target_set
    if event == cv2.EVENT_LBUTTONDOWN:
        target_position = (x, y)
        target_set = True
        print(f"Target set at {target_position}")

# ✅ Function to provide movement direction based on hand and target position
def provide_direction(hand_position, target_position):
    # Calculate direction based on the target and hand position
    if hand_position and target_position:
        # Simplified direction calculation based on hand position and target
        dx = target_position[0] - hand_position[0]
        dy = target_position[1] - hand_position[1]
        
        direction = ""
        
        if dx < 0:
            direction += "left"
        elif dx > 0:
            direction += "right"
        
        if dy < 0:
            direction += " up"
        elif dy > 0:
            direction += " down"

        # Construct a natural-sounding direction response
        direction_message = f"Move in a {direction} direction to reach the target."
        print(direction_message)
        speak_text(direction_message)

# ✅ Main Loop
cap = cv2.VideoCapture(0)

# Object position (user sets target via click)
target_position = None
target_set = False

cv2.namedWindow("Live Camera Feed")
cv2.setMouseCallback("Live Camera Feed", set_target)

print("Please point your hand to the camera first.")

while True:
    try:
        ret, frame = cap.read()
        if not ret:
            print("⚠ Camera error! Unable to capture image.")
            break

        # Track hand position
        hand_position = track_hand(frame)

        # If the hand is detected and target is not set yet, ask the user to point at the object
        if hand_position and not target_set:
            print("Please now click on the target location to set the object position.")

        # If target is set, calculate direction
        if target_set:
            provide_direction(hand_position, target_position)

        # Show the frame with the hand position
        cv2.imshow("Live Camera Feed", frame)

        # Close webcam window if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    except KeyboardInterrupt:
        print("\n👋 Exiting...")
        break

# ✅ Cleanup
cap.release()
stream.stop_stream()
stream.close()
audio.terminate()
cv2.destroyAllWindows()
