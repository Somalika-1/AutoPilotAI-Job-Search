from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SavedJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    title: str | None
    company: str | None
    location: str | None
    url: str | None
    posted_at: datetime | None
    raw_text: str
    created_at: datetime