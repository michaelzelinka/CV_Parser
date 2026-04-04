import os
import json
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_json(raw: str):
    raw = raw.strip().replace("```json", "").replace("```", "")
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError("No JSON found in LLM output")
    return json.loads(match.group(0))


async def extract_structured_cv(text: str):
    prompt = f"""
    Extract structured CV data and return ONLY valid JSON with keys:
    name, email, phone, years_experience,
    technologies, languages, seniority,
    last_position, summary.

    CV text:
    {text}
    """

    # ✅ Responses API uses input=, not messages=
    response = await client.responses.create(
        model="gpt-4.1",
        input=prompt
    )

    raw = response.output_text

    # Attempt JSON decoding
    try:
        return extract_json(raw)
    except Exception:
        # ask model to fix JSON
        fix_prompt = f"Fix this into valid JSON only, no text: {raw}"
        fix_response = await client.responses.create(
            model="gpt-4.1",
            input=fix_prompt
        )
        return extract_json(fix_response.output_text)
