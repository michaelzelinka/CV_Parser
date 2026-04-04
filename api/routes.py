from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.models import ParsedCVResponse, CVData, JDData
from parser.extract_text import extract_text_from_file
from parser.llm_extractor import extract_structured_cv
from parser.llm_jd import extract_structured_jd


router = APIRouter()


# ---------------------------------------
# ✅ Helper functions
# ---------------------------------------

def safe_float(value):
    """Convert LLM outputs to float where possible."""
    if value is None:
        return None
    try:
        return float(value)
    except:
        return None


def ensure_list(value):
    """Make sure value is always a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # split string lists: "Python, SQL" → ["Python", "SQL"]
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


def sanitize_cv_data(data: dict):
    """Fix typical LLM errors before inserting into CVData model."""
    data["years_experience"] = safe_float(data.get("years_experience"))
    data["technologies"] = ensure_list(data.get("technologies"))
    data["languages"] = ensure_list(data.get("languages"))

    # Ensure email is string even if LLM returns null
    email = data.get("email")
    data["email"] = email if isinstance(email, str) else None

    return data


def sanitize_jd_data(data: dict):
    """Fix JDData values so Pydantic won't crash."""
    data["required_skills"] = ensure_list(data.get("required_skills"))
    data["nice_to_have_skills"] = ensure_list(data.get("nice_to_have_skills"))
    data["min_experience"] = safe_float(data.get("min_experience"))
    return data


# ---------------------------------------
# ✅ Main endpoint
# ---------------------------------------

@router.post("/parse", response_model=ParsedCVResponse)
async def parse_cv(
    file: UploadFile = File(...),
    jd: str = Form(None)
):
    # ✅ Check file exists
    if not file:
        raise HTTPException(status_code=400, detail="No CV file uploaded.")

    # ✅ Extract raw text from PDF/DOCX
    try:
        raw_text = await extract_text_from_file(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {e}")

    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=422, detail="Unable to extract text from CV.")

    # ✅ Extract structured CV with LLM
    cv_raw = await extract_structured_cv(raw_text)
    cv_clean = sanitize_cv_data(cv_raw)

    try:
        cv_data = CVData(**cv_clean)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CV data: {e}")

    # ✅ Extract JD (optional)
    jd_data = None
    if jd:
        jd_raw = await extract_structured_jd(jd)
        jd_clean = sanitize_jd_data(jd_raw)

        try:
            jd_data = JDData(**jd_clean)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JD data: {e}")

    # ✅ Compute match score manually here to avoid circular imports
    score = 50  # default

    try:
        # simple scoring logic
        cv_skills = set(cv_clean.get("technologies", []))
        jd_skills = set(jd_clean.get("required_skills", [])) if jd_data else set()

        score = 0

        # Skills: 40%
        if jd_skills:
            overlap = len(cv_skills & jd_skills) / len(jd_skills)
            score += overlap * 40

        # Experience: 30%
        req_exp = jd_clean.get("min_experience") if jd_data else None
        cv_exp = cv_clean.get("years_experience")

        if req_exp and cv_exp:
            score += min(cv_exp / req_exp, 1) * 30

        # Seniority: 30%
        if jd_data and cv_clean.get("seniority") == jd_clean.get("seniority"):
            score += 30

        score = round(score)

    except Exception:
        score = 50  # fallback

    # ✅ Final response
    return ParsedCVResponse(
        cv_data=cv_data,
        jd_data=jd_data,
        match_score=score,
        summary=cv_clean.get("summary")
    )
