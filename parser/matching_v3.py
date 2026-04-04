import numpy as np
from openai import AsyncOpenAI

client = AsyncOpenAI()

_embedding_cache = {}

async def get_embedding(text: str):
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


def cosine_sim(a, b):
    if a is None or b is None:
        return 0.0
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


# ----------------------------------------------------
# ✅ Skill categories
# ----------------------------------------------------
CATEGORY_KEYWORDS = {
    "backend": ["python", "fastapi", "django", "api", "backend", "server"],
    "data": ["sql", "power bi", "tableau", "data analysis", "analytics"],
    "ai": ["ai", "machine learning", "automation", "chatbot"],
    "enterprise": ["sap", "sap fiori", "crm"],
    "testing": ["testing", "qa", "software testing"],
    "devops": ["docker", "kubernetes", "ci", "cd"]
}

CATEGORY_WEIGHTS = {
    "backend": 3,
    "data": 3,
    "ai": 3,
    "enterprise": 3,
    "testing": 2,
    "devops": 2,
}

# ----------------------------------------------------
# ✅ Seniority mismatch penalties
# ----------------------------------------------------
SENIORITY_PENALTY = {
    ("Trainee", "Senior"): -15,
    ("Trainee", "Mid"): -8,
    ("Senior", "Junior"): -12,
    ("Senior", "Trainee"): -20,
    ("Mid", "Senior"): -5,
}


async def compute_matching_v4(cv: dict, jd: dict | None):
    if jd is None:
        return {"score": 50, "details": {"reason": "No JD provided"}}

    cv_skills = cv.get("technologies_normalized", [])
    jd_req = jd.get("required_skills", [])
    jd_opt = jd.get("nice_to_have_skills", [])
    details = {}

    # -----------------------------------------
    # ✅ 1) Required skill fuzzy matching (weighted)
    # -----------------------------------------
    required_score = 0
    total_required_weight = 0

    cv_embs = [await get_embedding(s) for s in cv_skills]

    for req in jd_req:
        req_emb = await get_embedding(req)

        best_sim = max(cosine_sim(req_emb, cv_emb) for cv_emb in cv_embs)
        category_weight = 1

        # category detection
        for cat, words in CATEGORY_KEYWORDS.items():
            if any(w in req.lower() for w in words):
                category_weight = CATEGORY_WEIGHTS[cat]

        total_required_weight += category_weight

        # similarity contribution
        if best_sim > 0.75:
            required_score += 1.0 * category_weight
        elif best_sim > 0.60:
            required_score += 0.6 * category_weight
        elif best_sim > 0.40:
            required_score += 0.3 * category_weight

    details["required_score_raw"] = required_score

    # normalize to 0–60
    if total_required_weight > 0:
        required_score = (required_score / total_required_weight) * 60
    else:
        required_score = 0

    # -----------------------------------------
    # ✅ 2) Optional skill fuzzy scoring (0–10)
    # -----------------------------------------
    optional_score = 0
    if jd_opt:
        for opt in jd_opt:
            opt_emb = await get_embedding(opt)
            sim = max(cosine_sim(opt_emb, cv_emb) for cv_emb in cv_embs)

            if sim > 0.75:
                optional_score += 1.5
            elif sim > 0.60:
                optional_score += 0.7

        optional_score = min(optional_score, 10)

    # -----------------------------------------
    # ✅ 3) Experience alignment (0–20)
    # -----------------------------------------
    cv_exp = cv.get("years_experience") or 0
    jd_exp = jd.get("min_experience") or 0

    if jd_exp == 0:
        exp_score = min(cv_exp * 0.5, 5)  # small bonus
    else:
        ratio = min(cv_exp / jd_exp, 1.0)
        exp_score = ratio * 20

    # -----------------------------------------
    # ✅ 4) Seniority mismatch (±10)
    # -----------------------------------------
    cv_sen = cv.get("seniority")
    jd_sen = jd.get("seniority")

    seniority_score = 0
    if (jd_sen, cv_sen) in SENIORITY_PENALTY:
        seniority_score = SENIORITY_PENALTY[(jd_sen, cv_sen)]
    elif jd_sen == cv_sen:
        seniority_score = +10

    # -----------------------------------------
    # ✅ 5) Hard floor rule
    # -----------------------------------------
    if required_score == 0 and optional_score == 0:
        final_score = min(exp_score + seniority_score, 10)
    else:
        final_score = required_score + optional_score + exp_score + seniority_score

    # clamp
    final_score = int(max(0, min(100, final_score)))

    # -----------------------------------------
    # ✅ 6) Details
    # -----------------------------------------
    details.update({
        "required_score": required_score,
        "optional_score": optional_score,
        "experience_score": exp_score,
        "seniority_score": seniority_score,
    })

    return {
        "score": final_score,
        "details": details
    }
``
