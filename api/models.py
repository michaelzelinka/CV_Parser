from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any


class CVData(BaseModel):
    """Structured data extracted from CV."""
    name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    years_experience: Optional[float]
    technologies: List[str] = []
    languages: List[str] = []
    seniority: Optional[str]


class JDData(BaseModel):
    """Structured data extracted from Job Description."""
    role: Optional[str]
    required_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    seniority: Optional[str]
    min_experience: Optional[float]


class ParsedCVResponse(BaseModel):
    """Final response returned by /parse endpoint."""
    name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    years_experience: Optional[float]
    technologies: List[str] = []
    languages: List[str] = []
    seniority: Optional[str]

    jd_data: Optional[JDData] = None
    match_score: int

    summary: Optional[str] = None   # Summary from LLM
