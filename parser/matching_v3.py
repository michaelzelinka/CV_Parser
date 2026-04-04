import numpy as np
from openai import AsyncOpenAI
import asyncio
import functools

client = AsyncOpenAI()

# -------------------------------------------------------
# ✅ Simple in-memory cache to avoid recomputing embeddings
# -------------------------------------------------------
_embedding_cache = {}

async def get_embedding(text: str):
    text = text.strip().lower()
    if text in _embedding_cache:
        return _embedding_cache[text]

    response = await client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    emb = np.array(response.data[0].embedding, dtype=np.float32)

    _embedding_cache[text] = emb
    return emb


# -------------------------------------------------------
# ✅ Cosine similarity
# -------------------------------------------------------
def cosine(a: np.ndarray, b: np.ndarray):
    if a is None or b is None:
        return 0.0
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


# -------------------------------------------------------
# ✅ Embedding-based skill match
# -------------------------------------------------------
async def embedding_skill_match(cv_skills, jd_skills, threshold=0.63):
    """
    Computes percentage of JD skills that have at least one CV skill
    with cosine similarity >= threshold.
    """
    if not jd_skills:
        return 0.0

    # Precompute CV embeddings
    cv_embs = []
    for skill in cv_skills:
        emb = await get_embedding(skill)
        cv_embs.append(emb)

    matches = 0

    # Compare each JD skill to all CV skills
    for jd_skill in jd_skills:
        jd_emb = await get_embedding(jd_skill)

        # best similarity for this JD skill
        sim = max(cosine(jd_emb, cv_emb) for cv_emb in cv_embs)
        if sim >= threshold:
            matches += 1

    return matches / len(jd_skills)


# -------------------------------------------------------
# ✅ Full matching v3.0
# -------------------------------------------------------
async def compute_matching_v3(cv: dict, jd: dict | None):
    """
    Returns:
    {
      "score": int,
      "details": {...}
    }
    """

    if not jd:
        return {
            "score": 50,
            "details": {"reason": "No JD provided"}
        }

    cv_skills = cv.get("technologies", [])
    jd_required = jd.get("required_skills", [])
    jd_optional = jd.get("nice_to_have_skills", [])

    # ----------------------------------------
    # ✅ Skills similarity (required) → 60 %
    # ----------------------------------------
    required_ratio = await embedding_skill_match(cv_skills, jd_required)

    # Optional → small boost
    optional_ratio = await embedding_skill_match(cv_skills, jd_optional)

    skill_score = (required_ratio * 60) + (optional_ratio * 10)

    # ----------------------------------------
    # ✅ Experience match → 20 %
    # ----------------------------------------
    cv_exp = cv.get("years_experience")
    jd_exp = jd.get("min_experience")

    if jd_exp and jd_exp > 0 and cv_exp:
        exp_ratio = min(cv_exp / jd_exp, 1.0)
        experience_score = exp_ratio * 20
    else:
        # If JD is trainee-type → give mid score by default
        experience_score = 10

    # ----------------------------------------
    # ✅ Seniority match → 10 %
    # ----------------------------------------
    seniority_score = 0
    if cv.get("seniority") and jd.get("seniority"):
        if cv["seniority"].lower() == jd["seniority"].lower():
            seniority_score = 10

    final_score = skill_score + experience_score + seniority_score
    final_score = int(round(min(final_score, 100)))

    # Detailed HR-friendly explanation
    details = {
        "required_ratio": required_ratio,
        "optional_ratio": optional_ratio,
        "skill_score": skill_score,
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
