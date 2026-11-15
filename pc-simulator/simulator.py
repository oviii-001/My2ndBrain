"""
Project Sidecar — PC Hardware Simulator Client
Simulates the ESP32 DevKit V1 + INMP441 Microphone using your laptop's microphone.
Supports continuous hands-free wake-word detection ("Hey Jarvis") and Push-to-Talk.
"""

import sys
import io
import wave
import time
import queue
import argparse
import requests
import numpy as np

# Audio I/O
try:
    import sounddevice as sd
except ImportError:
    print("[!] sounddevice missing. Run: pip install sounddevice numpy requests pyttsx3")
    sys.exit(1)

# Text-to-Speech
try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 175)
except Exception:
    tts_engine = None

# Wake Word Engine (openWakeWord)
try:
    from openwakeword.model import Model as OpenWakeWordModel
    WAKE_WORD_AVAILABLE = True
except ImportError:
    WAKE_WORD_AVAILABLE = False

# Platform-specific Chime
def play_wake_chime():
    """Play a short ascending two-tone chime when wake word is detected."""
    try:
        import winsound
        winsound.Beep(880, 100)   # A5 (880 Hz) for 100ms
        winsound.Beep(1320, 140)  # E6 (1320 Hz) for 140ms
    except Exception:
        # Fallback print if winsound is not available
        sys.stdout.write('\a')
        sys.stdout.flush()

# Configuration
SAMPLE_RATE = 16000     # 16kHz standard for Whisper and INMP441
CHANNELS = 1            # Mono
CHUNK_SIZE = 1280       # 80ms chunks (1280 samples @ 16kHz) for openWakeWord
GATEWAY_URL = "https://sidecar-cloud-gateway.ismamhasanovi.workers.dev/api/voice"


def record_audio(duration_sec=4):
    """Record audio from laptop microphone as 16kHz 16-bit mono PCM."""
    print(f"[*] Listening for {duration_sec}s... Speak your command now!")
    audio_data = sd.rec(
        int(duration_sec * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='int16'
    )
    sd.wait()
    print("[*] Recording captured. Sending to Jarvis Cloud Gateway...")

    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())

    wav_io.seek(0)
    return wav_io.read()


def play_wav_bytes(wav_bytes):
    """Play raw WAV bytes directly using sounddevice."""
    try:
        import io, wave
        with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
            fs = wf.getframerate()
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
            sd.play(audio, fs)
            sd.wait()
            return True
    except Exception as e:
        print(f"[!] Neural audio playback error: {e}")
        return False


def speak_reply(text):
    """Speak the reply using pyttsx3 or Windows SAPI."""
    if not text:
        return

    if tts_engine:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
            return
        except Exception:
            pass

    # Fallback to PowerShell speech synthesis
    try:
        import subprocess
        clean_text = text.replace('"', '').replace("'", "")
        cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{clean_text}\')"'
        subprocess.run(cmd, shell=True)
    except Exception as e:
        print(f"[!] Speech synthesis error: {e}")


def query_gateway(audio_bytes, url=GATEWAY_URL):
    """Send audio bytes to Cloudflare Gateway and print/speak response."""
    try:
        start_t = time.time()
        headers = {'Content-Type': 'audio/wav'}
        resp = requests.post(url, data=audio_bytes, headers=headers, timeout=25)
        latency = round((time.time() - start_t) * 1000)

        if resp.status_code == 200:
            data = resp.json()
            transcript = data.get('transcript', '')
            reply = data.get('reply', '')
            audio_b64 = data.get('audio')

            print(f"\n" + "-" * 50)
            print(f"[JARVIS RESPONSE] ({latency}ms roundtrip)")
            print(f"> You said: \"{transcript}\"")
            print(f"> Jarvis:   \"{reply}\"")
            print("-" * 50 + "\n")

            # Try high-fidelity neural audio from Cloudflare first
            played = False
            if audio_b64:
                try:
                    import base64
                    wav_data = base64.b64decode(audio_b64)
                    played = play_wav_bytes(wav_data)
                except Exception:
                    played = False

            # Fallback to local TTS if neural audio not available
            if not played:
                speak_reply(reply)
        else:
            print(f"[!] Gateway error {resp.status_code}: {resp.text}")
    except requests.exceptions.ConnectionError:
        print(f"[!] Cannot connect to Cloudflare Gateway at {url}")
        print("    Check your internet connection or verify the gateway URL.")
    except Exception as e:
        print(f"[!] Request error: {e}")


def run_wake_word_loop(threshold=0.5, duration_sec=4, url=GATEWAY_URL):
    """
    Continuous hands-free listening loop.
    Monitors audio for 'Hey Jarvis' using openWakeWord, chimes, records, queries, and speaks.
    """
    if not WAKE_WORD_AVAILABLE:
        print("[!] openWakeWord is not installed. Run: pip install openwakeword")
        return

    print("=" * 60)
    print(" PROJECT SIDECAR — HANDS-FREE WAKE WORD ENGINE")
    print("=" * 60)
    print("[*] Loading 'hey_jarvis' neural network model...")

    try:
        ow = OpenWakeWordModel(wakeword_models=["hey_jarvis"])
    except Exception as e:
        print(f"[!] Error loading model: {e}")
        return

    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"[Audio warning: {status}]", file=sys.stderr)
        audio_queue.put(indata.copy())

    print(f"[+] Model active: 'hey_jarvis' (Confidence threshold: {threshold})")
    print(f"[+] Gateway target: {url}")
    print("[+] Continuous listening active.")
    print(">>> Say 'Hey Jarvis' anytime to speak your command! (Press Ctrl+C to stop) <<<\n")

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='int16',
            blocksize=CHUNK_SIZE,
            callback=audio_callback
        ):
            while True:
                chunk = audio_queue.get()
                prediction = ow.predict(chunk.flatten())
                score = prediction.get("hey_jarvis", 0.0)

                if score >= threshold:
                    print(f"\n[>>>] 'Hey Jarvis' DETECTED! (Confidence: {score:.2f})")
                    
                    # 1. Play immediate acknowledgment chime
                    play_wake_chime()

                    # 2. Drain any residual queue audio
                    while not audio_queue.empty():
                        try:
                            audio_queue.get_nowait()
                        except queue.Empty:
                            break

                    # 3. Record user's command
                    command_wav = record_audio(duration_sec=duration_sec)

                    # 4. Query Cloudflare Whisper + Muse backend
                    query_gateway(command_wav, url=url)

                    # 5. Reset model state and clear echo audio accumulated during playback
                    ow.reset()
                    time.sleep(0.2)
                    while not audio_queue.empty():
                        try:
                            audio_queue.get_nowait()
                        except queue.Empty:
                            break

                    print("[+] Listening resumed... Say 'Hey Jarvis'")
    except KeyboardInterrupt:
        print("\n[*] Exiting wake word listener.")


def run_manual_loop(duration_sec=4, url=GATEWAY_URL):
    """Push-to-talk manual loop."""
    print("=" * 60)
    print(" PROJECT SIDECAR — MANUAL PUSH-TO-TALK MODE")
    print(f" Target Gateway: {url}")
    print("=" * 60)
    print("Press Enter to speak a command, or type 'q' to quit.")

    while True:
        try:
            choice = input("\n[Press ENTER to speak, 'q' to quit]: ").strip().lower()
            if choice == 'q':
                print("Exiting simulator.")
                break

            audio = record_audio(duration_sec=duration_sec)
            query_gateway(audio, url=url)
        except KeyboardInterrupt:
            print("\nExiting.")
            break


def test_hardware():
    """Hardware self-test: tests microphone sensitivity and audio playback."""
    print("=" * 60)
    print(" HARDWARE SELF-TEST: Microphone & Audio Playback")
    print("=" * 60)
    print("[*] Testing Wake Chime...")
    play_wake_chime()

    print("[*] Testing Text-to-Speech (Jarvis Voice)...")
    speak_reply("Jarvis audio output system initialized and operational.")

    print("\n[*] Testing Microphone: Recording 3 seconds of ambient room audio...")
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
        print("[!] WARNING: Audio level very low! Check microphone gain in Windows settings.")
    else:
        print("[+] SUCCESS: Microphone is capturing clean, active audio!")

    print("[*] Playing back your recorded audio through speakers...")
    sd.play(audio_data, samplerate=SAMPLE_RATE)
    sd.wait()
    print("[+] Audio playback finished. Hardware self-test complete!\n")


def main():
    parser = argparse.ArgumentParser(description="Project Sidecar PC Hardware Simulator")
    parser.add_argument(
        "--manual", action="store_true",
        help="Run in manual push-to-talk mode instead of hands-free wake word."
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Run microphone and speaker hardware self-test."
    )
    parser.add_argument(
        "--threshold", type=float, default=0.5,
        help="Wake word detection confidence threshold (default: 0.5)."
    )
    parser.add_argument(
        "--duration", type=int, default=4,
        help="Command recording duration in seconds (default: 4)."
    )
    parser.add_argument(
        "--gateway", type=str, default=GATEWAY_URL,
        help="Target Cloudflare Gateway URL."
    )

    args = parser.parse_args()

    if args.test:
        test_hardware()
        return

    if args.manual or not WAKE_WORD_AVAILABLE:
        if not WAKE_WORD_AVAILABLE and not args.manual:
            print("[!] openWakeWord not available, falling back to manual mode.")
        run_manual_loop(duration_sec=args.duration, url=args.gateway)
    else:
        run_wake_word_loop(
            threshold=args.threshold,
            duration_sec=args.duration,
            url=args.gateway
        )


if __name__ == "__main__":
    main()
