async def compute_matching_v7_5(cv: dict, jd: dict | None):

    if jd is None:
        return {"score": 0, "details": {"reason": "no_jd"}}

    cv_skills = [s.lower() for s in cv.get("technologies_normalized", [])]
    jd_skills = [s.lower() for s in jd.get("required_skills", [])]

    # ✅ 1) STRING MATCH
    matches = sum(1 for req in jd_skills if req in cv_skills)
    string_score = (matches / max(len(jd_skills), 1)) * 70  # weight 70%

    # ✅ 2) EXPERIENCE
    cv_exp = cv.get("years_experience") or 0
    jd_exp = jd.get("min_experience") or 0
    exp_score = 10 if cv_exp >= jd_exp else (cv_exp / (jd_exp or 1)) * 10

    # ✅ 3) SENIORITY
    cv_sen = (cv.get("seniority") or "").lower()
    jd_sen = (jd.get("seniority") or "").lower()
    seniority_score = 10 if cv_sen == jd_sen else 5

    final = int(min(100, string_score + exp_score + seniority_score))

    return {
        "score": final,
        "details": {
            "string_score": string_score,
            "experience_score": exp_score,
            "seniority_score": seniority_score,
            "embedding_score": 0,  # embeddings vypnuté
        }
    }
