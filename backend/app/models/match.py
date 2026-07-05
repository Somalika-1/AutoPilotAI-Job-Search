from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), nullable=False)
    job_description_id: Mapped[int] = mapped_column(ForeignKey("job_descriptions.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    missing_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    strengths: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    resume: Mapped["Resume"] = relationship(back_populates="matches")
    job_description: Mapped["JobDescription"] = relationship(back_populates="matches")
