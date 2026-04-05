async def compute_matching_v7_5(cv: dict, jd: dict | None):

    if jd is None:
        return {"score": 0, "details": {"reason": "no_jd"}}

    cv_sk = [s.lower() for s in cv.get("technologies_normalized", [])]
    jd_req = [s.lower() for s in jd.get("required_skills", [])]
    jd_tech = [s.lower() for s in jd.get("tech_stack", [])]

    # 1) TECH MATCH (0–70)
    if jd_tech:
        tech_hits = sum(1 for s in jd_tech if s in cv_sk)
        tech_score = (tech_hits / len(jd_tech)) * 70
    else:
        tech_score = 0

    # 2) REQUIRED MATCH (0–20)
    if jd_req:
        req_hits = sum(1 for s in jd_req if s in cv_sk)
        req_score = (req_hits / len(jd_req)) * 20
    else:
        req_score = 0

    # 3) EXPERIENCE (0–5)
    cv_exp = cv.get("years_experience") or 0
    jd_exp = jd.get("min_experience") or 0
    exp_score = 5 if cv_exp >= jd_exp else (cv_exp / max(1, jd_exp)) * 5

    # 4) SENIORITY (0–5)
    cv_sen = (cv.get("seniority") or "").lower()
    jd_sen = (jd.get("seniority") or "").lower()
    seniority_score = 5 if cv_sen == jd_sen else 0

    # HARD PENALTY for non-technical candidates on technical roles
    penalty = 0
    if jd_tech and sum(1 for s in jd_tech if s in cv_sk) == 0:
        penalty = -50  # Sanitářka → okamžitě 0–5 %

    total = max(0, min(100, tech_score + req_score + exp_score + seniority_score + penalty))

    return {
        "score": int(total),
        "details": {
            "tech_score": tech_score,
            "required_score": req_score,
            "experience_score": exp_score,
            "seniority_score": seniority_score,
            "penalty": penalty
        }
    }
