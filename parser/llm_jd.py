# ============================================================
# ✅ JD EXTRACTOR v9.0 — UNIVERSAL SAFE MODE (Render-optimized)
#    • Zero halucinací
#    • FAST embeddings (preloaded once)
#    • 100% stable for Render FREE tier
# ============================================================

from openai import AsyncOpenAI
import json
import glob
import numpy as np
import os

client = AsyncOpenAI()
EMBED_MODEL = "text-embedding-3-large"

# ------------------------------
# ✅ Absolute path to skill files
# ------------------------------
BASE_DIR = os.path.dirname(__file__)
SKILLS_DIR = os.path.join(BASE_DIR, "universal_skills")

# ------------------------------
# ✅ Load skill names
# ------------------------------
def load_universal_skills():
    skills = []
    for path in glob.glob(os.path.join(SKILLS_DIR, "*.json")):
        with open(path, "r", encoding="utf-8") as f:
            skills.extend(json.load(f))
    return list(set(skills))

UNIVERSAL_SKILLS = load_universal_skills()

# ------------------------------
# ✅ PRELOAD ALL SKILL EMBEDDINGS (once at startup)
# ------------------------------
_skill_emb_cache = {}
_embeddings_loaded = False

async def preload_skill_embeddings():
    global _embeddings_loaded

    if _embeddings_loaded:
        return

    for skill in UNIVERSAL_SKILLS:
        emb = await client.embeddings.create(
            model=EMBED_MODEL,
            input=skill
        )
        _skill_emb_cache[skill] = np.array(emb.data[0].embedding, dtype=np.float32)

    _embeddings_loaded = True


def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


async def extract_skills_embeddings(jd_text: str, threshold=0.78):
    """
    ✅ Ultra fast: JD embedding computed once
    ✅ Skill embeddings preloaded in memory
    """

    if not _embeddings_loaded:
        await preload_skill_embeddings()

    # JD embedding
    resp = await client.embeddings.create(
        model=EMBED_MODEL,
        input=jd_text
    )
    jd_emb = np.array(resp.data[0].embedding, dtype=np.float32)

    matched = []
    for skill, emb in _skill_emb_cache.items():
        sim = cos(jd_emb, emb)
        if sim >= threshold:
            matched.append(skill)

    return matched


# ------------------------------
# ✅ LLM SAFE EXTRACTOR
# ------------------------------
SYSTEM_PROMPT = """
You are an HR job analysis expert.

Rules:
1) Extract ONLY skills explicitly mentioned in the JD.
2) No hallucinations.
3) Ignore marketing fluff.
4) Infer seniority only from wording.
5) If no years mentioned → null.
6) Return ONLY valid JSON.
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


# ------------------------------
# ✅ FINAL SAFE JD PARSER
# ------------------------------
async def extract_structured_jd(jd_text: str) -> dict:

    jd_data = await llm_extract_jd(jd_text)

    # LLM skills
    llm_skills = jd_data.get("required_skills") or []

    # Embeddings skills
    embed_skills = await extract_skills_embeddings(jd_text)

    # Merge + clean
    merged = list({*llm_skills, *embed_skills})

    cleaned = [
        s for s in merged
        if len(s.strip()) > 2
        and "ovat" not in s.lower()
        and s.lower() not in ["systémy", "nástroje", "operace", "operations"]
    ]

    if not cleaned:
        cleaned = embed_skills[:8]

    jd_data["required_skills"] = cleaned
    jd_data["nice_to_have_skills"] = jd_data.get("nice_to_have_skills") or []

    # Seniority inference
    t = jd_text.lower()
    if not jd_data.get("seniority"):
        if "senior" in t or "zkušen" in t:
            jd_data["seniority"] = "Senior"
        elif "junior" in t or "začínaj" in t:
            jd_data["seniority"] = "Junior"
        else:
            jd_data["seniority"] = "Mid"

    return jd_data
