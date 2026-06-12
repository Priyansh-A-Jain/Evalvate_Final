from datetime import datetime
from typing import Literal, Any, Optional

from pydantic import BaseModel, Field


InterviewStatus = Literal["ongoing", "completed"]


class StartInterviewRequest(BaseModel):
    role: str = Field(min_length=1)
    difficulty: str = Field(min_length=1)
    persona: str = Field(min_length=1)
    max_questions: int | None = Field(default=None, ge=1, le=30)
    duration_minutes: int | None = Field(default=None, ge=1, le=120)


class StartInterviewResponse(BaseModel):
    interview_id: str
    first_question: str
    first_question_audio_data_uri: str | None = None
    questions_bank: list[str] = []
    total_questions: int = 25
    status: InterviewStatus
    duration_minutes: int | None = None
    deadline_at: datetime | None = None


class SubmitAnswerRequest(BaseModel):
    interview_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)


class AnswerEvaluationOut(BaseModel):
    score: int = Field(ge=1, le=10)
    feedback: str
    strengths: list[str]
    weaknesses: list[str]

class ContradictionAnalysis(BaseModel):
    contradiction: bool
    confidence: float
    topic: str
    previous_claim: str
    current_claim: str
    explanation: str
    severity: str


class SubmitAnswerResponse(BaseModel):
    interview_id: str
    evaluation: AnswerEvaluationOut
    next_question: str | None
    next_question_audio_data_uri: str | None = None
    status: InterviewStatus
    contradiction_analysis: ContradictionAnalysis | None = None
    time_expired: bool = False


class KeyMoment(BaseModel):
    time: str
    description: str


class TimelineItem(BaseModel):
    timestamp: float
    label: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SessionAnalysisData(BaseModel):
    voice_summary: str | None = None
    key_moments: list[KeyMoment] | None = None
    confidence: float | None = None
    clarity: float | None = None
    nervousness: float | None = None
    posture_score: float | None = None
    gaze_score: float | None = None
    fidgeting_score: float | None = None
    dominant_emotion: str | None = None
    duration_seconds: int | None = None
    video_timeline: list[TimelineItem] | None = None
    voice_timeline: list[TimelineItem] | None = None
    prosody: dict[str, Any] | None = None
    pace_wpm: float | None = None
    multi_face_ratio: float | None = None
    background_person_detected: bool | None = None
    component_scores: dict[str, float] | None = None
    overall_score: float | None = None
    grade: str | None = None


class SaveSessionAnalysisRequest(BaseModel):
    interview_id: str = Field(min_length=1)
    session_analysis: SessionAnalysisData


class InterviewOut(BaseModel):
    id: str
    user_id: str
    role: str
    difficulty: str
    persona: str
    status: InterviewStatus
    created_at: datetime
    questions_bank: list[str] = []
    total_questions: int = 0
    session_analysis: SessionAnalysisData | None = None
    duration_minutes: int | None = None
    deadline_at: datetime | None = None
    questions_meta: list[dict[str, Any]] | None = None


class ResponseOut(BaseModel):
    id: str
    interview_id: str
    user_id: str
    question: str
    answer: str
    score: int | None = None
    feedback: str | None = None
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    contradiction_analysis: ContradictionAnalysis | None = None
    created_at: datetime


class InterviewDetailResponse(BaseModel):
    interview: InterviewOut
    responses: list[ResponseOut]
