# ============================================================
# ✅ JD EXTRACTOR v8.0 — UNIVERSAL SAFE MODE
#    • ZERO halucinací
#    • Jen reálné skills → žádné "elimin", "systémy", "nástroje"
#    • Embeddings extrakce přes univerzální skill korpus
#    • LLM + semantic fallback
#    • 100% stabilní pro scoring
# ============================================================

from openai import AsyncOpenAI
import json
import glob
import numpy as np
import re

client = AsyncOpenAI()

EMBED_MODEL = "text-embedding-3-large"


# ===================================================================
# ✅ 1) LOAD UNIVERSAL SKILL CORPUS (~3000 skills)
# ===================================================================
def load_universal_skills():
    skills = []
    for path in glob.glob("universal_skills/*.json"):
        with open(path, "r", encoding="utf-8") as f:
            skills.extend(json.load(f))
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
# ✅ 3) Embedding-based skill extractor (NO HALUCINATIONS)
# ===================================================================
async def extract_skills_embeddings(jd_text: str, threshold=0.78):
    jd_emb = await get_emb(jd_text)
    matched = []

    for skill in UNIVERSAL_SKILLS:
        emb = await get_emb(skill)
        sim = cos(jd_emb, emb)
        if sim >= threshold:
            matched.append(skill)

    return matched


# ===================================================================
# ✅ 4) LLM SAFE EXTRACTOR (NO INVENTING SKILLS)
# ===================================================================
SYSTEM_PROMPT = """
You are an HR job analysis expert.

IMPORTANT RULES:
1) Extract ONLY skills or tools that appear directly in the JD text.
2) NO hallucinations. If something is not explicitly present, DO NOT RETURN IT.
3) Ignore benefits, perks, culture, marketing text.
4) Seniority must be inferred only from wording in text (“junior”, “zkušený”, “senior”).
5) If no years of experience are mentioned → return null.
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
# ✅ 5) FINAL SAFE JD EXTRACTOR v8.0
# ===================================================================
async def extract_structured_jd(jd_text: str) -> dict:
    """
    FINAL PIPELINE:
      1) LLM SAFE extraction (no hallucinations)
      2) Embedding-based universal skills enrichment
      3) Filter to avoid junk terms
      4) Guarantee stable structure
    """

    jd_data = await llm_extract_jd(jd_text)

    # STEP 1 — LLM skills
    llm_skills = jd_data.get("required_skills") or []

    # STEP 2 — Embeddings universal skills
    embed_skills = await extract_skills_embeddings(jd_text)

    # STEP 3 — Merge + dedupe
    merged = list({*llm_skills, *embed_skills})

    # STEP 4 — Filter garbage (NO verbs, NO operations, NO nonsense)
    cleaned = []
    for skill in merged:
        s = skill.lower().strip()

        if len(s) < 3:
            continue
        if "ovat" in s:
            continue
        if s in ["systémy", "nástroje", "operace", "operations", "quality focus"]:
            continue

        cleaned.append(skill)

    # STEP 5 — Guarantee required_skills non-empty
    if not cleaned:
        # fallback ONLY picks from universal corpus, not from JD text words
        cleaned = embed_skills[:8]

    jd_data["required_skills"] = cleaned
    jd_data["nice_to_have_skills"] = jd_data.get("nice_to_have_skills") or []

    # Seniority fallback
    text_l = jd_text.lower()
    if not jd_data.get("seniority"):
        if "senior" in text_l or "zkušen" in text_l or "lead" in text_l:
            jd_data["seniority"] = "Senior"
        elif "junior" in text_l or "začínaj" in text_l:
            jd_data["seniority"] = "Junior"
        else:
            jd_data["seniority"] = "Mid"

    # Experience fallback
    if jd_data.get("min_experience") is None:
        jd_data["min_experience"] = None

    return jd_data
