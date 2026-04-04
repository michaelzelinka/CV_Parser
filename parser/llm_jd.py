import os
import json
import re
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------------------------------------
# ✅ Robust JSON extractor
# -------------------------------------------------------
def extract_json(raw: str):
    raw = raw.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError(f"No JSON found in output: {raw}")
    return json.loads(match.group(0))


# -------------------------------------------------------
# ✅ JD extractor v2.0 — intelligent HR inference
# -------------------------------------------------------
async def extract_structured_jd(text: str):
    prompt = f"""
    You are an expert HR assistant that extracts structured Job Description data
    from ANY natural text (including unstructured job ads, HR marketing text, 
    trainee program descriptions, mixed languages CZ/EN, long paragraphs, etc.)

    Your goal is to infer ALL relevant skills, even if they are not explicitly listed,
    but implied by the text.

    RULES:
    - Extract all technical skills, tools, technologies, methods and software.
    - Extract all soft skills ONLY IF clearly job-related.
    - Identify technologies mentioned anywhere in text including:
      programming languages, SQL, BI, SAP, testing, automation, AI, cloud, data, analysis.
    - From context like "trainee", "graduate", "junior", infer seniority.
    - From context like "trainee" or "graduate", min_experience must be 0–1.
    - If JD talks about IT projects, include general IT fundamentals.
    - If JD lists skills in text sentences (e.g. "oceníme zkušenost s…"), extract them.
    - Output ONLY valid JSON (no commentary).

    JSON KEYS TO RETURN:
    {{
      "role": string,
      "required_skills": array of strings,
      "nice_to_have_skills": array of strings,
      "seniority": one of ["Trainee", "Junior", "Mid", "Senior"],
      "min_experience": float or null
    }}

    JOB DESCRIPTION TEXT:
    {text}
    """

    # Create initial attempt
    response = await client.responses.create(
        model="gpt-4.1",
        input=prompt
    )

    raw = response.output_text

    # Try first extraction
    try:
        return extract_json(raw)
    except Exception:
        # Fallback repair
        fix_prompt = f"Convert the following text into valid JSON only, with the schema described earlier:\n\n{raw}"

        fix_response = await client.responses.create(
            model="gpt-4.1",
            input=fix_prompt
        )

        fixed_raw = fix_response.output_text
        return extract_json(fixed_raw)
