async def compute_matching_v7_5(cv: dict, jd: dict | None):
    if jd is None:
        return {"score": 0, "details": {"reason": "no_jd"}}

    # LOWERCASE
    cv_sk = [s.lower() for s in cv.get("technologies_normalized", [])]
    jd_req = [s.lower() for s in jd.get("required_skills", [])]
    jd_tech = [s.lower() for s in jd.get("tech_stack", [])]

    # ✅ 1) REQUIRED SKILLS score (0–40)
    req_matches = sum(1 for s in jd_req if s in cv_sk)
    req_score = (req_matches / max(len(jd_req), 1)) * 40 if jd_req else 20

    # ✅ 2) TECH STACK score (0–40)
    tech_matches = sum(1 for s in jd_tech if s in cv_sk)
    tech_score = (tech_matches / max(len(jd_tech), 1)) * 40 if jd_tech else 0

    # ✅ 3) EXPERIENCE (0–10)
    cv_exp = cv.get("years_experience") or 0
    jd_exp = jd.get("min_experience") or 0
    exp_score = 10 if cv_exp >= jd_exp else max(0, (cv_exp / max(jd_exp, 1)) * 10)

    # ✅ 4) SENIORITY (0–10)
    cv_s = (cv.get("seniority") or "").lower()
    jd_s = (jd.get("seniority") or "").lower()
    seniority_score = 10 if cv_s == jd_s else 5

    final = int(min(100, req_score + tech_score + exp_score + seniority_score))

    return {
        "score": final,
        "details": {
            "required_score": req_score,
            "tech_stack_score": tech_score,
            "experience_score": exp_score,
            "seniority_score": seniority_score,
        }
    }
