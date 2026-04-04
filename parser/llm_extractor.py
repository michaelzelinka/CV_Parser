import os
import json
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------
# ✅ Robust JSON extractor
# ---------------------------------------------
def extract_json(raw: str):
    """
    Extracts valid JSON from any LLM response.
    Removes markdown, searches for the first {...} block.
    Returns dict or raises ValueError.
    """
    if not raw:
        raise ValueError("Empty LLM output")

    # Remove backticks & markdown fences
    raw = raw.replace("```json", "").replace("```", "").strip()

    # Find the first JSON object using regex (allows nested structures)
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError(f"No JSON found in LLM output: {raw}")

    json_str = match.group(0)

    return json.loads(json_str)


# ---------------------------------------------
# ✅ Extract structured CV via OpenAI
# ---------------------------------------------
async def extract_structured_cv(text: str):
    prompt = f"""
    Extract structured CV data and return ONLY valid JSON.
    Required keys:
    - name
    - email
    - phone
    - years_experience
    - technologies (array)
    - languages (array)
    - seniority
    - last_position
    - summary (3–5 sentences)

    CV text:
    {text}
    """

    # ✅ Responses API uses ONLY "input", not "messages"
    response = await client.responses.create(
        model="gpt-4.1",
        input=prompt
    )

    raw = response.output_text

    # Try normal JSON extraction
    try:
        return extract_json(raw)
    except Exception:
        # ✅ Repair step — ask the model to reformat into clean JSON
        fix_prompt = f"Convert this into valid JSON only, no text around it:\n\n{raw}"

        fix_response = await client.responses.create(
            model="gpt-4.1",
            input=fix_prompt
        )

        fixed_raw = fix_response.output_text
        return extract_json(fixed_raw)
