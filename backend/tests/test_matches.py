import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.routes.matches as matches_module
from app.main import app
from app.services.ai_engine.schemas import CoverLetterResult, MatchResult

client = TestClient(app)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _auth_headers() -> dict[str, str]:
    email = f"match-test-{uuid.uuid4().hex}@example.com"
    password = "supersecret123"
    client.post("/auth/signup", json={"email": email, "password": password})
    login_response = client.post("/auth/login", json={"email": email, "password": password})
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _upload_resume(headers: dict[str, str]) -> int:
    file_bytes = (FIXTURES_DIR / "sample_resume.pdf").read_bytes()
    response = client.post(
        "/resumes/upload",
        headers=headers,
        files={"file": ("sample_resume.pdf", file_bytes, "application/pdf")},
    )
    return response.json()["id"]


def _create_match(headers: dict[str, str]) -> int:
    resume_id = _upload_resume(headers)
    response = client.post(
        "/matches",
        headers=headers,
        json={"resume_id": resume_id, "job_description_text": "Looking for a backend engineer."},
    )
    return response.json()["id"]


@pytest.fixture
def mock_ai_match(monkeypatch: pytest.MonkeyPatch) -> MatchResult:
    fake_result = MatchResult(
        score=72,
        missing_skills=["Kubernetes", "GraphQL"],
        strengths=["Java", "Spring Boot", "MySQL"],
    )
    monkeypatch.setattr(matches_module, "score_resume_against_job", lambda resume_text, jd_text: fake_result)
    return fake_result


@pytest.fixture
def mock_ai_cover_letter(monkeypatch: pytest.MonkeyPatch) -> CoverLetterResult:
    fake_result = CoverLetterResult(cover_letter="Dear Hiring Manager, I am writing to apply for this role...")
    monkeypatch.setattr(matches_module, "generate_cover_letter", lambda resume_text, jd_text: fake_result)
    return fake_result


def test_create_match_success(mock_ai_match: MatchResult) -> None:
    headers = _auth_headers()
    resume_id = _upload_resume(headers)

    response = client.post(
        "/matches",
        headers=headers,
        json={"resume_id": resume_id, "job_description_text": "Looking for a backend engineer with Kubernetes."},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["score"] == 72
    assert body["missing_skills"] == ["Kubernetes", "GraphQL"]
    assert body["strengths"] == ["Java", "Spring Boot", "MySQL"]
    assert body["cover_letter"] is None


def test_create_match_for_someone_elses_resume_rejected(mock_ai_match: MatchResult) -> None:
    owner_headers = _auth_headers()
    resume_id = _upload_resume(owner_headers)

    other_user_headers = _auth_headers()
    response = client.post(
        "/matches",
        headers=other_user_headers,
        json={"resume_id": resume_id, "job_description_text": "Some job description."},
    )

    assert response.status_code == 404


def test_create_match_missing_resume_rejected(mock_ai_match: MatchResult) -> None:
    headers = _auth_headers()
    response = client.post(
        "/matches",
        headers=headers,
        json={"resume_id": 999999999, "job_description_text": "Some job description."},
    )

    assert response.status_code == 404


def test_create_match_requires_auth(mock_ai_match: MatchResult) -> None:
    response = client.post(
        "/matches",
        json={"resume_id": 1, "job_description_text": "Some job description."},
    )

    assert response.status_code == 401


def test_create_cover_letter_success(
    mock_ai_match: MatchResult, mock_ai_cover_letter: CoverLetterResult
) -> None:
    headers = _auth_headers()
    match_id = _create_match(headers)

    response = client.post(f"/matches/{match_id}/cover-letter", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["cover_letter"] == mock_ai_cover_letter.cover_letter
    assert body["score"] == 72


def test_create_cover_letter_for_someone_elses_match_rejected(
    mock_ai_match: MatchResult, mock_ai_cover_letter: CoverLetterResult
) -> None:
    owner_headers = _auth_headers()
    match_id = _create_match(owner_headers)

    other_user_headers = _auth_headers()
    response = client.post(f"/matches/{match_id}/cover-letter", headers=other_user_headers)

    assert response.status_code == 404


def test_create_cover_letter_missing_match_rejected(mock_ai_cover_letter: CoverLetterResult) -> None:
    headers = _auth_headers()
    response = client.post("/matches/999999999/cover-letter", headers=headers)

    assert response.status_code == 404


def test_create_cover_letter_requires_auth(mock_ai_cover_letter: CoverLetterResult) -> None:
    response = client.post("/matches/1/cover-letter")

    assert response.status_code == 401
