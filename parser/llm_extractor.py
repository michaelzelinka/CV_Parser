import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def extract_structured_cv(text: str):
    prompt = f"""
    Extract structured CV data from the following text and return ONLY valid JSON.
    Required JSON keys:
    name,
    email,
    phone,
    years_experience,
    technologies,
    languages,
    seniority,
    last_position,
    summary.

    CV text:
    {text}
    """

    response = await client.responses.create(
        model="gpt-4.1",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # response.output_text contains the assistant message text
    raw = response.output_text

    # try to load JSON
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # fallback: attempt to extract JSON between braces
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
``
