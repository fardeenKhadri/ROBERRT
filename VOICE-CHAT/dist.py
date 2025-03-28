import os
import sys
import cv2
import time
import pyaudio
import wave
import numpy as np
import base64
import matplotlib.pyplot as plt
import mediapipe as mp
from groq import Groq
from together import Together

# ✅ API Keys (Replace with your own)
GROQ_API_KEY = "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"
TOGETHER_API_KEY = "99c0398a7d67df14aa70ab08597fd43e779736922611c10e9a76c773544d02b3"

# ✅ Initialize API Clients
groq_client = Groq(api_key=GROQ_API_KEY)
together_client = Together(api_key=TOGETHER_API_KEY)

# ✅ Audio Streaming Configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)

print("🎤 Speak naturally... (It detects pauses)")

# ✅ Function to record audio with VAD
def record_audio():
    frames = []
    silence_threshold = 100  # Adjust based on mic sensitivity
    silence_duration = 2  # Stop recording after 2 seconds of silence
    silence_counter = 0

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

        # Convert audio to numpy array
        audio_data = np.frombuffer(data, dtype=np.int16)
        volume = np.abs(audio_data).mean()

        if volume < silence_threshold:
            silence_counter += 1
        else:
            silence_counter = 0

        if silence_counter > (silence_duration * RATE / CHUNK):
            print("🎤 Silence detected. Processing audio...")
            break

    return frames

# ✅ Function to save recorded audio as WAV file
def save_audio(frames, filename="temp_audio.wav"):
    wf = wave.open(filename, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()
    return filename

# ✅ Function to transcribe audio using Groq Whisper
def transcribe_audio(filename):
    with open(filename, "rb") as audio_file:
        response = groq_client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file,
            language="en"
        )

    if response and response.text:
        return response.text.strip()
    return "Could not transcribe audio."

# ✅ Function to encode an image to base64
def encode_image_to_base64(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')

# ✅ Function to analyze an image using TogetherAI
def analyze_scene(frame):
    image_b64 = encode_image_to_base64(frame)

    payload = {
        "model": "meta-llama/Llama-Vision-Free",
        "messages": [
            {"role": "system", "content": "Answer questions based on the given image."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]}
        ]
    }

    response = together_client.chat.completions.create(**payload)

    if response and response.choices:
        return response.choices[0].message.content
    return "No relevant information found."

# ✅ Function to get chatbot response using Groq LLaMA-3
def get_groq_response(prompt):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=256
    )
    
    if response and response.choices:
        return response.choices[0].message.content
    return "I couldn't understand that."

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

# ✅ Function to plot the object on the screen and divide the frame into 3x3 grid
def plot_object(frame, object_position):
    # 3x3 grid on the screen
    height, width, _ = frame.shape
    grid_size = (width // 3, height // 3)

    # Plot the object on the screen
    cv2.circle(frame, object_position, 10, (0, 0, 255), -1)  # Mark the object with a red circle

    # Plot 3x3 grid
    for i in range(1, 3):
        cv2.line(frame, (i * grid_size[0], 0), (i * grid_size[0], height), (255, 255, 255), 2)
        cv2.line(frame, (0, i * grid_size[1]), (width, i * grid_size[1]), (255, 255, 255), 2)
    
    return frame

# ✅ Function to handle the mouse click and set the target location
def set_target(event, x, y, flags, param):
    global target_position, target_set
    if event == cv2.EVENT_LBUTTONDOWN:
        target_position = (x, y)
        target_set = True
        print(f"Target set at {target_position}")

# ✅ Function to provide movement direction based on Groq LLaMA model
def provide_direction(hand_position, target_position):
    # Calculate direction based on the target and hand position
    if hand_position and target_position:
        # Use the Groq LLaMA model to generate a response
        prompt = f"The user is at {hand_position}, and the target is at {target_position}. What direction should the user move to reach the target?"
        direction = get_groq_response(prompt)
        print(f"Direction: {direction}")
        speak_text(direction)

# ✅ Main Loop
cap = cv2.VideoCapture(0)

# Object position (user sets target via click)
target_position = None
target_set = False

cv2.namedWindow("Live Camera Feed")
cv2.setMouseCallback("Live Camera Feed", set_target)

while True:
    try:
        ret, frame = cap.read()
        if not ret:
            print("⚠ Camera error! Unable to capture image.")
            break

        # Analyze the scene and get description from Together AI every 1 second
        if time.time() % 1 < 0.1:  # Trigger every second
            print("📷 Processing visual input...")
            description = analyze_scene(frame)
            print(f"🌍 Vision AI: {description}")
            speak_text(description)

        # Track hand position
        hand_position = track_hand(frame)

        # If target is set, plot the object and calculate direction
        if target_set:
            frame = plot_object(frame, target_position)
            provide_direction(hand_position, target_position)

        # Show the frame with the plotted object and grid
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
