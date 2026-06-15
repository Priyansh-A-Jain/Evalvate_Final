# Evalvate

Evalvate is an AI-native interview preparation and talent intelligence platform that simulates high-pressure hiring environments and provides candidates with deep, actionable feedback across content quality, communication style, confidence signals, and behavioral consistency.

Evalvate is incubated by the **London School of Economics (LSE) Generate** program, which supports high-impact startups building next-generation technology. The project also won the **SE Hackathon** 

This repository contains the full product stack:
- `backend/`: FastAPI + MongoDB + AI services (Hume AI, Simli, DeepFace) + real-time media analysis
- `se-hack/`: Next.js frontend (App Router) for interview flows, analytics, and coaching UX

It is not just a question-answer chatbot. Evalvate combines:
- **Adaptive Interview Intelligence**: Tailored role/difficulty questions with dynamic challenges.
- **Multimodal Behavioral Analysis**: Fusion of video (iris tracking, face/gaze/pose), voice (vocal emotion/prosody), and text.
- **Resume Understanding & ATS Coaching**: Deep resume analysis and actionable enhancement tips.
- **Longitudinal Trend Analytics**: Cross-session progress, weakness clustering, and targeted coaching plans.

---

## The Problem Evalvate Solves
Most interview preparation tools test only one dimension: whether your verbal answer sounds correct. Real-world interviews evaluate much more:
- **Under-Pressure Thinking**: How clearly you structure answers when challenged.
- **Communication Consistency**: Whether your claims remain internally consistent across time.
- **Non-Verbal Signals**: How your posture, gaze, and vocal emotions reflect confidence and engagement.
- **Adaptability**: How effectively you recover when interviewer personas push back.

Evalvate is built from the ground up to analyze and coach candidates on this broader, multi-dimensional reality.

---

## Key Capabilities

### 1. Adaptive 1-on-1 Interview Engine
The 1-on-1 interview flow is designed as an adaptive, graph-driven system:
- **Customizable Sessions**: Candidates select target roles, difficulty levels, and interviewer personas (e.g., mentor, friendly, aggressive, or "devil's advocate").
- **Dynamic Challenges**: If uncertainty is detected or scores decline, the engine generates challenge follow-ups.
- **Context Integration**: Injecting candidate resume context and recent turn summaries directly into evaluation/generation prompts.

### 2. Contradiction & Consistency Detection
Evalvate includes semantic contradiction analysis across past and current candidate statements:
- Compares new responses against prior claims (e.g., skills, experience, preferences).
- Detects logical inconsistencies and returns structured contradiction details including confidence and severity.
- Focuses coaching on alignment and consistency, not just correctness scoring.

### 3. Real-Time Voice Intelligence (Hume AI)
The voice pipeline supports live vocal feature analysis and transcripts:
- WebSocket-based real-time audio streaming.
- **Prosody & Tone Analysis**: Powered by Hume AI to measure pitch variation, speaking pace (WPM), volume dynamics, filler word density ("um", "uh", "like"), and 48 vocal emotions (confidence, hesitation, nervousness).
- Automatic word-level events and periodic acoustic/semantic insight payloads.

### 4. Real-Time Video & Behavioral Intelligence (MediaPipe + DeepFace)
The video analysis module fuses multiple visual signals:
- **Iris Landmark tracking**: Real gaze estimation math relative to eye sockets for eye contact tracking.
- **Posture & Gestures**: Shoulder alignment and nervous gesture proxies (face-touching/fidget patterns).
- **Emotion Distribution**: Dominant emotion tracking (confidence vs. nervousness ratio) using DeepFace.
- **Multi-face Detection**: Background person flagging to verify environment integrity.

### 5. Group Interview Simulation
Simulates rotating panel interview formats:
- Multi-interviewer flows (Technical, HR, Mixed).
- Turn progression and context carry-over.
- Per-turn evaluations and a synthesized final summary of overall scores and unique insights.

### 6. Team-Fit Meeting Room Simulation
Simulates real-world collaboration and meeting dynamics:
- Scenario-based team discussions with multiple participant roles.
- Interruption tracking and message timeline capture.
- Collaboration-focused reports indicating team fit, leadership, and listening metrics.

### 7. Resume Parsing & ATS Coaching
Deep resume integration:
- Ingests PDF/DOCX files (with size/type constraints).
- Parses documents using LLMs into structured JSON.
- Generates ATS-style analysis and actionable resume building tips.

### 8. Longitudinal Coaching Analytics
A dashboard tracking improvement over time:
- Cluster trendlines (sessions completed, average scores, improvement delta, contradiction rate).
- Core weakness and strength clustering.
- Focus radar charts and automatically generated weekly coaching action-plans.

---

## Technical Architecture

### System Flow
- **Frontend (`se-hack`)**: Next.js App Router handling state orchestration, media stream capture, live WebSocket connectivity, and visualization dashboards.
- **Backend (`backend`)**: FastAPI handling database persistence, Google OAuth + JWT cookie lifecycle, AI provider orchestration, scoring formulas, and MediaPipe/DeepFace media pipelines.
- **Database (`MongoDB`)**: Stores user profiles, resume structured text, interview sessions, meeting logs, and longitudinal snapshots.

### Subsystem Directory Structure
```text
Evalvate/
  backend/
    app/
      auth/             # Google OAuth, JWT cookies, user records
      interview_agent/  # LLM prompt graphs, question banks, adaptive paths
      interviews/       # 1-on-1 session records, contradiction checks
      meeting_room/     # Multi-agent scenarios, metrics, collaborative rooms
      group_interview/  # Rotating panel flow, HR/technical context handoffs
      resume_parser/    # File ingestion, LLM parsing, ATS analysis
      video_analysis/   # MediaPipe iris tracking, pose, DeepFace emotion
      voice/            # Audio buffers, Hume prosody websocket, STT engine
      results/          # Coaching reports, score aggregation, snapshots
      middlewares/      # CORS, JWT context injectors, connection configs
      main.py           # FastAPI entrypoint
      db.py             # MongoDB client connection
    requirements.txt    # Python dependencies
  se-hack/
    app/                # Next.js App Router (dashboard, interview, results, etc.)
    components/         # Reusable charts, UI elements, TalkingAvatar, widgets
    hooks/              # useVideoAnalysis, useVoiceWebSocket, capture hooks
    lib/                # Auth APIs, backend API adapters, analytics
    store/              # Zustand state management
    package.json        # NPM dependencies
  .gitignore            # Root-level ignores
  README.md             # This document
```

---

## Local Setup

### Prerequisites
- **Python 3.11**
- **Node.js 18+** & npm
- **MongoDB** instance
- API keys (OAuth + OpenRouter/LLM + Hume AI / Speech features)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# Activate virtual environment:
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Create a `backend/.env` file with the required environment variables:
```env
MONGO_URI=mongodb://localhost:27017/evalvate
OPENROUTER_API_KEY=your_openrouter_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SECRET_KEY=your_jwt_secret_key
```

Run the FastAPI backend server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup
```bash
cd se-hack
npm install
```

Create a `se-hack/.env.local` file with variables:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
```

Run the Next.js development server:
```bash
npm run dev
```

The frontend will run at `http://localhost:3000` and the backend documentation (Swagger docs) will be available at `http://localhost:8000/docs`.

---

## Evaluation Metric Formulas
Evalvate uses deterministic, multi-modal scoring matrices:

- **Overall Score**:
  $$\text{Overall} = \left( 0.35 \times \text{Technical} + 0.25 \times \text{Communication} + 0.20 \times \text{Eye Contact} + 0.10 \times \text{Emotion} + 0.10 \times \text{Structure} \right) \times 10$$
- **Eye Contact**:
  $$\text{EyeContactScore} = \frac{\text{frames with gaze score } > 0.6}{\text{total frames}} \times 10$$
- **Communication Score**:
  $$\text{Communication} = \frac{\text{pace\_score} + \text{clarity\_score} + \text{confidence\_score} + \text{energy\_score}}{4}$$

---

## Testing
Run backend unit/contradiction tests:
```bash
cd backend
python test_contradiction.py
```
