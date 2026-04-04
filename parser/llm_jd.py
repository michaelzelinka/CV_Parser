import os
import json
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def extract_structured_jd(text: str):
    prompt = f"""
    Extract structured Job Description data and return ONLY valid JSON.
    Required JSON keys:
    role,
    required_skills,
    nice_to_have_skills,
    seniority,
    min_experience.

    JD text:
    {text}
    """

    response = await client.responses.create(
        model="gpt-4.1",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.output_text

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
