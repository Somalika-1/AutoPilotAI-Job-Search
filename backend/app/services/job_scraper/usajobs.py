from datetime import datetime

import httpx

from app.config import settings
from app.services.job_scraper.date_filters import days_for
from app.services.job_scraper.schemas import JobListing

USAJOBS_URL = "https://data.usajobs.gov/api/search"


def search(query: str, location: str | None = None, date_posted: str | None = None) -> list[JobListing]:
    if not settings.usajobs_api_key or not settings.usajobs_user_agent:
        return []  # no key configured yet - treat like an unconfigured, skippable provider

    params: dict[str, str | int] = {"Keyword": query}
    if location:
        params["LocationName"] = location
    days = days_for(date_posted)
    if days is not None:
        params["DatePosted"] = days

    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": settings.usajobs_user_agent,
        "Authorization-Key": settings.usajobs_api_key,
    }
    response = httpx.get(USAJOBS_URL, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    items = response.json().get("SearchResult", {}).get("SearchResultItems", [])

    results: list[JobListing] = []
    for item in items:
        descriptor = item.get("MatchedObjectDescriptor", {})
        posted_at = (
            datetime.fromisoformat(descriptor["PublicationStartDate"])
            if descriptor.get("PublicationStartDate")
            else None
        )
        results.append(
            JobListing(
                external_id=str(item.get("MatchedObjectId") or descriptor.get("PositionID", "")),
                source="usajobs",
                title=descriptor.get("PositionTitle", ""),
                company=descriptor.get("OrganizationName") or None,
                location=descriptor.get("PositionLocationDisplay") or None,
                url=descriptor.get("PositionURI", ""),
                posted_at=posted_at,
                description=descriptor.get("UserArea", {}).get("Details", {}).get("JobSummary", ""),
            )
        )
    return results