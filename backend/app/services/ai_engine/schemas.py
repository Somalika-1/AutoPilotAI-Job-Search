from pydantic import BaseModel, Field


class MatchResult(BaseModel):
    score: int = Field(ge=0, le=100)
    missing_skills: list[str]
    strengths: list[str]


class CoverLetterResult(BaseModel):
    cover_letter: str
