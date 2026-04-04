from pydantic import BaseModel, EmailStr
from typing import List, Optional


class CVData(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    years_experience: Optional[float]
    technologies: List[str] = []
    languages: List[str] = []
    seniority: Optional[str]
    last_position: Optional[str]


class JDData(BaseModel):
    role: Optional[str]
    required_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    seniority: Optional[str]
    min_experience: Optional[float]


class ParsedCVResponse(BaseModel):
    cv_data: CVData
    jd_data: Optional[JDData]
    match_score: int
    summary: Optional[str]
