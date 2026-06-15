# Evalvate - Architecture & Product Roadmap

## Project Overview

Evalvate is an AI-powered mock interview platform that evaluates:

* Technical interview performance
* Communication skills
* Eye contact and gaze behavior
* Confidence and vocal delivery
* Facial expressions and engagement

The goal is to provide interview-quality feedback that goes beyond simple question-answer scoring.

---

# Current Technology Stack

## Frontend

* Next.js 14 (App Router)
* TypeScript
* TailwindCSS
* Framer Motion
* Recharts

## Backend

* FastAPI
* Python
* MongoDB Atlas
* Motor (async MongoDB driver)

## AI Services

### Implemented

* Gemini (OpenRouter) → Interview generation + answer evaluation
* Deepgram → Speech-to-text + text-to-speech
* MediaPipe → Face tracking and landmark detection
* DeepFace → Emotion detection
* Hume AI → Prosody analysis
* Simli AI → Human avatar interviewer

---

# Core Interview Pipeline

1. User starts interview
2. Gemini generates interview questions
3. Deepgram TTS speaks questions
4. User answers using microphone
5. Deepgram STT transcribes response
6. Gemini evaluates answer quality
7. MediaPipe analyzes gaze and attention
8. DeepFace analyzes facial emotion
9. Results stored in MongoDB
10. Final report generated

---

# Evaluation Categories

## Technical Performance

Source:

* Gemini evaluation

Measures:

* Correctness
* Depth of knowledge
* Relevance
* Completeness

---

## Communication

Current:

* Transcript-based analysis
* Hume AI prosody analysis

Measures:

* Confidence
* Speaking pace
* Clarity
* Engagement
* Nervousness

---

## Eye Contact

Current:

* MediaPipe facial landmarks
* Iris-based gaze estimation

Measures:

* Eye contact percentage
* Gaze direction
* Attention consistency

---

## Emotional Presence

Source:

* DeepFace

Measures:

* Confidence indicators
* Nervousness indicators
* Emotional consistency

---

## Answer Structure

Source:

* Gemini

Measures:

* STAR methodology usage
* Clarity
* Organization
* Logical flow

---

# Scoring Philosophy

Final score should combine:

| Category              | Weight |
| --------------------- | ------ |
| Technical Performance | 35%    |
| Communication         | 25%    |
| Eye Contact           | 15%    |
| Emotional Presence    | 15%    |
| Answer Structure      | 10%    |

These weights may evolve through testing.

---

## Modularity

Keep services separated:

* interview/
* video_analysis/
* voice_analysis/
* results/
* ai/
* database/

Each subsystem should be replaceable independently.