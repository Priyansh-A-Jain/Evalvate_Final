# 🎭 CURSOR BUILD PROMPT — PART 2 OF 3
## AI Human Avatar + Real Voice Prosody + Real Facial Analysis
### Paste this entire prompt into Cursor Composer (Cmd+I) — ONLY after Part 1 is complete and verified

---

## CONTEXT

You are working on **Evalvate**. Part 1 is complete. Now we add the three core technical upgrades that make this product genuinely impressive and defensible:

1. **Real AI Human Interviewer** (Simli.ai — real-time lip-synced avatar)
2. **Real Vocal Prosody Analysis** (Hume AI — measures confidence, nervousness, pace, energy)
3. **Real Facial + Eye Contact Analysis** (proper iris-based gaze math, multi-person detection)

Every implementation here must be REAL. No Math.random(), no setTimeout fakes, no static returns.

---

## TASK 1 — AI HUMAN INTERVIEWER AVATAR (Simli.ai)

### Background
The current interviewer UI shows text or a static image. We replace it with a real-time AI human face that lip-syncs to the Deepgram TTS audio.

Simli works like this:
1. Your backend generates audio (Deepgram TTS → audio buffer)
2. You send that audio to Simli via their SDK
3. Simli streams back a video of a realistic human face speaking

### Step 1: Install Simli SDK
In `se-hack/`:
```bash
npm install @simli/react-simli
```

### Step 2: Create Simli Interviewer Component

**Create `se-hack/components/interview/SimliInterviewer.tsx`:**
```tsx
'use client';
import { SimliClient } from '@simli/react-simli';
import { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';
import { config } from '@/lib/config';

export interface SimliInterviewerHandle {
  speakAudio: (audioData: ArrayBuffer) => void;
  stopSpeaking: () => void;
}

interface SimliInterviewerProps {
  isActive: boolean;
  isSpeaking: boolean;
  interviewerName?: string;
  interviewerTitle?: string;
  onReady?: () => void;
  onSpeakingEnd?: () => void;
}

export const SimliInterviewer = forwardRef<SimliInterviewerHandle, SimliInterviewerProps>(
  ({ isActive, isSpeaking, interviewerName = 'Alex Chen', interviewerTitle = 'Senior Engineer, Evalvate', onReady, onSpeakingEnd }, ref) => {
    const simliClientRef = useRef<SimliClient | null>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    const audioRef = useRef<HTMLAudioElement>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [connectionError, setConnectionError] = useState<string | null>(null);

    useImperativeHandle(ref, () => ({
      speakAudio: (audioData: ArrayBuffer) => {
        if (simliClientRef.current && isConnected) {
          const audioArray = new Int16Array(audioData);
          simliClientRef.current.sendAudioData(audioArray);
        }
      },
      stopSpeaking: () => {
        // Simli auto-handles lip sync end
      },
    }));

    useEffect(() => {
      if (!isActive || !process.env.NEXT_PUBLIC_SIMLI_API_KEY) return;

      const simliClient = new SimliClient();
      simliClientRef.current = simliClient;

      simliClient.Initialize({
        apiKey: process.env.NEXT_PUBLIC_SIMLI_API_KEY,
        faceID: 'tmp9i8bbq',  // Default: professional male face. Browse at simli.ai/faces
        handleSilence: true,
        videoRef: videoRef,
        audioRef: audioRef,
      });

      simliClient.on('connected', () => {
        setIsConnected(true);
        setConnectionError(null);
        onReady?.();
      });

      simliClient.on('disconnected', () => {
        setIsConnected(false);
      });

      simliClient.on('failed', (error: Error) => {
        setConnectionError(error.message);
        console.error('Simli connection failed:', error);
      });

      simliClient.start();

      return () => {
        simliClient.close();
      };
    }, [isActive]);

    return (
      <div className="relative">
        {/* Avatar Container */}
        <div className="relative w-full aspect-[3/4] max-w-[280px] mx-auto rounded-2xl overflow-hidden bg-gradient-to-b from-slate-800 to-slate-900">
          
          {/* Video feed from Simli */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className={`w-full h-full object-cover transition-opacity duration-500 ${isConnected ? 'opacity-100' : 'opacity-0'}`}
          />
          <audio ref={audioRef} autoPlay />
          
          {/* Loading state */}
          {!isConnected && !connectionError && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
              <div className="w-16 h-16 rounded-full bg-slate-700 animate-pulse" />
              <div className="w-24 h-3 bg-slate-700 rounded animate-pulse" />
              <p className="text-slate-400 text-xs mt-2">Connecting interviewer...</p>
            </div>
          )}

          {/* Error fallback — show professional static avatar */}
          {connectionError && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-gradient-to-b from-slate-700 to-slate-800">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center text-3xl font-bold text-white">
                {interviewerName.charAt(0)}
              </div>
              <div className="text-center">
                <p className="text-white text-sm font-medium">{interviewerName}</p>
                <p className="text-slate-400 text-xs">{interviewerTitle}</p>
              </div>
            </div>
          )}

          {/* Speaking indicator */}
          {isConnected && isSpeaking && (
            <div className="absolute bottom-3 left-3 flex items-center gap-2 bg-black/60 backdrop-blur rounded-full px-3 py-1.5">
              <div className="flex gap-0.5 items-center h-4">
                {[0, 1, 2].map(i => (
                  <div
                    key={i}
                    className="w-1 bg-violet-400 rounded-full animate-[soundwave_0.8s_ease-in-out_infinite]"
                    style={{
                      height: '60%',
                      animationDelay: `${i * 0.15}s`,
                    }}
                  />
                ))}
              </div>
              <span className="text-white text-xs">Speaking</span>
            </div>
          )}

          {/* Thinking indicator */}
          {isConnected && !isSpeaking && isActive && (
            <div className="absolute bottom-3 left-3 flex items-center gap-2 bg-black/40 backdrop-blur rounded-full px-3 py-1.5">
              <div className="flex gap-1 items-center">
                {[0, 1, 2].map(i => (
                  <div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
              <span className="text-slate-300 text-xs">Listening</span>
            </div>
          )}

          {/* Connection quality indicator */}
          {isConnected && (
            <div className="absolute top-3 right-3 w-2 h-2 rounded-full bg-emerald-400" />
          )}
        </div>

        {/* Interviewer info */}
        <div className="text-center mt-4">
          <p className="text-white font-medium text-sm">{interviewerName}</p>
          <p className="text-slate-400 text-xs mt-0.5">{interviewerTitle}</p>
        </div>
      </div>
    );
  }
);
SimliInterviewer.displayName = 'SimliInterviewer';
```

### Step 3: Wire Simli to the Interview Flow

In `se-hack/app/interview/page.tsx`, find where TTS audio is played.
Currently it plays Deepgram TTS through an `<audio>` element.

Replace that logic:
```tsx
// OLD (remove this):
const audioEl = new Audio(URL.createObjectURL(audioBlob));
audioEl.play();

// NEW — send audio to Simli instead:
const arrayBuffer = await audioBlob.arrayBuffer();
simliRef.current?.speakAudio(arrayBuffer);
```

Import and add `<SimliInterviewer>` to the interview layout where the interviewer currently appears.

---

## TASK 2 — REAL VOCAL PROSODY ANALYSIS (Hume AI)

### Background
After each answer, we send the audio recording of that answer to Hume AI.
Hume returns: pitch analysis, speaking rate (WPM), volume dynamics, and 48 emotional dimensions including confidence, hesitation, excitement, nervousness.

This is **not rule-based**. Hume has trained a 300M parameter model on prosodic features.

### Step 1: Install Hume Python SDK in backend
```bash
pip install hume --break-system-packages
# Add to backend/requirements.txt:
# hume>=0.7.0
```

### Step 2: Create Vocal Analysis Service

**Create `backend/app/voice_analysis/prosody_analyzer.py`:**
```python
import asyncio
import base64
import io
import json
from typing import Optional
import httpx
from app.core.config import settings

class ProsodyAnalyzer:
    """
    Analyzes vocal prosody using Hume AI Expression Measurement API.
    Returns real ML-based scores for speaking confidence, pace, emotion.
    """
    
    HUME_API_URL = "https://api.hume.ai/v0/batch/jobs"
    HUME_PREDICTIONS_URL = "https://api.hume.ai/v0/batch/jobs/{job_id}/predictions"
    
    def __init__(self):
        self.api_key = settings.HUME_API_KEY
    
    async def analyze_answer_audio(
        self, 
        audio_bytes: bytes,
        audio_format: str = "webm",
        question_text: str = "",
        answer_transcript: str = ""
    ) -> dict:
        """
        Send audio to Hume and return prosody scores.
        Falls back to transcript-based estimation if Hume fails.
        """
        if not self.api_key:
            return self._transcript_fallback(answer_transcript)
        
        try:
            # Submit job to Hume
            job_id = await self._submit_job(audio_bytes, audio_format)
            if not job_id:
                return self._transcript_fallback(answer_transcript)
            
            # Poll for results (Hume is async)
            predictions = await self._poll_predictions(job_id, max_wait=30)
            if not predictions:
                return self._transcript_fallback(answer_transcript)
            
            return self._parse_predictions(predictions, answer_transcript)
            
        except Exception as e:
            print(f"Hume analysis failed: {e}")
            return self._transcript_fallback(answer_transcript)
    
    async def _submit_job(self, audio_bytes: bytes, audio_format: str) -> Optional[str]:
        audio_b64 = base64.b64encode(audio_bytes).decode()
        
        payload = {
            "models": {
                "prosody": {
                    "granularity": "utterance",
                    "identify_speakers": False
                }
            },
            "raw_text": [],
            "urls": [],
            "files": [
                {
                    "filename": f"answer.{audio_format}",
                    "content": audio_b64,
                    "content_type": f"audio/{audio_format}"
                }
            ]
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.HUME_API_URL,
                json=payload,
                headers={"X-Hume-Api-Key": self.api_key},
                timeout=15.0
            )
            if resp.status_code != 200:
                return None
            return resp.json().get("job_id")
    
    async def _poll_predictions(self, job_id: str, max_wait: int = 30) -> Optional[list]:
        url = self.HUME_PREDICTIONS_URL.format(job_id=job_id)
        headers = {"X-Hume-Api-Key": self.api_key}
        
        async with httpx.AsyncClient() as client:
            for _ in range(max_wait):
                await asyncio.sleep(1)
                resp = await client.get(url, headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    if data and len(data) > 0:
                        return data
        return None
    
    def _parse_predictions(self, predictions: list, transcript: str) -> dict:
        """Extract meaningful interview-relevant scores from Hume predictions"""
        try:
            # Navigate Hume response structure
            prosody_data = predictions[0]["results"]["predictions"][0]["models"]["prosody"]
            grouped = prosody_data.get("grouped_predictions", [])
            
            if not grouped:
                return self._transcript_fallback(transcript)
            
            # Aggregate emotion scores across all utterances
            emotion_totals = {}
            utterance_count = 0
            total_duration = 0.0
            
            for group in grouped:
                for pred in group.get("predictions", []):
                    utterance_count += 1
                    duration = pred.get("time", {}).get("end", 0) - pred.get("time", {}).get("begin", 0)
                    total_duration += duration
                    
                    for emotion in pred.get("emotions", []):
                        name = emotion["name"]
                        score = emotion["score"]
                        emotion_totals[name] = emotion_totals.get(name, 0) + score
            
            if utterance_count == 0:
                return self._transcript_fallback(transcript)
            
            # Average emotion scores
            avg_emotions = {k: v / utterance_count for k, v in emotion_totals.items()}
            
            # Calculate interview-specific composite scores
            confidence_score = self._calc_confidence(avg_emotions)
            nervousness_score = self._calc_nervousness(avg_emotions)
            engagement_score = self._calc_engagement(avg_emotions)
            clarity_score = self._calc_clarity_from_transcript(transcript)
            pace_score = self._calc_pace(transcript, total_duration)
            
            # Tone classification
            tone = self._classify_tone(avg_emotions)
            
            # Top emotions for the report
            top_emotions = sorted(avg_emotions.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "confidence_score": round(confidence_score * 10, 2),   # 0-10
                "nervousness_score": round(nervousness_score * 10, 2), # 0-10
                "engagement_score": round(engagement_score * 10, 2),   # 0-10
                "clarity_score": round(clarity_score * 10, 2),         # 0-10
                "pace_score": round(pace_score * 10, 2),               # 0-10 (10 = ideal pace)
                "tone_classification": tone,                            # "confident", "nervous", "monotone", "engaged", "aggressive"
                "top_emotions": [{"name": e[0], "score": round(e[1] * 10, 2)} for e in top_emotions],
                "speaking_duration_seconds": round(total_duration, 1),
                "utterance_count": utterance_count,
                "source": "hume_ai",
            }
            
        except (KeyError, IndexError, TypeError) as e:
            print(f"Prediction parsing error: {e}")
            return self._transcript_fallback(transcript)
    
    def _calc_confidence(self, emotions: dict) -> float:
        """Higher confidence = more Determination + Pride + less Anxiety"""
        positive = (
            emotions.get("Determination", 0) * 1.5 +
            emotions.get("Interest", 0) * 1.2 +
            emotions.get("Concentration", 0) * 1.0 +
            emotions.get("Calmness", 0) * 0.8 +
            emotions.get("Satisfaction", 0) * 0.7
        ) / 5.2
        negative = (
            emotions.get("Anxiety", 0) * 1.5 +
            emotions.get("Fear", 0) * 1.2 +
            emotions.get("Doubt", 0) * 1.0
        ) / 3.7
        return max(0.0, min(1.0, positive - (negative * 0.5)))
    
    def _calc_nervousness(self, emotions: dict) -> float:
        """Nervousness = Anxiety + Fear + Distress"""
        return min(1.0, (
            emotions.get("Anxiety", 0) * 1.5 +
            emotions.get("Fear", 0) * 1.2 +
            emotions.get("Distress", 0) * 1.0 +
            emotions.get("Nervousness", 0) * 1.3
        ) / 4.0)
    
    def _calc_engagement(self, emotions: dict) -> float:
        """Engagement = Interest + Excitement + Enthusiasm"""
        return min(1.0, (
            emotions.get("Interest", 0) * 1.5 +
            emotions.get("Excitement", 0) * 1.2 +
            emotions.get("Enthusiasm", 0) * 1.3 +
            emotions.get("Determination", 0) * 0.8
        ) / 4.8)
    
    def _calc_clarity_from_transcript(self, transcript: str) -> float:
        """Penalize filler words and short answers"""
        if not transcript or len(transcript.split()) < 5:
            return 0.3
        
        words = transcript.lower().split()
        total = len(words)
        fillers = sum(1 for w in words if w in {
            "um", "uh", "like", "you know", "basically", "literally", 
            "actually", "so", "right", "yeah", "okay"
        })
        filler_ratio = fillers / max(total, 1)
        
        # Penalize: every 10% filler ratio = -0.15 score
        base = 0.85
        penalty = filler_ratio * 1.5
        return max(0.2, min(1.0, base - penalty))
    
    def _calc_pace(self, transcript: str, duration_seconds: float) -> float:
        """
        Ideal interview pace: 120-160 WPM
        Returns 1.0 at 140 WPM, decreasing toward 0 as pace deviates
        """
        if not transcript or duration_seconds < 1:
            return 0.5
        
        word_count = len(transcript.split())
        wpm = (word_count / duration_seconds) * 60
        
        # Gaussian centered at 140 WPM
        import math
        ideal_wpm = 140
        std_dev = 40
        score = math.exp(-((wpm - ideal_wpm) ** 2) / (2 * std_dev ** 2))
        return max(0.1, min(1.0, score))
    
    def _classify_tone(self, emotions: dict) -> str:
        """Classify overall vocal tone for human-readable report"""
        confidence = self._calc_confidence(emotions)
        nervousness = self._calc_nervousness(emotions)
        engagement = self._calc_engagement(emotions)
        excitement = emotions.get("Excitement", 0)
        
        if confidence > 0.65 and engagement > 0.5:
            return "confident"
        elif nervousness > 0.5:
            return "nervous"
        elif excitement < 0.15 and confidence < 0.4:
            return "monotone"
        elif engagement > 0.6:
            return "engaged"
        elif confidence > 0.5:
            return "composed"
        else:
            return "uncertain"
    
    def _transcript_fallback(self, transcript: str) -> dict:
        """Basic estimation when Hume is unavailable — clearly labeled as estimated"""
        clarity = self._calc_clarity_from_transcript(transcript)
        word_count = len(transcript.split()) if transcript else 0
        
        return {
            "confidence_score": 5.0,
            "nervousness_score": 5.0,
            "engagement_score": 5.0,
            "clarity_score": round(clarity * 10, 2),
            "pace_score": 5.0,
            "tone_classification": "unknown",
            "top_emotions": [],
            "speaking_duration_seconds": 0,
            "utterance_count": 0,
            "source": "transcript_estimation",  # CLEARLY labeled — never misrepresent
        }


prosody_analyzer = ProsodyAnalyzer()
```

### Step 3: Add Prosody Analysis to Interview Flow

In `backend/app/interviews/service.py`, find where answers are evaluated (after STT + Gemini eval).
Add prosody analysis in parallel:

```python
from app.voice_analysis.prosody_analyzer import prosody_analyzer

async def evaluate_answer(self, session_id: str, question_index: int, 
                           audio_bytes: bytes, transcript: str, question_text: str) -> dict:
    # Run Gemini eval + Hume prosody in PARALLEL for speed
    gemini_eval_task = asyncio.create_task(
        self._gemini_evaluate_answer(question_text, transcript)
    )
    prosody_task = asyncio.create_task(
        prosody_analyzer.analyze_answer_audio(
            audio_bytes=audio_bytes,
            audio_format="webm",
            question_text=question_text,
            answer_transcript=transcript
        )
    )
    
    gemini_result, prosody_result = await asyncio.gather(gemini_eval_task, prosody_task)
    
    # Merge into answer evaluation
    return {
        **gemini_result,
        "prosody": prosody_result,
        "transcript": transcript,
    }
```

---

## TASK 3 — REAL FACIAL + EYE CONTACT ANALYSIS

### Step 1: Replace bucketed scores with real iris math

In `backend/app/video_analysis/gaze_analyzer.py`, find the function that calculates eye contact scores.
Replace any bucketed/static logic with this real implementation:

```python
import numpy as np
from typing import Optional

# MediaPipe Face Landmarker iris landmark indices
LEFT_IRIS_INDICES = [468, 469, 470, 471, 472]
RIGHT_IRIS_INDICES = [473, 474, 475, 476, 477]
LEFT_EYE_OUTER = 33
LEFT_EYE_INNER = 133
RIGHT_EYE_INNER = 362
RIGHT_EYE_OUTER = 263
LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145
RIGHT_EYE_TOP = 386
RIGHT_EYE_BOTTOM = 374

def calculate_real_gaze_score(face_landmarks) -> dict:
    """
    Calculates where a person is looking using iris landmark positions.
    Returns:
    - gaze_score: 0.0-1.0 (1.0 = looking directly at camera)
    - eye_contact: bool (True if gaze_score > 0.65)
    - gaze_direction: "center" | "left" | "right" | "up" | "down" | "away"
    - blink_detected: bool
    """
    if not face_landmarks or len(face_landmarks) < 478:
        return {"gaze_score": 0.0, "eye_contact": False, "gaze_direction": "unknown", "blink_detected": False}
    
    lm = face_landmarks  # shorthand
    
    # ─── Blink Detection ───────────────────────────────────
    left_eye_openness = abs(lm[LEFT_EYE_TOP].y - lm[LEFT_EYE_BOTTOM].y)
    right_eye_openness = abs(lm[RIGHT_EYE_TOP].y - lm[RIGHT_EYE_BOTTOM].y)
    avg_openness = (left_eye_openness + right_eye_openness) / 2
    blink_detected = avg_openness < 0.01  # Threshold from empirical calibration
    
    if blink_detected:
        return {"gaze_score": 0.0, "eye_contact": False, "gaze_direction": "blink", "blink_detected": True}
    
    # ─── Iris Center Calculation ───────────────────────────
    left_iris_x = np.mean([lm[i].x for i in LEFT_IRIS_INDICES])
    left_iris_y = np.mean([lm[i].y for i in LEFT_IRIS_INDICES])
    right_iris_x = np.mean([lm[i].x for i in RIGHT_IRIS_INDICES])
    right_iris_y = np.mean([lm[i].y for i in RIGHT_IRIS_INDICES])
    
    # ─── Normalized Iris Position in Eye Socket ───────────
    # Horizontal: 0 = far left in eye, 0.5 = center, 1 = far right
    left_eye_width = abs(lm[LEFT_EYE_INNER].x - lm[LEFT_EYE_OUTER].x)
    right_eye_width = abs(lm[RIGHT_EYE_OUTER].x - lm[RIGHT_EYE_INNER].x)
    
    if left_eye_width < 1e-6 or right_eye_width < 1e-6:
        return {"gaze_score": 0.5, "eye_contact": False, "gaze_direction": "unknown", "blink_detected": False}
    
    left_h_ratio = (left_iris_x - lm[LEFT_EYE_OUTER].x) / left_eye_width
    right_h_ratio = (right_iris_x - lm[RIGHT_EYE_INNER].x) / right_eye_width
    avg_h_ratio = (left_h_ratio + right_h_ratio) / 2  # 0.5 = looking at camera
    
    # Vertical
    left_eye_height = abs(lm[LEFT_EYE_TOP].y - lm[LEFT_EYE_BOTTOM].y)
    right_eye_height = abs(lm[RIGHT_EYE_TOP].y - lm[RIGHT_EYE_BOTTOM].y)
    
    left_v_ratio = (left_iris_y - lm[LEFT_EYE_TOP].y) / max(left_eye_height, 1e-6)
    right_v_ratio = (right_iris_y - lm[RIGHT_EYE_TOP].y) / max(right_eye_height, 1e-6)
    avg_v_ratio = (left_v_ratio + right_v_ratio) / 2
    
    # ─── Gaze Score Calculation ────────────────────────────
    # Horizontal deviation from center (0.5)
    h_deviation = abs(avg_h_ratio - 0.5)
    v_deviation = abs(avg_v_ratio - 0.5)
    
    # Weighted: horizontal deviation penalized more than vertical
    combined_deviation = (h_deviation * 1.5 + v_deviation * 0.8) / 2.3
    gaze_score = max(0.0, min(1.0, 1.0 - (combined_deviation * 2.5)))
    
    # ─── Direction Classification ──────────────────────────
    if h_deviation < 0.08 and v_deviation < 0.08:
        direction = "center"
    elif avg_h_ratio < 0.35:
        direction = "right"  # mirrored: iris left in frame = looking right
    elif avg_h_ratio > 0.65:
        direction = "left"
    elif avg_v_ratio < 0.35:
        direction = "up"
    elif avg_v_ratio > 0.65:
        direction = "down"
    else:
        direction = "away"
    
    return {
        "gaze_score": round(gaze_score, 4),
        "eye_contact": gaze_score > 0.60,
        "gaze_direction": direction,
        "blink_detected": False,
        "h_ratio": round(avg_h_ratio, 4),
        "v_ratio": round(avg_v_ratio, 4),
    }
```

### Step 2: Multi-Person Detection — Flag Background Intruder

In `backend/app/video_analysis/` find where face detection runs on each frame.
Add this function and call it alongside gaze analysis:

```python
class MultiPersonDetector:
    def __init__(self):
        self.flag_threshold = 0.05  # Flag if >5% of frames have 2+ people
        self.multi_person_frames = 0
        self.total_frames = 0
    
    def analyze_frame(self, detection_result) -> dict:
        """Check if multiple faces are in the frame"""
        self.total_frames += 1
        face_count = len(detection_result.detections) if detection_result.detections else 0
        
        is_multiple = face_count > 1
        if is_multiple:
            self.multi_person_frames += 1
        
        return {
            "face_count": face_count,
            "multiple_persons_detected": is_multiple,
            "background_intrusion_ratio": self.multi_person_frames / max(self.total_frames, 1)
        }
    
    def get_session_flag(self) -> dict:
        """Get end-of-session integrity flag"""
        ratio = self.multi_person_frames / max(self.total_frames, 1)
        return {
            "integrity_violation": ratio > self.flag_threshold,
            "multiple_person_frames": self.multi_person_frames,
            "total_frames": self.total_frames,
            "intrusion_percentage": round(ratio * 100, 1),
            "severity": "high" if ratio > 0.20 else "medium" if ratio > 0.05 else "none"
        }
```

### Step 3: Update Session Analysis Storage

In `backend/app/interviews/models.py` (or wherever session analysis is stored in MongoDB), ensure these fields exist in the interview document:

```python
# Per-frame tracking (stored as running averages, not every frame)
"gaze_data": {
    "eye_contact_score": float,        # 0-10, real iris math
    "gaze_distribution": {             # % of time looking in each direction
        "center": float,
        "left": float,
        "right": float, 
        "up": float,
        "down": float,
        "away": float,
    },
    "eye_contact_percentage": float,   # % of frames with gaze_score > 0.60
    "blink_rate_per_minute": float,    # normal: 15-20/min; high = stress signal
},
"integrity_check": {
    "integrity_violation": bool,
    "multiple_person_frames": int,
    "intrusion_percentage": float,
    "severity": str,  # "none" | "medium" | "high"
},
"prosody_data": {                      # Aggregated from per-question Hume results
    "avg_confidence_score": float,
    "avg_nervousness_score": float,
    "avg_engagement_score": float,
    "avg_clarity_score": float,
    "avg_pace_score": float,
    "dominant_tone": str,
    "per_question_prosody": list,      # One entry per question
}
```

### Step 4: Remove the bucketed score fallback in interview/page.tsx

In `se-hack/app/interview/page.tsx` around lines 379-380, find:
```
// Something like: gaze: 85, posture: 40   OR   gaze: 90, posture: 50
```

Replace with: always use the actual `engagement_score` or `gaze_score` returned from the backend's session analysis endpoint. If the backend returns null/undefined, show a loading spinner or "--" — **never show a hardcoded fallback number**.

---

## TASK 4 — Add Filler Word Detection to Deepgram

In `backend/app/voice/` wherever Deepgram STT options are configured, add:

```python
# Deepgram transcription options
transcription_options = {
    "model": "nova-2",
    "language": "en-US",
    "smart_format": True,
    "filler_words": True,       # Detects "um", "uh", "like" etc. — NEW
    "utterances": True,
    "punctuate": True,
    "diarize": False,
}
```

Then in transcript processing, extract filler words and include in per-question prosody:
```python
filler_count = sum(1 for w in result.words if w.get("type") == "filler")
filler_ratio = filler_count / max(len(result.words), 1)
```

---

## VERIFICATION CHECKLIST FOR PART 2

```
[ ] SimliInterviewer component renders — at minimum shows fallback avatar if no Simli key
[ ] TTS audio is routed to Simli instead of direct <audio> element
[ ] Simli video shows a human face speaking when TTS plays (if SIMLI_API_KEY set)
[ ] Hume analysis runs after each answer is submitted (check backend logs for "Hume job_id:")
[ ] Hume prosody scores appear in per-question response from backend
[ ] Source field in prosody is "hume_ai" not "transcript_estimation" when Hume key is set
[ ] Eye contact score in session analysis is a float between 0-10 (NOT 85 or 90)
[ ] Gaze direction is one of: center, left, right, up, down, away (not hardcoded)
[ ] Multiple faces in frame → background_intrusion_ratio increases in real-time
[ ] interview/page.tsx has ZERO hardcoded numbers for gaze/posture
[ ] Deepgram filler_words flag is set in transcription options
[ ] Prosody analysis runs in parallel with Gemini evaluation (not sequential)
```
