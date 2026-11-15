export interface Env {
  AI: any;
  WAKE_WORD?: string;
  META_C_USER?: string;
  META_XS?: string;
  META_DATR?: string;
}

/**
 * Query Meta MuseAI backend with the authenticated user session.
 */
async function queryMetaMuse(prompt: string, env: Env): Promise<string> {
  // If user hasn't set credentials yet, return a helpful onboarding message
  if (!env.META_C_USER || !env.META_XS) {
    return `Sir, your voice was received: "${prompt}". To connect to your real-time Meta Muse account, please set your META_C_USER and META_XS session cookies in Cloudflare.`;
  }

  try {
    const response = await fetch("https://www.meta.ai/api/graphql", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Cookie": `c_user=${env.META_C_USER}; xs=${env.META_XS}; datr=${env.META_DATR || ""};`,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Origin": "https://www.meta.ai",
        "Referer": "https://www.meta.ai/"
      },
      body: JSON.stringify({
        doc_id: "7884841804968846",
        variables: {
          message: prompt,
          session_id: "sidecar-ambient-" + Date.now()
        }
      })
    });

    if (!response.ok) {
      return `Meta Muse returned an HTTP ${response.status} error. Please verify your session cookies.`;
    }

    const data: any = await response.json();
    return data?.data?.meta_ai_chat?.message?.text || "I processed your request, but received an empty text response from Muse.";
  } catch (error: any) {
    return `Error reaching Meta Muse: ${error.message}`;
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Health check
    if (url.pathname === "/" || url.pathname === "/health") {
      return new Response(JSON.stringify({
        status: "ok",
        service: "Project Sidecar Cloud Gateway",
        whisperModel: "@cf/openai/whisper",
        museConfigured: Boolean(env.META_C_USER && env.META_XS)
      }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    // Direct text chat endpoint (for testing without voice)
    if (url.pathname === "/api/chat" && request.method === "POST") {
      try {
        const body: any = await request.json();
        const prompt = body?.message || "Hello Jarvis";
        const reply = await queryMetaMuse(prompt, env);
        return new Response(JSON.stringify({ prompt, reply }), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (err: any) {
        return new Response(JSON.stringify({ error: err.message }), { status: 400 });
      }
    }

    // Voice endpoint: Accepts audio buffer (WAV / PCM)
    if (url.pathname === "/api/voice" && request.method === "POST") {
      try {
        const audioBuffer = await request.arrayBuffer();
        if (!audioBuffer || audioBuffer.byteLength === 0) {
          return new Response(JSON.stringify({ error: "Empty audio payload" }), { status: 400 });
        }

        // 1. Run Cloudflare Workers AI Whisper Speech-to-Text
        const input = {
          audio: [...new Uint8Array(audioBuffer)]
        };

        const sttResult: any = await env.AI.run("@cf/openai/whisper", input);
        const transcript = sttResult?.text?.trim() || "";

        if (!transcript) {
          return new Response(JSON.stringify({
            transcript: "",
            reply: "I couldn't hear any clear speech.",
            audioUrl: null
          }), { headers: { "Content-Type": "application/json" } });
        }

        // 2. Query Meta Muse
        const replyText = await queryMetaMuse(transcript, env);

        // 3. Return response payload
        return new Response(JSON.stringify({
          transcript,
          reply: replyText
        }), {
          headers: { "Content-Type": "application/json" }
        });
      } catch (error: any) {
        return new Response(JSON.stringify({ error: error.message }), { status: 500 });
      }
    }

    return new Response("Not Found", { status: 404 });
  }
};
