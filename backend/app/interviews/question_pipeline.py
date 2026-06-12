"""
Hybrid question pipeline.

Mixes three sources into one interview question bank:
    ~40% curated questions from questions/*.json (founder-authored, with
         follow_ups / evaluation_criteria / expected_keywords metadata)
    ~40% Gemini-generated questions (role + difficulty + resume aware)
    ~20% dynamic follow-up budget, spent at answer time (clarify weak
         answers, escalate strong ones, challenge contradictions)

Curated questions are matched to the candidate's resume skills first,
then to role defaults, so resume projects/skills actually get tested.
"""

import json
import logging
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# backend/app/interviews/question_pipeline.py -> repo_root/questions
QUESTIONS_DIR = Path(__file__).resolve().parents[3] / "questions"

# Resume skill keywords -> question bank subject files
SUBJECT_SKILL_KEYWORDS: dict[str, list[str]] = {
    "JAVASCRIPT": ["javascript", "js", "typescript", "react", "next", "vue", "angular", "frontend"],
    "HTML": ["html", "css", "frontend", "web design", "tailwind", "sass"],
    "NODEJS": ["node", "nodejs", "node.js", "backend javascript"],
    "EXPRESSJS": ["express", "expressjs", "rest api", "api development"],
    "PYTHON": ["python", "django", "flask", "fastapi", "pandas"],
    "JAVA": ["java", "spring", "springboot", "jvm"],
    "C": ["c programming", " c,", "embedded"],
    "CPP": ["c++", "cpp"],
    "DSA": ["data structures", "algorithms", "dsa", "leetcode", "competitive programming"],
    "DBMS": ["sql", "mysql", "postgres", "postgresql", "mongodb", "database", "dbms", "redis"],
    "OS": ["operating system", "linux", "unix", "kernel"],
    "CN": ["networking", "computer networks", "tcp", "http", "dns"],
    "OOP": ["oop", "object oriented", "design patterns"],
    "AI": ["machine learning", "deep learning", "ai", "ml", "nlp", "tensorflow", "pytorch", "llm"],
    "DEVOPS": ["devops", "docker", "kubernetes", "ci/cd", "jenkins", "terraform", "ansible"],
    "CLOUDENGINEERING": ["aws", "azure", "gcp", "cloud", "serverless", "lambda"],
    "ProgrammingFundamentals": ["programming", "software engineering"],
}

# Default subjects per interview role (used when resume gives no signal)
ROLE_SUBJECTS: dict[str, list[str]] = {
    "frontend engineer": ["JAVASCRIPT", "HTML", "OOP", "DSA", "CN", "ProgrammingFundamentals"],
    "backend engineer": ["NODEJS", "EXPRESSJS", "DBMS", "OS", "CN", "DSA", "OOP"],
    "full stack engineer": ["JAVASCRIPT", "NODEJS", "EXPRESSJS", "DBMS", "HTML", "DSA", "OOP"],
    "machine learning engineer": ["AI", "PYTHON", "DSA", "DBMS", "ProgrammingFundamentals"],
    "devops engineer": ["DEVOPS", "CLOUDENGINEERING", "OS", "CN", "ProgrammingFundamentals"],
}

DIFFICULTY_LABELS = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}

# Adjacent difficulties used to top up when one band runs dry
DIFFICULTY_NEIGHBORS = {
    "easy": ["Easy", "Medium"],
    "medium": ["Medium", "Easy", "Hard"],
    "hard": ["Hard", "Medium"],
}


@lru_cache(maxsize=1)
def load_question_bank() -> dict[str, list[dict[str, Any]]]:
    """Load all curated subject files once per process."""
    bank: dict[str, list[dict[str, Any]]] = {}
    if not QUESTIONS_DIR.exists():
        logger.warning("Curated questions directory not found: %s", QUESTIONS_DIR)
        return bank

    for path in sorted(QUESTIONS_DIR.glob("*.json")):
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Failed to load question file %s", path.name)
            continue
        if not isinstance(items, list):
            continue
        cleaned = [
            item
            for item in items
            if isinstance(item, dict) and str(item.get("question") or "").strip()
        ]
        if cleaned:
            bank[path.stem] = cleaned

    logger.info(
        "Curated question bank loaded",
        extra={"subjects": len(bank), "questions": sum(len(v) for v in bank.values())},
    )
    return bank


def _match_subjects(role: str, resume_skills: list[str]) -> list[str]:
    """Resume-skill matched subjects first, then role defaults."""
    bank = load_question_bank()
    skills_text = " ".join(skill.lower() for skill in resume_skills)

    matched: list[str] = []
    for subject, keywords in SUBJECT_SKILL_KEYWORDS.items():
        if subject not in bank:
            continue
        if any(keyword in skills_text for keyword in keywords):
            matched.append(subject)

    defaults = [s for s in ROLE_SUBJECTS.get(role.strip().lower(), []) if s in bank]
    for subject in defaults:
        if subject not in matched:
            matched.append(subject)

    if not matched:
        matched = list(bank.keys())
    return matched


def select_curated_questions(
    *,
    role: str,
    difficulty: str,
    resume_skills: list[str],
    count: int,
    seed: str,
) -> list[dict[str, Any]]:
    """
    Pick `count` curated questions, spread round-robin across the
    candidate's matched subjects and filtered to the difficulty band.
    """
    if count <= 0:
        return []

    bank = load_question_bank()
    if not bank:
        return []

    rng = random.Random(seed)
    subjects = _match_subjects(role, resume_skills)
    allowed_difficulties = DIFFICULTY_NEIGHBORS.get(difficulty, ["Medium", "Easy", "Hard"])

    # Bucket per subject, primary difficulty first then neighbors
    pools: dict[str, list[dict[str, Any]]] = {}
    for subject in subjects:
        items = bank.get(subject, [])
        ordered: list[dict[str, Any]] = []
        for label in allowed_difficulties:
            tier = [q for q in items if str(q.get("difficulty")) == label]
            rng.shuffle(tier)
            ordered.extend(tier)
        if ordered:
            pools[subject] = ordered

    selected: list[dict[str, Any]] = []
    seen_questions: set[str] = set()
    subject_cycle = [s for s in subjects if s in pools]
    cursor = 0
    while len(selected) < count and subject_cycle:
        subject = subject_cycle[cursor % len(subject_cycle)]
        pool = pools[subject]
        while pool:
            candidate = pool.pop(0)
            text = str(candidate["question"]).strip()
            key = " ".join(text.lower().split())
            if key not in seen_questions:
                seen_questions.add(key)
                selected.append(candidate)
                break
        if not pool:
            subject_cycle = [s for s in subject_cycle if s != subject]
            continue
        cursor += 1

    return selected[:count]


def curated_meta(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "curated",
        "id": item.get("id"),
        "subject": item.get("subject"),
        "difficulty": item.get("difficulty"),
        "type": item.get("type"),
        "follow_ups": item.get("follow_ups") or [],
        "evaluation_criteria": item.get("evaluation_criteria") or [],
        "expected_keywords": item.get("expected_keywords") or [],
    }


def compose_hybrid_bank(
    *,
    intro_question: str,
    llm_questions: list[str],
    curated_items: list[dict[str, Any]],
    max_questions: int,
) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Interleave curated and LLM questions after the intro, returning the
    final ordered bank plus aligned per-question metadata.
    """
    questions: list[str] = [intro_question]
    meta: list[dict[str, Any]] = [{"source": "llm", "kind": "intro"}]

    seen = {" ".join(intro_question.lower().split())}

    curated_queue = list(curated_items)
    llm_queue = [q for q in llm_questions if q.strip()]

    take_curated = True
    while len(questions) < max_questions and (curated_queue or llm_queue):
        item: str | None = None
        item_meta: dict[str, Any] | None = None

        if take_curated and curated_queue:
            curated = curated_queue.pop(0)
            item = str(curated["question"]).strip()
            item_meta = curated_meta(curated)
        elif llm_queue:
            item = llm_queue.pop(0).strip()
            item_meta = {"source": "llm"}
        elif curated_queue:
            curated = curated_queue.pop(0)
            item = str(curated["question"]).strip()
            item_meta = curated_meta(curated)

        take_curated = not take_curated

        if not item or item_meta is None:
            continue
        key = " ".join(item.lower().split())
        if key in seen:
            continue
        seen.add(key)
        questions.append(item)
        meta.append(item_meta)

    return questions, meta


def dynamic_followup_budget(max_questions: int) -> int:
    """~20% of the session may be replaced by adaptive follow-ups."""
    return max(1, round(max_questions * 0.2))
