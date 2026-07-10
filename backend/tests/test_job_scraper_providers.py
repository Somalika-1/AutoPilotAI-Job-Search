import pytest

from app.services.job_scraper import adzuna, usajobs
from app.services.job_scraper.date_filters import cutoff_for, days_for


class _FakeResponse:
    def __init__(self, json_data: dict) -> None:
        self._json = json_data

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._json


def test_days_for_maps_known_values() -> None:
    assert days_for("24h") == 1
    assert days_for("3d") == 3
    assert days_for("7d") == 7
    assert days_for("30d") == 30
    assert days_for(None) is None
    assert days_for("not-a-real-value") is None


def test_cutoff_for_only_returns_a_value_for_known_windows() -> None:
    assert cutoff_for(None) is None
    assert cutoff_for("not-a-real-value") is None
    assert cutoff_for("7d") is not None


def test_adzuna_search_skips_silently_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adzuna.settings, "adzuna_app_id", "")
    monkeypatch.setattr(adzuna.settings, "adzuna_app_key", "")

    assert adzuna.search("python") == []


def test_adzuna_search_maps_documented_response_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adzuna.settings, "adzuna_app_id", "fake-id")
    monkeypatch.setattr(adzuna.settings, "adzuna_app_key", "fake-key")
    fake_json = {
        "results": [
            {
                "id": "123",
                "title": "Backend Engineer",
                "company": {"display_name": "Acme Inc"},
                "location": {"display_name": "London"},
                "redirect_url": "https://www.adzuna.com/details/123",
                "created": "2026-07-01T00:00:00Z",
                "description": "Python and Postgres role",
            }
        ]
    }
    monkeypatch.setattr(adzuna.httpx, "get", lambda *args, **kwargs: _FakeResponse(fake_json))

    results = adzuna.search("python", location="London", date_posted="7d")

    assert len(results) == 1
    listing = results[0]
    assert listing.source == "adzuna"
    assert listing.external_id == "123"
    assert listing.title == "Backend Engineer"
    assert listing.company == "Acme Inc"
    assert listing.location == "London"
    assert listing.url == "https://www.adzuna.com/details/123"


def test_usajobs_search_skips_silently_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(usajobs.settings, "usajobs_api_key", "")
    monkeypatch.setattr(usajobs.settings, "usajobs_user_agent", "")

    assert usajobs.search("data") == []


def test_usajobs_search_maps_documented_response_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(usajobs.settings, "usajobs_api_key", "fake-key")
    monkeypatch.setattr(usajobs.settings, "usajobs_user_agent", "test@example.com")
    fake_json = {
        "SearchResult": {
            "SearchResultItems": [
                {
                    "MatchedObjectId": "abc123",
                    "MatchedObjectDescriptor": {
                        "PositionID": "abc123",
                        "PositionTitle": "Data Analyst",
                        "OrganizationName": "Department of Example",
                        "PositionLocationDisplay": "Washington, DC",
                        "PositionURI": "https://www.usajobs.gov/job/abc123",
                        "PublicationStartDate": "2026-07-01",
                        "UserArea": {"Details": {"JobSummary": "Analyze data for the agency."}},
                    },
                }
            ]
        }
    }
    monkeypatch.setattr(usajobs.httpx, "get", lambda *args, **kwargs: _FakeResponse(fake_json))

    results = usajobs.search("data", location="Washington, DC")

    assert len(results) == 1
    listing = results[0]
    assert listing.source == "usajobs"
    assert listing.external_id == "abc123"
    assert listing.title == "Data Analyst"
    assert listing.company == "Department of Example"
    assert listing.description == "Analyze data for the agency."