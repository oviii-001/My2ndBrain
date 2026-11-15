"""
My2ndBrain — Iron Man JARVIS Voice Audition Sample
Plays a live preview of the British Male Neural Voice (en-GB-RyanNeural).
100% Free ($0.00/mo), Zero API keys, Zero Subscriptions.
"""

import asyncio
import io
import time
import edge_tts
import pygame

SAMPLE_TEXT = (
    "Good evening, Boss. All systems are online and fully operational. "
    "I am standing by to assist you from your room station. What are your orders, sir?"
)

async def play_sample():
    print("=" * 60)
    print(" MY2NDBRAIN — JARVIS VOICE AUDITION (en-GB-RyanNeural)")
    print("=" * 60)
    print(f"[*] Voice: British Male (en-GB-RyanNeural)")
    print(f"[*] Pitch: -1Hz (Calm butler resonance)")
    print(f"[*] Rate:  +2% (Articulate pacing)")
    print(f"[*] Cost:  $0.00 / month forever (No ElevenLabs subscription required)")
    print("-" * 60)
    print(f"> Synthesizing: \"{SAMPLE_TEXT}\"")
    
    t0 = time.time()
    comm = edge_tts.Communicate(SAMPLE_TEXT, "en-GB-RyanNeural", pitch="-1Hz", rate="+2%")
    
    mp3_buf = bytearray()
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            mp3_buf.extend(chunk["data"])
            
    gen_time = round(time.time() - t0, 2)
    print(f"[+] Audio generated in {gen_time}s ({len(mp3_buf)} bytes). Playing now...")
    
    if not pygame.mixer.get_init():
        pygame.mixer.init()
        
    pygame.mixer.music.load(io.BytesIO(mp3_buf))
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        time.sleep(0.05)
        
    print("[+] Playback complete. That is the authentic $0.00/mo Jarvis voice!\n")

if __name__ == "__main__":
    asyncio.run(play_sample())
