from datetime import datetime

import httpx

from app.services.job_scraper.date_filters import cutoff_for
from app.services.job_scraper.schemas import JobListing

REMOTEOK_URL = "https://remoteok.com/api"


def search(query: str, location: str | None = None, date_posted: str | None = None) -> list[JobListing]:
    response = httpx.get(REMOTEOK_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    response.raise_for_status()
    jobs = response.json()

    query_lower = query.lower()
    location_lower = location.lower() if location else None
    cutoff = cutoff_for(date_posted)

    results: list[JobListing] = []
    for job in jobs:
        if "id" not in job:
            continue  # the first item in RemoteOK's feed is a legal notice, not a job

        haystack = " ".join(
            [job.get("position", ""), job.get("company", ""), job.get("description", ""), *job.get("tags", [])]
        ).lower()
        if query_lower not in haystack:
            continue

        job_location = job.get("location") or None
        if location_lower and (not job_location or location_lower not in job_location.lower()):
            continue

        posted_at = datetime.fromisoformat(job["date"]) if job.get("date") else None
        if cutoff and posted_at and posted_at < cutoff:
            continue

        results.append(
            JobListing(
                external_id=str(job["id"]),
                source="remoteok",
                title=job.get("position", ""),
                company=job.get("company") or None,
                location=job_location,
                url=job.get("url") or job.get("apply_url", ""),
                posted_at=posted_at,
                description=job.get("description", ""),
            )
        )
    return results