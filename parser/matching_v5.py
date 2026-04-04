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


# ---------------------------------------------------------
# ✅ Skill categories
# ---------------------------------------------------------
CATEGORIES = {
    "backend": {
        "keywords": ["python", "fastapi", "django", "javascript", "node", "backend", "api"],
        "weight": 3
    },
    "data": {
        "keywords": ["sql", "data analysis", "analytics", "power bi", "tableau"],
        "weight": 3
    },
    "ai": {
        "keywords": ["ai", "llm", "machine learning", "automation", "chatbot"],
        "weight": 3
    },
    "enterprise": {
        "keywords": ["sap", "sap fiori", "crm"],
        "weight": 3
    },
    "testing": {
        "keywords": ["testing", "qa", "software testing"],
        "weight": 2
    },
    "devops": {
        "keywords": ["docker", "kubernetes", "ci", "cd"],
        "weight": 2
    },
    "soft": {
        "keywords": ["communication", "teamwork", "presentation"],
        "weight": 1
    }
}

# ---------------------------------------------------------
# ✅ Seniority alignment model
# ---------------------------------------------------------
SENIORITY_GRID = {
    ("Trainee", "Senior"): -20,
    ("Trainee", "Mid"): -10,
    ("Trainee", "Junior"): +2,
    ("Trainee", "Trainee"): +5,

    ("Junior", "Senior"): -12,
    ("Junior", "Mid"): -5,
    ("Junior", "Junior"): +5,
    ("Junior", "Trainee"): +3,

    ("Mid", "Senior"): +3,
    ("Mid", "Mid"): +5,
    ("Mid", "Junior"): -8,
    ("Mid", "Trainee"): -15,

    ("Senior", "Senior"): +5,
    ("Senior", "Mid"): +3,
    ("Senior", "Junior"): -10,
    ("Senior", "Trainee"): -20,
}

async def compute_matching_v5(cv: dict, jd: dict | None):
    if jd is None:
        return {"score": 50, "details": {"reason": "No JD provided"}}

    cv_sk = cv.get("technologies_normalized", [])
    jd_req = jd.get("required_skills", [])
    jd_opt = jd.get("nice_to_have_skills", [])

    cv_embs = [await embed(s) for s in cv_sk]

    # -----------------------------------------------------
    # ✅ 1) Required skill fuzzy matching (max 60)
    # -----------------------------------------------------
    required_raw = 0
    required_total_weight = 0

    for skill in jd_req:
        s_emb = await embed(skill)
        sim = max(cos(s_emb, cv_emb) for cv_emb in cv_embs)

        # find category weight
        weight = 1
        sl = skill.lower()
        for c in CATEGORIES.values():
            if any(k in sl for k in c["keywords"]):
                weight = c["weight"]

        required_total_weight += weight

        # fuzzy matching buckets
        if sim > 0.80:
            required_raw += 1.0 * weight
        elif sim > 0.65:
            required_raw += 0.6 * weight
        elif sim > 0.45:
            required_raw += 0.3 * weight

    required_score = 0
    if required_total_weight > 0:
        required_score = (required_raw / required_total_weight) * 60

    # -----------------------------------------------------
    # ✅ 2) Optional skill fuzzy scoring (max 10)
    # -----------------------------------------------------
    optional_score = 0
    for skill in jd_opt:
        s_emb = await embed(skill)
        sim = max(cos(s_emb, cv_emb) for cv_emb in cv_embs)

        if sim > 0.80:
            optional_score += 1.5
        elif sim > 0.65:
            optional_score += 0.7

    optional_score = min(optional_score, 10)

    # -----------------------------------------------------
    # ✅ 3) Experience alignment (0–15)
    # -----------------------------------------------------
    cv_exp = cv.get("years_experience") or 0
    jd_exp = jd.get("min_experience") or 0

    if jd_exp == 0:
        exp_score = min(cv_exp * 0.4, 4)    # small bonus
    else:
        ratio = min(cv_exp / jd_exp, 1.0)
        exp_score = ratio * 15

    # -----------------------------------------------------
    # ✅ 4) Seniority alignment (−20 to +5)
    # -----------------------------------------------------
    cv_sen = cv.get("seniority") or "Unknown"
    jd_sen = jd.get("seniority") or "Unknown"

    seniority_score = SENIORITY_GRID.get((jd_sen, cv_sen), 0)

    # -----------------------------------------------------
    # ✅ 5) Hard Floor Safety
    # -----------------------------------------------------
    if required_score == 0 and optional_score == 0:
        final_score = min(exp_score + seniority_score, 10)
    else:
        final_score = required_score + optional_score + exp_score + seniority_score

    # -----------------------------------------------------
    # ✅ 6) Score shaping (ATS-like realism)
    # -----------------------------------------------------
    if required_score < 5:
        final_score = min(final_score, 25)
    if required_score < 2:
        final_score = min(final_score, 15)

    # prevent negative
    final_score = int(max(0, min(100, final_score)))

    details = {
        "required_score": required_score,
        "optional_score": optional_score,
        "experience_score": exp_score,
        "seniority_score": seniority_score,
    }

    return {
        "score": final_score,
        "details": details
    }
