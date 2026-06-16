"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Mic, AudioLines, FileText, Activity, TrendingUp, ArrowUpRight } from "lucide-react";
import { TID } from "@/constants/landingTestIds";

const FEATURES = [
  { id: TID.featureMockInterview, icon: Mic, title: "AI Mock Interviews",
    desc: "Domain-specific simulations that adapt to your role, your level, and the questions that actually get asked.",
    span: "md:col-span-7 md:row-span-2", visual: "interview" },
  { id: TID.featureSpeech, icon: AudioLines, title: "Speech Analysis",
    desc: "Pace, filler words, clarity, and tone - measured to the millisecond.",
    span: "md:col-span-5", visual: "waveform" },
  { id: TID.featureResume, icon: FileText, title: "Resume Analysis",
    desc: "ATS scoring, gap detection, line-by-line rewrites.",
    span: "md:col-span-5", visual: "doc" },
  { id: TID.featureConfidence, icon: Activity, title: "Confidence Scoring",
    desc: "Micro-expressions, posture, vocal stability - quantified into a single trust score.",
    span: "md:col-span-6", visual: "score" },
  { id: TID.featureMetrics, icon: TrendingUp, title: "Performance Improvement",
    desc: "Track every session. See the delta. Walk in different than you came.",
    span: "md:col-span-6", visual: "chart" },
];

function FeatureVisual({ type }: { type: string }) {
  if (type === "waveform") {
    return (
      <img src="/mockups/vocal_facial.png" className="absolute bottom-0 left-0 w-full h-[160px] object-cover object-top opacity-80" alt="Vocal and Facial Analysis" style={{ WebkitMaskImage: 'linear-gradient(to top, transparent 0%, black 100%)' }} />
    );
  }
  if (type === "doc") {
    return (
      <img src="/mockups/resume_report.png" className="absolute bottom-0 left-0 w-full h-[160px] object-cover object-top opacity-80" alt="Resume Analysis" style={{ WebkitMaskImage: 'linear-gradient(to top, transparent 0%, black 100%)' }} />
    );
  }
  if (type === "score") {
    return (
      <img src="/mockups/confidence.png" className="absolute bottom-0 right-0 w-full h-[160px] object-cover object-top opacity-80" alt="Confidence Score" style={{ WebkitMaskImage: 'linear-gradient(to top, transparent 0%, black 100%)' }} />
    );
  }
  if (type === "chart") {
    return (
      <svg viewBox="0 0 300 100" className="absolute bottom-0 left-0 right-0 w-full h-32 opacity-90">
        <defs>
          <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f97316" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#f97316" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d="M0,80 C40,75 60,65 90,55 C120,45 150,52 180,38 C210,25 240,20 270,12 L300,8 L300,100 L0,100 Z" fill="url(#cg)" />
        <path d="M0,80 C40,75 60,65 90,55 C120,45 150,52 180,38 C210,25 240,20 270,12 L300,8" fill="none" stroke="#f97316" strokeWidth="1.5" />
        {[10, 40, 70, 100, 130, 160, 190, 220, 250, 280].map((x, i) => (
          <circle key={i} cx={x} cy={80 - i * 7} r="1.6" fill="#fff" opacity="0.5" />
        ))}
      </svg>
    );
  }
  // interview
  return (
    <div className="absolute inset-0 p-6 flex flex-col justify-end">
      <div className="rounded-xl border border-white/10 bg-black/50 backdrop-blur-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="font-mono text-[10px] tracking-[0.25em] uppercase text-white/60">live · session 04</span>
          </div>
          <span className="font-mono text-[10px] tracking-[0.2em] text-orange-400">00:12:48</span>
        </div>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-orange-400 pt-1">AI</span>
            <p className="text-white/90 text-[14px] font-medium leading-snug">
              Walk me through a time you led a project under pressure. What was the moment you knew it would work?
            </p>
          </div>
          <div className="flex items-start gap-3">
            <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-white/40 pt-1">YOU</span>
            <div className="flex items-end gap-[2px] h-6">
              {Array.from({ length: 32 }).map((_, i) => (
                <span key={i} className="w-[2px] rounded-sm bg-white/70"
                  style={{ height: `${Math.round(8 + (Math.sin(i * 0.7) + 1) * 8)}px` }} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ProductShowcase() {
  const sectionRef = useRef<HTMLElement>(null);
  const headingRef = useRef<HTMLDivElement>(null);
  const cardsRef = useRef<HTMLDivElement[]>([]);
  cardsRef.current = [];

  const addCard = (el: HTMLDivElement | null) => {
    if (el && !cardsRef.current.includes(el)) cardsRef.current.push(el);
  };

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    const ctx = gsap.context(() => {
      gsap.from(headingRef.current, {
        opacity: 0, y: 60, duration: 1.2, ease: "expo.out",
        scrollTrigger: { trigger: headingRef.current, start: "top 80%" },
      });
      gsap.from(cardsRef.current, {
        opacity: 0, y: 40, duration: 1, ease: "expo.out", stagger: 0.1,
        scrollTrigger: { trigger: cardsRef.current[0], start: "top 85%" },
      });
    }, sectionRef);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={sectionRef} data-testid={TID.productSection} className="relative bg-[#050505] pt-32 pb-32 px-6 md:px-12">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[120vmin] h-[40vmin] door-light opacity-25 blur-3xl pointer-events-none" />
      <div className="relative max-w-7xl mx-auto">
        <div ref={headingRef} className="max-w-4xl mb-20">
          <h2 className="font-display font-extrabold text-[clamp(40px,6vw,84px)] leading-[1.02] tracking-[-0.04em] text-white">
            Everything you need <br />
            <span className="text-orange-500">to succeed.</span>
          </h2>
          <p className="mt-8 text-white/55 text-[17px] max-w-xl leading-relaxed">
            Comprehensive interview preparation tools. Built to help you succeed in any technical or behavioral interview.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-12 auto-rows-[260px] gap-5">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.id} ref={addCard} data-testid={f.id}
                className={`bento-card group p-7 flex flex-col justify-between ${f.span}`}>
                <div className="flex items-start justify-between relative z-10">
                  <div className="w-11 h-11 rounded-xl border border-white/10 bg-white/[0.03] flex items-center justify-center text-orange-500">
                    <Icon strokeWidth={1.5} className="w-5 h-5" />
                  </div>
                  <ArrowUpRight strokeWidth={1.5}
                    className="w-5 h-5 text-white/30 group-hover:text-orange-500 group-hover:rotate-[12deg] transition-all duration-300" />
                </div>
                <div className="relative z-10 max-w-md">
                  <h3 className="font-display font-bold text-[22px] md:text-[26px] text-white tracking-[-0.02em] mb-2.5">
                    {f.title}
                  </h3>
                  <p className="text-[14px] text-white/55 leading-relaxed">{f.desc}</p>
                </div>
                <FeatureVisual type={f.visual} />
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
