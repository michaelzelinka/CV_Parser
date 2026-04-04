import numpy as np
from openai import AsyncOpenAI

client = AsyncOpenAI()

# =====================================================================
# ✅ Simple in-memory embedding cache
# =====================================================================
_embedding_cache = {}

async def get_embedding(text: str):
    """
    Returns embedding for given text with caching.
    Makes scoring extremely cheap after first request.
    """
    cleaned = text.strip().lower()
    if cleaned in _embedding_cache:
        return _embedding_cache[cleaned]

    resp = await client.embeddings.create(
        model="text-embedding-3-large",
        input=cleaned
    )

    emb = np.array(resp.data[0].embedding, dtype=np.float32)
    _embedding_cache[cleaned] = emb
    return emb


# =====================================================================
# ✅ Cosine similarity
# =====================================================================
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a is None or b is None:
        return 0.0
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


# =====================================================================
# ✅ Embedding-based skill matching
# =====================================================================
async def embedding_skill_match(cv_skills, jd_skills, threshold=0.63):
    """
    Returns ratio (0–1) of JD skills that have CV skill match
    based on cosine similarity >= threshold.
    """

    if not jd_skills:
        return 0.0

    # Precompute embeddings for CV skills
    cv_embs = []
    for skill in cv_skills:
        emb = await get_embedding(skill)
        cv_embs.append(emb)

    matches = 0

    for jd_skill in jd_skills:
        jd_emb = await get_embedding(jd_skill)

        best_sim = max(
            cosine_similarity(jd_emb, cv_emb) for cv_emb in cv_embs
        )

        if best_sim >= threshold:
            matches += 1

    return matches / len(jd_skills)


# =====================================================================
# ✅ Full matching v3.0 (embedding-based)
# =====================================================================
async def compute_matching_v3(cv: dict, jd: dict | None):
    """
    Computes match score using:
    - embedding skill similarity (required + optional)
    - experience match
    - seniority match

    Returns: { "score": int, "details": {...} }
    """

    if not jd:
        return {
            "score": 50,
            "details": {"reason": "No JD provided"}
        }

    cv_skills = cv.get("technologies_normalized", [])
    jd_required = jd.get("required_skills", [])
    jd_optional = jd.get("nice_to_have_skills", [])

    # ------------------------------------------------------------
    # ✅ REQUIRED SKILLS — 60%
    # ------------------------------------------------------------
    required_ratio = await embedding_skill_match(
        cv_skills, jd_required, threshold=0.63
    )
    required_score = required_ratio * 60

    # ------------------------------------------------------------
    # ✅ NICE-TO-HAVE SKILLS — 10%
    # ------------------------------------------------------------
    optional_ratio = await embedding_skill_match(
        cv_skills, jd_optional, threshold=0.63
    )
    optional_score = optional_ratio * 10

    # ------------------------------------------------------------
    # ✅ EXPERIENCE MATCH — 20%
    # ------------------------------------------------------------
    cv_exp = cv.get("years_experience")
    jd_exp = jd.get("min_experience")

    if jd_exp and jd_exp > 0 and cv_exp:
        exp_ratio = min(cv_exp / jd_exp, 1.0)
        experience_score = exp_ratio * 20
    else:
        experience_score = 10  # neutral for trainees, unclear JD

    # ------------------------------------------------------------
    # ✅ SENIORITY MATCH — 10%
    # ------------------------------------------------------------
    seniority_score = 0
    if cv.get("seniority") and jd.get("seniority"):
        if cv["seniority"].lower() == jd["seniority"].lower():
            seniority_score = 10

    # ------------------------------------------------------------
    # ✅ FINAL SCORE
    # ------------------------------------------------------------
    final_score = required_score + optional_score + experience_score + seniority_score
    final_score = int(round(min(final_score, 100)))

    # ------------------------------------------------------------
    # ✅ DETAILS FOR DEBUG / UI
    # ------------------------------------------------------------
    details = {
        "required_ratio": required_ratio,
        "optional_ratio": optional_ratio,
        "required_score": required_score,
        "optional_score": optional_score,
        "experience_score": experience_score,
        "seniority_score": seniority_score,
        "cv_experience": cv_exp,
        "jd_experience": jd_exp,
        "cv_seniority": cv.get("seniority"),
        "jd_seniority": jd.get("seniority"),
    }

    return {
        "score": final_score,
        "details": details
    }
