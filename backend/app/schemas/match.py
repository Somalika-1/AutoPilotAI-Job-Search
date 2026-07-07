from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MatchCreate(BaseModel):
    resume_id: int
    job_description_text: str


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    job_description_id: int
    score: int
    missing_skills: list[str]
    strengths: list[str]
    cover_letter: str | None
    created_at: datetime
