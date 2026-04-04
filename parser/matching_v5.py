import numpy as np
from openai import AsyncOpenAI

client = AsyncOpenAI()
_embedding_cache = {}

async def embed(text: str):
    """
    Simple embed with caching.
    Universal, no bias.
    """
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
    """
    Safe cosine similarity.
    """
    if a is None or b is None:
        return 0.0
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


# ========================================================================
# ✅ UNIVERSAL HR-FRIENDLY SCORING ENGINE (v7.0 LIGHT)
# ========================================================================
async def compute_matching_v5(cv: dict, jd: dict | None):
    """
    v7.0 LIGHT scoring:
    - Works for ALL job types (factory worker ↔ marketing ↔ IT ↔ healthcare)
    - HR-friendly
    - Transparent
    - No category bias
    - No over-penalization
    - VERY clear separation:
        - non-fit candidate: 0–3
        - partially relevant: 10–30
        - relevant: 30–60
        - strong fit: 60–85
        - exceptional: 85–100
    """

    if jd is None:
        return {"score": 0, "details": {"reason": "no_jd"}}

    # Extract data
    cv_skills = cv.get("technologies_normalized", [])
    jd_req = jd.get("required_skills", [])
    jd_opt = jd.get("nice_to_have_skills", [])

    cv_embs = [await embed(s) for s in cv_skills]

    # =====================================================================
    # ✅ 1) STRING MATCH (0–40)
    # =====================================================================
    string_score = 0
    max_string_score = len(jd_req) * 4

    for req in jd_req:
        r = req.lower()
        if any(r in skill.lower() for skill in cv_skills):
            string_score += 4

    string_score = (string_score / max_string_score * 40) if max_string_score else 0

    # =====================================================================
    # ✅ 2) EMBEDDING MATCH (0–40)
    # Only strong & medium similarity count (>0.60)
    # =====================================================================
    embed_score = 0
    embed_max = len(jd_req) * 4

    for req in jd_req:
        req_emb = await embed(req)
        sims = [cos(req_emb, cv_emb) for cv_emb in cv_embs] if cv_embs else []
        sim = max(sims) if sims else 0

        if sim > 0.75:
            embed_score += 4    # strong match
        elif sim > 0.60:
            embed_score += 2    # medium match
        else:
            embed_score += 0    # ✅ ignore weak similarities

    embed_score = (embed_score / embed_max * 40) if embed_max else 0

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
    # Binary: match = +10, else 0
    # =====================================================================
    cv_sen = cv.get("seniority") or ""
    jd_sen = jd.get("seniority") or ""
    seniority_score = 10 if cv_sen and cv_sen == jd_sen else 0

    # =====================================================================
    # ✅ FINAL AGGREGATION
    # =====================================================================
    raw_score = string_score + embed_score + exp_score + seniority_score

    # Hard cap for totally irrelevant candidates
    # If NO skill match at all:
    if string_score == 0 and embed_score == 0:
        final = min(raw_score, 3)  # ✅ HR‑friendly cap
    else:
        final = raw_score

    final = int(max(0, min(100, final)))

    return {
        "score": final,
        "details": {
            "string_score": string_score,
            "embedding_score": embed_score,
            "experience_score": exp_score,
            "seniority_score": seniority_score,
        }
    }
