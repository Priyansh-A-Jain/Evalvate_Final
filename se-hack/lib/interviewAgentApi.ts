import { backendClient } from "@/lib/backend";

export type InterviewStatus = "ongoing" | "completed";

export type StartInterviewRequest = {
  role: string;
  difficulty: string;
  persona: string;
  max_questions?: number;
  duration_minutes?: number;
};

export type StartInterviewResponse = {
  interview_id: string;
  first_question: string;
  first_question_audio_data_uri?: string | null;
  questions_bank: string[];
  total_questions: number;
  status: InterviewStatus;
  duration_minutes?: number | null;
  deadline_at?: string | null;
};

export type AnswerEvaluation = {
  score: number;
  feedback: string;
  strengths: string[];
  weaknesses: string[];
};

export type SubmitAnswerRequest = {
  interview_id: string;
  answer: string;
};

export type SubmitAnswerResponse = {
  interview_id: string;
  evaluation: AnswerEvaluation;
  next_question: string | null;
  next_question_audio_data_uri?: string | null;
  status: InterviewStatus;
  time_expired?: boolean;
};

export type SessionAnalysisData = {
  voice_summary?: string | null;
  key_moments?: Array<{ time: string; description: string }> | null;
  confidence?: number | null;
  clarity?: number | null;
  nervousness?: number | null;
  posture_score?: number | null;
  gaze_score?: number | null;
  fidgeting_score?: number | null;
  dominant_emotion?: string | null;
  duration_seconds?: number | null;
  prosody?: Record<string, unknown> | null;
  pace_wpm?: number | null;
  multi_face_ratio?: number | null;
  background_person_detected?: boolean | null;
  component_scores?: Record<string, number> | null;
  overall_score?: number | null;
  grade?: string | null;
  video_timeline?: Array<{
    timestamp: number;
    label?: string | null;
    payload?: Record<string, unknown>;
  }> | null;
  voice_timeline?: Array<{
    timestamp: number;
    label?: string | null;
    payload?: Record<string, unknown>;
  }> | null;
};

export type InterviewDetailResponse = {
  interview: {
    id: string;
    user_id: string;
    role: string;
    difficulty: string;
    persona: string;
    status: InterviewStatus;
    created_at: string;
    questions_bank?: string[];
    total_questions?: number;
    session_analysis?: SessionAnalysisData | null;
    duration_minutes?: number | null;
    deadline_at?: string | null;
    questions_meta?: Array<Record<string, unknown>> | null;
  };
  responses: Array<{
    id: string;
    interview_id: string;
    user_id: string;
    question: string;
    answer: string;
    score?: number | null;
    feedback?: string | null;
    strengths?: string[] | null;
    weaknesses?: string[] | null;
    contradiction_analysis?: {
      contradiction: boolean;
      confidence: number;
      topic: string;
      previous_claim: string;
      current_claim: string;
      explanation: string;
      severity: string;
    } | null;
    created_at: string;
  }>;
};

export async function startInterview(payload: StartInterviewRequest): Promise<StartInterviewResponse> {
  const response = await backendClient.post<StartInterviewResponse>("/start-interview", payload);
  return response.data;
}

export async function submitInterviewAnswer(payload: SubmitAnswerRequest): Promise<SubmitAnswerResponse> {
  const response = await backendClient.post<SubmitAnswerResponse>("/submit-answer", payload);
  return response.data;
}

export async function getInterviewDetails(interviewId: string): Promise<InterviewDetailResponse> {
  const response = await backendClient.get<InterviewDetailResponse>(`/interview/${interviewId}`);
  return response.data;
}

export async function saveSessionAnalysis(
  interviewId: string,
  sessionAnalysis: SessionAnalysisData,
): Promise<void> {
  await backendClient.post(`/interview/${interviewId}/session-analysis`, {
    interview_id: interviewId,
    session_analysis: sessionAnalysis,
  });
}

export async function createShareToken(interviewId: string): Promise<{ share_token: string }> {
  const response = await backendClient.post<{ share_token: string }>(`/interview/${interviewId}/share`);
  return response.data;
}

export async function getSharedReport(token: string): Promise<InterviewDetailResponse> {
  const response = await backendClient.get<InterviewDetailResponse>(`/shared-report/${token}`);
  return response.data;
}
