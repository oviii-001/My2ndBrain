"""
Muse AI 24/7 Protocol Bridge Server
Exposes an HTTP / JSON API for ESP32 and PC Simulator voice stations,
communicating directly with Meta Muse / Hatch over the Noise_XX WebSocket protocol.
Optimized for high-speed sub-second conversational turns.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from aiohttp import web

REPO_DIR = Path(__file__).resolve().parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from muse_ai.auth import MuseAuth
from muse_ai.client import MuseClient

STATE_DIR = REPO_DIR / ".muse-state"

class MuseBridge:
    def __init__(self):
        self.auth = None
        self.client = None
        self.lock = asyncio.Lock()

    async def get_client(self):
        if self.client and self.client.conn:
            try:
                pong = await self.client.ping()
                if pong.status == 200:
                    return self.client
            except Exception:
                pass
        
        # Connect & warm up
        if self.auth:
            try:
                await self.auth.close()
            except Exception:
                pass
        
        self.auth = MuseAuth(state_dir=STATE_DIR)
        self.client = MuseClient(self.auth, state_dir=STATE_DIR)
        await self.client.connect()
        return self.client

    async def ask(self, prompt: str) -> str:
        async with self.lock:
            client = await self.get_client()
            
            # 1. Baseline sequence tracking
            hist_before = await client.history(limit=5)
            events_before = hist_before.get("result", {}).get("chat_events", [])
            last_seq = events_before[-1].get("seq", 0) if events_before else 0

            # 2. Fast prompt dispatch (break on first server ACK event)
            payload = {
                "items": [{"type": "text", "text": prompt}],
                "node_id": client.device_id(),
                "capabilities": ["chat.send", "chat.read_history"],
            }
            try:
                async with asyncio.timeout(2.0):
                    async for _ in client._conn().subscribe("POST", "/chat/stream", payload):
                        break
            except TimeoutError:
                pass

            # 3. High-frequency polling (200ms interval, max 35 attempts = 7.0s)
            reply_text = None
            stable_count = 0
            last_partial = ""
            for _ in range(35):
                await asyncio.sleep(0.20)
                hist = await client.history(limit=5)
                events = hist.get("result", {}).get("chat_events", [])
                for e in reversed(events):
                    if e.get("seq", 0) > last_seq and e.get("role") == "assistant":
                        text = (e.get("display_text") or "").strip()
                        ready = e.get("display_text_ready")
                        if ready is True and text:
                            reply_text = text
                            break
                        if text:
                            if text == last_partial:
                                stable_count += 1
                                if stable_count >= 3:  # Text unchanged for 600ms
                                    reply_text = text
                                    break
                            else:
                                last_partial = text
                                stable_count = 0
                if reply_text:
                    break

            if not reply_text and events:
                for e in reversed(events):
                    if e.get("seq", 0) > last_seq and e.get("role") == "assistant":
                        reply_text = (e.get("display_text") or "").strip()
                        if reply_text:
                            break

            return reply_text or "Systems nominal, Boss."

bridge = MuseBridge()

async def handle_chat(request):
    try:
        data = await request.json()
        prompt = data.get("prompt") or data.get("message") or "Hello Jarvis"
        reply = await bridge.ask(prompt)
        return web.json_response({"prompt": prompt, "reply": reply})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_health(request):
    return web.json_response({"status": "ok", "backend": "muse.ai (Hatch Noise XX - UltraFast)"})

def create_app():
    app = web.Application()
    app.router.add_post("/api/chat", handle_chat)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/", handle_health)
    return app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8130))
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=port)
