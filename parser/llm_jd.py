import json
from openai import AsyncOpenAI
import os

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def extract_structured_jd(text: str):
    prompt = """
    Extract structured Job Description fields.
    Return JSON with:
    - role
    - required_skills
    - nice_to_have_skills
    - seniority
    - min_experience
    """

    response = await client.responses.create(
        model="gpt-4.1",
        input=[
            {"type": "input_text", "text": prompt},
            {"type": "input_text", "text": text}
        ]
    )

    return json.loads(response.output_text)
