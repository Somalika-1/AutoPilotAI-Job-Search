from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import Resume, User
from app.schemas.resume import ResumeOut
from app.services.resume_parser import UnsupportedFileTypeError, extract_text

router = APIRouter(prefix="/resumes", tags=["resumes"])

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024


@router.post("/upload", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Resume:
    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File too large (max 5MB)")

    try:
        extracted_text = extract_text(file.filename or "", file_bytes)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    if not extracted_text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not extract any text from the uploaded file")

    resume = Resume(
        user_id=current_user.id,
        original_filename=file.filename or "unknown",
        extracted_text=extracted_text,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume
