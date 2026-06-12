"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  AlertCircle,
  ArrowRight,
  Brain,
  Camera,
  CheckCircle2,
  Eye,
  FileText,
  Loader2,
  Mic,
  Volume2,
  Wifi,
} from "lucide-react";

import { backendClient } from "@/lib/backend";
import { config } from "@/lib/config";

type CheckState = "idle" | "checking" | "pass" | "fail";

interface SystemCheck {
  camera: CheckState;
  microphone: CheckState;
  network: CheckState;
}

type ResumeStatus =
  | { state: "loading" }
  | { state: "missing" }
  | { state: "ready"; skills: string[]; filename: string };

const ROLE_OPTIONS = [
  "Frontend Engineer",
  "Backend Engineer",
  "Full Stack Engineer",
  "Machine Learning Engineer",
  "DevOps Engineer",
] as const;

const DIFFICULTY_OPTIONS = ["easy", "medium", "hard"] as const;
const PERSONA_OPTIONS = ["mentor", "friendly", "aggressive", "neutral", "devil's advocate"] as const;
const QUESTION_OPTIONS = [3, 5, 10, 15] as const;
const DURATION_OPTIONS = [5, 10, 15, 20] as const;

function PreInterviewInner() {
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const animFrameRef = useRef<number>(0);

  const [role, setRole] = useState<(typeof ROLE_OPTIONS)[number]>("Full Stack Engineer");
  const [difficulty, setDifficulty] = useState<(typeof DIFFICULTY_OPTIONS)[number]>("medium");
  const [persona, setPersona] = useState<(typeof PERSONA_OPTIONS)[number]>("mentor");
  const [questionCount, setQuestionCount] = useState<number>(5);
  const [durationMinutes, setDurationMinutes] = useState<number>(10);

  const [systemCheck, setSystemCheck] = useState<SystemCheck>({
    camera: "idle",
    microphone: "idle",
    network: "idle",
  });
  const [micVolume, setMicVolume] = useState(0);
  const [isStarting, setIsStarting] = useState(false);
  const [resumeStatus, setResumeStatus] = useState<ResumeStatus>({ state: "loading" });

  const allPassed =
    systemCheck.camera === "pass" &&
    systemCheck.microphone === "pass" &&
    systemCheck.network === "pass";

  const stopMedia = useCallback(() => {
    cancelAnimationFrame(animFrameRef.current);
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    void audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
  }, []);

  const runSystemChecks = useCallback(async () => {
    // Network: ping the backend root
    setSystemCheck((s) => ({ ...s, network: "checking" }));
    try {
      await fetch(`${config.backendUrl}/`, { method: "GET", cache: "no-store" });
      setSystemCheck((s) => ({ ...s, network: "pass" }));
    } catch {
      setSystemCheck((s) => ({ ...s, network: "fail" }));
    }

    // Camera + mic
    setSystemCheck((s) => ({ ...s, camera: "checking", microphone: "checking" }));
    try {
      stopMedia();
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setSystemCheck((s) => ({ ...s, camera: "pass" }));

      const audioCtx = new AudioContext();
      audioCtxRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyzer = audioCtx.createAnalyser();
      analyzer.fftSize = 256;
      source.connect(analyzer);

      const data = new Uint8Array(analyzer.frequencyBinCount);
      const tick = () => {
        analyzer.getByteFrequencyData(data);
        const avg = data.reduce((a, b) => a + b, 0) / data.length;
        setMicVolume(avg / 128);
        animFrameRef.current = requestAnimationFrame(tick);
      };
      tick();
      setSystemCheck((s) => ({ ...s, microphone: "pass" }));
    } catch {
      setSystemCheck((s) => ({ ...s, camera: "fail", microphone: "fail" }));
    }
  }, [stopMedia]);

  // Resume status check runs quietly in the background
  useEffect(() => {
    let mounted = true;

    async function loadResume() {
      try {
        const res = await backendClient.get("/resume");
        if (!mounted) return;
        const skills: string[] = res.data?.parsed_resume?.skills ?? [];
        setResumeStatus({
          state: "ready",
          skills: skills.slice(0, 6),
          filename: res.data?.filename ?? "resume",
        });
      } catch {
        if (mounted) setResumeStatus({ state: "missing" });
      }
    }

    void loadResume();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void runSystemChecks();
    }, 0);
    return () => {
      window.clearTimeout(timer);
      stopMedia();
    };
  }, [runSystemChecks, stopMedia]);

  function handleStart() {
    setIsStarting(true);
    stopMedia();
    const params = new URLSearchParams({
      role,
      difficulty,
      persona,
      questions: String(questionCount),
      duration: String(durationMinutes),
    });
    router.push(`/interview?${params.toString()}`);
  }

  const checkItems = [
    { key: "camera" as const, icon: Camera, label: "Camera", hint: "Needed for facial tracking" },
    { key: "microphone" as const, icon: Mic, label: "Microphone", hint: "Needed for voice analysis" },
    { key: "network" as const, icon: Wifi, label: "Connection", hint: "Needed for AI processing" },
  ];

  const whatWeAnalyze = [
    { icon: Eye, label: "Eye contact", sub: "Gaze direction tracking" },
    { icon: Volume2, label: "Voice quality", sub: "Confidence, pace, clarity" },
    { icon: Brain, label: "Answer quality", sub: "Structure, relevance, depth" },
    { icon: Camera, label: "Body language", sub: "Posture, expressions, focus" },
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      <div className="fixed inset-0 bg-gradient-to-b from-violet-950/20 via-transparent to-transparent pointer-events-none" />

      {/* Top nav */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-5 border-b border-white/5">
        <button
          onClick={() => router.push("/dashboard")}
          className="text-slate-400 hover:text-white text-sm flex items-center gap-2 transition-colors"
        >
          <span>&larr;</span> Back
        </button>
        <span className="text-white font-semibold tracking-tight lowercase">{config.appName}</span>
        <div className="w-20" />
      </nav>

      <div className="relative z-10 max-w-6xl mx-auto px-6 py-10">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
            <span className="text-violet-400 text-sm font-medium tracking-wide uppercase">Pre-Interview Check</span>
          </div>
          <h1 className="text-3xl font-bold text-white">Ready to start your session?</h1>
          <p className="text-slate-400 mt-2">
            Configure your interview and make sure everything is working. This takes 30 seconds.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* LEFT: Session config + resume + what we analyze */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2 space-y-4"
          >
            {/* Session Config */}
            <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-6">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-5">Your Session</h3>
              <div className="space-y-4">
                <ConfigSelect label="Role" value={role} options={ROLE_OPTIONS} onChange={(v) => setRole(v as (typeof ROLE_OPTIONS)[number])} />
                <ConfigSelect label="Difficulty" value={difficulty} options={DIFFICULTY_OPTIONS} onChange={(v) => setDifficulty(v as (typeof DIFFICULTY_OPTIONS)[number])} />
                <ConfigSelect label="Persona" value={persona} options={PERSONA_OPTIONS} onChange={(v) => setPersona(v as (typeof PERSONA_OPTIONS)[number])} />

                {/* Question count */}
                <div className="space-y-2">
                  <label className="text-sm text-slate-400">Number of Questions</label>
                  <div className="flex gap-2 flex-wrap">
                    {QUESTION_OPTIONS.map((n) => (
                      <button
                        key={n}
                        onClick={() => setQuestionCount(n)}
                        className={`px-3.5 py-2 rounded-xl text-sm font-medium transition-all ${
                          questionCount === n
                            ? "bg-violet-600 text-white"
                            : "bg-white/5 text-slate-400 hover:bg-white/10"
                        }`}
                      >
                        {n}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Duration */}
                <div className="space-y-2">
                  <label className="text-sm text-slate-400">Time Limit</label>
                  <div className="flex gap-2 flex-wrap">
                    {DURATION_OPTIONS.map((n) => (
                      <button
                        key={n}
                        onClick={() => setDurationMinutes(n)}
                        className={`px-3.5 py-2 rounded-xl text-sm font-medium transition-all ${
                          durationMinutes === n
                            ? "bg-violet-600 text-white"
                            : "bg-white/5 text-slate-400 hover:bg-white/10"
                        }`}
                      >
                        {n} min
                      </button>
                    ))}
                  </div>
                  <p className="text-xs text-slate-500">
                    The interview ends automatically when the time limit is reached.
                  </p>
                </div>
              </div>
            </div>

            {/* Resume Card */}
            <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Resume</h3>
                {resumeStatus.state === "loading" && <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />}
                {resumeStatus.state === "ready" && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                {resumeStatus.state === "missing" && <AlertCircle className="w-4 h-4 text-amber-400" />}
              </div>

              {resumeStatus.state === "ready" ? (
                <div className="space-y-3">
                  <p className="text-sm text-emerald-400 font-medium">Resume linked — questions will be personalized</p>
                  {resumeStatus.skills.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {resumeStatus.skills.map((skill) => (
                        <span
                          key={skill}
                          className="text-[11px] px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                  <Link
                    href="/resume"
                    target="_blank"
                    className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 underline transition-colors"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    Manage resume
                  </Link>
                </div>
              ) : resumeStatus.state === "missing" ? (
                <div className="space-y-3">
                  <p className="text-sm text-slate-400 leading-relaxed">
                    No resume uploaded. Your interview will use generic role questions — upload a resume so the AI can
                    test your actual projects and skills.
                  </p>
                  <Link
                    href="/resume"
                    target="_blank"
                    className="inline-flex items-center gap-1.5 text-sm text-violet-400 hover:text-violet-300 font-medium transition-colors"
                  >
                    <FileText className="w-4 h-4" />
                    Upload resume (opens in new tab)
                  </Link>
                </div>
              ) : (
                <p className="text-sm text-slate-500">Checking resume status...</p>
              )}
            </div>

            {/* What We Analyze */}
            <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-6">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-5">What We Analyze</h3>
              <div className="space-y-4">
                {whatWeAnalyze.map((item) => (
                  <div key={item.label} className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center flex-shrink-0">
                      <item.icon className="w-4 h-4 text-violet-400" />
                    </div>
                    <div>
                      <div className="text-white text-sm font-medium">{item.label}</div>
                      <div className="text-slate-500 text-xs mt-0.5">{item.sub}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* RIGHT: System Checks + Camera Preview */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.15 }}
            className="lg:col-span-3 space-y-4"
          >
            {/* Camera Preview */}
            <div className="bg-white/[0.03] border border-white/10 rounded-2xl overflow-hidden">
              <div className="relative aspect-video bg-black">
                <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover scale-x-[-1]" />
                {systemCheck.camera === "checking" && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/80">
                    <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
                  </div>
                )}
                {systemCheck.camera === "fail" && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/90 gap-3">
                    <AlertCircle className="w-10 h-10 text-red-400" />
                    <p className="text-slate-300 text-sm">Camera access denied</p>
                    <button onClick={() => void runSystemChecks()} className="text-violet-400 text-xs underline">
                      Try again
                    </button>
                  </div>
                )}
                {systemCheck.camera === "pass" && (
                  <>
                    <div className="absolute top-3 left-3 flex items-center gap-2 bg-black/60 rounded-full px-3 py-1.5">
                      <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                      <span className="text-white text-xs font-medium">Preview</span>
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="w-32 h-40 border-2 border-violet-400/30 rounded-full" />
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* System Checks */}
            <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-6">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-5">System Check</h3>
              <div className="space-y-4">
                {checkItems.map((item) => {
                  const state = systemCheck[item.key];
                  return (
                    <div key={item.key} className="flex items-center gap-4">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors ${
                          state === "pass"
                            ? "bg-emerald-500/10 border border-emerald-500/20"
                            : state === "fail"
                              ? "bg-red-500/10 border border-red-500/20"
                              : "bg-white/5 border border-white/10"
                        }`}
                      >
                        <item.icon
                          className={`w-5 h-5 ${
                            state === "pass" ? "text-emerald-400" : state === "fail" ? "text-red-400" : "text-slate-400"
                          }`}
                        />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-white text-sm font-medium">{item.label}</span>
                          {state === "checking" && <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />}
                          {state === "pass" && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                          {state === "fail" && <AlertCircle className="w-4 h-4 text-red-400" />}
                        </div>
                        {item.key === "microphone" && state === "pass" ? (
                          <>
                            <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-violet-500 to-blue-500 rounded-full transition-all duration-100"
                                style={{ width: `${Math.min(micVolume * 100, 100)}%` }}
                              />
                            </div>
                            <p className="text-slate-500 text-xs mt-1">
                              {micVolume > 0.1
                                ? "Microphone active — speak normally"
                                : "Try speaking — checking input level..."}
                            </p>
                          </>
                        ) : (
                          <p className="text-slate-500 text-xs">{item.hint}</p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Start Button */}
            <motion.button
              onClick={handleStart}
              disabled={!allPassed || isStarting}
              whileHover={{ scale: allPassed ? 1.01 : 1 }}
              whileTap={{ scale: allPassed ? 0.99 : 1 }}
              className={`w-full py-4 rounded-2xl font-semibold text-base flex items-center justify-center gap-3 transition-all duration-200 ${
                allPassed && !isStarting
                  ? "bg-violet-600 hover:bg-violet-500 text-white cursor-pointer shadow-lg shadow-violet-500/25"
                  : "bg-white/5 text-slate-500 cursor-not-allowed"
              }`}
            >
              {isStarting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Starting session...
                </>
              ) : allPassed ? (
                <>
                  Start Interview
                  <ArrowRight className="w-5 h-5" />
                </>
              ) : (
                "Complete system check to continue"
              )}
            </motion.button>

            {!allPassed && !isStarting && (
              <p className="text-center text-slate-500 text-xs">
                Please allow camera and microphone access to continue
              </p>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function ConfigSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: readonly string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm text-slate-400">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 w-full rounded-xl border border-white/10 bg-white/5 px-3 text-sm text-white outline-none transition focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20 [&>option]:bg-[#14141c]"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function PreInterviewPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
        </div>
      }
    >
      <PreInterviewInner />
    </Suspense>
  );
}
