from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.models import ParsedCVResponse, CVData, JDData
from parser.extract_text import extract_text_from_file
from parser.llm_extractor import extract_structured_cv
from parser.llm_jd import extract_structured_jd

# ✅ SANITIZERS (verze 1.1)
from parser.sanitizers import (
    normalize_experience,
    normalize_list,
    normalize_email,
    normalize_seniority,
    normalize_language_items,
)


router = APIRouter()


# ---------------------------------------------------------------------
# ✅ Sanitize CV data
# ---------------------------------------------------------------------
def sanitize_cv_data(data: dict) -> dict:
    return {
        "name": data.get("name"),
        "email": normalize_email(data.get("email")),
        "phone": data.get("phone"),

        # years: 5, "5 let", "pět let", "2020–2025", "around 3"
        "years_experience": normalize_experience(data.get("years_experience")),

        # technologies: "Python, SQL" → ["Python","SQL"]
        "technologies": normalize_list(data.get("technologies")),

        # languages: dicts, mixed formats → ["čeština (native)", "angličtina (B2)"]
        "languages": normalize_language_items(data.get("languages")),

        "seniority": normalize_seniority(data.get("seniority")),
        "last_position": data.get("last_position"),

        # summary může být None
        "summary": data.get("summary")
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
# ✅ MAIN ENDPOINT: /parse
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
        raise HTTPException(status_code=400, detail=f"Invalid CV data: {e}")

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
            raise HTTPException(status_code=400, detail=f"Invalid JD data: {e}")

    # ---------------------------------------
    # ✅ MATCHING 1.0 (jednoduchý)
    # ---------------------------------------
    # aby fungoval i s minimem dat

    score = 50  # default neutral

    try:
        score = 0

        # SKILLS — 40 %
        cv_skills = set(cv_clean["technologies"])
        jd_required = set(jd_clean["required_skills"]) if jd_clean else set()

        if jd_required:
            overlap = len(cv_skills & jd_required) / len(jd_required)
            score += overlap * 40

        # EXPERIENCE — 30 %
        cv_exp = cv_clean["years_experience"]
        jd_exp = jd_clean["min_experience"] if jd_clean else None

        if cv_exp and jd_exp:
            score += min(cv_exp / jd_exp, 1.0) * 30

        # SENIORITY — 30 %
        if jd_clean and cv_clean["seniority"] == jd_clean["seniority"]:
            score += 30

        score = int(round(min(score, 100)))

    except Exception:
        score = 50  # fallback

    # ---------------------------------------
    # ✅ Final response
    # ---------------------------------------
    return ParsedCVResponse(
        cv_data=cv_data,
        jd_data=jd_data,
        match_score=score,
        summary=cv_clean.get("summary")
    )
