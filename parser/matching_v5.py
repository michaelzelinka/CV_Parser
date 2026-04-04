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


# =============================================================================
# ✅ Skill Categories (weights)
# =============================================================================
CATEGORIES = {
    "backend": {
        "keywords": ["python", "fastapi", "api", "backend", "microservice", "server"],
        "weight": 4
    },
    "ai": {
        "keywords": ["ai", "llm", "automation", "machine learning", "chatbot"],
        "weight": 3
    },
    "data": {
        "keywords": ["sql", "etl", "data", "analytics"],
        "weight": 2
    },
    "frontend": {
        "keywords": ["vue", "javascript", "typescript"],
        "weight": 1
    },
}


# =============================================================================
# ✅ Seniority alignment matrix
# =============================================================================
SENIORITY_GRID = {
    ("Senior", "Senior"): +10,
    ("Mid", "Senior"): +3,
    ("Junior", "Senior"): -10,
    ("Trainee", "Senior"): -20,

    ("Senior", "Mid"): +3,
    ("Mid", "Mid"): +5,
    ("Junior", "Mid"): -5,
    ("Trainee", "Mid"): -15,

    ("Senior", "Junior"): -8,
    ("Mid", "Junior"): -3,
    ("Junior", "Junior"): +6,
    ("Trainee", "Junior"): -5,

    ("Senior", "Trainee"): -20,
    ("Mid", "Trainee"): -10,
    ("Junior", "Trainee"): +1,
    ("Trainee", "Trainee"): +6,
}


# =============================================================================
# ✅ MAIN SCORING FUNCTION v5.0
# =============================================================================
async def compute_matching_v5(cv: dict, jd: dict | None):
    if jd is None:
        return {"score": 50, "details": {"reason": "No JD provided"}}

    cv_sk = cv.get("technologies_normalized", [])
    jd_req = jd.get("required_skills", [])
    jd_opt = jd.get("nice_to_have_skills", [])

    cv_embs = [await embed(s) for s in cv_sk]

    # =============================================================
    # ✅ 1) Required skill fuzzy scoring → 0–60
    # =============================================================
    req_raw = 0
    req_total_weight = 0

    for skill in jd_req:
        s_emb = await embed(skill)
        similarities = [cos(s_emb, e) for e in cv_embs]
        sim = max(similarities) if similarities else 0.0

        weight = 1
        sl = skill.lower()
        for cat in CATEGORIES.values():
            if any(k in sl for k in cat["keywords"]):
                weight = cat["weight"]

        req_total_weight += weight

        if sim > 0.80:
            req_raw += 1.0 * weight
        elif sim > 0.65:
            req_raw += 0.6 * weight
        elif sim > 0.45:
            req_raw += 0.2 * weight

    required_score = 0
    if req_total_weight > 0:
        required_score = (req_raw / req_total_weight) * 60


    # =============================================================
    # ✅ 2) Optional skill scoring → 0–10
    # =============================================================
    opt_score = 0

    for skill in jd_opt:
        s_emb = await embed(skill)
        sim = max(cos(s_emb, e) for e in cv_embs) if cv_embs else 0.0

        if sim > 0.80:
            opt_score += 1.5
        elif sim > 0.60:
            opt_score += 0.7

    opt_score = min(opt_score, 10)


    # =============================================================
    # ✅ 3) Experience alignment → 0–15
    # =============================================================
    cv_exp = cv.get("years_experience") or 0
    jd_exp = jd.get("min_experience") or 0

    if jd_exp == 0:
        exp_score = min(cv_exp * 0.5, 4)
    else:
        ratio = min(cv_exp / jd_exp, 1.0)
        exp_score = ratio * 15


    # =============================================================
    # ✅ 4) Seniority alignment (penalty/bonus)
    # =============================================================
    cv_sen = cv.get("seniority") or "Unknown"
    jd_sen = jd.get("seniority") or "Unknown"

    seniority_score = SENIORITY_GRID.get((jd_sen, cv_sen), 0)


    # =============================================================
    # ✅ 5) Hard-fail rule (no relevant match → max 10)
    # =============================================================
    if required_score < 5 and opt_score < 3:
        final_score = min(exp_score + seniority_score, 10)
    else:
        final_score = required_score + opt_score + exp_score + seniority_score

    final_score = int(max(0, min(100, final_score)))

    return {
        "score": final_score,
        "details": {
            "required_score": required_score,
            "optional_score": opt_score,
            "experience_score": exp_score,
            "seniority_score": seniority_score
        }
    }
``
