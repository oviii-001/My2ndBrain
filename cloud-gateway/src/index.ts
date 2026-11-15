export interface Env {
  AI: any;
  WAKE_WORD?: string;
  HATCH_SESS?: string;
  HATCH_GW?: string;
  DATR?: string;
  ELEVENLABS_API_KEY?: string;
  ELEVENLABS_VOICE_ID?: string;
  TTS_SPEAKER?: string; // e.g. "angus" (British/Irish male), "orion" (deep calm male)
}

/**
 * Fallback Jarvis persona via Cloudflare Workers AI Meta Llama 3.1.
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
 * Tier 1: ElevenLabs Paul Bettany Jarvis voice clone (if ELEVENLABS_API_KEY configured).
 * Tier 2: Cloudflare Native Deepgram Aura-1 British/Irish natural male ('angus' / 'orion').
 * Tier 3: Cloudflare Deepgram Aura-2-en.
 * Tier 4: Edge fallback MeloTTS.
 */
async function generateSpeech(text: string, env: Env): Promise<string | null> {
  const cleanedText = text.slice(0, 350);

  // 1. High-Fidelity Cloned Jarvis Voice via ElevenLabs (Paul Bettany) if configured
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

  // 2. Cloudflare Native Deepgram Aura-1 (Natural British/Male conversational voice)
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
    console.warn("Deepgram Aura-1 error, attempting Aura-2-en:", err);
  }

  // 3. Fallback: Deepgram Aura-2-en
  try {
    const aura2Result: any = await env.AI.run("@cf/deepgram/aura-2-en", { text: cleanedText });
    if (aura2Result?.audio) return aura2Result.audio;
  } catch {}

  // 4. Edge Fallback: MeloTTS
  try {
    const ttsResult: any = await env.AI.run("@cf/myshell-ai/melotts", { prompt: cleanedText });
    return ttsResult?.audio || null;
  } catch (err) {
    console.error("MeloTTS fallback failed:", err);
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
        service: "My2ndBrain Cloud Gateway",
        sttModels: ["@cf/deepgram/nova-3", "@cf/openai/whisper"],
        ttsEngine: env.ELEVENLABS_API_KEY ? "ElevenLabs (Paul Bettany Jarvis)" : "Deepgram Aura (British Male)",
        ttsSpeaker: env.TTS_SPEAKER || "angus",
        fallbackLLM: "@cf/meta/llama-3.1-8b-instruct-fp8",
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
  }
};
