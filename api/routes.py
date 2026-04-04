from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.models import ParsedCVResponse, CVData, JDData
from parser.extract_text import extract_text_from_file
from parser.llm_extractor import extract_structured_cv
from parser.llm_jd import extract_structured_jd
from parser.matching import compute_match_score

router = APIRouter()


@router.post("/parse", response_model=ParsedCVResponse)
async def parse_cv(
    file: UploadFile = File(...),
    jd: str = Form(None)
):
    if not file:
        raise HTTPException(status_code=400, detail="No CV file uploaded.")

    # Extract raw text from PDF/DOCX
    raw_text = await extract_text_from_file(file)

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Unable to extract text from file.")

    # Extract CV structured data
    cv_dict = await extract_structured_cv(raw_text)
    cv_data = CVData(**cv_dict)

    # Extract JD structured data (optional)
    jd_data = None
    if jd:
        jd_dict = await extract_structured_jd(jd)
        jd_data = JDData(**jd_dict)

    # Compute match score
    score = compute_match_score(
        cv_data.dict(),
        jd_data.dict() if jd_data else None
    )

    return ParsedCVResponse(
        cv_data=cv_data,
        jd_data=jd_data,
        match_score=score,
        summary=cv_dict.get("summary")
    )
