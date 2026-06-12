"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, UserRound } from "lucide-react";
import { LogLevel, SimliClient, generateSimliSessionToken } from "simli-client";

import TalkingAvatar from "@/components/interview/TalkingAvatar";

export const SIMLI_API_KEY = process.env.NEXT_PUBLIC_SIMLI_API_KEY ?? "";
export const isSimliEnabled = SIMLI_API_KEY.length > 0;

// Fallback if NEXT_PUBLIC_SIMLI_FACE_ID is unset (your deployed avatar)
const DEFAULT_FACE_ID = "cace3ef7-a4c4-425d-a8cf-a5358eb0c427";

type SimliInterviewerProps = {
  audioSrc: string;
  isPlaying?: boolean;
  interviewerName?: string;
  interviewerTitle?: string;
  className?: string;
};

type ConnectionState = "connecting" | "connected" | "failed";

/**
 * Decode a TTS audio data URI (mp3/wav), resample it to 16 kHz mono
 * PCM16 and return the raw bytes Simli expects.
 */
async function decodeToPcm16(dataUri: string): Promise<Uint8Array | null> {
  try {
    const response = await fetch(dataUri);
    const encoded = await response.arrayBuffer();

    const decodeCtx = new AudioContext();
    const decoded = await decodeCtx.decodeAudioData(encoded);
    await decodeCtx.close();

    const targetRate = 16000;
    const frameCount = Math.ceil(decoded.duration * targetRate);
    const offline = new OfflineAudioContext(1, frameCount, targetRate);
    const source = offline.createBufferSource();
    source.buffer = decoded;
    source.connect(offline.destination);
    source.start();
    const rendered = await offline.startRendering();

    const samples = rendered.getChannelData(0);
    const pcm = new Int16Array(samples.length);
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return new Uint8Array(pcm.buffer);
  } catch {
    return null;
  }
}

/**
 * Real-time lip-synced human interviewer driven by Simli.
 * Falls back to the sprite-based TalkingAvatar if the Simli
 * session cannot be established (no key, no credits, network).
 */
export default function SimliInterviewer({
  audioSrc,
  isPlaying,
  interviewerName = "Alex Chen",
  interviewerTitle = "Senior Engineer, Evalvate",
  className = "",
}: SimliInterviewerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const clientRef = useRef<SimliClient | null>(null);

  const [connectionState, setConnectionState] = useState<ConnectionState>(
    isSimliEnabled ? "connecting" : "failed",
  );
  const [isSpeaking, setIsSpeaking] = useState(false);
  const lastSentAudioRef = useRef<string | null>(null);

  // ── Establish the Simli session once on mount ──
  useEffect(() => {
    if (!isSimliEnabled) {
      return;
    }

    let cancelled = false;
    let client: SimliClient | null = null;

    async function connect() {
      try {
        const { session_token } = await generateSimliSessionToken({
          apiKey: SIMLI_API_KEY,
          config: {
            faceId: process.env.NEXT_PUBLIC_SIMLI_FACE_ID || DEFAULT_FACE_ID,
            handleSilence: true,
            maxSessionLength: 3600,
            maxIdleTime: 600,
          },
        });
        if (cancelled || !videoRef.current || !audioRef.current) return;

        // LiveKit mode avoids needing ICE servers (P2P requires generateIceServers).
        client = new SimliClient(
          session_token,
          videoRef.current,
          audioRef.current,
          null,
          LogLevel.ERROR,
          "livekit",
        );
        clientRef.current = client;

        client.on("start", () => {
          if (!cancelled) setConnectionState("connected");
        });
        client.on("speaking", () => {
          if (!cancelled) setIsSpeaking(true);
        });
        client.on("silent", () => {
          if (!cancelled) setIsSpeaking(false);
        });
        client.on("error", (detail: string) => {
          console.error("Simli error:", detail);
        });
        client.on("startup_error", (message: string) => {
          console.error("Simli startup error:", message);
          if (!cancelled) setConnectionState("failed");
        });
        client.on("stop", () => {
          if (!cancelled) setConnectionState("failed");
        });

        await client.start();
      } catch (err) {
        console.error("Simli connection failed:", err);
        if (!cancelled) setConnectionState("failed");
      }
    }

    void connect();

    return () => {
      cancelled = true;
      if (client) {
        void client.stop().catch(() => {});
      }
      clientRef.current = null;
    };
  }, []);

  // ── Stream the current question's TTS audio to the avatar ──
  const sendCurrentAudio = useCallback(async () => {
    const client = clientRef.current;
    if (!client || connectionState !== "connected" || !audioSrc) return;

    client.ClearBuffer();
    const pcm = await decodeToPcm16(audioSrc);
    if (!pcm || clientRef.current !== client) return;

    // Send in ~6KB chunks so the worklet buffers smoothly
    const chunkBytes = 6000;
    for (let offset = 0; offset < pcm.length; offset += chunkBytes) {
      client.sendAudioData(pcm.subarray(offset, Math.min(offset + chunkBytes, pcm.length)));
    }
  }, [audioSrc, connectionState]);

  useEffect(() => {
    if (!isPlaying || !audioSrc) return;
    // Re-send when a new question arrives or a replay is requested.
    const key = `${audioSrc.slice(0, 64)}:${audioSrc.length}`;
    if (lastSentAudioRef.current === key && isPlaying) {
      // Replay of the same audio: clear + resend
      void sendCurrentAudio();
      return;
    }
    lastSentAudioRef.current = key;
    void sendCurrentAudio();
  }, [audioSrc, isPlaying, sendCurrentAudio]);

  // Fallback: Simli unavailable -> keep the interview fully functional
  if (connectionState === "failed") {
    return <TalkingAvatar audioSrc={audioSrc} isPlaying={isPlaying} />;
  }

  return (
    <div className={`relative w-full ${className}`}>
      <div className="relative w-full aspect-video mx-auto rounded-2xl overflow-hidden bg-gradient-to-b from-slate-800 to-slate-900 shadow-md">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="w-full h-full object-cover"
        />
        <audio ref={audioRef} autoPlay />

        {connectionState === "connecting" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-slate-900/90">
            <Loader2 className="w-7 h-7 text-violet-400 animate-spin" />
            <p className="text-xs text-slate-400">Connecting your interviewer...</p>
          </div>
        )}

        {/* Name plate */}
        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent px-4 pb-3 pt-8">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-violet-500/20 border border-violet-400/30 flex items-center justify-center">
              <UserRound className="w-3.5 h-3.5 text-violet-300" />
            </div>
            <div>
              <p className="text-white text-sm font-semibold leading-tight">{interviewerName}</p>
              <p className="text-slate-400 text-[11px] leading-tight">{interviewerTitle}</p>
            </div>
            {isSpeaking && (
              <span className="ml-auto flex items-center gap-1.5 rounded-full bg-emerald-500/15 border border-emerald-400/25 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-300">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Speaking
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
