"""
Muse AI 24/7 Protocol Bridge Server
Exposes an HTTP / JSON API for ESP32 and PC Simulator voice stations,
communicating directly with Meta Muse / Hatch over the Noise_XX WebSocket protocol.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from aiohttp import web

# Local package
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
        
        # Reconnect
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
            
            # Baseline history
            history_before = await client.history(limit=5)
            events_before = history_before.get("result", {}).get("chat_events", [])
            last_id = events_before[-1].get("event_id") if events_before else None

            # Dispatch prompt
            await client.chat_stream(prompt=prompt, stream_timeout=15.0)

            # Poll for Jarvis response
            reply_text = None
            for _ in range(12):
                await asyncio.sleep(1.2)
                hist = await client.history(limit=5)
                events = hist.get("result", {}).get("chat_events", [])
                for e in reversed(events):
                    display_text = e.get("display_text", "")
                    if display_text and e.get("event_id") != last_id and (e.get("agent_id") or "assistant" in str(e).lower()):
                        reply_text = display_text
                        break
                if reply_text:
                    break

            if not reply_text and events:
                latest = events[-1]
                reply_text = latest.get("display_text") or "I am listening, sir."

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
    return web.json_response({"status": "ok", "backend": "muse.ai (Hatch Noise XX)"})

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
