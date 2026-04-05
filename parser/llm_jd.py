from openai import AsyncOpenAI

client = AsyncOpenAI()

SYSTEM_PROMPT = """
You extract ALL technologies, tools, platforms, frameworks, and systems mentioned in a job description.

Extract ONLY the following:
- tech_stack: list of technologies from the text (Python, Kubernetes, AWS, Redis…)
- required_skills: same as tech_stack (duplicate for scoring)
- seniority: based ONLY on words (junior, mid, senior)
- min_experience: years if mentioned
- role: job title if present

Do NOT be conservative. If the JD mentions Kubernetes, Python, or GCP ANYWHERE — include it.
Do NOT return soft skills unless they are explicitly mentioned.
Return valid JSON:
{
  "role": string | null,
  "required_skills": [string],
  "tech_stack": [string],
  "seniority": "Junior" | "Mid" | "Senior" | null,
  "min_experience": number | null
}
"""

async def extract_structured_jd(jd_text: str) -> dict:
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": jd_text}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        jd = resp.choices[0].message.parsed

    except Exception:
        return {
            "role": None,
            "required_skills": [],
            "tech_stack": [],
            "seniority": None,
            "min_experience": None
        }

    # Fallbacks
    if not jd.get("tech_stack"):
        jd["tech_stack"] = []

    jd["required_skills"] = jd["tech_stack"]

    if jd.get("seniority") is None:
        if "senior" in jd_text.lower():
            jd["seniority"] = "Senior"
        elif "junior" in jd_text.lower():
            jd["seniority"] = "Junior"
        else:
            jd["seniority"] = "Mid"

    if jd.get("min_experience") is None:
        jd["min_experience"] = 0

    return jd
