# Video Analysis Module

## Purpose

The Video Analysis module evaluates candidate behavior during interviews using computer vision.

It provides:

* Confidence scoring
* Engagement scoring
* Eye-contact analysis
* Gaze tracking
* Head pose estimation
* Gesture detection
* Facial emotion analysis

---

# Technology Stack

| Technology          | Purpose                                   |
| ------------------- | ----------------------------------------- |
| MediaPipe Pose      | Body landmark tracking                    |
| MediaPipe Hands     | Hand tracking                             |
| MediaPipe Face Mesh | Face and iris tracking                    |
| OpenCV              | Image processing and head pose estimation |
| DeepFace            | Emotion classification                    |
| NumPy               | Mathematical calculations                 |

---

# Architecture

```text
backend/app/video_analysis/
├── pose_analyzer.py
├── face_analyzer.py
├── gaze_analyzer.py
├── confidence_scorer.py
├── router.py
├── schemas.py
└── utils.py
```

---

# Features

## 1. Posture Analysis

Uses MediaPipe Pose landmarks.

Measures:

* Shoulder alignment
* Body posture
* Spine alignment

Used for confidence scoring.

---

## 2. Nervous Gesture Detection

Uses wrist and facial landmarks.

Detects:

* Face touching
* Excessive hand movement
* Fidgeting

Used as a confidence penalty.

---

## 3. Emotion Detection

Uses DeepFace.

Detected emotions:

* Happy
* Neutral
* Surprise
* Sad
* Angry
* Fear
* Disgust

Emotion results modify confidence scores.

---

## 4. Eye Tracking

Uses MediaPipe iris landmarks.

Tracks:

* Left pupil position
* Right pupil position
* Eye-contact consistency

Output:

* Eye-contact percentage
* Gaze direction

---

## 5. Gaze Direction Detection

Classifies gaze as:

* Center
* Left
* Right
* Up
* Down

Used for engagement scoring.

---

## 6. Head Pose Estimation

Uses OpenCV solvePnP.

Calculates:

* Pitch
* Yaw
* Roll

Determines whether candidate is facing the screen.

---

# Confidence Score

Measures physical confidence.

Components:

| Component          | Weight |
| ------------------ | ------ |
| Shoulder Alignment | 30%    |
| Nervous Gestures   | 35%    |
| Posture            | 35%    |

Emotion analysis may increase or decrease the final score.

Output Range:

```text
0.0 - 1.0
```

---

# Engagement Score

Measures visual attention.

Components:

| Component   | Weight |
| ----------- | ------ |
| Eye Contact | 40%    |
| Head Yaw    | 30%    |
| Head Pitch  | 30%    |

Output Range:

```text
0.0 - 1.0
```

---

# API Endpoints

## Analyze Single Frame

```http
POST /video/analyze-frame
```

Returns:

* confidence_score
* engagement_score
* emotion analysis
* gaze analysis
* head pose data

---

## Analyze Batch

```http
POST /video/analyze-batch
```

Processes multiple frames and returns aggregated results.

---

## Health Check

```http
GET /video/health
```

Verifies model availability.

---

# Integration

Video analysis produces:

* confidence_score
* engagement_score

These scores are combined with:

* Interview evaluation scores
* Speech analysis scores
* LLM evaluation scores

to generate the final interview report.

---

# Future Improvements

* Multi-person detection
* Improved iris gaze estimation
* Session-level eye-contact tracking
* Real-time behavioral alerts
* Confidence trend visualization
