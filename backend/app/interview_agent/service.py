"""
Interview agent service — PostgreSQL version.

Only the DB-touching helpers (_load_resume_context, _load_recent_history,
evaluate_answer_only, evaluate_and_generate_next_question,
generate_question_bank, generate_first_question) are changed.
All LLM/graph/prompt logic is unchanged.
"""

import logging
import os
import uuid
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.interview_agent.graph import interview_agent_graph
from app.interview_agent.llm import invoke_llm_json
from app.interview_agent.prompts import (
    EVALUATION_SYSTEM_PROMPT,
    QUESTION_BANK_SYSTEM_PROMPT,
    build_evaluation_prompt,
    build_question_bank_prompt,
)
from app.interview_agent.schemas import InterviewAgentState, ResumeContext
from app.models.interview import InterviewResponse
from app.models.resume import Resume

logger = logging.getLogger(__name__)


def _normalize_string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def _normalize_question_key(question: str) -> str:
    return " ".join(question.strip().lower().split())


def _format_recent_history(history: list[dict[str, Any]]) -> str:
    if not history:
        return "No prior turns."
    parts = []
    for idx, item in enumerate(history[-5:], start=1):
        parts.append(
            f"Turn {idx}:\nQuestion: {item.get('question', '')}\n"
            f"Answer: {item.get('answer', '')}\nScore: {item.get('score', 'N/A')}\n"
            f"Feedback: {item.get('feedback', '')}"
        )
    return "\n\n".join(parts)


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _load_resume_context(db: AsyncSession, user_id: str) -> ResumeContext:
    """Load the user's most recent resume from PostgreSQL."""
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .limit(1)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        logger.warning("No resume found for user", extra={"user_id": user_id})
        return {"skills": [], "projects": [], "raw_text": ""}

    parsed = doc.parsed_resume or {}
    skills = _normalize_string_list(parsed.get("skills"))

    projects: list[str] = []
    experience = parsed.get("experience")
    if isinstance(experience, list):
        for item in experience:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip()
            description = str(item.get("description") or "").strip()
            if role and description:
                projects.append(f"{role}: {description}")
            elif description:
                projects.append(description)

    raw_text = str(doc.raw_text or "").strip()
    if not raw_text:
        summary = str(parsed.get("summary") or "").strip()
        education = ", ".join(_normalize_string_list(parsed.get("education")))
        raw_text = "\n".join(p for p in [summary, education, " ".join(projects)] if p)

    return {"skills": skills, "projects": projects, "raw_text": raw_text}


async def _load_recent_history(
    db: AsyncSession,
    interview_id: uuid.UUID,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(InterviewResponse)
        .where(InterviewResponse.interview_id == interview_id)
        .order_by(InterviewResponse.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    rows = list(reversed(rows))  # chronological order
    return [
        {
            "question": row.question,
            "answer": row.answer,
            "score": row.score or 5,
            "feedback": row.feedback or "",
            "strengths": _normalize_string_list(row.strengths),
            "weaknesses": _normalize_string_list(row.weaknesses),
        }
        for row in rows
    ]


# ── Public API (unchanged signatures) ────────────────────────────────────────

def get_max_questions() -> int:
    raw = os.getenv("INTERVIEW_MAX_QUESTIONS", "5")
    try:
        value = int(raw)
    except ValueError:
        value = 5
    return max(1, min(30, value))


async def generate_question_bank(
    *,
    db: AsyncSession,
    user_id: str,
    role: str,
    difficulty: str,
    persona: str,
    max_questions: int,
) -> list[str]:
    resume = await _load_resume_context(db, user_id)
    variation_token = uuid4().hex[:10]

    payload = await invoke_llm_json(
        system_prompt=QUESTION_BANK_SYSTEM_PROMPT,
        user_prompt=build_question_bank_prompt(
            role=role,
            difficulty=difficulty,
            persona=persona,
            resume=resume,
            max_questions=max_questions,
            variation_token=variation_token,
        ),
        temperature=0.65,
    )

    questions = payload.get("questions")
    if not isinstance(questions, list) or len(questions) == 0:
        raise ValueError("Question bank generation failed: no questions returned")

    cleaned: list[str] = []
    seen: set[str] = set()
    for q in questions:
        text = str(q).strip()
        key = _normalize_question_key(text)
        if text and key not in seen:
            seen.add(key)
            cleaned.append(text)

    intro = "Introduce yourself and summarize your background relevant to this role."
    intro_key = _normalize_question_key(intro)
    if cleaned:
        if _normalize_question_key(cleaned[0]) != intro_key:
            cleaned = [intro] + [q for q in cleaned if _normalize_question_key(q) != intro_key]
    else:
        cleaned = [intro]
    seen.add(intro_key)

    idx = 1
    while len(cleaned) < max_questions:
        fallback = f"Tell me more about your experience relevant to the {role} role (follow-up {idx})."
        idx += 1
        fkey = _normalize_question_key(fallback)
        if fkey not in seen:
            seen.add(fkey)
            cleaned.append(fallback)

    return cleaned[:max_questions]


async def generate_first_question(
    *,
    db: AsyncSession,
    user_id: str,
    role: str,
    difficulty: str,
    persona: str,
    max_questions: int,
) -> dict[str, Any]:
    bank = await generate_question_bank(
        db=db, user_id=user_id, role=role,
        difficulty=difficulty, persona=persona, max_questions=max_questions,
    )
    return {"question": bank[0], "difficulty": difficulty, "questions_bank": bank}


async def evaluate_answer_only(
    *,
    db: AsyncSession,
    interview_id: uuid.UUID,
    user_id: str,
    role: str,
    difficulty: str,
    persona: str,
    question: str,
    answer: str,
    expected_keywords: list[str] | None = None,
    evaluation_criteria: list[str] | None = None,
) -> dict[str, Any]:
    history_limit = int(os.getenv("INTERVIEW_AGENT_HISTORY_LIMIT", "5"))
    history = await _load_recent_history(db, interview_id, limit=max(1, min(10, history_limit)))

    payload = await invoke_llm_json(
        system_prompt=EVALUATION_SYSTEM_PROMPT,
        user_prompt=build_evaluation_prompt(
            role=role,
            difficulty=difficulty,
            persona=persona,
            question=question,
            answer=answer,
            history=history,
            expected_keywords=expected_keywords,
            evaluation_criteria=evaluation_criteria,
        ),
        temperature=0.15,
    )

    try:
        score = max(1, min(10, int(payload.get("score", 5))))
    except (TypeError, ValueError):
        score = 5

    strengths = payload.get("strengths")
    weaknesses = payload.get("weaknesses")

    return {
        "evaluation": {
            "score": score,
            "feedback": str(payload.get("feedback", "No feedback provided")).strip(),
            "strengths": [str(i) for i in strengths] if isinstance(strengths, list) else [],
            "weaknesses": [str(i) for i in weaknesses] if isinstance(weaknesses, list) else [],
        }
    }


async def evaluate_and_generate_next_question(
    *,
    db: AsyncSession,
    interview_id: uuid.UUID,
    user_id: str,
    role: str,
    difficulty: str,
    persona: str,
    question: str,
    answer: str,
    max_questions: int,
    current_turn: int,
    last_score: int | None,
) -> dict[str, Any]:
    history_limit = int(os.getenv("INTERVIEW_AGENT_HISTORY_LIMIT", "5"))
    resume = await _load_resume_context(db, user_id)
    history = await _load_recent_history(db, interview_id, limit=max(1, min(10, history_limit)))
    variation_token = str(interview_id)

    state: InterviewAgentState = {
        "stage": "evaluate_and_generate_next",
        "variation_token": variation_token,
        "role": role,
        "difficulty": difficulty,
        "persona": persona,
        "resume": resume,
        "history": history,
        "max_questions": max_questions,
        "current_turn": current_turn,
        "last_question": question,
        "last_answer": answer,
        "last_score": last_score if last_score is not None else 5,
    }

    result = await interview_agent_graph.ainvoke(state)
    evaluation = result.get("evaluation") or {}

    return {
        "evaluation": {
            "score": int(evaluation.get("score", 5)),
            "feedback": str(evaluation.get("feedback", "No feedback generated")),
            "strengths": _normalize_string_list(evaluation.get("strengths") or []),
            "weaknesses": _normalize_string_list(evaluation.get("weaknesses") or []),
        },
        "next_question": str(result.get("question", "")).strip(),
        "difficulty": str(result.get("generated_difficulty", difficulty)),
    }


# ── Adaptive follow-up generation (pure LLM calls, no DB dependency) ─────────

ADAPTIVE_MODES = {
    "clarify": (
        "The candidate's last answer was weak (score below 5). "
        "Generate ONE clarifying follow-up on the SAME topic that gives them a chance "
        "to demonstrate understanding at a more fundamental level. Be encouraging but precise."
    ),
    "escalate": (
        "The candidate's last answer was excellent (score 8+). "
        "Generate ONE harder follow-up that escalates the SAME topic: edge cases, scale, "
        "trade-offs, or production failure scenarios. Push for senior-level depth."
    ),
    "challenge": (
        "The candidate's last answer contradicts something they said earlier. "
        "Generate ONE professional challenge question that surfaces the inconsistency "
        "and asks them to reconcile the two claims with specifics."
    ),
}


async def generate_adaptive_followup(
    *,
    mode: str,
    role: str,
    difficulty: str,
    last_question: str,
    last_answer: str,
    context_note: str = "",
) -> str | None:
    """Generate one dynamic follow-up question (the 20% adaptive slice)."""
    directive = ADAPTIVE_MODES.get(mode)
    if not directive:
        return None

    system_prompt = (
        "You are a professional AI interviewer reacting in real time to a candidate's answer. "
        "Return strict JSON only."
    )
    user_prompt = (
        f"{directive}\n\n"
        f"Role: {role}\n"
        f"Difficulty: {difficulty}\n"
        f"Previous question: {last_question}\n"
        f"Candidate's answer: {last_answer}\n"
        f"{('Additional context: ' + context_note) if context_note else ''}\n\n"
        'Return JSON object: {"question": "string"}'
    )

    try:
        payload = await invoke_llm_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
        )
        question = str(payload.get("question") or "").strip()
        return question or None
    except Exception:
        logger.exception("Adaptive follow-up generation failed", extra={"mode": mode})
        return None


async def generate_devils_advocate_challenge_question(
    *,
    role: str,
    difficulty: str,
    last_question: str,
    last_answer: str,
    history: list[dict[str, Any]],
    trigger_reasons: list[str],
) -> str:
    """Generate a targeted pressure-test follow-up for Devil's Advocate persona."""
    system_prompt = (
        "You are a Devil's Advocate interviewer. "
        "Challenge weak logic professionally and force precise technical defense. "
        "Return strict JSON only."
    )
    user_prompt = (
        "Generate exactly one high-pressure follow-up question.\n"
        "Goal: test emotional stability, recovery speed, and ability to defend technical logic under pressure.\n"
        "Rules:\n"
        "1) Challenge assumptions from the candidate's latest answer.\n"
        "2) Ask for concrete trade-offs, evidence, and fallback plan.\n"
        "3) Keep wording professional; no insults or personal attacks.\n"
        "4) Keep the question concise and interview-ready.\n"
        "5) Do not repeat the prior question wording.\n\n"
        f"Role: {role}\n"
        f"Difficulty: {difficulty}\n"
        f"Trigger reasons: {', '.join(trigger_reasons) if trigger_reasons else 'uncertainty detected'}\n"
        f"Latest question: {last_question}\n"
        f"Latest answer: {last_answer}\n"
        f"Recent history:\n{_format_recent_history(history)}\n\n"
        'Return JSON object: {"question": "string"}'
    )

    try:
        payload = await invoke_llm_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.55,
        )
        question = str(payload.get("question") or "").strip()
        if question:
            return question
    except Exception:
        logger.exception("Failed to generate Devil's Advocate challenge question")

    return (
        "You sounded uncertain in parts of your answer. Defend your approach with concrete trade-offs, "
        "state the first recovery step you would execute, and explain how you would verify it worked."
    )