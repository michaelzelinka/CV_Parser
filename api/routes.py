from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.models import ParsedCVResponse, CVData, JDData
from parser.extract_text import extract_text_from_file
from parser.llm_extractor import extract_structured_cv
from parser.llm_jd import extract_structured_jd

# Sanitizace + skill normalizer v2.0
from parser.sanitizers import (
    normalize_experience,
    normalize_list,
    normalize_email,
    normalize_seniority,
    normalize_language_items,
    normalize_skill_label
)

# Embedding matching v3.0
from parser.matching_v3 import compute_matching_v3

router = APIRouter()


# ---------------------------------------------------------------------
# ✅ Sanitize CV data (RAW + NORMALIZED)
# ---------------------------------------------------------------------
def sanitize_cv_data(data: dict) -> dict:

    # Raw skills used for UI
    raw_skills = normalize_list(data.get("technologies"))

    # Normalized skills used for scoring
    normalized_skills = [normalize_skill_label(t) for t in raw_skills]

    return {
        "name": data.get("name"),
        "email": normalize_email(data.get("email")),
        "phone": data.get("phone"),

        "years_experience": normalize_experience(data.get("years_experience")),

        # ✅ RAW technologies → UI sees these
        "technologies": raw_skills,

        # ✅ NORMALIZED technologies → scoring uses these
        "technologies_normalized": normalized_skills,

        "languages": normalize_language_items(data.get("languages")),
        "seniority": normalize_seniority(data.get("seniority")),
        "last_position": data.get("last_position"),
        "summary": data.get("summary"),
    }


# ---------------------------------------------------------------------
# ✅ Sanitize JD data
# ---------------------------------------------------------------------
def sanitize_jd_data(data: dict) -> dict:
    return {
        "role": data.get("role"),
        "required_skills": normalize_list(data.get("required_skills")),
        "nice_to_have_skills": normalize_list(data.get("nice_to_have_skills")),
        "seniority": normalize_seniority(data.get("seniority")),
        "min_experience": normalize_experience(data.get("min_experience")),
    }


# ---------------------------------------------------------------------
# ✅ MAIN ENDPOINT /parse
# ---------------------------------------------------------------------
@router.post("/parse", response_model=ParsedCVResponse)
async def parse_cv(
    file: UploadFile = File(...),
    jd: str = Form(None)
):
    # ---------------------------------------
    # ✅ Validate file
    # ---------------------------------------
    if not file:
        raise HTTPException(400, "No CV file uploaded.")

    # ---------------------------------------
    # ✅ Extract text from PDF/DOCX
    # ---------------------------------------
    try:
        raw_text = await extract_text_from_file(file)
    except Exception as e:
        raise HTTPException(400, f"Could not read file: {e}")

    if not raw_text or not raw_text.strip():
        raise HTTPException(422, "Unable to extract text from CV. Possibly scanned PDF.")

    # ---------------------------------------
    # ✅ Extract & sanitize CV data via LLM
    # ---------------------------------------
    cv_raw = await extract_structured_cv(raw_text)
    cv_clean = sanitize_cv_data(cv_raw)

    try:
        cv_data = CVData(**cv_clean)
    except Exception as e:
        raise HTTPException(400, f"Invalid CV data: {e}")

    # ---------------------------------------
    # ✅ Extract & sanitize JD (optional)
    # ---------------------------------------
    jd_data = None
    jd_clean = None

    if jd:
        jd_raw = await extract_structured_jd(jd)
        jd_clean = sanitize_jd_data(jd_raw)

        try:
            jd_data = JDData(**jd_clean)
        except Exception as e:
            raise HTTPException(400, f"Invalid JD data: {e}")

    # ---------------------------------------
    # ✅ MATCHING v3.0 (embedding-based)
    # ---------------------------------------
    try:
        score_block = await compute_matching_v3(cv_clean, jd_clean)
        score = score_block["score"]
    except Exception:
        score = 50  # fallback if AI scoring fails

    # ---------------------------------------
    # ✅ Final response
    # ---------------------------------------
    return ParsedCVResponse(
        cv_data=cv_data,      # UI uses RAW technologies
        jd_data=jd_data,
        match_score=score,
        summary=cv_clean.get("summary"),
    )
