import numpy as np
from openai import AsyncOpenAI

client = AsyncOpenAI()
_embedding_cache = {}

async def embed(text: str):
    text = text.strip().lower()
    if text in _embedding_cache:
        return _embedding_cache[text]

    resp = await client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    emb = np.array(resp.data[0].embedding, dtype=np.float32)
    _embedding_cache[text] = emb
    return emb


def cos(a, b):
    if a is None or b is None:
        return 0.0
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


# ============================================================================
# ✅ UNIVERSÁLNÍ SCORING ENGINE (v6) S PŮVODNÍM NÁZVEM compute_matching_v5
# ============================================================================
async def compute_matching_v5(cv: dict, jd: dict | None):
    """
    Universal matching engine.
    Funguje pro TECH, NON-TECH, dělnické pozice, healthcare, finance… všechno.
    Není tam žádný IT bias, žádné hard-faily, žádné oborové váhy.
    """
    if jd is None:
        return {"score": 0, "details": {"reason": "no_jd"}}

    cv_skills = cv.get("technologies_normalized", [])
    jd_req = jd.get("required_skills", [])
    jd_opt = jd.get("nice_to_have_skills", [])

    # Prepare embeddings
    cv_embs = [await embed(s) for s in cv_skills]

    # =====================================================================
    # ✅ 1) STRING MATCH (0–40)
    # =====================================================================
    string_score = 0
    max_string_score = len(jd_req) * 4  # každá required skill max 4 body

    for skill in jd_req:
        s_low = skill.lower()
        matched = any(s_low in cv_s.lower() for cv_s in cv_skills)
        if matched:
            string_score += 4

    string_score = (string_score / max_string_score) * 40 if max_string_score > 0 else 0

    # =====================================================================
    # ✅ 2) EMBEDDING MATCH (0–40)
    # =====================================================================
    embed_score = 0
    embed_max = len(jd_req) * 4

    for skill in jd_req:
        req_emb = await embed(skill)
        sims = [cos(req_emb, cv_emb) for cv_emb in cv_embs] if cv_embs else []
        sim = max(sims) if sims else 0

        if sim > 0.75:
            embed_score += 4
        elif sim > 0.55:
            embed_score += 2
        elif sim > 0.40:
            embed_score += 1

    embed_score = (embed_score / embed_max) * 40 if embed_max > 0 else 0

    # =====================================================================
    # ✅ 3) EXPERIENCE SCORE (0–10)
    # =====================================================================
    cv_exp = cv.get("years_experience") or 0
    jd_exp = jd.get("min_experience") or 0

    if jd_exp == 0:
        exp_score = min(cv_exp, 10)
    else:
        ratio = min(cv_exp / jd_exp, 1.0)
        exp_score = ratio * 10

    # =====================================================================
    # ✅ 4) SENIORITY SCORE (0–10)
    # =====================================================================
    cv_sen = cv.get("seniority") or ""
    jd_sen = jd.get("seniority") or ""

    seniority_score = 10 if cv_sen == jd_sen and cv_sen != "" else 0

    # =====================================================================
    # ✅ FINAL
    # =====================================================================
    final = string_score + embed_score + exp_score + seniority_score
    final = int(max(0, min(100, final)))

    return {
        "score": final,
        "details": {
            "string_score": string_score,
            "embedding_score": embed_score,
            "experience_score": exp_score,
            "seniority_score": seniority_score
        }
    }
