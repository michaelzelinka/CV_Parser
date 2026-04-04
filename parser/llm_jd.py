import os
import json
import re
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_json(raw: str):
    raw = raw.strip().replace("```json", "").replace("```", "")
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group(0))


async def extract_structured_jd(text: str):
    prompt = f"""
    Extract JD data and return ONLY pure JSON.
    Required keys:
    role, required_skills, nice_to_have_skills, seniority, min_experience.

    JD text:
    {text}
    """

    response = await client.responses.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.output_text

    try:
        return extract_json(raw)
    except:
        fix_prompt = f"Fix this into valid JSON only: {raw}"

        fix_response = await client.responses.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": fix_prompt}]
        )
        return extract_json(fix_response.output_text)
