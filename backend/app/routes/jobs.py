from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import JobDescription, User
from app.schemas.job import SavedJobOut
from app.services.job_scraper import JobListing, search_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/search", response_model=list[JobListing])
def search(
    query: str = Query(..., min_length=1),
    location: str | None = Query(None),
    date_posted: str | None = Query(None, pattern="^(24h|3d|7d|30d)$"),
    current_user: User = Depends(get_current_user),
) -> list[JobListing]:
    return search_jobs(query, location, date_posted)


@router.post("/save", response_model=SavedJobOut, status_code=status.HTTP_201_CREATED)
def save_job(
    listing: JobListing,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobDescription:
    existing = db.scalar(
        select(JobDescription).where(
            JobDescription.user_id == current_user.id,
            JobDescription.source == listing.source,
            JobDescription.external_id == listing.external_id,
        )
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Job already saved")

    job_description = JobDescription(
        user_id=current_user.id,
        source=listing.source,
        title=listing.title,
        company=listing.company,
        raw_text=listing.description,
        url=listing.url,
        location=listing.location,
        external_id=listing.external_id,
        posted_at=listing.posted_at,
    )
    db.add(job_description)
    db.commit()
    db.refresh(job_description)
    return job_description