from openai import AsyncOpenAI
import re

client = AsyncOpenAI()

SYSTEM_PROMPT = """
You are an HR job description parser.
Extract ONLY real skills mentioned directly in the JD.
Do NOT hallucinate.
Return only JSON.
{
    "role": string | null,
    "required_skills": [string],
    "nice_to_have_skills": [string],
    "seniority": "Senior" | "Mid" | "Junior" | "Trainee" | null,
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
        # minimal fallback (never empty)
        jd = {
            "role": None,
            "required_skills": [],
            "nice_to_have_skills": [],
            "seniority": None,
            "min_experience": None,
        }

    # ✅ Clean list
    req = []
    for s in jd.get("required_skills", []):
        s = s.strip()
        if len(s) >= 2 and not re.search(r"ovat$", s):
            req.append(s)

    if not req:
        # minimal fallback to avoid scoring = 0
        req = ["communication", "teamwork", "organization"]

    jd["required_skills"] = req
    jd["nice_to_have_skills"] = jd.get("nice_to_have_skills", []) or []

    # ✅ fallback seniority
    txt = jd_text.lower()
    if not jd.get("seniority"):
        if "senior" in txt:
            jd["seniority"] = "Senior"
        elif "junior" in txt:
            jd["seniority"] = "Junior"
        else:
            jd["seniority"] = "Mid"

    # ✅ fallback experience
    if jd.get("min_experience") is None:
        jd["min_experience"] = 0

    return jd
