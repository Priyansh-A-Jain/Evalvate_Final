"use client";

import React, { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useVideoAnalysis } from "@/hooks/useVideoAnalysis";
import type { VideoAnalysis } from "@/hooks/useVideoAnalysis";
import { useVoiceWebSocket } from "@/hooks/useVoiceWebSocket";
import { VideoOverlay } from "@/components/interview/VideoOverlay";
import { TranscriptTimeline } from "@/components/interview/TranscriptTimeline";
import { LiveMetrics } from "@/components/interview/LiveMetrics";
import TalkingAvatar from "@/components/interview/TalkingAvatar";
import SimliInterviewer, { isSimliEnabled } from "@/components/interview/SimliInterviewer";
import {
  startInterview as apiStartInterview,
  submitInterviewAnswer,
  saveSessionAnalysis,
  type AnswerEvaluation,
  type StartInterviewResponse,
  type SubmitAnswerResponse,
  type SessionAnalysisData,
} from "@/lib/interviewAgentApi";
import { track } from "@/lib/analytics";
import {
  Square,
  Timer,
  Mic,
  MicOff,
  Video,
  VideoOff,
  Sparkles,
  ChevronRight,
  RotateCcw,
  LoaderCircle,
  Volume2,
  Bot,
  AlertTriangle,
  Send,
  AlarmClock,
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────────
type InterviewPhase = "loading" | "active" | "submitting" | "finalizing" | "completed";

interface TurnRecord {
  question: string;
  answer: string;
  evaluation: AnswerEvaluation;
}

function InterviewPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // ── Refs ──
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // ── Config from /pre-interview (query params) ──
  const role = searchParams.get("role") ?? "";
  const difficulty = searchParams.get("difficulty") ?? "";
  const persona = searchParams.get("persona") ?? "";
  const parsedQuestions = parseInt(searchParams.get("questions") ?? "", 10);
  const questionCount = Number.isFinite(parsedQuestions) && parsedQuestions > 0 ? parsedQuestions : null;
  const parsedDuration = parseInt(searchParams.get("duration") ?? "", 10);
  const durationMinutes = Number.isFinite(parsedDuration) && parsedDuration > 0 ? parsedDuration : null;

  // ── Interview State ──
  const [phase, setPhase] = useState<InterviewPhase>("loading");
  const [interviewId, setInterviewId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);
  const [currentQuestionAudio, setCurrentQuestionAudio] = useState<string | null>(null);
  const [isQuestionAudioPlaying, setIsQuestionAudioPlaying] = useState(false);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(25);
  const [turns, setTurns] = useState<TurnRecord[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState(""); // Manual text fallback
  const [useVoiceInput, setUseVoiceInput] = useState(true);
  const [finalizingCountdown, setFinalizingCountdown] = useState(0);
  const [deadlineAt, setDeadlineAt] = useState<number | null>(null);
  const [remainingSec, setRemainingSec] = useState<number | null>(null);
  const [timeExpired, setTimeExpired] = useState(false);
  const timeUpFiredRef = useRef(false);
  const autoStartRef = useRef(false);
  const [isCameraEnabled, setIsCameraEnabled] = useState(true);
  const [isMicEnabled, setIsMicEnabled] = useState(true);
  const [hasVideoTrack, setHasVideoTrack] = useState(false);
  const [hasAudioTrack, setHasAudioTrack] = useState(false);
  const [micStream, setMicStream] = useState<MediaStream | null>(null);

  // ── Video snapshots for analysis (collect ALL during session) ──
  const lastVideoAnalysisRef = useRef<VideoAnalysis | null>(null);
  const videoSnapshotsRef = useRef<VideoAnalysis[]>([]);
  const sessionStartedAtRef = useRef<number>(Date.now());

  const questionReplayTimeoutRef = useRef<number | null>(null);

  // ── Hooks ──
  const video = useVideoAnalysis(videoRef, canvasRef);
  const voice = useVoiceWebSocket(isRecording, micStream);

  const logInterview = useCallback((message: string, payload?: unknown) => {
    const stamp = new Date().toISOString();
    if (payload === undefined) {
      console.log(`[Interview][${stamp}] ${message}`);
      return;
    }
    console.log(`[Interview][${stamp}] ${message}`, payload);
  }, []);

  // ── Keep latest video analysis for saving (and collect all snapshots) ──
  useEffect(() => {
    if (video.analysis) {
      lastVideoAnalysisRef.current = video.analysis;
      videoSnapshotsRef.current.push(video.analysis);
      if (videoSnapshotsRef.current.length % 10 === 0) {
        logInterview("Video snapshots buffered", {
          count: videoSnapshotsRef.current.length,
          latestEmotion: video.analysis.dominant_emotion,
          latestCapturedAt: video.analysis.captured_at,
        });
      }
      // Keep only last 300 snapshots (~5 min at 1/s)
      if (videoSnapshotsRef.current.length > 300) {
        videoSnapshotsRef.current = videoSnapshotsRef.current.slice(-300);
      }
    }
  }, [video.analysis, logInterview]);

  // ── Webcam setup ──
  useEffect(() => {
    let mounted = true;

    const attachStream = (mediaStream: MediaStream) => {
      streamRef.current = mediaStream;
      setMicStream(mediaStream);
      const videoTracks = mediaStream.getVideoTracks();
      const audioTracks = mediaStream.getAudioTracks();
      setHasVideoTrack(videoTracks.length > 0);
      setHasAudioTrack(audioTracks.length > 0);
      setIsCameraEnabled(videoTracks.some((track) => track.enabled));
      setIsMicEnabled(audioTracks.some((track) => track.enabled));

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    };

    async function setupStream() {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: true,
        });
        if (!mounted) {
          mediaStream.getTracks().forEach((track) => track.stop());
          return;
        }
        attachStream(mediaStream);
      } catch (err) {
        console.error("Failed to access camera + microphone:", err);
        try {
          const fallbackStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 },
            audio: false,
          });
          if (!mounted) {
            fallbackStream.getTracks().forEach((track) => track.stop());
            return;
          }
          attachStream(fallbackStream);
          setHasAudioTrack(false);
          setIsMicEnabled(false);
        } catch (fallbackErr) {
          console.error("Failed to access camera:", fallbackErr);
          setHasVideoTrack(false);
          setHasAudioTrack(false);
          setIsCameraEnabled(false);
          setIsMicEnabled(false);
        }
      }
    }

    void setupStream();
    return () => {
      mounted = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, []);

  // ── Reattach stream on phase change (video element remounts) ──
  useEffect(() => {
    if (streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [phase]);

  // ── Session timer + hard deadline countdown ──
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    if (phase === "active" || phase === "submitting") {
      intervalId = setInterval(() => {
        setElapsed((p) => p + 1);
        if (deadlineAt !== null) {
          const remaining = Math.max(0, Math.ceil((deadlineAt - Date.now()) / 1000));
          setRemainingSec(remaining);
          if (remaining <= 0 && !timeUpFiredRef.current) {
            timeUpFiredRef.current = true;
            setTimeExpired(true);
          }
        }
      }, 1000);
    }
    return () => clearInterval(intervalId);
  }, [phase, deadlineAt]);

  // ── Emotion bridge: pipe video emotions → voice WebSocket ──
  useEffect(() => {
    if (phase !== "active" || !video.analysis) return;
    const interval = setInterval(() => {
      if (video.analysis) {
        voice.sendEmotionContext(
          video.analysis.dominant_emotion,
          video.analysis.confidence_score,
          video.analysis.details.emotion_breakdown,
          {
            posture: video.analysis.details.posture,
            gaze: video.analysis.details.gaze,
            nervous_gestures: video.analysis.details.nervous_gestures,
          }
        );
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [phase, video.analysis, voice.sendEmotionContext]);

  // ── Auto-play question audio when it changes ──
  useEffect(() => {
    setIsQuestionAudioPlaying(Boolean(currentQuestionAudio));
  }, [currentQuestionAudio]);

  // ── Cleanup on unmount ──
  useEffect(() => {
    return () => {
      if (questionReplayTimeoutRef.current !== null) {
        window.clearTimeout(questionReplayTimeoutRef.current);
      }
    };
  }, []);

  // ── Finalizing phase: wait for voice final_summary then save & transition ──
  useEffect(() => {
    if (phase !== "finalizing") return;

    // Check if final_summary arrived
    if (voice.metrics.final_summary) {
      // Save session analysis and transition immediately
      void saveAndComplete();
      return;
    }

    // Countdown timer — after 10s, proceed even without summary
    if (finalizingCountdown <= 0) {
      void saveAndComplete();
      return;
    }

    const timer = setTimeout(() => {
      setFinalizingCountdown((prev) => prev - 1);
    }, 1000);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, finalizingCountdown, voice.metrics.final_summary]);

  // ── Helpers ──
  const formatElapsed = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
  };

  const toggleCamera = useCallback(() => {
    const stream = streamRef.current;
    if (!stream) return;

    const videoTracks = stream.getVideoTracks();
    if (videoTracks.length === 0) return;

    const nextState = !isCameraEnabled;
    videoTracks.forEach((track) => {
      track.enabled = nextState;
    });
    setIsCameraEnabled(nextState);
  }, [isCameraEnabled]);

  const toggleMic = useCallback(() => {
    const stream = streamRef.current;
    if (!stream) return;

    const audioTracks = stream.getAudioTracks();
    if (audioTracks.length === 0) return;

    const nextState = !isMicEnabled;
    audioTracks.forEach((track) => {
      track.enabled = nextState;
    });
    setIsMicEnabled(nextState);
  }, [isMicEnabled]);

  const replayQuestionAudio = () => {
    if (!currentQuestionAudio) return;
    setIsQuestionAudioPlaying(false);
    if (questionReplayTimeoutRef.current !== null) {
      window.clearTimeout(questionReplayTimeoutRef.current);
    }
    questionReplayTimeoutRef.current = window.setTimeout(() => {
      setIsQuestionAudioPlaying(true);
      questionReplayTimeoutRef.current = null;
    }, 50);
  };

  // ── Save session analysis to DB and transition to completed ──
  const saveAndComplete = useCallback(async () => {
    if (!interviewId) {
      logInterview("No interviewId during saveAndComplete; skipping DB save");
      setPhase("completed");
      return;
    }

    try {
      const lastVideo = lastVideoAnalysisRef.current;
      const allSnapshots = videoSnapshotsRef.current;
      const voiceSummary = voice.metrics.final_summary;
      const semanticData = voice.metrics.semantic;
      logInterview("Preparing session analysis payload", {
        interviewId,
        snapshotCount: allSnapshots.length,
        insightCount: voice.insights.length,
        hasFinalSummary: Boolean(voiceSummary),
      });

      // ── Aggregate video snapshots: continuous scores from real analysis ──
      let postureScore: number | null = null;
      let gazeScore: number | null = null;
      let avgFidgeting: number | null = null;
      let multiFaceRatio: number | null = null;
      let dominantEmotion: string | null = lastVideo?.dominant_emotion ?? null;

      if (allSnapshots.length > 0) {
        // Continuous posture: average of MediaPipe spine/posture sub-score (0-1)
        const postureScores = allSnapshots
          .map((s) => s?.details?.posture?.score)
          .filter((v): v is number => typeof v === "number");
        if (postureScores.length > 0) {
          postureScore = Math.round((postureScores.reduce((a, b) => a + b, 0) / postureScores.length) * 100);
        }

        // Continuous eye contact: average iris-based engagement score (0-1)
        const engagementScores = allSnapshots
          .map((s) => s?.engagement_score)
          .filter((v): v is number => typeof v === "number");
        if (engagementScores.length > 0) {
          gazeScore = Math.round((engagementScores.reduce((a, b) => a + b, 0) / engagementScores.length) * 100);
        }

        const fidgetScores = allSnapshots
          .map((s) => s?.details?.nervous_gestures?.fidgeting_score)
          .filter((v): v is number => typeof v === "number");
        if (fidgetScores.length > 0) {
          avgFidgeting = Math.round(
            (1 - fidgetScores.reduce((a, b) => a + b, 0) / fidgetScores.length) * 100
          );
        }

        // Background person detection: fraction of windows with >1 face
        const multiFaceCount = allSnapshots.filter((s) => (s?.faces_detected ?? 0) > 1).length;
        multiFaceRatio = multiFaceCount / allSnapshots.length;

        // Most common emotion across all snapshots
        const emotionCounts: Record<string, number> = {};
        for (const s of allSnapshots) {
          const e = s?.dominant_emotion;
          if (e) emotionCounts[e] = (emotionCounts[e] || 0) + 1;
        }
        const sorted = Object.entries(emotionCounts).sort(([, a], [, b]) => (b as number) - (a as number));
        if (sorted.length > 0) dominantEmotion = sorted[0][0];
      } else if (lastVideo) {
        postureScore = typeof lastVideo.details?.posture?.score === "number"
          ? Math.round(lastVideo.details.posture.score * 100)
          : null;
        gazeScore = typeof lastVideo.engagement_score === "number"
          ? Math.round(lastVideo.engagement_score * 100)
          : null;
      }

      const prosody = voice.metrics.prosody ?? null;

      const analysisData: SessionAnalysisData = {
        voice_summary: voiceSummary?.overall_summary ?? null,
        key_moments: voiceSummary?.key_moments ?? null,
        confidence: semanticData?.confidence_score ? Math.round(semanticData.confidence_score * 100) : null,
        clarity: null, // derived from evaluation scores below
        nervousness: null,
        posture_score: postureScore,
        gaze_score: gazeScore,
        fidgeting_score: avgFidgeting,
        dominant_emotion: dominantEmotion,
        duration_seconds: elapsed,
        prosody: prosody as Record<string, unknown> | null,
        pace_wpm: prosody?.pace_wpm ?? null,
        multi_face_ratio: multiFaceRatio,
        background_person_detected: multiFaceRatio !== null ? multiFaceRatio > 0.05 : null,
        video_timeline: allSnapshots.map((snapshot) => {
          const relativeSeconds = Math.max(
            0,
            Math.round((snapshot.captured_at - sessionStartedAtRef.current) / 1000)
          );
          return {
            timestamp: relativeSeconds,
            label: snapshot.dominant_emotion,
            payload: {
              confidence_score: snapshot.confidence_score,
              engagement_score: snapshot.engagement_score,
              posture: snapshot.details.posture ?? null,
              gaze: snapshot.details.gaze ?? null,
              nervous_gestures: snapshot.details.nervous_gestures ?? null,
              emotion_breakdown: snapshot.details.emotion_breakdown ?? {},
            },
          };
        }),
        voice_timeline: voice.insights
          .filter((insight): insight is NonNullable<typeof insight> => Boolean(insight))
          .map((insight) => ({
            timestamp: Math.max(0, Math.round(insight.time_range?.[0] ?? 0)),
            label: insight.stress_level ?? "unknown",
            payload: {
              insight: insight.insight,
              confidence_score: insight.confidence_score,
              stress_level: insight.stress_level,
              time_range: insight.time_range ?? null,
              words: insight.words ?? [],
            },
          })),
      };

      // Confidence/nervousness: prefer Hume prosody (real ML), fall back to
      // LLM semantic insights when Hume is unavailable.
      if (prosody?.source === "hume") {
        if (typeof prosody.confidence === "number") {
          analysisData.confidence = Math.round(prosody.confidence * 100);
        }
        if (typeof prosody.nervousness === "number") {
          analysisData.nervousness = Math.round(prosody.nervousness * 100);
        }
      } else if (voice.insights.length > 0) {
        const confidenceScores = voice.insights
          .filter((i): i is NonNullable<typeof i> => !!i && typeof i.confidence_score === "number")
          .map((i) => i!.confidence_score);
        if (confidenceScores.length > 0) {
          analysisData.confidence = Math.round(
            (confidenceScores.reduce((a, b) => a + b, 0) / confidenceScores.length) * 100
          );
        }

        const stressLevels = voice.insights
          .filter((i): i is NonNullable<typeof i> => !!i && typeof i.stress_level === "string")
          .map((i) => {
            const level = i!.stress_level?.toLowerCase() ?? "";
            if (level.includes("high")) return 80;
            if (level.includes("moderate") || level.includes("medium")) return 50;
            return 20;
          });
        if (stressLevels.length > 0) {
          analysisData.nervousness = Math.round(stressLevels.reduce((a, b) => a + b, 0) / stressLevels.length);
        }
      }

      // Compute clarity from turn scores
      if (turns.length > 0) {
        const avgScore = turns.reduce((s, t) => s + t.evaluation.score, 0) / turns.length;
        analysisData.clarity = Math.round(avgScore * 10);
      }

      await saveSessionAnalysis(interviewId, analysisData);
      logInterview("Session analysis saved successfully", {
        interviewId,
        videoTimelineItems: analysisData.video_timeline?.length ?? 0,
        voiceTimelineItems: analysisData.voice_timeline?.length ?? 0,
      });
      track("interview_completed", {
        interview_id: interviewId,
        questions_answered: turns.length,
        duration_seconds: elapsed,
        time_expired: timeExpired,
      });

      router.push(`/interview/analysis?id=${interviewId}`);
      return;
    } catch (err) {
      console.error("Failed to save session analysis:", err);
      logInterview("Session analysis save failed", err);
      setPhase("completed");
    }
  }, [interviewId, voice.metrics, voice.insights, elapsed, turns, timeExpired, logInterview, router]);

  // ── Start Interview ──
  const handleStartInterview = useCallback(async () => {
    setError(null);
    setPhase("loading");
    logInterview("Starting interview request", { role, difficulty, persona, questionCount, durationMinutes });

    try {
      const result: StartInterviewResponse = await apiStartInterview({
        role,
        difficulty,
        persona,
        ...(questionCount ? { max_questions: questionCount } : {}),
        ...(durationMinutes ? { duration_minutes: durationMinutes } : {}),
      });
      logInterview("Interview started", {
        interviewId: result.interview_id,
        totalQuestions: result.total_questions,
        firstQuestion: result.first_question,
        deadlineAt: result.deadline_at,
      });

      track("interview_started", {
        interview_id: result.interview_id,
        role,
        difficulty,
        persona,
        question_count: result.total_questions,
        duration_minutes: durationMinutes,
      });

      setInterviewId(result.interview_id);
      setCurrentQuestion(result.first_question);
      setCurrentQuestionAudio(result.first_question_audio_data_uri ?? null);
      setTotalQuestions(result.total_questions ?? result.questions_bank?.length ?? questionCount ?? 5);
      setQuestionIndex(0);
      setTurns([]);
      setElapsed(0);
      setAnswerText("");
      videoSnapshotsRef.current = [];
      sessionStartedAtRef.current = Date.now();
      // Client-side deadline drives the countdown UI; the backend enforces its own copy.
      if (durationMinutes) {
        setDeadlineAt(Date.now() + durationMinutes * 60_000);
        setRemainingSec(durationMinutes * 60);
      }
      timeUpFiredRef.current = false;
      setTimeExpired(false);
      setPhase("active");
      setIsRecording(true);
      video.startCapture();
      voice.resetState();
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? "Failed to start interview. Make sure backend is running.";
      logInterview("Start interview failed", err?.response?.data ?? err);
      setError(detail);
      setPhase("loading");
    }
  }, [role, difficulty, persona, questionCount, durationMinutes, video, voice, logInterview]);

  // ── Auto-start: config comes from /pre-interview via query params ──
  useEffect(() => {
    if (autoStartRef.current) return;
    if (!role || !difficulty || !persona) {
      router.replace("/pre-interview");
      return;
    }
    autoStartRef.current = true;
    void handleStartInterview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Submit Answer & Get Next Question ──
  const handleSubmitAnswer = useCallback(async () => {
    if (!interviewId || !currentQuestion) return;
    if (timeExpired) return;

    // Get answer text from voice transcript or manual input
    const voiceTranscript = voice.getTranscriptText();
    const answer = useVoiceInput && voiceTranscript.trim().length > 0
      ? voiceTranscript.trim()
      : answerText.trim();

    if (!answer) {
      logInterview("Blocked submit due to empty answer", {
        useVoiceInput,
        transcriptLength: voiceTranscript.trim().length,
        typedLength: answerText.trim().length,
      });
      setError("Please provide an answer before submitting. Speak your answer or type it in the text box.");
      return;
    }

    setError(null);
    setPhase("submitting");
    logInterview("Submitting answer", {
      interviewId,
      questionIndex,
      currentQuestion,
      answerLength: answer.length,
    });

    try {
      const result: SubmitAnswerResponse = await submitInterviewAnswer({
        interview_id: interviewId,
        answer,
      });
      logInterview("Submit answer response received", {
        status: result.status,
        nextQuestion: result.next_question,
        score: result.evaluation?.score,
      });

      // Store turn record
      setTurns((prev) => [
        ...prev,
        {
          question: currentQuestion,
          answer,
          evaluation: result.evaluation,
        },
      ]);

      // Clear transcript for next question
      voice.clearTranscript();
      setAnswerText("");

      if (result.time_expired) {
        setTimeExpired(true);
        timeUpFiredRef.current = true;
      }

      if (result.status === "completed" || !result.next_question) {
        // Interview is done — enter finalizing phase to wait for voice summary
        setIsRecording(false);
        video.stopCapture();
        setCurrentQuestion(null);
        setCurrentQuestionAudio(null);
        setFinalizingCountdown(10);
        setPhase("finalizing");
        logInterview("Interview moved to finalizing", {
          reason: result.time_expired ? "time-expired" : "completed-or-no-next-question",
        });
      } else {
        // Next question
        setCurrentQuestion(result.next_question);
        setCurrentQuestionAudio(result.next_question_audio_data_uri ?? null);
        setQuestionIndex((prev) => prev + 1);
        setPhase("active");
        logInterview("Advanced to next question", {
          nextQuestionIndex: questionIndex + 1,
          nextQuestion: result.next_question,
        });
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? "Failed to submit answer";
      logInterview("Submit answer failed", err?.response?.data ?? err);
      setError(detail);
      setPhase("active");
    }
  }, [interviewId, currentQuestion, voice, answerText, useVoiceInput, video, questionIndex, logInterview, timeExpired]);

  // ── End Interview Early ──
  const handleEndInterview = useCallback(() => {
    logInterview("Ending interview", { interviewId, elapsed });
    setIsRecording(false); // This triggers voice WS to send "STOP" and wait for final_summary
    video.stopCapture();
    setFinalizingCountdown(10);
    setPhase("finalizing");
  }, [video, interviewId, elapsed, logInterview]);

  // ── Hard stop: when the session time limit is reached, end immediately ──
  useEffect(() => {
    if (!timeExpired) return;
    if (phase === "active") {
      logInterview("Session time limit reached; ending interview now");
      handleEndInterview();
    }
  }, [timeExpired, phase, handleEndInterview, logInterview]);

  // ── Restart ──
  const handleRestart = useCallback(() => {
    router.push("/pre-interview");
  }, [router]);

  // ── Navigate to Analysis ──
  const goToAnalysis = useCallback(() => {
    if (interviewId) {
      router.push(`/interview/analysis?id=${interviewId}`);
    }
  }, [interviewId, router]);

  // ────────────────────────────────────────────────────────────────
  // LOADING PHASE
  // ────────────────────────────────────────────────────────────────
  if (phase === "loading") {
    return (
      <section className="mx-auto max-w-2xl flex flex-col items-center justify-center min-h-[60vh] space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] flex items-center justify-center shadow-lg shadow-[var(--accent-primary)]/20 animate-pulse">
          <Bot className="w-8 h-8 text-white" />
        </div>
        {error ? (
          <div className="text-center space-y-4">
            <div className="rounded-xl border border-[var(--accent-danger)]/20 bg-[var(--accent-danger)]/5 px-4 py-3 flex items-start gap-2 text-left">
              <AlertTriangle className="w-4 h-4 text-[var(--accent-danger)] mt-0.5 shrink-0" />
              <p className="text-sm text-[var(--accent-danger)]">{error}</p>
            </div>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => {
                  autoStartRef.current = true;
                  void handleStartInterview();
                }}
                className="rounded-xl bg-[var(--accent-primary)] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[var(--accent-primary)]/90 transition-all"
              >
                Try again
              </button>
              <button
                onClick={() => router.push("/pre-interview")}
                className="rounded-xl border border-[var(--border-default)] bg-white/80 px-5 py-2.5 text-sm font-medium text-[var(--text-secondary)] hover:bg-white transition-all"
              >
                Back to setup
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="text-center space-y-2">
              <h2 className="text-xl font-bold text-[var(--text-primary)]">Preparing Your Interview</h2>
              <p className="text-sm text-[var(--text-secondary)] max-w-md">
                Loading your resume context, generating your questions, and synthesizing AI voice...
              </p>
            </div>
            <LoaderCircle className="w-6 h-6 text-[var(--accent-primary)] animate-spin" />
          </>
        )}
      </section>
    );
  }

  // ────────────────────────────────────────────────────────────────
  // FINALIZING PHASE — waiting for voice final_summary
  // ────────────────────────────────────────────────────────────────
  if (phase === "finalizing") {
    return (
      <section className="mx-auto max-w-2xl flex flex-col items-center justify-center min-h-[60vh] space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--accent-success)] to-[var(--accent-primary)] flex items-center justify-center shadow-lg shadow-[var(--accent-success)]/20 animate-pulse">
          <Sparkles className="w-8 h-8 text-white" />
        </div>
        <div className="text-center space-y-2">
          <h2 className="text-xl font-bold text-[var(--text-primary)]">Finalizing Your Analysis</h2>
          <p className="text-sm text-[var(--text-secondary)] max-w-md">
            Generating voice analysis summary, saving behavioral data, and preparing your results...
          </p>
          <p className="text-xs text-[var(--text-tertiary)]">
            {voice.metrics.final_summary ? "Summary received! Saving..." : `Waiting for analysis (${finalizingCountdown}s)...`}
          </p>
        </div>
        <LoaderCircle className="w-6 h-6 text-[var(--accent-primary)] animate-spin" />
      </section>
    );
  }

  // ────────────────────────────────────────────────────────────────
  // COMPLETED PHASE
  // ────────────────────────────────────────────────────────────────
  if (phase === "completed") {
    const avgScore = turns.length > 0 ? Math.round(turns.reduce((s, t) => s + t.evaluation.score, 0) / turns.length * 10) : 0;

    return (
      <section className="mx-auto max-w-5xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">Interview Complete</h1>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Session duration: {formatElapsed(elapsed)} · {turns.length} questions answered
              {timeExpired && (
                <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-[var(--accent-warning)]/10 px-2 py-0.5 text-xs font-semibold text-[var(--accent-warning)]">
                  <AlarmClock className="w-3 h-3" />
                  Ended by time limit
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleRestart}
              className="flex items-center gap-2 rounded-xl border border-[var(--border-default)] bg-white/80 px-4 py-2.5 text-sm font-medium text-[var(--text-secondary)] hover:bg-white hover:text-[var(--accent-primary)] transition-all"
            >
              <RotateCcw className="w-4 h-4" />
              New Session
            </button>
            {interviewId && (
              <button
                onClick={goToAnalysis}
                className="flex items-center gap-2 rounded-xl bg-[var(--accent-primary)] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[var(--accent-primary)]/90 transition-all"
              >
                <Sparkles className="w-4 h-4" />
                View Full Analysis
              </button>
            )}
          </div>
        </div>

        {/* Overall Score */}
        <div className="rounded-2xl border border-[var(--border-default)] bg-gradient-to-br from-white to-[var(--surface-secondary)] p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-[var(--text-tertiary)]">Overall Score</p>
              <p className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-[var(--accent-primary)] to-[var(--accent-secondary)] mt-1">
                {avgScore}%
              </p>
            </div>
            <div className="flex gap-1">
              {turns.map((t, i) => (
                <div
                  key={i}
                  className="w-3 h-8 rounded-sm"
                  style={{
                    background:
                      t.evaluation.score >= 8
                        ? "var(--accent-success)"
                        : t.evaluation.score >= 5
                          ? "var(--accent-primary)"
                          : "var(--accent-warning)",
                    opacity: 0.3 + (t.evaluation.score / 10) * 0.7,
                  }}
                  title={`Q${i + 1}: ${t.evaluation.score}/10`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Turn-by-Turn Summary */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">Question-by-Question Breakdown</h2>
          {turns.map((turn, index) => (
            <div key={index} className="rounded-2xl border border-[var(--border-default)] bg-white/90 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--accent-primary)]">
                  Question {index + 1}
                </span>
                <span
                  className={`text-sm font-bold px-2.5 py-0.5 rounded-full ${turn.evaluation.score >= 8
                      ? "bg-[var(--accent-success)]/10 text-[var(--accent-success)]"
                      : turn.evaluation.score >= 5
                        ? "bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]"
                        : "bg-[var(--accent-warning)]/10 text-[var(--accent-warning)]"
                    }`}
                >
                  {turn.evaluation.score}/10
                </span>
              </div>
              <p className="text-sm font-medium text-[var(--text-primary)] leading-relaxed">{turn.question}</p>
              <p className="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">
                <span className="font-medium text-[var(--text-primary)]">Your answer:</span> {turn.answer}
              </p>
              <div className="mt-3 p-3 rounded-xl bg-[var(--surface-secondary)] border border-[var(--border-subtle)]">
                <p className="text-sm text-[var(--text-secondary)]">{turn.evaluation.feedback}</p>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3">
                {turn.evaluation.strengths.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--accent-success)]">Strengths</p>
                    {turn.evaluation.strengths.map((s, si) => (
                      <p key={si} className="text-xs text-[var(--text-secondary)]">• {s}</p>
                    ))}
                  </div>
                )}
                {turn.evaluation.weaknesses.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--accent-warning)]">Improve</p>
                    {turn.evaluation.weaknesses.map((w, wi) => (
                      <p key={wi} className="text-xs text-[var(--text-secondary)]">• {w}</p>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Voice Analysis Summary */}
        {voice.metrics.final_summary && (
          <div className="rounded-2xl border border-[var(--border-default)] bg-white/90 p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3">Voice & Behavioral Summary</h2>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              {voice.metrics.final_summary.overall_summary}
            </p>
            {voice.metrics.final_summary.key_moments?.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">Key Moments</p>
                {voice.metrics.final_summary.key_moments.map((m: any, i: number) => (
                  <div key={i} className="flex gap-3 text-sm">
                    <span className="text-[var(--accent-primary)] font-mono text-xs shrink-0 mt-0.5">{m.time}</span>
                    <span className="text-[var(--text-secondary)]">{m.description}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </section>
    );
  }

  // ────────────────────────────────────────────────────────────────
  // ACTIVE / SUBMITTING PHASE — Main interview UI
  // ────────────────────────────────────────────────────────────────
  const isSubmitting = phase === "submitting";
  const currentTranscriptText = voice.getTranscriptText();

  return (
    <div className="text-[var(--text-primary)] font-sans flex flex-col h-[calc(100dvh-4rem)] overflow-hidden">
      <div className="max-w-[1400px] mx-auto h-full w-full flex-1 flex flex-col space-y-3 min-h-0 overflow-hidden px-2">
        {/* ── Top Bar ─────────────────────────────────── */}
        <div className="flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] rounded-lg flex items-center justify-center shadow-sm">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="text-base font-bold text-[var(--text-primary)]">
                Evalvate Interview
              </span>
              <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
                <Timer className="w-3 h-3" />
                {formatElapsed(elapsed)}
                {remainingSec !== null && (
                  <>
                    <span className="text-[var(--border-default)]">·</span>
                    <span
                      className={`flex items-center gap-1 font-semibold ${
                        remainingSec <= 60 ? "text-[var(--accent-danger)]" : "text-[var(--text-secondary)]"
                      }`}
                    >
                      <AlarmClock className="w-3 h-3" />
                      {formatElapsed(remainingSec)} left
                    </span>
                  </>
                )}
                <span className="text-[var(--border-default)]">·</span>
                Q{questionIndex + 1}/{totalQuestions}
                <span className="text-[var(--border-default)]">·</span>
                <span className="capitalize">{role}</span>
              </div>
            </div>
          </div>

          <button
            onClick={handleEndInterview}
            disabled={isSubmitting}
            className="flex items-center gap-2 rounded-xl bg-[var(--accent-danger)]/8 text-[var(--accent-danger)] px-4 py-2 text-sm font-semibold hover:bg-[var(--accent-danger)]/15 transition-all disabled:opacity-50"
          >
            <Square className="w-3.5 h-3.5" />
            End Interview
          </button>
        </div>

        {error && (
          <div className="rounded-xl border border-[var(--accent-danger)]/20 bg-[var(--accent-danger)]/5 px-4 py-2 flex items-start gap-2 flex-shrink-0">
            <AlertTriangle className="w-4 h-4 text-[var(--accent-danger)] mt-0.5 shrink-0" />
            <p className="text-sm text-[var(--accent-danger)]">{error}</p>
          </div>
        )}

        {/* ── Main Grid ──────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-0 overflow-hidden">
          {/* LEFT: Video + Metrics */}
          <div className="lg:col-span-7 flex flex-col gap-4 min-h-0 overflow-y-auto pr-1">
            {/* Video Feed */}
            <div className="relative overflow-hidden rounded-2xl border border-[var(--border-default)] bg-[var(--surface-tertiary)] aspect-video shadow-sm flex-shrink-0">
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="w-full h-full object-cover scale-x-[-1]"
              />
              <canvas ref={canvasRef} className="hidden" />
              <VideoOverlay
                analysis={video.analysis}
                isCapturing={video.isCapturing}
                fps={video.fps}
              />

              {!isCameraEnabled ? (
                <div className="absolute inset-0 flex items-center justify-center bg-black/55 text-sm font-medium text-white/90">
                  Camera is paused
                </div>
              ) : null}

              <div className="absolute bottom-3 left-3 flex gap-2">
                <button
                  type="button"
                  onClick={toggleCamera}
                  disabled={!hasVideoTrack}
                  className={`rounded-full border p-2 shadow-sm backdrop-blur-md transition-all ${isCameraEnabled
                      ? "border-[var(--border-default)] bg-white/80 text-[var(--accent-success)] hover:bg-white"
                      : "border-[var(--accent-danger)]/60 bg-[var(--accent-danger)]/85 text-white hover:bg-[var(--accent-danger)]"
                    } disabled:cursor-not-allowed disabled:opacity-50`}
                  title={isCameraEnabled ? "Turn camera off" : "Turn camera on"}
                  aria-label={isCameraEnabled ? "Turn camera off" : "Turn camera on"}
                >
                  {isCameraEnabled ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
                </button>
                <button
                  type="button"
                  onClick={toggleMic}
                  disabled={!hasAudioTrack}
                  className={`rounded-full border p-2 shadow-sm backdrop-blur-md transition-all ${isMicEnabled
                      ? "border-[var(--border-default)] bg-white/80 text-[var(--accent-success)] hover:bg-white"
                      : "border-[var(--accent-danger)]/60 bg-[var(--accent-danger)]/85 text-white hover:bg-[var(--accent-danger)]"
                    } disabled:cursor-not-allowed disabled:opacity-50`}
                  title={isMicEnabled ? "Mute microphone" : "Unmute microphone"}
                  aria-label={isMicEnabled ? "Mute microphone" : "Unmute microphone"}
                >
                  {isMicEnabled ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Voice diagnostics strip */}
            <LiveMetrics metrics={voice.metrics} isRecording={isRecording} />

            {/* Compact video metrics */}
            {video.analysis && (
              <div className="grid grid-cols-3 gap-3 flex-shrink-0">
                <MetricChip
                  label="Posture"
                  value={video.analysis.details.posture?.is_upright ? "Upright" : "Slouched"}
                  good={video.analysis.details.posture?.is_upright}
                />
                <MetricChip
                  label="Gaze"
                  value={video.analysis.details.gaze?.direction ?? "—"}
                  good={video.analysis.details.gaze?.direction === "center"}
                />
                <MetricChip
                  label="Fidgeting"
                  value={`${Math.round((video.analysis.details.nervous_gestures?.fidgeting_score ?? 0) * 100)}%`}
                  good={(video.analysis.details.nervous_gestures?.fidgeting_score ?? 0) < 0.3}
                />
              </div>
            )}
          </div>

          {/* RIGHT: Question + Answer + Transcript */}
          <div className="lg:col-span-5 flex flex-col gap-4 min-h-0 overflow-y-auto pr-1">
            {/* AI Interviewer Avatar + Question */}
            <div className="rounded-2xl border border-[var(--border-default)] bg-white/90 p-5 shadow-sm flex-shrink-0">
              {/* Question Header */}
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--accent-primary)]">
                  Question {questionIndex + 1} of {totalQuestions}
                </span>
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    {Array.from({ length: totalQuestions }).map((_, i) => (
                      <div
                        key={i}
                        className={`w-2 h-2 rounded-full transition-colors ${i < questionIndex
                            ? "bg-[var(--accent-success)]"
                            : i === questionIndex
                              ? "bg-[var(--accent-primary)]"
                              : "bg-[var(--border-default)]"
                          }`}
                      />
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={replayQuestionAudio}
                    disabled={!currentQuestionAudio}
                    className="p-1.5 rounded-lg border border-[var(--border-default)] text-[var(--text-tertiary)] hover:text-[var(--accent-primary)] hover:border-[var(--accent-primary)]/30 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                    title="Replay question audio"
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Avatar: real-time Simli human when configured, sprite fallback otherwise */}
              <div className="mb-3">
                {isSimliEnabled ? (
                  <SimliInterviewer
                    audioSrc={currentQuestionAudio ?? ""}
                    isPlaying={Boolean(currentQuestionAudio) && isQuestionAudioPlaying}
                  />
                ) : (
                  <TalkingAvatar
                    audioSrc={currentQuestionAudio ?? ""}
                    isPlaying={Boolean(currentQuestionAudio) && isQuestionAudioPlaying}
                  />
                )}
              </div>

              {/* Question Text */}
              {currentQuestion && (
                <p className="text-base font-medium text-[var(--text-primary)] leading-relaxed">
                  {currentQuestion}
                </p>
              )}
            </div>

            {/* Answer Area */}
            <div className="rounded-2xl border border-[var(--border-default)] bg-white/90 p-5 shadow-sm flex-shrink-0">
              <div className="flex items-center justify-between mb-3">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">Your Answer</p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setUseVoiceInput(true)}
                    className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium transition-all ${useVoiceInput
                        ? "bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] border border-[var(--accent-primary)]/20"
                        : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
                      }`}
                  >
                    <Mic className="w-3 h-3" />
                    Voice
                  </button>
                  <button
                    onClick={() => setUseVoiceInput(false)}
                    className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium transition-all ${!useVoiceInput
                        ? "bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] border border-[var(--accent-primary)]/20"
                        : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
                      }`}
                  >
                    <Send className="w-3 h-3" />
                    Type
                  </button>
                </div>
              </div>

              {useVoiceInput ? (
                <div className="space-y-2">
                  <div className="min-h-[80px] max-h-[120px] overflow-y-auto rounded-xl bg-[var(--surface-secondary)] border border-[var(--border-subtle)] px-4 py-3">
                    {currentTranscriptText ? (
                      <p className="text-sm text-[var(--text-primary)] leading-relaxed">{currentTranscriptText}</p>
                    ) : (
                      <p className="text-sm text-[var(--text-tertiary)] italic">
                        {isRecording ? "Start speaking to answer the question..." : "Recording not active"}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
                    <div className={`w-2 h-2 rounded-full ${isRecording ? "bg-[var(--accent-danger)] animate-pulse" : "bg-[var(--border-default)]"}`} />
                    {voice.sttError ??
                      (isRecording
                        ? voice.sttMode === "browser"
                          ? "Listening (browser speech)..."
                          : "Listening..."
                        : "Microphone off")}
                  </div>
                </div>
              ) : (
                <textarea
                  rows={4}
                  value={answerText}
                  onChange={(e) => setAnswerText(e.target.value)}
                  disabled={isSubmitting}
                  placeholder="Type your answer here..."
                  className="w-full resize-none rounded-xl border border-[var(--border-default)] bg-[var(--surface-secondary)] px-4 py-3 text-sm text-[var(--text-primary)] outline-none ring-[var(--accent-primary)]/30 transition placeholder:text-[var(--text-tertiary)] focus:ring-2 focus:border-[var(--accent-primary)]/30"
                />
              )}

              {/* Submit / Next Button */}
              <button
                onClick={handleSubmitAnswer}
                disabled={isSubmitting || (!currentTranscriptText && useVoiceInput && !answerText.trim())}
                className="mt-3 w-full flex items-center justify-center gap-2 rounded-xl bg-[var(--accent-primary)] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[var(--accent-primary)]/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]"
              >
                {isSubmitting ? (
                  <>
                    <LoaderCircle className="w-4 h-4 animate-spin" />
                    Evaluating & Loading Next...
                  </>
                ) : (
                  <>
                    Submit & Next Question
                    <ChevronRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>

            {/* Live Transcript Panel */}
            <div className="rounded-2xl border border-[var(--border-default)] bg-white/90 shadow-sm flex-1 min-h-0 overflow-hidden">
              <TranscriptTimeline
                transcript={voice.transcript}
                insights={voice.insights}
                isRecording={isRecording}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Helper Components ──────────────────────────────────────────────

function MetricChip({ label, value, good }: { label: string; value: string; good?: boolean }) {
  return (
    <div className="rounded-xl border border-[var(--border-default)] bg-white/90 px-3 py-2.5 shadow-sm">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
        {label}
      </p>
      <div className="flex items-center gap-1.5 mt-1">
        <div
          className={`w-1.5 h-1.5 rounded-full ${good ? "bg-[var(--accent-success)]" : "bg-[var(--accent-warning)]"}`}
        />
        <span className="text-sm font-semibold text-[var(--text-primary)] capitalize">{value}</span>
      </div>
    </div>
  );
}

export default function InterviewPage() {
  return (
    <Suspense
      fallback={
        <section className="mx-auto max-w-2xl flex flex-col items-center justify-center min-h-[60vh]">
          <LoaderCircle className="w-6 h-6 text-[var(--accent-primary)] animate-spin" />
        </section>
      }
    >
      <InterviewPageInner />
    </Suspense>
  );
}
