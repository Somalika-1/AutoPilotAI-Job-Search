import uuid

import pytest
from fastapi.testclient import TestClient

import app.routes.jobs as jobs_module
from app.database import SessionLocal
from app.main import app
from app.models import JobDescription
from app.services.job_scraper import JobListing

client = TestClient(app)


def _auth_headers() -> dict[str, str]:
    email = f"jobs-test-{uuid.uuid4().hex}@example.com"
    password = "supersecret123"
    client.post("/auth/signup", json={"email": email, "password": password})
    login_response = client.post("/auth/login", json={"email": email, "password": password})
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _current_user_id(headers: dict[str, str]) -> int:
    return client.get("/auth/me", headers=headers).json()["id"]


@pytest.fixture
def mock_search_jobs(monkeypatch: pytest.MonkeyPatch) -> list[JobListing]:
    fake_results = [
        JobListing(
            external_id="1",
            source="remoteok",
            title="Backend Engineer",
            company="Acme Inc",
            location="Remote",
            url="https://remoteok.com/remote-jobs/1",
            posted_at=None,
            description="Python and Postgres role",
        )
    ]
    monkeypatch.setattr(jobs_module, "search_jobs", lambda query, location, date_posted: fake_results)
    return fake_results


def test_search_jobs_success(mock_search_jobs: list[JobListing]) -> None:
    headers = _auth_headers()

    response = client.get("/jobs/search", headers=headers, params={"query": "backend"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Backend Engineer"
    assert body[0]["source"] == "remoteok"


def test_search_jobs_requires_auth(mock_search_jobs: list[JobListing]) -> None:
    response = client.get("/jobs/search", params={"query": "backend"})

    assert response.status_code == 401


def test_search_jobs_requires_query_param() -> None:
    headers = _auth_headers()

    response = client.get("/jobs/search", headers=headers)

    assert response.status_code == 422


def test_search_jobs_accepts_location_and_date_posted(mock_search_jobs: list[JobListing]) -> None:
    headers = _auth_headers()

    response = client.get(
        "/jobs/search",
        headers=headers,
        params={"query": "backend", "location": "Remote", "date_posted": "7d"},
    )

    assert response.status_code == 200


def test_search_jobs_rejects_invalid_date_posted(mock_search_jobs: list[JobListing]) -> None:
    headers = _auth_headers()

    response = client.get(
        "/jobs/search",
        headers=headers,
        params={"query": "backend", "date_posted": "last-week"},
    )

    assert response.status_code == 422


def _listing_payload(external_id: str = "1", source: str = "remoteok") -> dict:
    return {
        "external_id": external_id,
        "source": source,
        "title": "Backend Engineer",
        "company": "Acme Inc",
        "location": "Remote",
        "url": "https://remoteok.com/remote-jobs/1",
        "posted_at": None,
        "description": "Python and Postgres role",
    }


def test_save_job_success() -> None:
    headers = _auth_headers()

    response = client.post("/jobs/save", headers=headers, json=_listing_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "remoteok"
    assert body["title"] == "Backend Engineer"
    assert body["raw_text"] == "Python and Postgres role"


def test_save_job_duplicate_rejected() -> None:
    headers = _auth_headers()
    client.post("/jobs/save", headers=headers, json=_listing_payload())

    response = client.post("/jobs/save", headers=headers, json=_listing_payload())

    assert response.status_code == 409


def test_save_job_same_listing_different_users_both_succeed() -> None:
    headers_a = _auth_headers()
    headers_b = _auth_headers()
    client.post("/jobs/save", headers=headers_a, json=_listing_payload())

    response = client.post("/jobs/save", headers=headers_b, json=_listing_payload())

    assert response.status_code == 201


def test_save_job_requires_auth() -> None:
    response = client.post("/jobs/save", json=_listing_payload())

    assert response.status_code == 401


def test_list_saved_jobs_returns_only_current_users_saved_jobs() -> None:
    headers_a = _auth_headers()
    headers_b = _auth_headers()
    client.post("/jobs/save", headers=headers_a, json=_listing_payload(external_id="1"))
    client.post("/jobs/save", headers=headers_b, json=_listing_payload(external_id="2"))

    response = client.get("/jobs/saved", headers=headers_a)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Backend Engineer"


def test_list_saved_jobs_excludes_manually_pasted_job_descriptions() -> None:
    headers = _auth_headers()
    user_id = _current_user_id(headers)

    db = SessionLocal()
    db.add(JobDescription(user_id=user_id, source="manual", raw_text="A manually pasted job description."))
    db.commit()
    db.close()

    response = client.get("/jobs/saved", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_list_saved_jobs_requires_auth() -> None:
    response = client.get("/jobs/saved")

    assert response.status_code == 401


def test_unsave_job_success() -> None:
    headers = _auth_headers()
    save_response = client.post("/jobs/save", headers=headers, json=_listing_payload())
    job_id = save_response.json()["id"]

    response = client.delete(f"/jobs/saved/{job_id}", headers=headers)

    assert response.status_code == 204
    assert client.get("/jobs/saved", headers=headers).json() == []


def test_unsave_job_for_someone_elses_job_rejected() -> None:
    owner_headers = _auth_headers()
    save_response = client.post("/jobs/save", headers=owner_headers, json=_listing_payload())
    job_id = save_response.json()["id"]

    other_user_headers = _auth_headers()
    response = client.delete(f"/jobs/saved/{job_id}", headers=other_user_headers)

    assert response.status_code == 404


def test_unsave_job_missing_rejected() -> None:
    headers = _auth_headers()

    response = client.delete("/jobs/saved/999999999", headers=headers)

    assert response.status_code == 404


def test_unsave_job_requires_auth() -> None:
    response = client.delete("/jobs/saved/1")

    assert response.status_code == 401