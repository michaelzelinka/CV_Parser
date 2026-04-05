from openai import AsyncOpenAI
import json
import re

client = AsyncOpenAI()

MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = """
You are an HR Job Description Parser.

Extract two layers from the JD:
- required_skills: explicit requirements (must-have) IF present
- tech_stack: technologies/tools/platforms/systems mentioned ANYWHERE in the JD

Rules:
1) Do NOT hallucinate. Only extract what is present in the text.
2) Include technologies, tools, platforms, certifications, domain skills.
3) Ignore benefits and company culture.
4) Seniority only from keywords: junior/mid/senior/lead.
5) min_experience = years if mentioned, else null.
6) Output ONLY valid JSON with keys:
{
  "role": string | null,
  "required_skills": [string],
  "tech_stack": [string],
  "nice_to_have_skills": [string],
  "seniority": "Junior" | "Mid" | "Senior" | "Trainee" | null,
  "min_experience": number | null
}
"""

def _extract_json(text: str) -> dict:
    """
    Robust JSON extractor:
    - strips markdown fences
    - finds first {...} block
    """
    if not text:
        raise ValueError("Empty LLM output")

    t = text.strip()
    t = t.replace("```json", "").replace("```", "").strip()

    m = re.search(r"\{[\s\S]*\}", t)
    if not m:
        raise ValueError(f"No JSON object found in: {t[:200]}...")

    return json.loads(m.group(0))

def _clean_list(items):
    out = []
    for x in items or []:
        s = str(x).strip()
        if len(s) < 2:
            continue
        # avoid old CZ verb artifacts if any appear
        if s.lower().endswith("ovat"):
            continue
        out.append(s)
    # dedupe while preserving order
    seen = set()
    deduped = []
    for s in out:
        k = s.lower()
        if k not in seen:
            seen.add(k)
            deduped.append(s)
    return deduped

def _infer_seniority(jd_text: str):
    t = jd_text.lower()
    if "senior" in t or "lead" in t or "experienced" in t:
        return "Senior"
    if "junior" in t or "graduate" in t or "trainee" in t:
        return "Junior"
    return "Mid"

async def extract_structured_jd(jd_text: str) -> dict:
    try:
        resp = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": jd_text},
            ],
            temperature=0,
        )

        content = resp.choices[0].message.content
        jd = _extract_json(content)

    except Exception as e:
        # IMPORTANT: we log the real reason
        print("JD_EXTRACTOR_ERROR:", repr(e))
        jd = {
            "role": None,
            "required_skills": [],
            "tech_stack": [],
            "nice_to_have_skills": [],
            "seniority": None,
            "min_experience": None,
        }

    # Clean lists
    jd["required_skills"] = _clean_list(jd.get("required_skills"))
    jd["tech_stack"] = _clean_list(jd.get("tech_stack"))
    jd["nice_to_have_skills"] = _clean_list(jd.get("nice_to_have_skills"))

    # If LLM was conservative, ensure tech_stack at least captures obvious tech mentions
    if not jd["tech_stack"]:
        t = jd_text.lower()
        fallback = []
        if "python" in t: fallback.append("Python")
        if "kubernetes" in t: fallback.append("Kubernetes")
        if "google cloud" in t or "gcp" in t: fallback.append("Google Cloud Platform")
        if "rabbitmq" in t: fallback.append("RabbitMQ")
        if "redis" in t: fallback.append("Redis")
        if "mongo" in t: fallback.append("MongoDB")
        if "rest" in t and "api" in t: fallback.append("REST API")
        jd["tech_stack"] = fallback

    # MVP rule: if required_skills empty, use tech_stack (so scoring always has signal)
    if not jd["required_skills"]:
        jd["required_skills"] = jd["tech_stack"][:]  # copy

    # Seniority
    if not jd.get("seniority"):
        jd["seniority"] = _infer_seniority(jd_text)

    # Experience
    if jd.get("min_experience") is None:
        jd["min_experience"] = 0

    # Role fallback
    if "role" not in jd:
        jd["role"] = None

    return jd
