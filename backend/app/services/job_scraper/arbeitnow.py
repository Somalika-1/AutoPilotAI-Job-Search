from datetime import datetime, timezone

import httpx

from app.services.job_scraper.date_filters import cutoff_for
from app.services.job_scraper.schemas import JobListing

ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"


def search(query: str, location: str | None = None, date_posted: str | None = None) -> list[JobListing]:
    response = httpx.get(ARBEITNOW_URL, timeout=10)
    response.raise_for_status()
    jobs = response.json()["data"]

    query_lower = query.lower()
    location_lower = location.lower() if location else None
    cutoff = cutoff_for(date_posted)

    results: list[JobListing] = []
    for job in jobs:
        haystack = " ".join(
            [job.get("title", ""), job.get("company_name", ""), job.get("description", ""), *job.get("tags", [])]
        ).lower()
        if query_lower not in haystack:
            continue

        job_location = job.get("location") or None
        if location_lower and (not job_location or location_lower not in job_location.lower()):
            continue

        posted_at = (
            datetime.fromtimestamp(job["created_at"], tz=timezone.utc) if job.get("created_at") else None
        )
        if cutoff and posted_at and posted_at < cutoff:
            continue

        results.append(
            JobListing(
                external_id=job["slug"],
                source="arbeitnow",
                title=job.get("title", ""),
                company=job.get("company_name") or None,
                location=job_location,
                url=job.get("url", ""),
                posted_at=posted_at,
                description=job.get("description", ""),
            )
        )
    return results