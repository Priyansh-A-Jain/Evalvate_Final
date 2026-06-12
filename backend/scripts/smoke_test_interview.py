"""
Smoke test for the interview flow: question count + hard session deadline.

Run from backend/ with the venv python while the API is up on :8000:
    .venv/Scripts/python.exe scripts/smoke_test_interview.py
"""
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND_DIR))
load_dotenv(_BACKEND_DIR / ".env")

from app.auth.jwt import create_access_token  # noqa: E402

BASE_URL = "http://localhost:8000"
MAX_QUESTIONS = 3
DURATION_MINUTES = 1


def main() -> None:
    token = create_access_token(user_id="smoke-test-user", email="smoke@test.local")
    client = httpx.Client(base_url=BASE_URL, cookies={"access_token": token}, timeout=120)

    print(f"[1] POST /start-interview (max_questions={MAX_QUESTIONS}, duration_minutes={DURATION_MINUTES})")
    start = client.post(
        "/start-interview",
        json={
            "role": "Backend Engineer",
            "difficulty": "easy",
            "persona": "mentor",
            "max_questions": MAX_QUESTIONS,
            "duration_minutes": DURATION_MINUTES,
        },
    )
    start.raise_for_status()
    data = start.json()
    bank = data["questions_bank"]
    print(f"    interview_id={data['interview_id']}")
    print(f"    total_questions={data['total_questions']} (expected {MAX_QUESTIONS})")
    print(f"    deadline_at={data.get('deadline_at')}")
    print(f"    first_question={data['first_question'][:80]}...")
    print(f"    tts_audio={'yes' if data.get('first_question_audio_data_uri') else 'no'}")
    assert data["total_questions"] == MAX_QUESTIONS, "question count not honored!"
    assert len(bank) == MAX_QUESTIONS, "bank size mismatch!"
    assert data.get("deadline_at"), "deadline_at missing!"

    interview_id = data["interview_id"]

    print("[2] POST /submit-answer (answer 1 — before deadline)")
    sub1 = client.post(
        "/submit-answer",
        json={"interview_id": interview_id, "answer": "I am a backend engineer with three years of Python and FastAPI experience."},
    )
    sub1.raise_for_status()
    d1 = sub1.json()
    print(f"    status={d1['status']} time_expired={d1.get('time_expired')} score={d1['evaluation']['score']}")
    assert d1["status"] == "ongoing", "interview should still be ongoing"
    assert d1.get("time_expired") is False

    wait_s = DURATION_MINUTES * 60 + 5
    print(f"[3] Waiting {wait_s}s for the deadline to pass...")
    time.sleep(wait_s)

    print("[4] POST /submit-answer (answer 2 — after deadline)")
    sub2 = client.post(
        "/submit-answer",
        json={"interview_id": interview_id, "answer": "I would add an index on the user_id column and profile the query."},
    )
    sub2.raise_for_status()
    d2 = sub2.json()
    print(f"    status={d2['status']} time_expired={d2.get('time_expired')} next_question={d2.get('next_question')}")
    assert d2["status"] == "completed", "interview should be force-completed after deadline"
    assert d2.get("time_expired") is True, "time_expired flag should be true"
    assert d2.get("next_question") is None, "no next question after deadline"

    print("[5] GET /interview/{id} — verify persisted state")
    detail = client.get(f"/interview/{interview_id}")
    detail.raise_for_status()
    dd = detail.json()
    print(f"    persisted status={dd['interview']['status']} responses={len(dd['responses'])}")
    print(f"    duration_minutes={dd['interview'].get('duration_minutes')} deadline_at={dd['interview'].get('deadline_at')}")
    assert dd["interview"]["status"] == "completed"

    meta = dd["interview"].get("questions_meta") or []
    sources = [m.get("source") for m in meta if isinstance(m, dict)]
    print(f"    hybrid bank sources: {sources}")
    # 'curated' = founder bank question; 'followup' = a slot adaptively replaced
    # at runtime (weak/strong answer) — both prove the hybrid pipeline is live.
    assert any(s in {"curated", "followup"} for s in sources) or MAX_QUESTIONS <= 2, (
        "hybrid pipeline produced neither curated nor adaptive questions"
    )

    print("[6] POST /interview/{id}/share + public GET /shared-report/{token}")
    share = client.post(f"/interview/{interview_id}/share")
    share.raise_for_status()
    token = share.json()["share_token"]
    public_client = httpx.Client(base_url=BASE_URL, timeout=30)  # no auth cookie
    shared = public_client.get(f"/shared-report/{token}")
    shared.raise_for_status()
    assert shared.json()["interview"]["id"] == interview_id
    print(f"    share_token={token[:12]}... public fetch OK (no auth)")

    print("[7] GET /demo/login (DEMO_MODE)")
    demo = public_client.get("/demo/login", follow_redirects=False)
    print(f"    status={demo.status_code} (302 expected when DEMO_MODE=true)")
    assert demo.status_code in (302, 404), "unexpected demo login behavior"
    if demo.status_code == 302:
        assert "access_token" in demo.headers.get("set-cookie", ""), "demo login should set auth cookies"
        print("    demo cookies set OK")

    print("\nALL SMOKE TESTS PASSED: hybrid bank, question count, hard deadline, share link, demo mode.")


if __name__ == "__main__":
    main()
