from openai import AsyncOpenAI
import re

client = AsyncOpenAI()

SYSTEM_PROMPT = """
You are an HR job description parser.

Extract two layers from the JD:

1) required_skills  = explicit REQUIREMENTS (must-have)
2) tech_stack       = all technologies, tools, platforms, or systems mentioned anywhere in the JD

This must work for ALL job categories:
- healthcare (nurses, doctors)
- administration
- finance & accounting
- customer service
- hospitality
- manufacturing, warehouse
- retail
- marketing & sales
- IT & technical roles
- management & leadership

RULES:
1) Extract ONLY skills explicitly or implicitly present in the text.
2) Do NOT hallucinate.
3) Extract ALL technologies (Kubernetes, SAP, CRM systems, X-ray equipment, Python…)
4) Extract ALL tools and platforms (EPIC, SAP, Salesforce, etc.)
5) Extract ALL domain skills (patient care, bookkeeping, logistics operations…)
6) Extract ALL soft skills if mentioned or implied (communication, teamwork…)
7) Seniority must be based on keywords.
8) min_experience = number of years if mentioned.
9) role = job title if present.

Return ONLY valid JSON in this structure:
{
  "role": string | null,
  "required_skills": [string],
  "tech_stack": [string],
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
        return {
            "role": None,
            "required_skills": [],
            "tech_stack": [],
            "nice_to_have_skills": [],
            "seniority": None,
            "min_experience": None
        }

    # ✅ Clean required skills
    req = []
    for s in jd.get("required_skills", []):
        s = s.strip()
        if len(s) < 2:
            continue
        if s.lower().endswith("ovat"):
            continue
        req.append(s)

    # ✅ Clean tech stack
    tech = []
    for s in jd.get("tech_stack", []):
        s = s.strip()
        if len(s) < 2:
            continue
        if s.lower().endswith("ovat"):
            continue
        tech.append(s)

    # ✅ Fallback — JD must contain SOMETHING
    if not tech:
        # ultra-safe fallback based on categories
        lower = jd_text.lower()
        if any(word in lower for word in ["python", "api", "cloud", "kubernetes"]):
            tech = ["Python", "APIs", "Cloud", "Kubernetes"]
        elif any(word in lower for word in ["patient", "clinical", "nurse"]):
            tech = ["patient care", "documentation"]
        elif any(word in lower for word in ["invoice", "accounting"]):
            tech = ["Excel", "bookkeeping"]
        else:
            tech = ["communication"]

    jd["required_skills"] = req or ["communication"]
    jd["tech_stack"] = tech
    jd["nice_to_have_skills"] = jd.get("nice_to_have_skills", []) or []

    # ✅ Seniority
    t = jd_text.lower()
    if not jd.get("seniority"):
        if "senior" in t or "lead" in t:
            jd["seniority"] = "Senior"
        elif "junior" in t:
            jd["seniority"] = "Junior"
        else:
            jd["seniority"] = "Mid"

    # ✅ Experience
    if jd.get("min_experience") is None:
        jd["min_experience"] = 0

    return jd
