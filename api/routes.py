from fastapi import APIRouter, UploadFile, File, Form
from api.models import ParsedCVResponse
from parser.extract_text import extract_text_from_file
from parser.llm_extractor import extract_structured_cv, extract_structured_jd
from parser.matching import compute_match_score

router = APIRouter()

@router.post("/parse", response_model=ParsedCVResponse)
async def parse_cv(
    file: UploadFile = File(...),
    jd: str = Form(None)
):
    raw_text = await extract_text_from_file(file)
    cv_data = await extract_structured_cv(raw_text)

    jd_data = await extract_structured_jd(jd) if jd else {}

    score = compute_match_score(cv_data, jd_data)

    return {
        **cv_data,
        "match_score": score,
        "jd_data": jd_data,
    }
