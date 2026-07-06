from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    extracted_text: str
    uploaded_at: datetime
