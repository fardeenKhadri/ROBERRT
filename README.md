# ROBERRT Project

## Overview

The **ROBERRT** project integrates multiple components, including depth estimation, object tracking, and audio-visual interaction. It leverages machine learning models and APIs for real-time video and audio analysis. The system allows users to interact with the environment by tracking objects, estimating depth, and receiving feedback in natural language or through serial communication.

This project is designed to provide real-time interaction through a webcam, using depth estimation models, and it includes a mechanism for controlling a device via serial communication based on the detected movement or position.

---

## Files

1. **run.py**: This file is responsible for real-time depth estimation from a webcam feed, using a pre-trained model to calculate depth and map it into a colored visualization. It also divides the frame into a grid, detects certain movement patterns, and sends commands to an external device via serial communication.

2. **main.py**: The core of this program handles communication with a remote model, where audio and video frames are sent asynchronously. It processes audio input and output streams, providing real-time feedback based on visual input. It leverages the **GenAI** client to manage interactions.

3. **eyeglasses_esp8266.ino**: This is an Arduino sketch for controlling an ESP8266 device, likely part of the physical setup to interact with the system via wireless communication (though details are minimal in the context of the provided files).

---

## Setup and Requirements

To set up the project, you'll need the following dependencies. You can install them by running the command:

```bash
pip install -r requirements.txt
```

### Requirements

- **Python 3.7+**
- **PyTorch**: For running the depth estimation and other machine learning models.
- **OpenCV**: For video capture and frame manipulation.
- **MediaPipe**: For hand tracking.
- **PyAudio**: For handling audio input and output.
- **Matplotlib**: For visualizing depth maps.
- **groq**: For integrating with Groq API for AI-powered responses.
- **GenAI**: To process audio-video interaction asynchronously.

### Dependencies List (requirements.txt)

```text
torch==1.11.0
opencv-python==4.5.1.48
mediapipe==0.8.10
pyaudio==0.2.11
pyttsx3==2.90
numpy==1.21.0
matplotlib==3.3.4
groq==0.1.0
genai==0.3.0
huggingface-hub==0.0.8
```

---

## Running the Project

### Step 1: Start the Depth Estimation

To begin the project, start by running the **run.py** file. This will capture frames from the webcam, estimate depth, and send commands to an external device.

```bash
python run.py
```

### Step 2: Use the Audio Loop

To enable audio interactions with the **GenAI** model, run the **main.py** file. This will establish a live connection to the model and handle both audio input and output.

```bash
python main.py --source 0
```

Make sure the microphone and audio input are set up correctly.

### Step 3: Interacting with the System

Once both parts are running:
1. Point your hand to the camera.
2. Click on the target area on the screen.
3. The system will provide a movement direction ("left", "right", "up", "down") to help the user navigate toward the selected target.

---

## Hardware Setup

If you're using the **eyeglasses_esp8266.ino** file for an embedded system, upload it to your **ESP8266** using the Arduino IDE or PlatformIO. This allows the system to wirelessly communicate with the computer and send/receive data as part of the interaction.

### Serial Communication

The system communicates with an external device via serial communication (e.g., to control a robot or a device). The serial commands ("S" for stop, "L" for left, "R" for right) are sent based on the movement suggestions determined by the system.

---

## Project Structure

```
ROBERRT/
├── run.py                # Depth estimation and device control
├── main.py               # Audio-video interaction with GenAI
├── eyeglasses_esp8266.ino # Arduino code for ESP8266 (embedded system)
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

---

## Troubleshooting

- **Serial Port Issues**: Ensure that the correct serial port is specified in **run.py** (e.g., `COM4` on Windows, `/dev/ttyUSB0` on Linux).
- **Model Loading Issues**: Make sure that the pre-trained model files are available in the specified directory (e.g., `checkpoints/depth_anything_v2_vits.pth`).
- **Webcam Issues**: If the webcam is not recognized, check the OpenCV installation or try manually specifying the camera source in **run.py**.

---

## Conclusion

The **ROBERRT** project is a comprehensive system for real-time depth estimation, visual interaction, and serial communication. It combines machine learning models for depth estimation, hand tracking, and object detection, along with audio-video interaction capabilities. The project provides a real-time, interactive system for users, making it useful for assistive technologies and robotic control applications.

