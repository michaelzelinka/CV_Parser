from openai import AsyncOpenAI
import re

client = AsyncOpenAI()

SYSTEM_PROMPT = """
You extract the real technology stack and required skills from a job description.

Extract the following:
- required_skills: list of explicit requirements
- tech_stack: technologies, tools, platforms from ANYWHERE in the text
- seniority: Junior / Mid / Senior
- min_experience: years of experience if mentioned, else null

Return valid JSON:
{
  "required_skills": [string],
  "tech_stack": [string],
  "seniority": "Junior" | "Mid" | "Senior" | null,
  "min_experience": number | null
}
"""

async def extract_structured_jd(jd_text: str) -> dict:
    try:
        resp = await client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": jd_text}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        jd = resp.choices[0].message.parsed

    except Exception as e:
        print("JD_EXTRACTOR_ERROR:", repr(e))
        return {
            "required_skills": [],
            "tech_stack": [],
            "seniority": None,
            "min_experience": None
        }

    # --- cleanup ---
    def clean_list(lst):
        out = []
        for s in lst or []:
            s = s.strip()
            if len(s) < 2: continue
            if s.lower().endswith("ovat"): continue
            out.append(s)
        return out

    jd["required_skills"] = clean_list(jd.get("required_skills"))
    jd["tech_stack"] = clean_list(jd.get("tech_stack"))

    # --- tech fallback ---
    if not jd["tech_stack"]:
        text = jd_text.lower()
        fallback = []
        if "python" in text: fallback.append("Python")
        if "kubernetes" in text: fallback.append("Kubernetes")
        if "redis" in text: fallback.append("Redis")
        if "rabbitmq" in text: fallback.append("RabbitMQ")
        if "mongo" in text: fallback.append("MongoDB")
        if "cloud" in text: fallback.append("Cloud")
        jd["tech_stack"] = fallback

    # required skills fallback
    if not jd["required_skills"]:
        jd["required_skills"] = jd["tech_stack"]

    # --- seniority fallback ---
    txt = jd_text.lower()
    if not jd.get("seniority"):
        if "senior" in txt:
            jd["seniority"] = "Senior"
        elif "junior" in txt:
            jd["seniority"] = "Junior"
        else:
            jd["seniority"] = "Mid"

    # --- experience fallback ---
    if jd.get("min_experience") is None:
        jd["min_experience"] = 0

    return jd
