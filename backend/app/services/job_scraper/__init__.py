import httpx

from app.services.job_scraper import adzuna, arbeitnow, remoteok, usajobs
from app.services.job_scraper.schemas import JobListing


def search_jobs(query: str, location: str | None = None, date_posted: str | None = None) -> list[JobListing]:
    results: list[JobListing] = []
    for provider in (remoteok, arbeitnow, adzuna, usajobs):
        try:
            results.extend(provider.search(query, location, date_posted))
        except httpx.HTTPError:
            continue
    return results


__all__ = ["search_jobs", "JobListing"]