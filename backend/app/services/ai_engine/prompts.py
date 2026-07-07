SYSTEM_PROMPT = (
    "You are a resume screening assistant. Compare the candidate's resume against "
    "the job description and assess how well they match. Be specific and concrete "
    "about missing skills and strengths - reference actual technologies, tools, or "
    "experience mentioned (or absent) in the resume."
)

COVER_LETTER_SYSTEM_PROMPT = (
    "You are a professional cover letter writer. Write a concise, tailored cover letter "
    "for the candidate based on their resume and the job description below. Reference "
    "specific, real experience from the resume - do not invent skills or history that "
    "aren't there. Return only the cover letter body text: no subject line, no "
    "placeholder brackets like [Company Name], no preamble before or after it."
)


def build_match_prompt(resume_text: str, job_description_text: str) -> str:
    return f"Resume:\n{resume_text}\n\nJob Description:\n{job_description_text}"


def build_cover_letter_prompt(resume_text: str, job_description_text: str) -> str:
    return f"Resume:\n{resume_text}\n\nJob Description:\n{job_description_text}"
