import pyperclip
import pyaudio
import wave
import whisper
import os
import threading
import torch
import warnings
import time
from pynput import keyboard
from playsound import playsound  # Add this for playing beep sounds

WAVE_OUTPUT_FILENAME = "generated/output.wav"
TRANSCRIPTION_OUTPUT_FILENAME = "generated/transcription.txt"
START_BEEP_FILENAME = "sounds/beep-06.wav"  # Audio file for start beep
STOP_BEEP_FILENAME = "sounds/beep-08b.wav"    # Audio file for stop beep
COPY_BEEP_FILENAME = "sounds/beep-24.wav"    # Audio file for copy-to-clipboard beep

# Clean up: remove the WAV file if you no longer need it
try:
    os.remove(WAVE_OUTPUT_FILENAME)
except:
    pass

warnings.filterwarnings("ignore", category=FutureWarning)

if torch.cuda.is_available():
    print("Using GPU:", torch.cuda.get_device_name(0))
else:
    print("Using CPU")

# Global flags and variables
recording = False
stop_recording = False
key_presses = []  # To track recent 'a' keypress times

# Initialize PyAudio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
audio = pyaudio.PyAudio()

# Function to handle recording and transcription


def record_and_transcribe():
    global recording, stop_recording

    # Play start beep
    playsound(START_BEEP_FILENAME)

    # Open a stream on the first available input device
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    frames = []

    print("Recording...")
    while not stop_recording:
        data = stream.read(CHUNK)
        frames.append(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()

    # Play stop beep
    playsound(STOP_BEEP_FILENAME)

    # Save the recorded data as a WAV file
    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print("Recording stopped. Transcribing...")

    # Load Whisper model and transcribe audio
    model = whisper.load_model("base", device="cuda" if torch.cuda.is_available() else "cpu")
    result = model.transcribe(WAVE_OUTPUT_FILENAME)

    # Write the transcription result to a file
    with open(TRANSCRIPTION_OUTPUT_FILENAME, 'w') as f:
        f.write(result["text"])

    print(f"Transcription saved to {TRANSCRIPTION_OUTPUT_FILENAME}")

    # Copy the transcription to clipboard
    with open(TRANSCRIPTION_OUTPUT_FILENAME, 'r') as f:
        transcription_text = f.read()
    pyperclip.copy(transcription_text)
    print("Transcription copied to clipboard!")

    # Play copy-to-clipboard beep
    playsound(COPY_BEEP_FILENAME)

    # Reset flags for the next round
    recording = False
    stop_recording = False


def toggle_recording():
    global recording, stop_recording

    if not recording:
        # Start recording
        recording = True
        stop_recording = False
        record_thread = threading.Thread(target=record_and_transcribe)
        record_thread.start()
    else:
        # Stop recording
        stop_recording = True


def on_press(key):
    global key_presses

    # Check if the key pressed is 'a'
    if key == keyboard.KeyCode(char=';'):
        # Record the current time of the key press
        current_time = time.time()
        key_presses.append(current_time)

        # Remove key presses older than 1 second
        key_presses = [t for t in key_presses if current_time - t < 1]

        # Check if there were 3 ";" presses within the last second
        if len(key_presses) >= 2:
            toggle_recording()
            key_presses = []  # Reset after triggering


# Start listening to the hotkey pattern
print("Listening for ';' pressed 2 times in rapid succession to start/stop recording...")
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()  # Keep the listener running indefinitely

# Cleanup
audio.terminate()
