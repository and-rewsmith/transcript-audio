import pyaudio
import wave
import whisper
import os
import threading
import torch
import warnings
import sys

warnings.filterwarnings("ignore", category=FutureWarning)


# if torch.cuda.is_available():
#     print("Using GPU:", torch.cuda.get_device_name(0))
# else:
#     print("Using CPU")

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
WAVE_OUTPUT_FILENAME = "output.wav"

# Initialize PyAudio
audio = pyaudio.PyAudio()

# # List available input devices
# for i in range(audio.get_device_count()):
#     info = audio.get_device_info_by_index(i)
#     print(f"Device {i}: {info['name']}")

# Open a stream on the first available input device
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

print("Recording...")

frames = []

# Start the thread that listens for the 'p' key press
listener_thread = threading.Thread(target=listen_for_stop_key)
listener_thread.start()

# Record audio until 'p' is pressed
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

# print(f"Saved recording to {WAVE_OUTPUT_FILENAME}")

# Transcribe the audio using OpenAI Whisper
# print("Transcribing audio with Whisper...")
model = whisper.load_model("base")  # You can change this to "tiny", "small", "medium", or "large"
result = model.transcribe(WAVE_OUTPUT_FILENAME)

# Print the transcription result
print("Transcription:")
print(result["text"])

# Clean up: remove the WAV file if you no longer need it
os.remove(WAVE_OUTPUT_FILENAME)
