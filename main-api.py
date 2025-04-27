import pyperclip
import pyaudio
import wave
import os
import threading
import warnings
import time
from openai import OpenAI
from pynput import keyboard
from playsound import playsound

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Constants
WAVE_OUTPUT_FILENAME = "generated/output.wav"
TRANSCRIPTION_OUTPUT_FILENAME = "generated/transcription.txt"
START_BEEP_FILENAME = "sounds/beep-06.wav"
STOP_BEEP_FILENAME = "sounds/beep-08b.wav"
COPY_BEEP_FILENAME = "sounds/beep-24.wav"

# Setup
os.makedirs("generated", exist_ok=True)

try:
    os.remove(WAVE_OUTPUT_FILENAME)
except FileNotFoundError:
    pass

warnings.filterwarnings("ignore", category=FutureWarning)

# Global Flags
recording = False
stop_recording = False
key_presses = []

# PyAudio Setup
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
audio = pyaudio.PyAudio()


def upload_and_transcribe(file_path):
    """Uploads file to Whisper API and retrieves transcription."""
    try:
        with open(file_path, "rb") as audio_file:
            print("Sending audio to Whisper API...")
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return response.text
    except Exception as e:
        print(f"Error during transcription: {e}")
        return ""


def record_and_transcribe():
    global recording, stop_recording

    playsound(START_BEEP_FILENAME)

    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    print("Recording...")
    while not stop_recording:
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()

    playsound(STOP_BEEP_FILENAME)

    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print("Recording stopped. Starting transcription...")

    transcription_text = upload_and_transcribe(WAVE_OUTPUT_FILENAME)

    if transcription_text:
        with open(TRANSCRIPTION_OUTPUT_FILENAME, 'w') as f:
            f.write(transcription_text)
        print(f"Transcription saved to {TRANSCRIPTION_OUTPUT_FILENAME}")
        pyperclip.copy(transcription_text)
        print("Transcription copied to clipboard!")
        playsound(COPY_BEEP_FILENAME)
    else:
        print("No transcription was produced.")

    recording = False
    stop_recording = False


def toggle_recording():
    global recording, stop_recording

    if not recording:
        recording = True
        stop_recording = False
        record_thread = threading.Thread(target=record_and_transcribe)
        record_thread.start()
    else:
        stop_recording = True


def on_press(key):
    global key_presses

    if key == keyboard.KeyCode(char=';'):
        current_time = time.time()
        key_presses.append(current_time)

        key_presses = [t for t in key_presses if current_time - t < 1]

        if len(key_presses) >= 2:
            toggle_recording()
            key_presses = []


print("Listening for ';' pressed 2 times in rapid succession to start/stop recording...")
listener = keyboard.Listener(on_press=on_press)
listener.start()

try:
    listener.join()
except KeyboardInterrupt:
    print("\nShutting down gracefully...")
finally:
    audio.terminate()
