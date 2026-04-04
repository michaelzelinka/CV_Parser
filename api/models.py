from pydantic import BaseModel
from typing import List, Optional


class CVData(BaseModel):
    """
    Structured data extracted from a CV.
    Values are intentionally tolerant because LLMs are inconsistent.
    Sanitization happens in routes.py before this model is created.
    """

    name: Optional[str] = None
    email: Optional[str] = None              # was EmailStr → too strict
    phone: Optional[str] = None
    years_experience: Optional[float] = None
    technologies: List[str] = []
    languages: List[str] = []
    seniority: Optional[str] = None
    last_position: Optional[str] = None


class JDData(BaseModel):
    """
    Structured Job Description data.
    Tolerant defaults—LLM often returns strings instead of floats.
    Sanitized in routes.py before model initialization.
    """

    role: Optional[str] = None
    required_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    seniority: Optional[str] = None
    min_experience: Optional[float] = None   # string → float sanitization in routes.py


class ParsedCVResponse(BaseModel):
    """
    Final response returned to the frontend UI.
    """

    cv_data: CVData
    jd_data: Optional[JDData] = None
    match_score: int
    summary: Optional[str] = None
