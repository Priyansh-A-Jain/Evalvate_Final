"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  LoaderCircle,
  MessageSquare,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { getSharedReport, type InterviewDetailResponse } from "@/lib/interviewAgentApi";
import { config } from "@/lib/config";

export default function PublicReportPage() {
  const params = useParams<{ token: string }>();
  const token = params?.token;

  const [data, setData] = useState<InterviewDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setError("Invalid report link.");
      setLoading(false);
      return;
    }
    async function load() {
      try {
        const result = await getSharedReport(String(token));
        setData(result);
      } catch {
        setError("This report does not exist or is no longer shared.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
        <LoaderCircle className="w-8 h-8 text-violet-400 animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[#0A0A0F] flex flex-col items-center justify-center gap-4 px-6 text-center">
        <AlertTriangle className="w-10 h-10 text-amber-400" />
        <h1 className="text-xl font-bold text-white">Report unavailable</h1>
        <p className="text-sm text-slate-400 max-w-sm">{error}</p>
      </div>
    );
  }

  const { interview, responses } = data;
  const session = interview.session_analysis;
  const scores = responses.map((r) => r.score ?? 0);
  const avgScore = scores.length > 0 ? Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) : 0;
  const overall = session?.overall_score != null ? Math.round(session.overall_score) : avgScore;
  const grade = session?.grade ?? null;
  const components = session?.component_scores ?? null;
  const prosody = (session?.prosody ?? null) as { pace_wpm?: number; filler_count?: number } | null;

  const componentRows = components
    ? [
        { label: "Technical", value: components.technical ?? 0 },
        { label: "Communication", value: components.communication ?? 0 },
        { label: "Eye Contact", value: components.eye_contact ?? 0 },
        { label: "Emotion", value: components.emotion ?? 0 },
        { label: "Structure", value: components.structure ?? 0 },
      ]
    : [];

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      <div className="fixed inset-0 bg-gradient-to-b from-violet-950/20 via-transparent to-transparent pointer-events-none" />

      <div className="relative z-10 max-w-3xl mx-auto px-6 py-12 space-y-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Bot className="w-5 h-5 text-violet-400" />
              <span className="text-violet-400 text-xs font-semibold uppercase tracking-[0.2em]">
                {config.appName} Interview Report
              </span>
            </div>
            <h1 className="text-2xl font-bold">{interview.role}</h1>
            <p className="text-slate-400 text-sm mt-1 capitalize">
              {interview.difficulty} difficulty · {interview.persona} persona ·{" "}
              {new Date(interview.created_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          </div>
          <div className="text-right shrink-0">
            <div className="flex items-baseline gap-2">
              {grade && (
                <span className="rounded-lg bg-violet-500/15 border border-violet-400/25 px-2.5 py-1 text-lg font-extrabold text-violet-300">
                  {grade}
                </span>
              )}
              <span className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-blue-400">
                {overall}%
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">{components ? "Weighted Overall" : "Overall Score"}</p>
          </div>
        </div>

        {/* Component scores */}
        {componentRows.length > 0 && (
          <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-6">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-5 flex items-center gap-2">
              <Activity className="w-4 h-4 text-violet-400" />
              Score Breakdown
            </h2>
            <div className="space-y-4">
              {componentRows.map((row) => (
                <div key={row.label}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm text-slate-300">{row.label}</span>
                    <span className="text-sm font-semibold text-white">{row.value.toFixed(1)}/10</span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-violet-500 to-blue-500 rounded-full"
                      style={{ width: `${Math.min(100, row.value * 10)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Delivery metrics */}
        {(prosody?.pace_wpm != null || session?.dominant_emotion) && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {prosody?.pace_wpm != null && (
              <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-4">
                <p className="text-[11px] text-slate-500 uppercase tracking-wider">Speaking Pace</p>
                <p className="text-xl font-bold mt-1">{Math.round(prosody.pace_wpm)} WPM</p>
              </div>
            )}
            {prosody?.filler_count != null && (
              <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-4">
                <p className="text-[11px] text-slate-500 uppercase tracking-wider">Filler Words</p>
                <p className="text-xl font-bold mt-1">{prosody.filler_count}</p>
              </div>
            )}
            {session?.dominant_emotion && (
              <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-4">
                <p className="text-[11px] text-slate-500 uppercase tracking-wider">Dominant Emotion</p>
                <p className="text-xl font-bold mt-1 capitalize">{session.dominant_emotion}</p>
              </div>
            )}
          </div>
        )}

        {/* Voice summary */}
        {session?.voice_summary && (
          <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-6">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-violet-400" />
              AI Summary
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">{session.voice_summary}</p>
          </div>
        )}

        {/* Per-question breakdown */}
        <div className="space-y-4">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-violet-400" />
            Question-by-Question
          </h2>
          {responses.map((response, index) => (
            <div key={response.id} className="bg-white/[0.03] border border-white/10 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-violet-400">
                  Question {index + 1}
                </span>
                <span
                  className={`text-sm font-bold px-2.5 py-0.5 rounded-full ${
                    (response.score ?? 0) >= 8
                      ? "bg-emerald-500/15 text-emerald-300"
                      : (response.score ?? 0) >= 5
                        ? "bg-violet-500/15 text-violet-300"
                        : "bg-amber-500/15 text-amber-300"
                  }`}
                >
                  {response.score ?? "—"}/10
                </span>
              </div>
              <p className="text-sm font-medium text-white leading-relaxed">{response.question}</p>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                <span className="text-slate-300 font-medium">Answer:</span> {response.answer}
              </p>
              {response.feedback && (
                <div className="mt-3 rounded-xl bg-white/[0.04] border border-white/5 p-3">
                  <p className="text-sm text-slate-300">{response.feedback}</p>
                </div>
              )}
              {(response.strengths?.length || response.weaknesses?.length) ? (
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {response.strengths && response.strengths.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Strengths
                      </p>
                      {response.strengths.map((item, i) => (
                        <p key={i} className="text-xs text-slate-400">- {item}</p>
                      ))}
                    </div>
                  )}
                  {response.weaknesses && response.weaknesses.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-amber-400 flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" /> Improve
                      </p>
                      {response.weaknesses.map((item, i) => (
                        <p key={i} className="text-xs text-slate-400">- {item}</p>
                      ))}
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="border-t border-white/5 pt-6 text-center">
          <p className="text-xs text-slate-500">
            Generated by <span className="text-violet-400 font-semibold">{config.appName}</span> — AI-powered mock
            interviews with real multimodal analysis.
          </p>
        </div>
      </div>
    </div>
  );
}
