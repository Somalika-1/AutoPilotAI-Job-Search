from datetime import datetime

from pydantic import BaseModel


class JobListing(BaseModel):
    external_id: str
    source: str
    title: str
    company: str | None
    location: str | None
    url: str
    posted_at: datetime | None
    description: str