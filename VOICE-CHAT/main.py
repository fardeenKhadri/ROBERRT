import asyncio
import base64
import io
import os
import sys
import traceback
import argparse
import groq
import huggingface_hub

import cv2
import pyaudio
import PIL.Image
from dotenv import load_dotenv

from google import genai

if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup
    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 512

# Move load_dotenv() to the top, before we try to access any env vars
load_dotenv()

MODEL = os.getenv('MODELS')

SYSTEM_PROMPT = "Your name is Dharshini, when prompted to provide sources or code by the user tell them you cannot help them with that. You can see what the user sees you only analyse it and provide feedback imagining that the user is visually impaired and cannot see well. Be gentle in your replies"

# Get API key from environment variable
api_key = os.getenv('API_KEY')
if not api_key:
    raise ValueError("Please set the API_KEY environment variable")

client = genai.Client(
    api_key=api_key,
    http_options={'api_version': 'v1alpha'})

CONFIG = {
    "generation_config": {
        "response_modalities": ["AUDIO"],
        "speech_config": "Aoede",
    },
    "system_instruction": SYSTEM_PROMPT,
}




pya = pyaudio.PyAudio()

class AudioLoop:
    def __init__(self, source):
        self.audio_in_queue = asyncio.Queue()
        self.audio_out_queue = asyncio.Queue()
        self.video_out_queue = asyncio.Queue()
        self.source = source

        self.session = None

        self.send_text_task = None
        self.receive_audio_task = None
        self.play_audio_task = None

    async def send_text(self):
        while True:
            text = await asyncio.to_thread(input, "message > ")
            if text.lower() == "q":
                break
            await self.session.send(text or ".", end_of_turn=True)

    def _get_frame(self, cap):
        # Read the frame
        ret, frame = cap.read()
        if not ret:
            return None

        # Convert BGR (OpenCV default) to RGB (Pillow format)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        img = PIL.Image.fromarray(frame)
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        mime_type = "image/jpeg"
        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}


    async def get_frames(self):
        # This takes about a second, and will block the whole program
        # causing the audio pipeline to overflow if you don't to_thread it.
        cap = await asyncio.to_thread(cv2.VideoCapture, self.source)  # 0 represents the default camera

        while True:
            frame = await asyncio.to_thread(self._get_frame, cap)
            if frame is None:
                break

            await asyncio.sleep(1.0)

            self.video_out_queue.put_nowait(frame)

        # Release the VideoCapture object
        cap.release()

    async def send_frames(self):
        while True:
            frame = await self.video_out_queue.get()
            await self.session.send(frame)

    async def listen_audio(self):
        pya = pyaudio.PyAudio()

        mic_info = pya.get_default_input_device_info()
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        while True:
            data = await asyncio.to_thread(stream.read, CHUNK_SIZE)
            self.audio_out_queue.put_nowait(data)

    async def send_audio(self):
        while True:
            chunk = await self.audio_out_queue.get()
            await self.session.send({"data": chunk, "mime_type": "audio/pcm"})

    async def receive_audio(self):
        "Background task to reads from the websocket and write pcm chunks to the output queue"
        while True:
            async for response in self.session.receive():
                server_content = response.server_content
                if server_content is not None:
                    model_turn = server_content.model_turn
                    if model_turn is not None:
                        parts = model_turn.parts

                        for part in parts:
                            if part.text is not None:
                                print(part.text, end="")
                            elif part.inline_data is not None:
                                self.audio_in_queue.put_nowait(part.inline_data.data)

                    server_content.model_turn = None
                    turn_complete = server_content.turn_complete
                    if turn_complete:
                        # If you interrupt the model, it sends a turn_complete.
                        # For interruptions to work, we need to stop playback.
                        # So empty out the audio queue because it may have loaded
                        # much more audio than has played yet.
                        print("Turn complete")
                        while not self.audio_in_queue.empty():
                            self.audio_in_queue.get_nowait()

    async def play_audio(self):
        pya = pyaudio.PyAudio()
        stream = await asyncio.to_thread(
            pya.open, format=FORMAT, channels=CHANNELS, rate=RECEIVE_SAMPLE_RATE, output=True
        )
        while True:
            bytestream = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, bytestream)

    async def run(self):
        """Takes audio chunks off the input queue, and writes them to files.

        Splits and displays files if the queue pauses for more than `max_pause`.
        """
        async with (
            client.aio.live.connect(model=MODEL, config=CONFIG) as session,
            asyncio.TaskGroup() as tg,
        ):
            self.session = session

            send_text_task = tg.create_task(self.send_text())

            def cleanup(task):
                for t in tg._tasks:
                    t.cancel()

            send_text_task.add_done_callback(cleanup)

            tg.create_task(self.listen_audio())
            tg.create_task(self.send_audio())
            tg.create_task(self.get_frames())
            tg.create_task(self.send_frames())
            tg.create_task(self.receive_audio())
            tg.create_task(self.play_audio())

            def check_error(task):
                if task.cancelled():
                    return

                if task.exception() is None:
                    return

                e = task.exception()
                traceback.print_exception(None, e, e.__traceback__)
                sys.exit(1)

            for task in tg._tasks:
                task.add_done_callback(check_error)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Audio Loop Program")
    parser.add_argument("--source", type=int, required=True, help="Source argument (e.g., 0 for default audio source)")
    args = parser.parse_args()

    # Pass the parsed argument to the class
    main = AudioLoop(args.source)

    # Run the async function
    asyncio.run(main.run())