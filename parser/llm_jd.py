import os
import json
import re
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_json(raw: str):
    raw = raw.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError(f"No JSON found in output: {raw}")
    return json.loads(match.group(0))


async def extract_structured_jd(text: str):
    prompt = f"""
    You are an expert HR assistant extracting structured Job Description data from any text,
    including unstructured job ads and Czech/English descriptions.

    Your job is to INFER ALL relevant technical skills even if they are not listed as bullet points.

    RULES:
    - Extract ALL technologies, tools, software, skills mentioned anywhere.
    - Extract skills from narrative text like “oceníme zkušenosti s…”.
    - Infer implicit IT skills from context (IT environment = IT fundamentals).
    - Identify trainee/junior roles from context.
    - Determine seniority from text (Trainee, Junior, Mid, Senior).
    - Determine min_experience from text:
        - Trainee, graduate → 0
        - Junior → 0–1
        - Others if explicit

    RETURN JSON ONLY:
    {{
        "role": "...",
        "required_skills": [...],
        "nice_to_have_skills": [...],
        "seniority": "...",
        "min_experience": 0
    }}

    JOB DESCRIPTION:
    {text}
    """

    response = await client.responses.create(
        model="gpt-4.1",
        input=prompt
    )

    raw = response.output_text

    try:
        return extract_json(raw)
    except Exception:
        fix_prompt = f"Convert into valid JSON only:\n\n{raw}"
        fix_response = await client.responses.create(
            model="gpt-4.1",
            input=fix_prompt
        )
        return extract_json(fix_response.output_text)
