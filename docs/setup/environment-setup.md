# EVALVATE — WHAT YOU OWN vs WHAT YOU NEED TO REPLACE

---

## STEP 1 — Create a fresh `.env` file at `backend/.env` and `se-hack/.env.local`

### BACKEND `.env` — Replace every single one of these:

```env
# ─── MongoDB ───────────────────────────────────────────
# Go to: https://cloud.mongodb.com → free M0 cluster → connect → get URI
MONGODB_URL=mongodb+srv://YOUR_USER:YOUR_PASS@cluster0.xxxxx.mongodb.net/evalvate?retryWrites=true&w=majority

# ─── JWT Secret ────────────────────────────────────────
# Just generate one: openssl rand -hex 32
JWT_SECRET=your_random_64_char_hex_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ─── Google OAuth ──────────────────────────────────────
# Go to: console.cloud.google.com → APIs → Credentials → OAuth 2.0 Client
# Redirect URI: https://evalvate.dev/auth/callback (and http://localhost:3000/auth/callback for dev)
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback

# ─── OpenRouter (for Gemini) ───────────────────────────
# Go to: https://openrouter.ai → sign up → API Keys → create key
# They give free credits on signup
OPENROUTER_API_KEY=sk-or-v1-your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=google/gemini-2.0-flash-001

# ─── Deepgram (STT + TTS) ─────────────────────────────
# Go to: https://deepgram.com → sign up → API Keys
# $200 free credit on signup — more than enough for dev + demo
DEEPGRAM_API_KEY=your_deepgram_key_here

# ─── Hume AI (Vocal Prosody Analysis) ────────────
# Go to: https://hume.ai → sign up → API Keys
# Free tier: 100 minutes/month — enough for demos
HUME_API_KEY=your_hume_api_key_here

# ─── Simli (AI Human Avatar) ─────────────────────
# Go to: https://simli.ai → sign up → get API key
# Free tier available
SIMLI_API_KEY=your_simli_api_key_here

# ─── App config ────────────────────────────────────────
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
INTERVIEW_MAX_QUESTIONS=5
ENVIRONMENT=development
```

### FRONTEND `se-hack/.env.local`:

```env
# Backend URLs — NEVER hardcode localhost in component files
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Google OAuth (same client as backend)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com

# Simli (AI Avatar — can call from frontend)
NEXT_PUBLIC_SIMLI_API_KEY=your_simli_api_key_here

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_APP_NAME=Evalvate
```

---

## STEP 2 — Download MediaPipe Model Files (If NOT in repo, must do manually)

Run this script from `backend/` directory:

```bash
mkdir -p app/video_analysis/models
cd app/video_analysis/models

# Face Landmarker (for gaze + landmarks)
wget -O face_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task

# Pose Landmarker (for posture)
wget -O pose_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task

# Hand Landmarker (for gestures)
wget -O hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task

echo "All MediaPipe models downloaded"
```

Add this to `backend/setup.sh` and run it once after cloning.

---

## STEP 3 — Python dependencies (backend)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## STEP 4 — Node dependencies (frontend)

```bash
cd se-hack
npm install
```

---

## STEP 5 — Verify it runs

```bash
# Terminal 1 — Backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd se-hack && npm run dev
```

Open http://localhost:3000.

---

## WHAT IS ACTUALLY YOURS (no cofounder dependency):

| Component | You Own It? | Notes |
|---|---|---|
| All Python backend code | ✅ Yes | FastAPI, services, analyzers |
| All Next.js frontend code | ✅ Yes | Pages, components, hooks |
| MongoDB schema + data | ✅ Yes (once you create your cluster) | |
| MediaPipe models | ✅ Yes (free download) | See Step 2 |
| Questions you've written | ✅ Yes | Add to DB per Part 3 |
| OpenRouter API key | ❌ Need yours | Free credits on signup |
| Deepgram API key | ❌ Need yours | $200 free credits |
| Google OAuth credentials | ❌ Need yours | Free, 5 min setup |
| MongoDB Atlas | ❌ Need yours | Free M0 forever |
| Hume AI key  | ❌ Need yours | Free tier exists |
| Simli key  | ❌ Need yours | Free tier exists |
