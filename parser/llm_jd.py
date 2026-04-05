# ============================================================
# ✅ JD EXTRACTOR v8.1 — UNIVERSAL SAFE MODE (RENDER FIX)
#    • Zero halucinací
#    • Pouze reálné skills
#    • Embeddings + LLM SAFE extrakce
#    • ABSOLUTNÍ cesta k universal_skills (Render fix)
# ============================================================

from openai import AsyncOpenAI
import json
import glob
import numpy as np
import os

client = AsyncOpenAI()
EMBED_MODEL = "text-embedding-3-large"

# ===================================================================
# ✅ 0) ABSOLUTNÍ CESTA — KLÍČOVÉ PRO RENDER & FASTAPI
# ===================================================================
BASE_DIR = os.path.dirname(__file__)
SKILLS_DIR = os.path.join(BASE_DIR, "universal_skills")


# ===================================================================
# ✅ 1) LOAD UNIVERSAL SKILL CORPUS (~3000 skills)
# ===================================================================
def load_universal_skills():
    skills = []
    pattern = os.path.join(SKILLS_DIR, "*.json")

    for path in glob.glob(pattern):
        try:
            with open(path, "r", encoding="utf-8") as f:
                skills.extend(json.load(f))
        except Exception:
            continue

    return list(set(skills))


UNIVERSAL_SKILLS = load_universal_skills()


# ===================================================================
# ✅ 2) Embedding helper
# ===================================================================
async def get_emb(text: str):
    resp = await client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return np.array(resp.data[0].embedding, dtype=np.float32)


def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# ===================================================================
# ✅ 3) Embedding-based skill extractor
# ===================================================================
async def extract_skills_embeddings(jd_text: str, threshold=0.78):
    """
    Vrací skills z univerzálního korpusu, které významově odpovídají JD.
    """
    if not UNIVERSAL_SKILLS:
        return []

    jd_emb = await get_emb(jd_text)
    matched = []

    for skill in UNIVERSAL_SKILLS:
        emb = await get_emb(skill)
        sim = cos(jd_emb, emb)

        if sim >= threshold:
            matched.append(skill)

    return matched


# ===================================================================
# ✅ 4) LLM SAFE EXTRACTOR
# ===================================================================
SYSTEM_PROMPT = """
You are an HR job analysis expert.

Rules:
1) Extract ONLY skills/tools explicitly mentioned in the JD.
2) Do NOT hallucinate skills not mentioned.
3) Ignore benefits and HR marketing fluff.
4) Infer seniority only from wording (junior/senior/zkušený/lead).
5) If experience not mentioned, return null.
6) Output ONLY valid JSON.

Return JSON:
{
  "role": string | null,
  "required_skills": [string],
  "nice_to_have_skills": [string],
  "seniority": "Senior" | "Mid" | "Junior" | "Trainee" | null,
  "min_experience": number | null
}
"""


async def llm_extract_jd(jd_text: str):
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
        return resp.choices[0].message.parsed

    except Exception:
        return {
            "role": None,
            "required_skills": [],
            "nice_to_have_skills": [],
            "seniority": None,
            "min_experience": None
        }


# ===================================================================
# ✅ 5) FINAL SAFE JD EXTRACTOR v8.1
# ===================================================================
async def extract_structured_jd(jd_text: str) -> dict:
    """
    Full pipeline: LLM → Embeddings → Clean → Fallback-safe
    """

    jd_data = await llm_extract_jd(jd_text)

    # 1) LLM skills
    llm_skills = jd_data.get("required_skills") or []

    # 2) Embedding skills
    embed_skills = await extract_skills_embeddings(jd_text)

    # 3) Merge + dedupe
    merged = list({*llm_skills, *embed_skills})

    # 4) Filter junk
    cleaned = []
    for skill in merged:
        s = skill.lower().strip()

        if len(s) < 2:
            continue

        # eliminace starých heuristik
        if "ovat" in s:
            continue
        if s in ["systémy", "nástroje", "operace", "operations", "quality focus"]:
            continue

        cleaned.append(skill)

    # 5) Fallback (embedding-only)
    if not cleaned and embed_skills:
        cleaned = embed_skills[:8]

    jd_data["required_skills"] = cleaned
    jd_data["nice_to_have_skills"] = jd_data.get("nice_to_have_skills") or []

    # --- Seniority inference
    txt = jd_text.lower()
    if not jd_data.get("seniority"):
        if "senior" in txt or "zkušen" in txt or "lead" in txt:
            jd_data["seniority"] = "Senior"
        elif "junior" in txt or "začínaj" in txt:
            jd_data["seniority"] = "Junior"
        else:
            jd_data["seniority"] = "Mid"

    # Experience fallback
    if jd_data.get("min_experience") is None:
        jd_data["min_experience"] = None

    return jd_data
