import os
import time
import threading
import subprocess
from pynput import keyboard

# CONFIGURABLE PART
COMMAND_TO_EXECUTE = ["sh", "/home/andrew/Documents/scripts/screenshot.sh"]  # Replace with your bash command
TRIGGER_KEY = "["  # Key to detect
REQUIRED_PRESSES = 2  # Number of times it needs to be pressed
TIME_WINDOW = 1.0  # Seconds within which the key must be pressed

# Global tracking
key_presses = []


def execute_command():
    """Execute the configured shell command."""
    try:
        print(f"Executing command: {' '.join(COMMAND_TO_EXECUTE)}")
        subprocess.Popen(COMMAND_TO_EXECUTE)
    except Exception as e:
        print(f"Failed to execute command: {e}")


def on_press(key):
    global key_presses

    try:
        if key.char == TRIGGER_KEY:
            current_time = time.time()
            key_presses.append(current_time)

            # Keep only recent presses
            key_presses = [t for t in key_presses if current_time - t < TIME_WINDOW]

            if len(key_presses) >= REQUIRED_PRESSES:
                # Fire the command in a new thread to avoid blocking
                threading.Thread(target=execute_command).start()
                key_presses = []  # Reset after triggering
    except AttributeError:
        # Some keys like shift, ctrl, etc. have no .char attribute
        pass


def main():
    print(f"Listening for '{TRIGGER_KEY * REQUIRED_PRESSES}' pressed within {TIME_WINDOW}s to trigger command...")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == "__main__":
    main()
