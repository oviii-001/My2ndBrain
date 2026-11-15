export interface Env {
  AI: any;
  WAKE_WORD?: string;
  HATCH_SESS?: string;
  HATCH_GW?: string;
  DATR?: string;
  HF_TOKEN?: string; // Hugging Face Free User Token
  HF_SPACE_URL?: string; // Free Hugging Face Space Endpoint (jgkawell/jarvis)
  ELEVENLABS_API_KEY?: string;
  ELEVENLABS_VOICE_ID?: string;
  TTS_SPEAKER?: string; // e.g. "angus" (British/Irish male), "orion" (deep calm male)
}

/**
 * Dedicated Jarvis persona via Cloudflare Workers AI Meta Llama 3.1.
 */
async function queryJarvisBrain(prompt: string, env: Env): Promise<string> {
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
 * Generate speech audio from text.
 * Tier 1: Hugging Face Space Endpoint (Free jgkawell/jarvis Paul Bettany Piper model).
 * Tier 2: Hugging Face Serverless Inference API (Free HF_TOKEN).
 * Tier 3: ElevenLabs (Optional API key).
 * Tier 4: Cloudflare Native Deepgram Aura-1 British/Irish natural male ('angus' / 'orion').
 * Tier 5: Edge fallback MeloTTS.
 */
async function generateSpeech(text: string, env: Env): Promise<string | null> {
  const cleanedText = text.slice(0, 350);

  // 1. Hugging Face Space Free Endpoint (jgkawell/jarvis Paul Bettany Iron Man model)
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
    console.warn("Hugging Face Space TTS error:", e);
  }

  // 2. Hugging Face Free Serverless Inference API
  if (env.HF_TOKEN) {
    try {
      const hfModel = "facebook/mms-tts-eng";
      const resp = await fetch(`https://router.huggingface.co/hf-inference/models/${hfModel}`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${env.HF_TOKEN}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ inputs: cleanedText })
      });
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
      console.warn("Hugging Face Inference API error, falling back:", e);
    }
  }

  // 3. Optional ElevenLabs Voice Clone (if configured)
  if (env.ELEVENLABS_API_KEY) {
    try {
      const voiceId = env.ELEVENLABS_VOICE_ID || "21m00Tcm4TlvDq8ikWAM";
      const resp = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
        method: "POST",
        headers: {
          "xi-api-key": env.ELEVENLABS_API_KEY,
          "Content-Type": "application/json",
          "Accept": "audio/mpeg"
        },
        body: JSON.stringify({
          text: cleanedText,
          model_id: "eleven_turbo_v2_5",
          voice_settings: {
            stability: 0.72,
            similarity_boost: 0.85,
            style: 0.15,
            use_speaker_boost: true
          }
        })
      });
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
      console.warn("ElevenLabs TTS error, falling back to edge neural voice:", e);
    }
  }

  // 4. Cloudflare Native Deepgram Aura-1 (Natural British Male Jarvis voice)
  try {
    const speaker = env.TTS_SPEAKER || "angus"; // "angus" is British/Irish male, "orion" is deep calm male
    const auraResult: any = await env.AI.run("@cf/deepgram/aura-1", {
      text: cleanedText,
      speaker: speaker
    });
    if (auraResult?.audio) return auraResult.audio;
    if (auraResult instanceof ReadableStream || auraResult instanceof ArrayBuffer) {
      const buf = auraResult instanceof ArrayBuffer ? auraResult : await new Response(auraResult).arrayBuffer();
      const bytes = new Uint8Array(buf);
      let binary = "";
      for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      return btoa(binary);
    }
  } catch (err) {
    console.warn("Deepgram Aura-1 error:", err);
  }

  // 5. Deepgram Aura-2-en (Alternative Deepgram Aura checkpoint)
  try {
    const aura2Result: any = await env.AI.run("@cf/deepgram/aura-2-en", { text: cleanedText });
    if (aura2Result?.audio) return aura2Result.audio;
  } catch {}

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
        sttModels: ["@cf/deepgram/nova-3", "@cf/openai/whisper"],
        ttsEngine: "Hugging Face Piper JARVIS (Paul Bettany)",
        hfSpaceUrl: env.HF_SPACE_URL || "https://ekc4-jarvis-tts.hf.space",
        ttsSpeaker: env.TTS_SPEAKER || "angus",
        brainLLM: "@cf/meta/llama-3.1-8b-instruct-fp8",
        museConfigured: Boolean(env.HATCH_SESS && env.HATCH_GW)
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

    // Speech-to-Text Endpoint (Deepgram Nova-3 ultra-fast STT with Whisper fallback)
    if (url.pathname === "/api/stt" && request.method === "POST") {
      try {
        const audioBuffer = await request.arrayBuffer();
        if (!audioBuffer || audioBuffer.byteLength === 0) {
          return new Response(JSON.stringify({ error: "Empty audio payload" }), { status: 400 });
        }
        const audioBytes = [...new Uint8Array(audioBuffer)];
        let transcript = "";
        let engine = "deepgram-nova-3";

        try {
          const novaResult: any = await env.AI.run("@cf/deepgram/nova-3", { audio: audioBytes });
          transcript = novaResult?.result?.text?.trim() || novaResult?.text?.trim() || "";
        } catch {
          // Fallback to Whisper
        }

        if (!transcript) {
          engine = "openai-whisper";
          const whisperResult: any = await env.AI.run("@cf/openai/whisper", { audio: audioBytes });
          transcript = whisperResult?.text?.trim() || "";
        }

        return new Response(JSON.stringify({ transcript, engine }), {
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
