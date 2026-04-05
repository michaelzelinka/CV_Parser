from openai import AsyncOpenAI
import re

client = AsyncOpenAI()

SYSTEM_PROMPT = """
You are an HR Job Description Parser.

Extract ONLY skills, competencies, tools, or qualifications that are explicitly or implicitly required in the job description.

This must work for ALL job categories:
- healthcare (nurses, doctors, caregivers)
- administration (office, reception, assistant roles)
- finance & accounting
- customer service
- marketing & sales
- logistics & manufacturing
- hospitality
- IT & technical roles
- management & leadership
- blue collar roles (operators, cleaners, production workers, drivers)

RULES:
1) Extract ONLY skills that are explicitly mentioned OR clearly implied.
2) Include:
   - technical skills (Python, Excel, SAP...)
   - soft skills (communication, teamwork...)
   - industry skills (patient care, sterilization, bookkeeping...)
   - tools/platforms (EPIC, SAP, CRM systems, cash register...)
   - certifications (BLS, CPA, forklift license...)
3) Do NOT hallucinate or invent skills.
4) DO NOT return benefits or company culture.
5) Seniority is based ONLY on: junior, mid, senior, lead, supervisor.
6) min_experience = number of years if mentioned, else null.
7) Role = job title if found.

Return ONLY valid JSON structure:
{
  "role": string | null,
  "required_skills": [string],
  "nice_to_have_skills": [string],
  "seniority": "Senior" | "Mid" | "Junior" | "Trainee" | null,
  "min_experience": number | null
}
"""

async def extract_structured_jd(jd_text: str) -> dict:
    # Try LLM extraction
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
        # Minimal fallback (never empty)
        jd = {
            "role": None,
            "required_skills": [],
            "nice_to_have_skills": [],
            "seniority": None,
            "min_experience": None
        }

    # ✅ Clean required skills
    skills = []
    for s in jd.get("required_skills", []):
        s = s.strip()
        if len(s) < 2:
            continue
        if s.lower().endswith("ovat"):
            continue
        if re.match(r"^[0-9]+$", s):
            continue
        skills.append(s)

    # ✅ If LLM returned nothing → fallback basic extraction
    if not skills:
        lower = jd_text.lower()
        fallback = []

        # Healthcare
        if "nurse" in lower or "patient" in lower or "clinical" in lower:
            fallback = ["patient care", "documentation", "vitals monitoring"]

        # Administration
        elif "office" in lower or "assistant" in lower or "administration" in lower:
            fallback = ["excel", "email handling", "scheduling"]

        # Finance / accounting
        elif "accounting" in lower or "invoice" in lower or "finance" in lower:
            fallback = ["excel", "bookkeeping", "invoicing"]

        # Customer service
        elif "customer" in lower or "call" in lower or "support" in lower:
            fallback = ["communication", "problem solving", "crm systems"]

        # Manufacturing / warehouse
        elif "warehouse" in lower or "production" in lower:
            fallback = ["scanning", "inventory handling", "quality control"]

        # Hospitality
        elif "restaurant" in lower or "kitchen" in lower or "hospitality" in lower:
            fallback = ["customer service", "cash handling", "food safety"]

        # IT fallback
        else:
            fallback = ["communication"]

        skills = fallback

    jd["required_skills"] = skills

    # ✅ nice-to-have cleanup
    jd["nice_to_have_skills"] = jd.get("nice_to_have_skills", []) or []

    # ✅ Infer seniority
    text = jd_text.lower()
    if not jd.get("seniority"):
        if "senior" in text or "lead" in text:
            jd["seniority"] = "Senior"
        elif "junior" in text:
            jd["seniority"] = "Junior"
        else:
            jd["seniority"] = "Mid"

    # ✅ Experience fallback
    if jd.get("min_experience") is None:
        jd["min_experience"] = 0

    return jd
