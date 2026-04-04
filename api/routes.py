from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.models import ParsedCVResponse, CVData, JDData
from parser.extract_text import extract_text_from_file
from parser.llm_extractor import extract_structured_cv
from parser.llm_jd import extract_structured_jd

# Sanitizers
from parser.sanitizers import (
    normalize_experience,
    normalize_list,
    normalize_email,
    normalize_seniority,
    normalize_language_items,
    normalize_skill_label,
)

# CV validity
from parser.cv_validity import is_probably_cv

# ✅ MATCHING v5
from parser.matching_v5 import compute_matching_v5

router = APIRouter()


# =====================================================================
# ✅ CV SANITIZATION
# =====================================================================
def sanitize_cv_data(data: dict) -> dict:
    raw_skills = normalize_list(data.get("technologies"))
    normalized_skills = [normalize_skill_label(t) for t in raw_skills]

    return {
        "name": data.get("name"),
        "email": normalize_email(data.get("email")),
        "phone": data.get("phone"),
        "years_experience": normalize_experience(data.get("years_experience")),
        "technologies": raw_skills,                     # UI raw
        "technologies_normalized": normalized_skills,   # scoring
        "languages": normalize_language_items(data.get("languages")),
        "seniority": normalize_seniority(data.get("seniority")),
        "last_position": data.get("last_position"),
        "summary": data.get("summary"),
    }


# =====================================================================
# ✅ JD SANITIZATION
# =====================================================================
def sanitize_jd_data(data: dict) -> dict:
    return {
        "role": data.get("role"),
        "required_skills": normalize_list(data.get("required_skills")),
        "nice_to_have_skills": normalize_list(data.get("nice_to_have_skills")),
        "seniority": normalize_seniority(data.get("seniority")),
        "min_experience": normalize_experience(data.get("min_experience")),
    }


# =====================================================================
# ✅ /parse ENDPOINT
# =====================================================================
@router.post("/parse", response_model=ParsedCVResponse)
async def parse_cv(
    file: UploadFile = File(...),
    jd: str = Form(None)
):
    # 1) Validate file
    if not file:
        raise HTTPException(400, "No CV file uploaded.")

    # 2) Extract text
    try:
        raw_text = await extract_text_from_file(file)
    except Exception as e:
        raise HTTPException(400, f"Could not read file: {e}")

    if not raw_text or not raw_text.strip():
        raise HTTPException(422, "Unable to extract text – maybe scanned PDF.")

    # 3) Extract CV (LLM)
    cv_raw = await extract_structured_cv(raw_text)
    cv_clean = sanitize_cv_data(cv_raw)

    try:
        cv_data = CVData(**cv_clean)
    except Exception as e:
        raise HTTPException(400, f"Invalid CV data: {e}")

    # 4) Extract JD (optional)
    jd_clean = None
    jd_data = None

    if jd:
        jd_raw = await extract_structured_jd(jd)
        jd_clean = sanitize_jd_data(jd_raw)

        try:
            jd_data = JDData(**jd_clean)
        except Exception as e:
            raise HTTPException(400, f"Invalid JD data: {e}")

    # 5) ✅ CV VALIDITY CHECK
    if not is_probably_cv(raw_text, cv_clean):
        return ParsedCVResponse(
            cv_data=cv_data,
            jd_data=jd_data,
            match_score=0,
            summary="⚠️ This document does not appear to be a CV.",
            details={"reason": "non_cv_document"}
        )

    # 6) ✅ AI MATCHING v5
    try:
        scoring = await compute_matching_v5(cv_clean, jd_clean)
        score = scoring["score"]
        details = scoring["details"]
    except Exception as e:
        score = 50
        details = {"error": str(e)}

    # 7) FINAL RESPONSE
    return ParsedCVResponse(
        cv_data=cv_data,
        jd_data=jd_data,
        match_score=score,
        summary=cv_clean.get("summary"),
        details=details
    )
