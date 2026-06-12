# 🏆 CURSOR BUILD PROMPT — PART 3 OF 3
## Report System + Question Bank + Production Polish + Shareable Reports
### Paste this into Cursor Composer (Cmd+I) — ONLY after Parts 1 and 2 are complete

---

## CONTEXT

You are working on **Evalvate**. Parts 1 and 2 are complete. Part 3 delivers:
1. **Complete Report System** — real weighted scores, in-depth analysis, PDF export, shareable URLs
2. **Hybrid Question Bank** — your questions mixed with Gemini-generated questions
3. **Production Polish** — error monitoring, analytics, landing page, and demo mode

---

## TASK 1 — COMPLETE REPORT REDESIGN

The report is the product. This is what users pay for. It must be stunning, data-rich, and 100% derived from real session data.

### Step 1: Scoring Engine (Backend)

**Create `backend/app/results/scoring_engine.py`:**
```python
"""
Evalvate Interview Scoring Engine
All scores 0-10. All formulas documented and defensible.
"""
import math
from typing import Optional

class InterviewScoringEngine:
    
    # ─── Weights for Overall Score ─────────────────────────
    WEIGHTS = {
        "technical":      0.35,  # Gemini rubric evaluation
        "communication":  0.25,  # Hume prosody composite
        "eye_contact":    0.15,  # Real gaze estimation
        "emotion":        0.15,  # DeepFace emotion confidence ratio
        "structure":      0.10,  # STAR/answer structure from Gemini
    }
    
    def calculate_overall_score(self, session_data: dict) -> dict:
        """
        Master scoring function. Returns all component scores + overall.
        """
        scores = {}
        
        # 1. Technical Score — from Gemini evaluations
        scores["technical"] = self._calc_technical_score(session_data)
        
        # 2. Communication Score — from Hume prosody
        scores["communication"] = self._calc_communication_score(session_data)
        
        # 3. Eye Contact Score — from iris gaze math
        scores["eye_contact"] = self._calc_eye_contact_score(session_data)
        
        # 4. Emotion Score — from DeepFace
        scores["emotion"] = self._calc_emotion_score(session_data)
        
        # 5. Structure Score — from Gemini rubric
        scores["structure"] = self._calc_structure_score(session_data)
        
        # Weighted overall
        overall = sum(
            scores[k] * self.WEIGHTS[k]
            for k in self.WEIGHTS
            if scores.get(k) is not None
        )
        
        # Percentile and grade
        grade = self._score_to_grade(overall)
        percentile = self._estimate_percentile(overall)
        
        return {
            "overall_score": round(overall, 2),
            "component_scores": {k: round(v, 2) for k, v in scores.items()},
            "weights_used": self.WEIGHTS,
            "grade": grade,
            "percentile": percentile,
            "score_breakdown_explanation": self._explain_scores(scores, overall),
        }
    
    def _calc_technical_score(self, session: dict) -> float:
        """Average Gemini technical score across all answered questions"""
        questions = session.get("questions", [])
        answered = [q for q in questions if q.get("answer_evaluation")]
        if not answered:
            return 5.0
        scores = [
            q["answer_evaluation"].get("technical_score", 5) 
            for q in answered
        ]
        return sum(scores) / len(scores)
    
    def _calc_communication_score(self, session: dict) -> float:
        """Composite from Hume prosody data"""
        prosody = session.get("prosody_data", {})
        if not prosody or prosody.get("source") == "transcript_estimation":
            # Fall back to transcript-based clarity only
            clarity = prosody.get("avg_clarity_score", 5.0)
            return clarity
        
        components = [
            prosody.get("avg_confidence_score", 5.0) * 0.30,
            prosody.get("avg_clarity_score", 5.0) * 0.30,
            prosody.get("avg_pace_score", 5.0) * 0.25,
            prosody.get("avg_engagement_score", 5.0) * 0.15,
        ]
        return sum(components)
    
    def _calc_eye_contact_score(self, session: dict) -> float:
        """Based on real iris tracking percentage"""
        gaze = session.get("gaze_data", {})
        pct = gaze.get("eye_contact_percentage", None)
        if pct is None:
            return 5.0
        # Convert percentage (0-100) to score (0-10)
        # 80%+ eye contact = 10/10, linear below
        return min(10.0, (pct / 80) * 10)
    
    def _calc_emotion_score(self, session: dict) -> float:
        """DeepFace: ratio of confident vs nervous frames"""
        emotion = session.get("emotion_data", {})
        confident_ratio = emotion.get("confident_frame_ratio", None)
        if confident_ratio is None:
            return 5.0
        nervous_ratio = emotion.get("nervous_frame_ratio", 0)
        # Score: confidence bonus, nervousness penalty
        score = (confident_ratio * 10) - (nervous_ratio * 5)
        return max(0.0, min(10.0, score))
    
    def _calc_structure_score(self, session: dict) -> float:
        """Gemini rubric: how well answers followed structure (STAR, clarity)"""
        questions = session.get("questions", [])
        answered = [q for q in questions if q.get("answer_evaluation")]
        if not answered:
            return 5.0
        scores = [
            q["answer_evaluation"].get("structure_score", 5)
            for q in answered
        ]
        return sum(scores) / len(scores)
    
    def _score_to_grade(self, score: float) -> str:
        if score >= 9.0: return "S"    # Exceptional
        elif score >= 8.0: return "A"   # Strong
        elif score >= 7.0: return "B"   # Good
        elif score >= 5.5: return "C"   # Average
        elif score >= 4.0: return "D"   # Below Average
        else: return "F"                # Needs Significant Work
    
    def _estimate_percentile(self, score: float) -> int:
        """Rough percentile based on normal distribution (mean=6.5, std=1.5)"""
        z = (score - 6.5) / 1.5
        # Approximate CDF
        percentile = int(50 * (1 + math.erf(z / math.sqrt(2))))
        return max(1, min(99, percentile))
    
    def _explain_scores(self, scores: dict, overall: float) -> dict:
        """Generate human-readable explanations for each score"""
        def explain(category: str, score: float) -> str:
            if score >= 8: return f"Strong {category.replace('_', ' ')} performance"
            elif score >= 6: return f"Adequate {category.replace('_', ' ')}"
            elif score >= 4: return f"{category.replace('_', ' ').title()} needs improvement"
            else: return f"Significant gaps in {category.replace('_', ' ')}"
        
        return {k: explain(k, v) for k, v in scores.items()}


scoring_engine = InterviewScoringEngine()
```

### Step 2: Add scoring to report generation

In `backend/app/results/service.py`, call `scoring_engine.calculate_overall_score(session_data)` and store the result alongside the report.

### Step 3: Build the Report UI

**Create `se-hack/app/interview/analysis/components/ReportView.tsx`** — a comprehensive, beautiful report component.

Design spec: dark background, color-coded scores, charts using recharts, professional typography.

```tsx
'use client';
import { motion } from 'framer-motion';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';
import { Shield, Eye, Mic, Brain, Activity, TrendingUp, AlertTriangle, Download, Share2 } from 'lucide-react';

interface ReportViewProps {
  report: {
    overall_score: number;
    component_scores: Record<string, number>;
    grade: string;
    percentile: number;
    questions: Array<{
      question_text: string;
      answer_transcript: string;
      technical_score: number;
      structure_score: number;
      feedback: string;
      strengths: string[];
      improvements: string[];
      prosody: {
        confidence_score: number;
        tone_classification: string;
        clarity_score: number;
        top_emotions: Array<{ name: string; score: number }>;
      };
    }>;
    gaze_data: {
      eye_contact_score: number;
      eye_contact_percentage: number;
      gaze_distribution: Record<string, number>;
    };
    integrity_check: {
      integrity_violation: boolean;
      intrusion_percentage: number;
      severity: string;
    };
    prosody_data: {
      avg_confidence_score: number;
      dominant_tone: string;
      avg_clarity_score: number;
      avg_pace_score: number;
    };
    created_at: string;
    role: string;
    difficulty: string;
  };
  onDownloadPdf: () => void;
  shareUrl?: string;
}

// Score color mapping
function scoreColor(score: number): string {
  if (score >= 8) return '#10B981'; // emerald
  if (score >= 6) return '#3B82F6'; // blue
  if (score >= 4) return '#F59E0B'; // amber
  return '#EF4444'; // red
}

function ScoreRing({ score, size = 120, label }: { score: number; size?: number; label: string }) {
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDash = (score / 10) * circumference;
  const color = scoreColor(score);
  
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size/2} cy={size/2} r={radius} stroke="rgba(255,255,255,0.06)" strokeWidth="8" fill="none" />
          <circle
            cx={size/2} cy={size/2} r={radius}
            stroke={color} strokeWidth="8" fill="none"
            strokeDasharray={`${strokeDash} ${circumference}`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 1s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-white">{score.toFixed(1)}</span>
          <span className="text-xs text-slate-400">/10</span>
        </div>
      </div>
      <span className="text-xs text-slate-400 text-center">{label}</span>
    </div>
  );
}

export function ReportView({ report, onDownloadPdf, shareUrl }: ReportViewProps) {
  const radarData = [
    { subject: 'Technical', score: report.component_scores.technical * 10 },
    { subject: 'Communication', score: report.component_scores.communication * 10 },
    { subject: 'Eye Contact', score: report.component_scores.eye_contact * 10 },
    { subject: 'Emotion', score: report.component_scores.emotion * 10 },
    { subject: 'Structure', score: report.component_scores.structure * 10 },
  ];

  const questionScores = report.questions.map((q, i) => ({
    name: `Q${i + 1}`,
    technical: q.technical_score,
    communication: q.prosody?.confidence_score || 5,
  }));

  const gazeDistData = Object.entries(report.gaze_data?.gaze_distribution || {}).map(([dir, pct]) => ({
    direction: dir.charAt(0).toUpperCase() + dir.slice(1),
    percentage: Math.round(pct * 100),
  }));

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white p-6 space-y-6">
      
      {/* ── HEADER ── */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        className="flex items-start justify-between"
      >
        <div>
          <p className="text-violet-400 text-sm font-medium uppercase tracking-wider mb-1">Interview Report</p>
          <h1 className="text-3xl font-bold">{report.role}</h1>
          <p className="text-slate-400 mt-1">{report.difficulty} · {new Date(report.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
        </div>
        <div className="flex gap-3">
          {shareUrl && (
            <button onClick={() => navigator.clipboard.writeText(shareUrl)}
              className="flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl px-4 py-2 text-sm transition-colors">
              <Share2 className="w-4 h-4" /> Share
            </button>
          )}
          <button onClick={onDownloadPdf}
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 rounded-xl px-4 py-2 text-sm font-medium transition-colors">
            <Download className="w-4 h-4" /> Download PDF
          </button>
        </div>
      </motion.div>

      {/* ── INTEGRITY VIOLATION BANNER ── */}
      {report.integrity_check?.integrity_violation && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="flex items-start gap-3 bg-amber-500/10 border border-amber-500/30 rounded-2xl p-4"
        >
          <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-amber-300 font-medium text-sm">Session Integrity Notice</p>
            <p className="text-amber-200/70 text-xs mt-1">
              Multiple individuals were detected in the frame during {report.integrity_check.intrusion_percentage.toFixed(1)}% of the session.
              This has been noted in the report. Severity: <span className="font-medium">{report.integrity_check.severity}</span>.
            </p>
          </div>
        </motion.div>
      )}

      {/* ── OVERALL SCORE HERO ── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="bg-white/[0.03] border border-white/10 rounded-2xl p-8"
      >
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
          {/* Big score */}
          <div className="text-center">
            <div className="text-7xl font-black mb-2" style={{ color: scoreColor(report.overall_score) }}>
              {report.overall_score.toFixed(1)}
            </div>
            <div className="text-slate-400 text-sm">Overall Score /10</div>
            <div className="flex items-center justify-center gap-3 mt-4">
              <span className="text-3xl font-bold text-white">{report.grade}</span>
              <div className="text-left">
                <div className="text-white text-sm font-medium">Grade</div>
                <div className="text-slate-400 text-xs">Top {100 - report.percentile}% percentile</div>
              </div>
            </div>
          </div>
          
          {/* Component score rings */}
          <div className="col-span-2 grid grid-cols-5 gap-4 justify-items-center">
            {[
              { key: 'technical', label: 'Technical' },
              { key: 'communication', label: 'Voice' },
              { key: 'eye_contact', label: 'Eye Contact' },
              { key: 'emotion', label: 'Confidence' },
              { key: 'structure', label: 'Structure' },
            ].map(item => (
              <ScoreRing
                key={item.key}
                score={report.component_scores[item.key] || 0}
                size={90}
                label={item.label}
              />
            ))}
          </div>
        </div>
      </motion.div>

      {/* ── CHARTS ROW ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar Chart */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          className="bg-white/[0.03] border border-white/10 rounded-2xl p-6"
        >
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-6">Performance Radar</h3>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.08)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#94A3B8', fontSize: 12 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
              <Radar dataKey="score" stroke="#7C3AED" fill="#7C3AED" fillOpacity={0.2} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Score Progression */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25 }}
          className="bg-white/[0.03] border border-white/10 rounded-2xl p-6"
        >
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-6">Score per Question</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={questionScores}>
              <XAxis dataKey="name" tick={{ fill: '#94A3B8', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 10]} tick={{ fill: '#94A3B8', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1E1E2E', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12 }}
                labelStyle={{ color: '#E2E8F0' }}
              />
              <Line type="monotone" dataKey="technical" stroke="#7C3AED" strokeWidth={2} dot={{ fill: '#7C3AED', r: 4 }} name="Technical" />
              <Line type="monotone" dataKey="communication" stroke="#3B82F6" strokeWidth={2} dot={{ fill: '#3B82F6', r: 4 }} name="Communication" />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* ── VOCAL ANALYSIS ── */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
        className="bg-white/[0.03] border border-white/10 rounded-2xl p-6"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
            <Mic className="w-4 h-4 text-blue-400" />
          </div>
          <h3 className="font-semibold text-white">Vocal Analysis</h3>
          <span className="text-xs text-slate-500 ml-auto">Powered by Hume AI Prosody</span>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Confidence', value: report.prosody_data?.avg_confidence_score, unit: '/10' },
            { label: 'Clarity', value: report.prosody_data?.avg_clarity_score, unit: '/10' },
            { label: 'Pace Score', value: report.prosody_data?.avg_pace_score, unit: '/10' },
            { label: 'Dominant Tone', value: null, text: report.prosody_data?.dominant_tone || '—' },
          ].map(item => (
            <div key={item.label} className="bg-white/[0.03] rounded-xl p-4">
              <p className="text-slate-400 text-xs mb-2">{item.label}</p>
              {item.text ? (
                <p className="text-white font-semibold capitalize">{item.text}</p>
              ) : (
                <p className="text-white font-bold text-xl" style={{ color: item.value ? scoreColor(item.value) : undefined }}>
                  {item.value?.toFixed(1)}<span className="text-slate-400 text-sm font-normal">{item.unit}</span>
                </p>
              )}
            </div>
          ))}
        </div>
      </motion.div>

      {/* ── EYE CONTACT ── */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }}
        className="bg-white/[0.03] border border-white/10 rounded-2xl p-6"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Eye className="w-4 h-4 text-emerald-400" />
          </div>
          <h3 className="font-semibold text-white">Eye Contact & Gaze Analysis</h3>
          <span className="text-xs text-slate-500 ml-auto">MediaPipe iris tracking</span>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="flex items-center gap-6">
            <ScoreRing score={report.gaze_data?.eye_contact_score || 0} size={100} label="Eye Contact" />
            <div>
              <p className="text-white font-semibold text-2xl">{report.gaze_data?.eye_contact_percentage?.toFixed(0)}%</p>
              <p className="text-slate-400 text-sm">of session with eye contact</p>
              <p className="text-slate-500 text-xs mt-1">Ideal: 70–80%</p>
            </div>
          </div>
          <div>
            <p className="text-slate-400 text-xs uppercase tracking-wider mb-3">Gaze Distribution</p>
            <ResponsiveContainer width="100%" height={120}>
              <BarChart data={gazeDistData} layout="vertical">
                <XAxis type="number" domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="direction" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} width={55} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1E1E2E', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                  formatter={(v: number) => [`${v}%`, 'Time']}
                />
                <Bar dataKey="percentage" radius={4}>
                  {gazeDistData.map((entry, i) => (
                    <Cell key={i} fill={entry.direction === 'Center' ? '#10B981' : '#374151'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </motion.div>

      {/* ── PER-QUESTION BREAKDOWN ── */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}
        className="space-y-4"
      >
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Brain className="w-5 h-5 text-violet-400" />
          Question-by-Question Breakdown
        </h3>
        {report.questions.map((q, i) => (
          <div key={i} className="bg-white/[0.03] border border-white/10 rounded-2xl p-6">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-semibold text-violet-400 bg-violet-500/10 px-2.5 py-1 rounded-full">Q{i + 1}</span>
                  {q.prosody?.tone_classification && (
                    <span className="text-xs text-slate-400 bg-white/5 px-2.5 py-1 rounded-full capitalize">
                      {q.prosody.tone_classification} tone
                    </span>
                  )}
                </div>
                <p className="text-white font-medium">{q.question_text}</p>
              </div>
              <div className="flex gap-3 flex-shrink-0">
                <div className="text-center">
                  <div className="text-xl font-bold" style={{ color: scoreColor(q.technical_score) }}>
                    {q.technical_score.toFixed(1)}
                  </div>
                  <div className="text-xs text-slate-500">Technical</div>
                </div>
                {q.prosody?.confidence_score && (
                  <div className="text-center">
                    <div className="text-xl font-bold" style={{ color: scoreColor(q.prosody.confidence_score) }}>
                      {q.prosody.confidence_score.toFixed(1)}
                    </div>
                    <div className="text-xs text-slate-500">Voice</div>
                  </div>
                )}
              </div>
            </div>
            
            {/* Transcript */}
            <div className="bg-black/20 rounded-xl p-4 mb-4">
              <p className="text-xs text-slate-500 mb-1">Your answer</p>
              <p className="text-slate-300 text-sm leading-relaxed">{q.answer_transcript || 'No transcript recorded'}</p>
            </div>
            
            {/* Feedback */}
            <p className="text-slate-300 text-sm mb-4">{q.feedback}</p>
            
            {/* Strengths + Improvements */}
            <div className="grid grid-cols-2 gap-4">
              {q.strengths?.length > 0 && (
                <div>
                  <p className="text-emerald-400 text-xs font-medium mb-2">✓ Strengths</p>
                  {q.strengths.map((s, j) => (
                    <p key={j} className="text-slate-400 text-xs mb-1">• {s}</p>
                  ))}
                </div>
              )}
              {q.improvements?.length > 0 && (
                <div>
                  <p className="text-amber-400 text-xs font-medium mb-2">↑ Improve</p>
                  {q.improvements.map((imp, j) => (
                    <p key={j} className="text-slate-400 text-xs mb-1">• {imp}</p>
                  ))}
                </div>
              )}
            </div>
            
            {/* Top emotions */}
            {q.prosody?.top_emotions?.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {q.prosody.top_emotions.slice(0, 3).map((e, j) => (
                  <span key={j} className="text-xs bg-blue-500/10 text-blue-300 border border-blue-500/20 px-2 py-1 rounded-full">
                    {e.name} · {e.score.toFixed(1)}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </motion.div>
    </div>
  );
}
```

### Step 4: PDF Export

Install: `npm install @react-pdf/renderer`

Create `se-hack/lib/generatePDF.ts`:
```typescript
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';

export async function generateReportPDF(report: any): Promise<Uint8Array> {
  const pdfDoc = await PDFDocument.create();
  const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
  const boldFont = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
  
  const page = pdfDoc.addPage([595, 842]); // A4
  const { width, height } = page.getSize();
  
  // Header
  page.drawRectangle({ x: 0, y: height - 80, width, height: 80, color: rgb(0.047, 0.047, 0.059) });
  page.drawText('Evalvate Interview Report', { x: 40, y: height - 45, size: 20, font: boldFont, color: rgb(1, 1, 1) });
  page.drawText(`${report.role} · ${report.difficulty}`, { x: 40, y: height - 65, size: 12, font, color: rgb(0.6, 0.6, 0.7) });
  
  // Overall Score
  page.drawText(`Overall: ${report.overall_score}/10  Grade: ${report.grade}  Top ${100 - report.percentile}%`, {
    x: 40, y: height - 120, size: 14, font: boldFont, color: rgb(0.5, 0.2, 0.9)
  });
  
  // Component scores
  let y = height - 160;
  const components = report.component_scores || {};
  Object.entries(components).forEach(([key, val]: [string, any]) => {
    page.drawText(`${key.replace(/_/g, ' ').toUpperCase()}: ${val.toFixed(1)}/10`, {
      x: 40, y, size: 11, font
    });
    y -= 20;
  });
  
  // Questions
  y -= 20;
  page.drawText('Question Breakdown', { x: 40, y, size: 14, font: boldFont });
  y -= 25;
  
  report.questions?.forEach((q: any, i: number) => {
    if (y < 100) {
      // Add new page if needed
      return;
    }
    page.drawText(`Q${i + 1}: ${q.question_text?.substring(0, 80)}...`, { x: 40, y, size: 10, font: boldFont });
    y -= 16;
    page.drawText(`Technical: ${q.technical_score?.toFixed(1)} | Feedback: ${q.feedback?.substring(0, 80)}`, { x: 55, y, size: 9, font, color: rgb(0.6, 0.6, 0.7) });
    y -= 24;
  });
  
  return await pdfDoc.save();
}
```

Add PDF download endpoint to backend: `GET /api/results/{session_id}/pdf`

### Step 5: Shareable Report URL

In `backend/app/results/router.py`, add:
```python
@router.get("/share/{share_token}")
async def get_shared_report(share_token: str):
    """Public endpoint — no auth required. Returns report for sharing."""
    report = await results_service.get_report_by_share_token(share_token)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or expired")
    return report
```

In results service, when generating a report, create a `share_token = secrets.token_urlsafe(16)` and store it. The share URL becomes `evalvate.dev/report/share/{share_token}`.

---

## TASK 2 — HYBRID QUESTION BANK

### Step 1: MongoDB Schema

**Create MongoDB collection `question_bank`:**
```python
# backend/app/question_bank/models.py
from pydantic import BaseModel
from typing import List, Optional

class QuestionBankItem(BaseModel):
    question_text: str
    job_roles: List[str]          # ["Software Engineer", "Product Manager"]
    difficulty: List[str]         # ["junior", "mid", "senior"]
    category: str                 # "technical" | "behavioral" | "situational"
    expected_keywords: List[str]  # Keywords Gemini uses to evaluate quality
    follow_up: Optional[str] = None
    source: str = "custom"        # "custom" | "gemini" | "import"
    created_by: Optional[str] = None  # user_id of who created it
    is_active: bool = True
```

### Step 2: Question Selection Pipeline

**Create `backend/app/interviews/question_pipeline.py`:**
```python
import random
from typing import List
from app.question_bank.service import question_bank_service
from app.llm.llm import llm_client

class QuestionPipeline:
    
    async def generate_question_set(
        self, 
        role: str, 
        difficulty: str, 
        question_count: int,
        resume_context: str = "",
        previous_questions: List[str] = []
    ) -> List[dict]:
        """
        Hybrid question generation:
        - 40% from your curated bank
        - 40% Gemini-generated (role/difficulty specific)
        - 20% reserved for dynamic follow-ups during interview
        """
        bank_count = max(1, int(question_count * 0.4))
        gemini_count = question_count - bank_count  # Reserve 20% for follow-ups
        
        # Fetch from question bank
        bank_questions = await question_bank_service.get_questions(
            role=role, difficulty=difficulty, limit=bank_count,
            exclude_texts=previous_questions
        )
        
        # Generate remaining with Gemini
        gemini_questions = await self._generate_with_gemini(
            role=role, difficulty=difficulty, count=gemini_count,
            resume_context=resume_context,
            exclude_questions=[q["question_text"] for q in bank_questions] + previous_questions
        )
        
        # Merge and shuffle
        all_questions = bank_questions + gemini_questions
        random.shuffle(all_questions)
        
        return all_questions[:question_count]
    
    async def generate_followup(self, question: dict, answer_transcript: str, score: float) -> dict:
        """
        Generate a dynamic follow-up based on the actual answer.
        Called during interview when score < 6 or contradiction detected.
        """
        if score < 5:
            # Probe deeper on weak answer
            prompt = f"""
The candidate gave a weak answer (score {score}/10) to: "{question['question_text']}"
Their answer: "{answer_transcript}"

Generate ONE follow-up question that:
1. Probes the specific weakness in their answer
2. Gives them a chance to elaborate or correct
3. Is direct but not harsh
Return only the question text, nothing else.
"""
        else:
            # Escalate difficulty
            prompt = f"""
The candidate gave a good answer to: "{question['question_text']}"
Generate ONE harder follow-up that escalates the technical/situational depth.
Return only the question text.
"""
        response = await llm_client.ainvoke(prompt)
        return {
            "question_text": response.content.strip(),
            "source": "dynamic_followup",
            "parent_question": question["question_text"],
        }

question_pipeline = QuestionPipeline()
```

### Step 3: Admin API to Add Your Own Questions

**Create `backend/app/question_bank/router.py`:**
```python
@router.post("/questions", dependencies=[Depends(get_authenticated_user_id)])
async def add_question(question: QuestionBankItem, user_id: str = Depends(get_authenticated_user_id)):
    """Add a question to the bank"""
    question.created_by = user_id
    result = await db.question_bank.insert_one(question.dict())
    return {"id": str(result.inserted_id), "message": "Question added"}

@router.get("/questions")
async def list_questions(role: str = None, difficulty: str = None):
    """List questions (for admin preview)"""
    filter = {"is_active": True}
    if role: filter["job_roles"] = role
    if difficulty: filter["difficulty"] = difficulty
    questions = await db.question_bank.find(filter).to_list(100)
    return questions
```

Add a simple **Question Bank Manager page** in the frontend at `/dashboard/question-bank`:
- Table showing all questions with role/difficulty tags
- "Add Question" button → modal with form
- CSV import button (parse CSV, bulk insert)

---

## TASK 3 — PRODUCTION POLISH

### A: Error Monitoring (Sentry)

```bash
# Frontend
npm install @sentry/nextjs

# Backend  
pip install sentry-sdk[fastapi] --break-system-packages
```

Frontend `se-hack/sentry.client.config.ts`:
```typescript
import * as Sentry from "@sentry/nextjs";
Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  enabled: process.env.NODE_ENV === 'production',
});
```

Backend `backend/app/main.py`:
```python
import sentry_sdk
sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
```

### B: Analytics (PostHog — free, open source)

```bash
npm install posthog-js
```

Track these specific events:
```typescript
// In interview flow:
posthog.capture('interview_started', { role, difficulty, question_count });
posthog.capture('question_answered', { question_index, score, has_prosody });
posthog.capture('interview_completed', { overall_score, duration_seconds });
posthog.capture('report_viewed');
posthog.capture('report_downloaded');
posthog.capture('report_shared');
```

These 6 events give you everything an investor needs: funnel, completion rate, engagement.

### C: Demo Mode (No Login Required)

Create `se-hack/app/demo/page.tsx` — a full interview experience that:
1. Uses a demo user account (pre-created in MongoDB)
2. Has 3 questions hardcoded to a known good demo: "Software Engineer, Mid Level"
3. Shows the full AI interviewer + voice + facial tracking
4. Redirects to a pre-generated sample report at the end

This is what you show investors without them needing to sign up.

```
Route: /demo
No auth required
Shows: "This is a live demo session — your data won't be saved"
Questions: ["Tell me about yourself", "Describe a technical challenge you solved", "Why are you a good fit for this role?"]
Post-interview: Shows real Gemini evaluation of their actual answers
```

### D: Clean Up lib/api.ts

This file is full of mock data. It's safe to gut it now that the real API is wired.
Replace its contents with:
```typescript
// se-hack/lib/api.ts
// THIS FILE IS DEPRECATED — use se-hack/lib/interviewAgentApi.ts for all interview calls
export {};
```

Or delete it and fix the one remaining import in voice-analysis (which is already on Coming Soon).

---

## VERIFICATION CHECKLIST FOR PART 3

```
[ ] Overall score is a weighted average (technical 35%, communication 25%, eye 15%, emotion 15%, structure 10%)
[ ] Component scores all show real values (not 5.0 defaults unless data is genuinely missing)
[ ] Report shows: radar chart, line chart per question, gaze distribution bar chart
[ ] PDF download works and generates a real A4 document
[ ] Share URL works — shareable without login
[ ] Question bank collection exists in MongoDB
[ ] Can add custom questions via dashboard
[ ] Interview uses hybrid questions (bank + Gemini mixed)
[ ] Follow-up questions are generated based on actual answer score
[ ] Sentry initialized (errors show in Sentry dashboard on first runtime error)
[ ] PostHog tracking fires for interview_started and interview_completed
[ ] /demo route works without any login
[ ] /demo shows a real interview with Gemini-evaluated answers
[ ] lib/api.ts no longer powers any real page
[ ] npm run build passes clean with zero errors
[ ] No console.log in production paths (run: grep -rn "console.log" se-hack/app se-hack/lib se-hack/hooks)
```

---

## FINAL OVERALL VERIFICATION (All 3 Parts)

After all 3 parts are complete:

```bash
# 1. Clean build
cd se-hack && npm run build && echo "BUILD PASSED ✅"

# 2. No hardcoded URLs
grep -rn "localhost:8000\|127.0.0.1" se-hack/app se-hack/lib se-hack/hooks se-hack/components 2>/dev/null | grep -v ".next" && echo "FOUND URLs ❌" || echo "NO HARDCODED URLs ✅"

# 3. No Math.random() for scores  
grep -rn "Math.random()" se-hack/app se-hack/lib backend/app 2>/dev/null | grep -v "node_modules" && echo "FOUND RANDOM ❌" || echo "NO FAKE RANDOM ✅"

# 4. No mock data
grep -rn "mock-jwt-token\|overallScore: 86\|MOCK-1234" se-hack/ backend/ 2>/dev/null && echo "FOUND MOCK ❌" || echo "NO MOCK DATA ✅"

# 5. Backend starts
cd backend && uvicorn app.main:app --port 8000 && echo "BACKEND OK ✅"
```

**TARGET OUTCOME: 9.5/10 Demo Readiness. 8/10 Investor Readiness.**
The remaining 0.5 and 2.0 come from real user sessions (traction) — which is something you earn, not build.
