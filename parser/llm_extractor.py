import os
import json
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_json(raw: str):
    """
    Robust JSON extraction from any text returned by LLM.
    Removes markdown, extracts first {...} block, and tries to load JSON.
    """
    # remove markdown blocks
    raw = raw.strip()
    raw = raw.replace("```json", "").replace("```", "")

    # find json braces
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError("No JSON found in LLM response")

    json_text = match.group(0)

    return json.loads(json_text)


async def extract_structured_cv(text: str):
    prompt = f"""
    Extract structured CV data and return ONLY pure JSON.
    Required keys:
    name, email, phone, years_experience,
    technologies, languages, seniority,
    last_position, summary.

    CV text:
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
        return extract_json(raw)
    except Exception:
        # ask model to fix JSON
        fix_prompt = f"Fix this into valid JSON only, no text: {raw}"

        fix_response = await client.responses.create(
            model="gpt-4.1",
            messages=[
                {"role": "user", "content": fix_prompt}
            ]
        )

        fixed_raw = fix_response.output_text

        return extract_json(fixed_raw)
