import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def extract_structured_cv(text: str):
    prompt = """
    Extract structured CV data from the following text.
    Return a VALID JSON object with fields:
    - name
    - email
    - phone
    - years_experience
    - technologies (list)
    - languages (list)
    - seniority
    - last_position
    - summary (3–5 sentences)
    """

    response = await client.responses.create(
        model="gpt-4.1",
        input=[
            {"type": "input_text", "text": prompt},
            {"type": "input_text", "text": text}
        ]
    )

    return json.loads(response.output_text)
