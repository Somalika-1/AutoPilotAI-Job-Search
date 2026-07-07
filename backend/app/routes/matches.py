from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import JobDescription, Match, Resume, User
from app.schemas.match import MatchCreate, MatchOut
from app.services.ai_engine import generate_cover_letter, score_resume_against_job

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("", response_model=MatchOut, status_code=status.HTTP_201_CREATED)
def create_match(
    payload: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Match:
    resume = db.get(Resume, payload.resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resume not found")

    job_description = JobDescription(
        user_id=current_user.id,
        source="manual",
        raw_text=payload.job_description_text,
    )
    db.add(job_description)
    db.commit()
    db.refresh(job_description)

    try:
        result = score_resume_against_job(resume.extracted_text, job_description.raw_text)
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "AI matching service is unavailable") from exc

    match = Match(
        resume_id=resume.id,
        job_description_id=job_description.id,
        score=result.score,
        missing_skills=result.missing_skills,
        strengths=result.strengths,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.post("/{match_id}/cover-letter", response_model=MatchOut)
def create_cover_letter(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Match:
    match = db.get(Match, match_id)
    if match is None or match.resume.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Match not found")

    try:
        result = generate_cover_letter(match.resume.extracted_text, match.job_description.raw_text)
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "AI cover letter service is unavailable") from exc

    match.cover_letter = result.cover_letter
    db.commit()
    db.refresh(match)
    return match
