import os
import json
import re
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------------------------------------
# ✅ Robust JSON extractor (stejně jako v llm_extractor)
# -------------------------------------------------------
def extract_json(raw: str):
    """
    Extract valid JSON from any LLM response.
    Strips markdown, finds first {...}, returns parsed dict.
    """
    if not raw:
        raise ValueError("Empty LLM output")

    # Remove markdown fences
    raw = raw.replace("```json", "").replace("```", "").strip()

    # Find first JSON block
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError(f"No JSON found in LLM output: {raw}")

    json_text = match.group(0)
    return json.loads(json_text)


# -------------------------------------------------------
# ✅ JD extractor using Responses API (input= only)
# -------------------------------------------------------
async def extract_structured_jd(text: str):
    prompt = f"""
    Extract structured Job Description and return ONLY valid JSON.
    Required keys:
    - role
    - required_skills (array)
    - nice_to_have_skills (array)
    - seniority
    - min_experience (float or null)

    JD text:
    {text}
    """

    # ✅ Responses API only accepts "input=", not messages
    response = await client.responses.create(
        model="gpt-4.1",
        input=prompt
    )

    raw = response.output_text

    # First attempt
    try:
        return extract_json(raw)
    except Exception:
        # -------------------------------------------------------
        # ✅ Fallback: ask LLM to convert to valid JSON only
        # -------------------------------------------------------
        fix_prompt = f"Convert this into valid JSON only, no text before or after:\n\n{raw}"

        fix_response = await client.responses.create(
            model="gpt-4.1",
            input=fix_prompt
        )

        fixed_raw = fix_response.output_text
        return extract_json(fixed_raw)
