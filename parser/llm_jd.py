from openai import AsyncOpenAI

client = AsyncOpenAI()

SYSTEM_PROMPT = """
Extract ALL technologies, tools, platforms, frameworks, or systems explicitly mentioned in a job description.

Examples:
- Python, Kubernetes, AWS, Docker, SAP, CRM systems, EPIC, EHR
- bookkeeping, patient care documentation
- Excel, Power BI, accounting software
- cash register, point-of-sale systems

Return JSON:
{
  "required_skills": [string],
  "tech_stack": [string],
  "seniority": "Junior" | "Mid" | "Senior" | null
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
            response_format={"type": "json_object"},
            temperature=0
        )
        jd = resp.choices[0].message.parsed

    except Exception:
        return {
            "required_skills": [],
            "tech_stack": [],
            "seniority": None
        }

    if not jd.get("tech_stack"):
        jd["tech_stack"] = []

    if not jd.get("required_skills"):
        jd["required_skills"] = jd["tech_stack"]

    text = jd_text.lower()
    if not jd.get("seniority"):
        if "senior" in text or "lead" in text:
            jd["seniority"] = "Senior"
        elif "junior" in text:
            jd["seniority"] = "Junior"
        else:
            jd["seniority"] = "Mid"

    return jd
