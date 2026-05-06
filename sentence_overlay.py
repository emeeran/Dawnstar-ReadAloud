#!/usr/bin/env python3
"""Display current sentence in an on-screen overlay while TTS is speaking."""

import os
import sys
import time
import subprocess
from pathlib import Path

SENTENCE_FILE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/tts_cursor_state/current_sentence.txt"

def show_notification(sentence: str) -> None:
    """Show desktop notification with current sentence."""
    # Use urgent hint and longer timeout for visibility
    # -r 12345: replace existing notification with same ID
    # -u critical: urgent priority (stays visible longer)
    subprocess.run([
        "notify-send",
        "-i", "audio-volume-high-symbolic",
        "-u", "normal",
        "-t", "3000",  # 3 second timeout
        "-r", "12345",  # Replace previous
        "TTS Speaking",
        sentence[:200] + ("..." if len(sentence) > 200 else "")
    ], capture_output=True)

def main() -> None:
    sentence_file = Path(SENTENCE_FILE)
    last_sentence = ""
    last_update = 0
    
    print(f"Monitoring: {sentence_file}", file=sys.stderr)
    
    while True:
        try:
            if sentence_file.exists():
                current = sentence_file.read_text().strip()
                if current and current != last_sentence:
                    last_sentence = current
                    show_notification(current)
                    last_update = time.time()
            else:
                # Check if TTS is still running
                tts_running = any(
                    "tts" in p and "sentence" in p 
                    for p in subprocess.run(
                        ["pgrep", "-fa", "tts"], 
                        capture_output=True, text=True
                    ).stdout.lower().split("\n")
                )
                if not tts_running and time.time() - last_update > 2:
                    break
                    
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            
        time.sleep(0.15)
    
    # Final notification
    subprocess.run([
        "notify-send",
        "-i", "audio-volume-high-symbolic",
        "-t", "1500",
        "TTS",
        "Finished speaking"
    ], capture_output=True)

if __name__ == "__main__":
    main()
