"use client";

import { motion } from "framer-motion";
import { Rocket } from "lucide-react";

interface ComingSoonPageProps {
  featureName: string;
  releaseEta?: string;
}

export function ComingSoonPage({ featureName, releaseEta = "Coming Soon" }: ComingSoonPageProps) {
  return (
    <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-6 max-w-md px-6"
      >
        {/* Animated ring */}
        <div className="relative mx-auto w-24 h-24">
          <div className="absolute inset-0 rounded-full border-2 border-violet-500/30 animate-ping" />
          <div className="absolute inset-2 rounded-full border-2 border-violet-500/50" />
          <div className="absolute inset-4 rounded-full bg-violet-500/10 flex items-center justify-center">
            <Rocket className="w-7 h-7 text-violet-300" />
          </div>
        </div>

        <div>
          <h1 className="text-2xl font-bold text-white mb-2">{featureName}</h1>
          <p className="text-slate-400 text-sm leading-relaxed">
            We&apos;re building something powerful. This feature is actively in development
            and will be available shortly.
          </p>
        </div>

        <div
          className="inline-flex items-center gap-2 bg-violet-500/10 border border-violet-500/20
                        rounded-full px-4 py-2 text-violet-300 text-sm font-medium"
        >
          <div className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
          {releaseEta}
        </div>

        <div>
          <button
            onClick={() => window.history.back()}
            className="text-slate-500 hover:text-slate-300 text-sm transition-colors underline"
          >
            &larr; Go back
          </button>
        </div>
      </motion.div>
    </div>
  );
}
