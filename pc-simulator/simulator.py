"""
Project Sidecar — PC Hardware Simulator Client
Simulates the ESP32 DevKit V1 + INMP441 Microphone using your laptop's microphone.
"""

import sys
import io
import wave
import time
import requests
import numpy as np

try:
    import sounddevice as sd
except ImportError:
    print("Please install sounddevice: pip install sounddevice numpy requests pyttsx3")
    sys.exit(1)

try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    # Set natural rate
    tts_engine.setProperty('rate', 175)
except Exception:
    tts_engine = None

# Configuration
SAMPLE_RATE = 16000  # 16kHz standard for Whisper and INMP441
CHANNELS = 1         # Mono
# Live production Cloudflare Worker deployed via Cloudflare MCP
GATEWAY_URL = "https://sidecar-cloud-gateway.ismamhasanovi.workers.dev/api/voice"

def record_audio(duration_sec=4):
    """Record audio from laptop microphone as 16kHz 16-bit mono PCM."""
    print(f"\n[*] Listening for {duration_sec} seconds... Speak now!")
    audio_data = sd.rec(
        int(duration_sec * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='int16'
    )
    sd.wait()
    print("[*] Recording complete. Sending to Jarvis Cloud Gateway...")
    
    # Pack into in-memory WAV file
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())
    
    wav_io.seek(0)
    return wav_io.read()

def speak_reply(text):
    """Speak the reply using pyttsx3 or Windows SAPI."""
    if tts_engine:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
            return
        except Exception:
            pass

    # Fallback to PowerShell speech synthesis
    import subprocess
    clean_text = text.replace('"', '').replace("'", "")
    cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{clean_text}\')"'
    subprocess.run(cmd, shell=True)

def query_gateway(audio_bytes, url=GATEWAY_URL):
    """Send audio bytes to Cloudflare Gateway and print response."""
    try:
        start_t = time.time()
        headers = {'Content-Type': 'audio/wav'}
        resp = requests.post(url, data=audio_bytes, headers=headers, timeout=20)
        latency = round((time.time() - start_t) * 1000)
        
        if resp.status_code == 200:
            data = resp.json()
            transcript = data.get('transcript', '')
            reply = data.get('reply', '')
            print(f"\n--- [JARVIS RESPONSE] ({latency}ms) ---")
            print(f"> You said: {transcript}")
            print(f"> Jarvis:   {reply}\n")
            
            # Speak the reply aloud through laptop speaker or Bluetooth Echo Dot
            speak_reply(reply)
        else:
            print(f"[!] Gateway error {resp.status_code}: {resp.text}")
    except requests.exceptions.ConnectionError:
        print(f"[!] Cannot connect to Cloudflare Gateway at {url}")
        print("    Make sure 'npm run dev' is running in the cloud-gateway directory,")
        print("    or point GATEWAY_URL to your deployed Cloudflare Worker URL.")

def test_mic_and_speaker():
    """Test recording from microphone and playing back through speakers immediately."""
    print("=" * 60)
    print(" HARDWARE SELF-TEST: Microphone & Audio Playback")
    print("=" * 60)
    print("[*] Testing Text-to-Speech (Jarvis Voice)...")
    speak_reply("Jarvis audio output system initialized and operational.")
    
    print("\n[*] Testing Microphone: Recording 3 seconds of your voice...")
    audio_data = sd.rec(
        int(3 * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='int16'
    )
    sd.wait()
    max_amp = np.max(np.abs(audio_data))
    print(f"[*] Recording complete. Peak amplitude: {max_amp} (out of 32767)")
    
    if max_amp < 500:
        print("[!] WARNING: Audio level very low! Check microphone volume in Windows settings.")
    else:
        print("[+] SUCCESS: Microphone is working cleanly!")
    
    print("[*] Playing back your recorded audio through speakers...")
    sd.play(audio_data, samplerate=SAMPLE_RATE)
    sd.wait()
    print("[+] Audio playback finished. Hardware self-test complete!\n")

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['--test', '-t', '--test-audio']:
        test_mic_and_speaker()
        return

    print("=" * 60)
    print(" PROJECT SIDECAR — PC AUDIO HARDWARE SIMULATOR")
    print(f" Target Gateway: {GATEWAY_URL}")
    print(" Tip: Run with '--test' to test mic and speakers offline")
    print("=" * 60)
    print("Press Enter to speak a command, or type 'q' to quit.")
    
    while True:
        choice = input("\n[Press ENTER to talk, 'q' to quit]: ").strip().lower()
        if choice == 'q':
            print("Exiting simulator.")
            break
        
        audio = record_audio(duration_sec=4)
        query_gateway(audio)

if __name__ == "__main__":
    main()
