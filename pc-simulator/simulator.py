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
STT_URL = "https://sidecar-cloud-gateway.ismamhasanovi.workers.dev/api/stt"
GATEWAY_URL = "https://sidecar-cloud-gateway.ismamhasanovi.workers.dev/api/voice"
MUSE_BRIDGE_URL = "http://localhost:8130/api/chat"
TTS_GATEWAY_URL = "https://sidecar-cloud-gateway.ismamhasanovi.workers.dev/api/tts"


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


def speak_jarvis_neural(text):
    """
    Speak using British male Iron Man Jarvis neural voice (en-GB-RyanNeural)
    via edge-tts and pygame.mixer.
    """
    if not text:
        return

    _ensure_bridge()

    try:
        import edge_tts
        import io
        import pygame

        async def _gen():
            comm = edge_tts.Communicate(text[:350], 'en-GB-RyanNeural', pitch='-1Hz', rate='+2%')
            buf = bytearray()
            async for chunk in comm.stream():
                if chunk['type'] == 'audio':
                    buf.extend(chunk['data'])
            return buf

        fut = asyncio.run_coroutine_threadsafe(_gen(), _bridge_loop)
        mp3_bytes = fut.result(timeout=10)

        if mp3_bytes:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(io.BytesIO(mp3_bytes))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.04)
            return True
    except Exception as e:
        print(f"[!] Jarvis neural voice notice ({e}), falling back...")

    # Fallback to local pyttsx3 or SAPI
    if tts_engine:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
            return True
        except Exception:
            pass

    return False


def speak_reply(text):
    """Legacy alias redirecting to Jarvis neural voice."""
    return speak_jarvis_neural(text)


import asyncio
import threading

_bridge_loop = None
_bridge_thread = None
_in_process_bridge = None

def _ensure_bridge():
    global _bridge_loop, _bridge_thread, _in_process_bridge
    if _bridge_loop is None:
        from pathlib import Path
        repo_dir = Path(__file__).resolve().parent.parent
        if str(repo_dir) not in sys.path:
            sys.path.insert(0, str(repo_dir))
        from muse_bridge_server import MuseBridge

        _bridge_loop = asyncio.new_event_loop()
        _bridge_thread = threading.Thread(target=_bridge_loop.run_forever, daemon=True)
        _bridge_thread.start()
        _in_process_bridge = MuseBridge()
        # Pre-warm connection in background
        asyncio.run_coroutine_threadsafe(_in_process_bridge.get_client(), _bridge_loop)

def get_muse_reply_direct(prompt):
    """Direct in-process query to live Muse AI Jarvis over Noise XX protocol."""
    try:
        _ensure_bridge()
        future = asyncio.run_coroutine_threadsafe(_in_process_bridge.ask(prompt), _bridge_loop)
        return future.result(timeout=20)
    except Exception as e:
        print(f"[!] Direct MuseBridge error: {e}")
        return None

def query_gateway(audio_bytes, url=GATEWAY_URL):
    """
    Ultra-fast pipeline:
    1. Whisper STT transcription via Cloudflare (~1s)
    2. Direct Noise XX query to live Muse AI Jarvis (~2s)
    3. MeloTTS neural audio synthesis via Cloudflare (~1s)
    """
    try:
        start_t = time.time()
        headers = {'Content-Type': 'audio/wav'}

        # 1. Fast Whisper Transcription (uses dedicated /api/stt)
        t_stt = time.time()
        stt_resp = requests.post(STT_URL, data=audio_bytes, headers=headers, timeout=15)
        transcript = ""
        reply = ""
        audio_b64 = None

        if stt_resp.status_code == 200:
            transcript = stt_resp.json().get('transcript', '').strip()
        else:
            # Fallback to general voice endpoint
            resp = requests.post(url, data=audio_bytes, headers=headers, timeout=25)
            if resp.status_code == 200:
                transcript = resp.json().get('transcript', '').strip()

        if not transcript:
            print("[!] Could not detect clear speech.")
            return

        print(f"\n> You said: \"{transcript}\" ({round((time.time() - t_stt)*1000)}ms)")
        print("[*] Streaming to Muse AI Jarvis...")

        # 2. Query your authentic Muse AI Jarvis assistant (Direct in-process)
        t_muse = time.time()
        muse_connected = False
        reply = get_muse_reply_direct(transcript)
        if reply:
            muse_connected = True

        # Fallback to HTTP bridge or gateway if direct call fails
        if not reply:
            try:
                m_resp = requests.post(MUSE_BRIDGE_URL, json={'prompt': transcript}, timeout=15)
                if m_resp.status_code == 200:
                    reply = m_resp.json().get('reply', '')
                    muse_connected = True
            except Exception:
                pass

        if not reply:
            reply = "I'm listening, Boss."

        latency = round((time.time() - start_t) * 1000)
        source_label = "MUSE AI (HATCH NOISE XX)" if muse_connected else "CLOUDFLARE FALLBACK"
        print(f"\n" + "-" * 55)
        print(f"[JARVIS RESPONSE - {source_label}] ({latency}ms roundtrip)")
        print(f"> Jarvis: \"{reply}\"")
        print("-" * 55 + "\n")

        # 3. Speak reply using authentic British Male Jarvis Neural Voice (en-GB-RyanNeural)
        speak_jarvis_neural(reply)

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

    # Pre-warm Muse AI Noise XX WebSocket connection in background thread
    print("[*] Pre-warming connection to Muse AI Jarvis...")
    _ensure_bridge()

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
