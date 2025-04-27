import os
import time
import threading
import subprocess
import select
from evdev import InputDevice, categorize, ecodes, list_devices

# CONFIGURABLE PART
COMMAND_TO_EXECUTE = ["sh", "/home/andrew/Documents/scripts/screenshot.sh"]  # Replace with your bash command
TRIGGER_KEYCODE = "KEY_LEFTBRACE"  # The evdev keycode for "["
REQUIRED_PRESSES = 2  # Number of presses required
TIME_WINDOW = 1.0  # Time window in seconds

# Global tracking
key_presses = []


def execute_command():
    """Execute the configured shell command."""
    try:
        print(f"Executing command: {' '.join(COMMAND_TO_EXECUTE)}")
        subprocess.Popen(COMMAND_TO_EXECUTE)
    except Exception as e:
        print(f"Failed to execute command: {e}")


def main():
    # Find the keyboard device
    devices = [InputDevice(path) for path in list_devices()]
    keyboard = None
    for device in devices:
        if "keyboard" in device.name.lower() or "kbd" in device.name.lower():
            keyboard = device
            break

    if not keyboard:
        raise RuntimeError("No keyboard device found. You may need sudo or adjust udev permissions.")

    print(f"Listening for '{TRIGGER_KEYCODE}' pressed {REQUIRED_PRESSES} times within {TIME_WINDOW}s to trigger command (device: {keyboard.path})...")

    # No grabbing — don't block keyboard
    try:
        while True:
            r, _, _ = select.select([keyboard.fd], [], [])
            for fd in r:
                for event in keyboard.read():
                    if event.type == ecodes.EV_KEY:
                        key_event = categorize(event)
                        if key_event.keystate == key_event.key_down:
                            if key_event.keycode == TRIGGER_KEYCODE:
                                current_time = time.time()
                                key_presses.append(current_time)

                                # Keep only recent key presses within the time window
                                key_presses[:] = [t for t in key_presses if current_time - t < TIME_WINDOW]

                                if len(key_presses) >= REQUIRED_PRESSES:
                                    # Fire the command in a new thread
                                    threading.Thread(target=execute_command).start()
                                    key_presses.clear()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")


if __name__ == "__main__":
    main()
