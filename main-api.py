import pyperclip
import pyaudio
import wave
import os
import threading
import warnings
import time
import select
from openai import OpenAI
from playsound import playsound
from evdev import InputDevice, categorize, ecodes, list_devices

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


# Find ALL keyboard input devices (not just the first one)
devices = [InputDevice(path) for path in list_devices()]
keyboards = []

# Exclude non-keyboard devices
exclude_keywords = ['mouse', 'trackpad', 'touchpad', 'touch', 'pointer']

for device in devices:
    try:
        caps = device.capabilities()
        # Check if device has keyboard capabilities
        if ecodes.EV_KEY in caps:
            device_name_lower = device.name.lower()
            # Skip if it's clearly not a keyboard
            if any(keyword in device_name_lower for keyword in exclude_keywords):
                continue
            
            # Check if it has typical keyboard keys to confirm it's a keyboard
            key_codes = caps.get(ecodes.EV_KEY, [])
            if any(key in key_codes for key in [ecodes.KEY_A, ecodes.KEY_SPACE, ecodes.KEY_ENTER]):
                keyboards.append(device)
    except (OSError, PermissionError) as e:
        # Skip devices we can't access (might need permissions)
        print(f"Warning: Could not access device {device.path}: {e}")
        continue

if not keyboards:
    print("No keyboard devices found. Attempting to list all input devices...")
    all_devices = [InputDevice(path) for path in list_devices()]
    print("Available input devices:")
    for dev in all_devices:
        try:
            print(f"  - {dev.name} ({dev.path})")
        except:
            pass
    raise RuntimeError("No keyboard device found. You may need to add your user to the 'input' group: sudo usermod -aG input $USER")

# Use all keyboard devices so USB keyboards work
print(f"Found {len(keyboards)} keyboard device(s):")
for kb in keyboards:
    print(f"  - {kb.name} ({kb.path})")

print("\nListening for ';' pressed 2 times in rapid succession to start/stop recording...")

# Main loop to detect key presses from ALL keyboards
try:
    while True:
        # Use select to wait for input on any keyboard
        fds = [kb.fd for kb in keyboards]
        r, _, _ = select.select(fds, [], [])
        
        for fd in r:
            # Find which keyboard this fd belongs to
            keyboard = next(kb for kb in keyboards if kb.fd == fd)
            try:
                for event in keyboard.read():
                    if event.type == ecodes.EV_KEY:
                        key_event = categorize(event)
                        if key_event.keystate == key_event.key_down:
                            # Handle keycode as string, list, or tuple
                            keycode = key_event.keycode
                            is_semicolon = False
                            
                            if isinstance(keycode, (list, tuple)):
                                is_semicolon = 'KEY_SEMICOLON' in keycode
                            else:
                                is_semicolon = keycode == 'KEY_SEMICOLON'
                            
                            if is_semicolon:
                                current_time = time.time()
                                key_presses.append(current_time)
                                key_presses = [t for t in key_presses if current_time - t < 1]
                                if len(key_presses) >= 2:
                                    toggle_recording()
                                    key_presses = []
            except OSError:
                # Device might have been disconnected, skip it
                continue
except KeyboardInterrupt:
    print("\nShutting down gracefully...")
finally:
    audio.terminate()
