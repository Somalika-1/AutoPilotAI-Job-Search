from datetime import datetime

import httpx

from app.config import settings
from app.services.job_scraper.date_filters import days_for
from app.services.job_scraper.schemas import JobListing

ADZUNA_URL_TEMPLATE = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"


def search(query: str, location: str | None = None, date_posted: str | None = None) -> list[JobListing]:
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        return []  # no key configured yet - treat like an unconfigured, skippable provider

    params: dict[str, str | int] = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "what": query,
        "results_per_page": 20,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location
    days = days_for(date_posted)
    if days is not None:
        params["max_days_old"] = days

    url = ADZUNA_URL_TEMPLATE.format(country=settings.adzuna_country)
    response = httpx.get(url, params=params, timeout=10)
    response.raise_for_status()
    jobs = response.json().get("results", [])

    results: list[JobListing] = []
    for job in jobs:
        posted_at = datetime.fromisoformat(job["created"]) if job.get("created") else None
        results.append(
            JobListing(
                external_id=str(job["id"]),
                source="adzuna",
                title=job.get("title", ""),
                company=(job.get("company") or {}).get("display_name"),
                location=(job.get("location") or {}).get("display_name"),
                url=job.get("redirect_url", ""),
                posted_at=posted_at,
                description=job.get("description", ""),
            )
        )
    return results