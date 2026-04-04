from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.models import ParsedCVResponse, CVData, JDData

# Text extraction
from parser.extract_text import extract_text_from_file

# LLM extractors
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

# CV validity checker
from parser.cv_validity import is_probably_cv

# ✅ scoring v7 LIGHT — stále se jmenuje compute_matching_v5
from parser.matching_v5 import compute_matching_v5


router = APIRouter()


# ==============================================================================
# ✅ SANITIZATION HELPERS
# ==============================================================================
def sanitize_cv_data(data: dict) -> dict:
    """Normalize raw CV JSON from LLM into a safe structure"""

    raw_skills = normalize_list(data.get("technologies"))
    normalized_skills = [normalize_skill_label(s) for s in raw_skills]

    return {
        "name": data.get("name"),
        "email": normalize_email(data.get("email")),
        "phone": data.get("phone"),

        "years_experience": normalize_experience(data.get("years_experience")),

        # Raw for UI
        "technologies": raw_skills,

        # Normalized for scoring
        "technologies_normalized": normalized_skills,

        "languages": normalize_language_items(data.get("languages")),
        "seniority": normalize_seniority(data.get("seniority")),
        "last_position": data.get("last_position"),
        "summary": data.get("summary"),
    }


def sanitize_jd_data(data: dict) -> dict:
    """Normalize JD JSON from LLM into consistent scoring structure"""

    return {
        "role": data.get("role"),
        "required_skills": normalize_list(data.get("required_skills")),
        "nice_to_have_skills": normalize_list(data.get("nice_to_have_skills")),
        "seniority": normalize_seniority(data.get("seniority")),
        "min_experience": normalize_experience(data.get("min_experience")),
    }


# ==============================================================================
# ✅ MAIN ENDPOINT: /parse
# ==============================================================================
@router.post("/parse", response_model=ParsedCVResponse)
async def parse_cv(
    file: UploadFile = File(...),
    jd: str = Form(None),
):
    # ------------------------------------------------------------
    # ✅ Validate input
    # ------------------------------------------------------------
    if not file:
        raise HTTPException(400, "No CV file uploaded.")

    # ------------------------------------------------------------
    # ✅ Extract CV text
    # ------------------------------------------------------------
    try:
        raw_text = await extract_text_from_file(file)
    except Exception as e:
        raise HTTPException(400, f"Could not read file: {e}")

    if not raw_text or not raw_text.strip():
        raise HTTPException(422, "Unable to extract text (possibly scanned).")

    # ------------------------------------------------------------
    # ✅ Parse CV using LLM
    # ------------------------------------------------------------
    cv_raw = await extract_structured_cv(raw_text)
    cv_clean = sanitize_cv_data(cv_raw)

    try:
        cv_data = CVData(**cv_clean)
    except Exception as e:
        raise HTTPException(400, f"Invalid CV structure: {e}")

    # ------------------------------------------------------------
    # ✅ Parse JD (optional)
    # ------------------------------------------------------------
    jd_clean = None
    jd_data = None

    if jd:
        jd_raw = await extract_structured_jd(jd)
        jd_clean = sanitize_jd_data(jd_raw)

        try:
            jd_data = JDData(**jd_clean)
        except Exception as e:
            raise HTTPException(400, f"Invalid JD structure: {e}")

    # ------------------------------------------------------------
    # ✅ CV VALIDITY CHECK
    # ------------------------------------------------------------
    if not is_probably_cv(raw_text, cv_clean):
        return ParsedCVResponse(
            cv_data=cv_data,
            jd_data=jd_data,
            match_score=0,
            summary="⚠️ Document does not appear to be a CV.",
            details={"reason": "non_cv_document"},
        )

    # ------------------------------------------------------------
    # ✅ SCORING — v7 LIGHT (named compute_matching_v5)
    # ------------------------------------------------------------
    try:
        scoring = await compute_matching_v5(cv_clean, jd_clean)
        score = scoring["score"]
        details = scoring["details"]
    except Exception as e:
        score = 0
        details = {"error": str(e)}

    # ------------------------------------------------------------
    # ✅ FINAL RESPONSE
    # ------------------------------------------------------------
    return ParsedCVResponse(
        cv_data=cv_data,
        jd_data=jd_data,
        match_score=score,
        summary=cv_clean.get("summary"),
        details=details,
    )
