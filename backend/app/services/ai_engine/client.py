from google import genai
from google.genai import types

from app.config import settings
from app.services.ai_engine.prompts import (
    COVER_LETTER_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_cover_letter_prompt,
    build_match_prompt,
)
from app.services.ai_engine.schemas import CoverLetterResult, MatchResult

_client: genai.Client | None = None


def get_gemini_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def score_resume_against_job(resume_text: str, job_description_text: str) -> MatchResult:
    client = get_gemini_client()
    prompt = build_match_prompt(resume_text, job_description_text)

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=MatchResult,
        ),
    )

    result = response.parsed
    if not isinstance(result, MatchResult):
        raise ValueError("Gemini response did not match the expected schema")
    return result


def generate_cover_letter(resume_text: str, job_description_text: str) -> CoverLetterResult:
    client = get_gemini_client()
    prompt = build_cover_letter_prompt(resume_text, job_description_text)

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=COVER_LETTER_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=CoverLetterResult,
        ),
    )

    result = response.parsed
    if not isinstance(result, CoverLetterResult):
        raise ValueError("Gemini response did not match the expected schema")
    return result
