import io
import uuid
from pathlib import Path

import docx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _auth_headers() -> dict[str, str]:
    email = f"resume-test-{uuid.uuid4().hex}@example.com"
    password = "supersecret123"
    client.post("/auth/signup", json={"email": email, "password": password})
    login_response = client.post("/auth/login", json={"email": email, "password": password})
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_docx_bytes(text: str) -> bytes:
    document = docx.Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_upload_docx_extracts_text() -> None:
    headers = _auth_headers()
    file_bytes = _make_docx_bytes("Experienced backend engineer skilled in Java and Spring Boot.")

    response = client.post(
        "/resumes/upload",
        headers=headers,
        files={
            "file": (
                "resume.docx",
                file_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "resume.docx"
    assert "Spring Boot" in body["extracted_text"]


def test_upload_pdf_extracts_text() -> None:
    headers = _auth_headers()
    file_bytes = (FIXTURES_DIR / "sample_resume.pdf").read_bytes()

    response = client.post(
        "/resumes/upload",
        headers=headers,
        files={"file": ("sample_resume.pdf", file_bytes, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert "AutoPilotAI" in body["extracted_text"]


def test_upload_unsupported_file_type_rejected() -> None:
    headers = _auth_headers()

    response = client.post(
        "/resumes/upload",
        headers=headers,
        files={"file": ("resume.txt", b"plain text resume", "text/plain")},
    )

    assert response.status_code == 400


def test_upload_requires_auth() -> None:
    response = client.post(
        "/resumes/upload",
        files={"file": ("resume.docx", b"irrelevant", "application/octet-stream")},
    )

    assert response.status_code == 401
