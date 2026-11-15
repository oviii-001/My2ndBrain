export interface Env {
  AI: any;
  WAKE_WORD?: string;
  MUSE_BRIDGE_URL?: string; // 24/7 Meta Muse AI Bridge endpoint
  HF_TOKEN?: string; // Hugging Face Free User Token
  HF_SPACE_URL?: string; // Free Hugging Face Space Endpoint (jgkawell/jarvis)
}

/**
 * Dedicated Brain: Meta Muse AI (Personal Account over Hatch Noise_XX Protocol).
 * Dispatches voice queries directly to your authentic Muse AI assistant with zero LLM fallbacks.
 */
async function queryJarvisBrain(prompt: string, env: Env): Promise<string> {
  if (env.MUSE_BRIDGE_URL) {
    try {
      const targetUrl = env.MUSE_BRIDGE_URL.replace(/\/$/, "");
      const resp = await fetch(`${targetUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt })
      });
      if (resp.ok) {
        const data: any = await resp.json();
        if (data?.reply) return data.reply;
      }
    } catch (err) {
      console.error("Muse AI Bridge connection error:", err);
      return "Unable to connect to Meta Muse AI, sir.";
    }
  }

  return "Meta Muse AI Bridge is offline, sir. Please start muse_bridge_server.";
}

/**
 * Dedicated Voice: Hugging Face Piper JARVIS (Paul Bettany Voice).
 * Zero robotic fallbacks.
 */
async function generateSpeech(text: string, env: Env): Promise<string | null> {
  const cleanedText = text.replace(/[*_#`]/g, "").slice(0, 500);
  const hfSpaceUrl = env.HF_SPACE_URL || "https://ekc4-jarvis-tts.hf.space";

  try {
    const targetUrl = hfSpaceUrl.replace(/\/$/, "");
    let resp = await fetch(`${targetUrl}/speak`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(env.HF_TOKEN ? { "Authorization": `Bearer ${env.HF_TOKEN}` } : {})
      },
      body: JSON.stringify({ text: cleanedText })
    });

    if (!resp.ok) {
      resp = await fetch(`${targetUrl}/api/tts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(env.HF_TOKEN ? { "Authorization": `Bearer ${env.HF_TOKEN}` } : {})
        },
        body: JSON.stringify({ text: cleanedText })
      });
    }

    if (resp.ok) {
      const arrayBuf = await resp.arrayBuffer();
      const bytes = new Uint8Array(arrayBuf);
      let binary = "";
      for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      return btoa(binary);
    }
  } catch (e) {
    console.error("Hugging Face Space TTS error:", e);
  }

  return null;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Health Check Endpoint
    if (url.pathname === "/" || url.pathname === "/health") {
      return new Response(JSON.stringify({
        status: "ok",
        service: "My2ndBrain Cloud Gateway",
        sttModel: "@cf/openai/whisper",
        ttsEngine: "Hugging Face Piper JARVIS (Paul Bettany)",
        hfSpaceUrl: env.HF_SPACE_URL || "https://ekc4-jarvis-tts.hf.space",
        brain: "Meta Muse AI (Hatch Noise_XX Protocol)",
        museBridgeConfigured: Boolean(env.MUSE_BRIDGE_URL)
      }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    // Text Chat Endpoint
    if (url.pathname === "/api/chat" && request.method === "POST") {
      try {
        const body: any = await request.json();
        const prompt = body?.message || body?.prompt || "Hello Jarvis";
        const reply = await queryJarvisBrain(prompt, env);
        return new Response(JSON.stringify({ prompt, reply }), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (err: any) {
        return new Response(JSON.stringify({ error: err.message }), { status: 400 });
      }
    }

    // Text-to-Speech Endpoint
    if (url.pathname === "/api/tts" && request.method === "POST") {
      try {
        const body: any = await request.json();
        const text = body?.text || "System operational";
        const audioBase64 = await generateSpeech(text, env);
        if (!audioBase64) {
          return new Response(JSON.stringify({ error: "TTS generation failed" }), { status: 500 });
        }
        return new Response(JSON.stringify({ text, audio: audioBase64 }), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (err: any) {
        return new Response(JSON.stringify({ error: err.message }), { status: 400 });
      }
    }

    // Dedicated Speech-to-Text Endpoint (OpenAI Whisper)
    if (url.pathname === "/api/stt" && request.method === "POST") {
      try {
        const audioBuffer = await request.arrayBuffer();
        if (!audioBuffer || audioBuffer.byteLength === 0) {
          return new Response(JSON.stringify({ error: "Empty audio payload" }), { status: 400 });
        }
        const audioBytes = [...new Uint8Array(audioBuffer)];
        const whisperResult: any = await env.AI.run("@cf/openai/whisper", { audio: audioBytes });
        const transcript = whisperResult?.text?.trim() || "";

        return new Response(JSON.stringify({ transcript, engine: "openai-whisper" }), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (err: any) {
        return new Response(JSON.stringify({ error: err.message }), { status: 500 });
      }
    }

    // Voice Processing Pipeline Endpoint
    if (url.pathname === "/api/voice" && request.method === "POST") {
      try {
        const audioBuffer = await request.arrayBuffer();
        if (!audioBuffer || audioBuffer.byteLength === 0) {
          return new Response(JSON.stringify({ error: "Empty audio payload" }), { status: 400 });
        }

        const input = {
          audio: [...new Uint8Array(audioBuffer)]
        };

        const sttResult: any = await env.AI.run("@cf/openai/whisper", input);
        const transcript = sttResult?.text?.trim() || "";

        if (!transcript) {
          return new Response(JSON.stringify({
            transcript: "",
            reply: "I couldn't hear any clear speech.",
            audio: null
          }), { headers: { "Content-Type": "application/json" } });
        }

        const replyText = await queryJarvisBrain(transcript, env);
        const audioBase64 = await generateSpeech(replyText, env);

        if (request.headers.get("Accept")?.includes("audio/wav") && audioBase64) {
          const binaryString = atob(audioBase64);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          return new Response(bytes, {
            headers: {
              "Content-Type": "audio/wav",
              "X-Transcript": encodeURIComponent(transcript),
              "X-Reply-Text": encodeURIComponent(replyText)
            }
          });
        }

        return new Response(JSON.stringify({
          transcript,
          reply: replyText,
          audio: audioBase64
        }), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (error: any) {
        return new Response(JSON.stringify({ error: error.message }), { status: 500 });
      }
    }

    return new Response("Not Found", { status: 404 });
  },

  async scheduled(event: any, env: Env, ctx: any): Promise<void> {
    // 24-hour keep-alive ping for Hugging Face Space so it never sleeps
    const hfSpaceUrl = env.HF_SPACE_URL || "https://ekc4-jarvis-tts.hf.space";
    try {
      await fetch(`${hfSpaceUrl.replace(/\/$/, "")}/health`);
      console.log("Hugging Face Space keep-alive ping sent to:", hfSpaceUrl);
    } catch (e) {
      console.warn("Hugging Face Space keep-alive ping error:", e);
    }
  }
};
