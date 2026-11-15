export interface Env {
  AI: any;
  WAKE_WORD?: string;
  HATCH_SESS?: string;
  HATCH_GW?: string;
  DATR?: string;
  META_C_USER?: string;
  META_XS?: string;
  META_DATR?: string;
}

/**
 * Query Meta MuseAI session or fallback to Cloudflare Workers AI Meta Llama 3.1 Jarvis.
 */
async function queryJarvisBrain(prompt: string, env: Env): Promise<string> {
  let cookieHeader = "";
  if (env.HATCH_SESS && env.HATCH_GW) {
    cookieHeader = `hatch_sess=${env.HATCH_SESS}; hatch_gw=${env.HATCH_GW}; datr=${env.DATR || ""};`;
  } else if (env.META_C_USER && env.META_XS) {
    cookieHeader = `c_user=${env.META_C_USER}; xs=${env.META_XS}; datr=${env.META_DATR || ""};`;
  }

  // 1. If session cookies are provided, attempt cloud bridge
  if (cookieHeader) {
    try {
      const response = await fetch("https://www.meta.ai/api/graphql", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Cookie": cookieHeader,
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

      if (response.ok) {
        const data: any = await response.json();
        const text = data?.data?.meta_ai_chat?.message?.text;
        if (text) return text;
      }
    } catch (err) {
      console.warn("Session bridge query skipped/failed:", err);
    }
  }

  // 2. High-speed local Jarvis persona via Cloudflare Workers AI Meta Llama 3.1 (2026 FP8 model)
  try {
    const aiResp: any = await env.AI.run("@cf/meta/llama-3.1-8b-instruct-fp8", {
      messages: [
        {
          role: "system",
          content: "You are Jarvis, a brilliant, concise, loyal AI personal assistant living in the user's room. Respond in 1-2 conversational sentences suitable for speech audio output. Do not use markdown, emojis, asterisks, or bullet points."
        },
        { role: "user", content: prompt }
      ]
    });
    return aiResp?.response?.trim() || "I am online and ready to assist you, sir.";
  } catch (err: any) {
    console.error("Workers AI error:", err);
    return `Systems operational, sir. Standing by.`;
  }
}

/**
 * Generate speech audio from text using Cloudflare Workers AI MeloTTS.
 */
async function generateSpeech(text: string, env: Env): Promise<string | null> {
  try {
    const cleanedText = text.slice(0, 300);
    const ttsResult: any = await env.AI.run("@cf/myshell-ai/melotts", { prompt: cleanedText });
    return ttsResult?.audio || null;
  } catch (err) {
    console.error("TTS generation error:", err);
    return null;
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Health Check Endpoint
    if (url.pathname === "/" || url.pathname === "/health") {
      return new Response(JSON.stringify({
        status: "ok",
        service: "Project Sidecar Cloud Gateway",
        sttModel: "@cf/openai/whisper",
        ttsModel: "@cf/myshell-ai/melotts",
        fallbackLLM: "@cf/meta/llama-3.1-8b-instruct-fp8",
        museConfigured: Boolean((env.HATCH_SESS && env.HATCH_GW) || (env.META_C_USER && env.META_XS))
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
  }
};
