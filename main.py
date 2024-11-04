import pyperclip
import pyaudio
import wave
import whisper
import os
import threading
import torch
import warnings
import sys

WAVE_OUTPUT_FILENAME = "output.wav"

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

# Global flag to control when to stop recording
stop_recording = False

# Function to capture key input in a separate thread


def listen_for_stop_key():
    global stop_recording
    input("Press Enter to stop recording...\n")
    stop_recording = True


# Recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
TRANSCRIPTION_OUTPUT_FILENAME = "transcription.txt"

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Open a stream on the first available input device
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

print("Recording...")

frames = []

# Start the thread that listens for the 'Enter' key press
listener_thread = threading.Thread(target=listen_for_stop_key)
listener_thread.start()

# Record audio until 'Enter' is pressed
while not stop_recording:
    data = stream.read(CHUNK)
    frames.append(data)

# Stop the stream
stream.stop_stream()
stream.close()
audio.terminate()

# Save the recorded data as a WAV file
with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))

# Load Whisper model and transcribe audio
model = whisper.load_model("base", device="cuda")  # You can change this to "tiny", "small", "medium", or "large"
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
