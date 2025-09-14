import wave
import os
from openai import OpenAI

# CONFIGURATION
INPUT_WAV_FILE = "generated/output1.wav"  # 7-minute WAV file
SPLIT_DIR = "generated/splits"
TRANSCRIPTION_OUTPUT = "generated/full_transcription.txt"
API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure split directory exists
os.makedirs(SPLIT_DIR, exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY)


def split_audio(file_path, output_dir):
    with wave.open(file_path, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()

        midpoint = n_frames // 2

        # First half
        wf.rewind()
        first_half = wf.readframes(midpoint)
        first_path = os.path.join(output_dir, "part1.wav")
        with wave.open(first_path, 'wb') as out:
            out.setnchannels(n_channels)
            out.setsampwidth(sampwidth)
            out.setframerate(framerate)
            out.writeframes(first_half)

        # Second half
        second_half = wf.readframes(n_frames - midpoint)
        second_path = os.path.join(output_dir, "part2.wav")
        with wave.open(second_path, 'wb') as out:
            out.setnchannels(n_channels)
            out.setsampwidth(sampwidth)
            out.setframerate(framerate)
            out.writeframes(second_half)

    return first_path, second_path


def transcribe(file_path):
    print(f"Transcribing: {file_path}")
    try:
        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return response.text
    except Exception as e:
        print(f"Failed to transcribe {file_path}: {e}")
        return ""


def main():
    part1, part2 = split_audio(INPUT_WAV_FILE, SPLIT_DIR)

    transcript1 = transcribe(part1)
    transcript2 = transcribe(part2)

    full_transcript = transcript1 + "\n\n" + transcript2
    print("\nFull Transcription:\n")
    print(full_transcript)

    with open(TRANSCRIPTION_OUTPUT, 'w') as f:
        f.write(full_transcript)
    print(f"\nSaved transcription to: {TRANSCRIPTION_OUTPUT}")


if __name__ == "__main__":
    main()
