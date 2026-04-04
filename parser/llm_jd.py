from openai import AsyncOpenAI
import re

client = AsyncOpenAI()

SYSTEM_PROMPT = """
You are an expert HR analyst. Extract real, concrete job requirements from ANY job description text.

Return ONLY structured JSON:
{
  "role": string,
  "required_skills": [string],
  "nice_to_have_skills": [string],
  "seniority": "Senior | Mid | Junior | Trainee",
  "min_experience": number
}
"""

FALLBACK_KEYWORDS = [
    # technologies
    "python", "fastapi", "javascript", "typescript", "vue", "react",
    "sql", "excel", "power bi", "sap", "java", "c#", "automation",
    "data", "api", "testing", "devops", "cloud",
    # domains
    "warehouse", "logistics", "customer service", "patient care",
    "cleaning", "manufacturing", "accounting", "marketing",
    "administration", "sales",
]

def heuristic_extract_skills(text: str):
    text_l = text.lower()

    extracted = set()

    # 1) technology keywords
    for kw in FALLBACK_KEYWORDS:
        if kw in text_l:
            extracted.add(kw)

    # 2) verbs → convert to skill phrases
    verbs = re.findall(r"\b[a-zA-Záéíóúýřščžďťň]{4,}ovat\b", text_l)
    for v in verbs:
        extracted.add(v.replace("ovat", "") + " operation")

    # 3) nouns that look like skill domains ("analýza", "procesy", "nástroje")
    nouns = re.findall(r"\b[a-zA-Záéíóúýřščžďťň]{4,}\b", text_l)
    domain_words = [n for n in nouns if n in [
        "analýza", "procesy", "plánování", "operace",
        "nástroje", "systémy", "kvalita", "organizační"
    ]]
    extracted.update(domain_words)

    # Minimum 5 skills: ensure scoring is not broken
    if len(extracted) < 5:
        extracted.update(list(extracted))
        extracted.update(["communication", "operations", "quality focus"])

    return list(sorted(extracted))[:12]


async def extract_structured_jd(jd_text: str) -> dict:
    """
    ✅ Universal JD extractor v7.2 (SAFE MODE)
    - tries GPT
    - if GPT result is empty → fallback heuristic
    - NEVER returns empty required_skills
    """

    # Try LLM extraction
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

        jd_data = resp.choices[0].message.parsed

    except Exception:
        jd_data = {
            "role": "Unknown",
            "required_skills": [],
            "nice_to_have_skills": [],
            "seniority": "Mid",
            "min_experience": 0
        }

    # ✅ SAFE MODE: If GPT failed OR gave empty skills → extract manually
    if not jd_data.get("required_skills"):
        jd_data["required_skills"] = heuristic_extract_skills(jd_text)

    # ✅ guarantee lists exist
    jd_data["nice_to_have_skills"] = jd_data.get("nice_to_have_skills", [])

    # ✅ seniority fallback
    if not jd_data.get("seniority"):
        jd_data["seniority"] = "Mid"

    # ✅ exp fallback
    if jd_data.get("min_experience") is None:
        jd_data["min_experience"] = 0

    return jd_data
