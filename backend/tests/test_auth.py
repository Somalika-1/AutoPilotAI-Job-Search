import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex}@example.com"


def test_signup_login_me() -> None:
    email = unique_email()
    password = "supersecret123"

    signup_response = client.post("/auth/signup", json={"email": email, "password": password})
    assert signup_response.status_code == 201
    assert signup_response.json()["email"] == email

    login_response = client.post("/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


def test_signup_duplicate_email_rejected() -> None:
    email = unique_email()
    client.post("/auth/signup", json={"email": email, "password": "supersecret123"})

    duplicate_response = client.post("/auth/signup", json={"email": email, "password": "anotherpassword"})
    assert duplicate_response.status_code == 400


def test_login_wrong_password_rejected() -> None:
    email = unique_email()
    client.post("/auth/signup", json={"email": email, "password": "correctpassword"})

    login_response = client.post("/auth/login", json={"email": email, "password": "wrongpassword"})
    assert login_response.status_code == 401


def test_me_without_token_rejected() -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401
