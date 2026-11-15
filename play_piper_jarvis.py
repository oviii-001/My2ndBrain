"""
My2ndBrain — YouTube/GitHub Developers' Community JARVIS Model (jgkawell/jarvis)
The exact open-source neural voice model used in viral YouTube JARVIS projects.
100% Free ($0.00/mo), Open Source, Trained on Paul Bettany's Marvel lines.
"""

import os
import time
import requests
import pygame

SAMPLE_URL = "https://huggingface.co/jgkawell/jarvis/resolve/main/en/en_GB/jarvis/high/samples/speaker_0.mp3"
CACHE_FILE = "piper_jarvis_sample.mp3"

def play():
    print("=" * 60)
    print(" VIRAL YOUTUBE / GITHUB COMMUNITY JARVIS MODEL")
    print(" Repo: jgkawell/jarvis (Piper ONNX)")
    print(" Training: Paul Bettany Voice Lines (Marvel Cinematic Universe)")
    print(" Cost: $0.00 / month (100% Free, Open Source)")
    print("=" * 60)

    if not os.path.exists(CACHE_FILE):
        print("[*] Downloading official community sample from Hugging Face...")
        resp = requests.get(SAMPLE_URL)
        with open(CACHE_FILE, "wb") as f:
            f.write(resp.content)
        print("[+] Download complete!")

    print("[*] Playing community JARVIS voice through your speakers...")
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.music.load(CACHE_FILE)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.05)
    print("[+] Playback complete!\n")

if __name__ == "__main__":
    play()
