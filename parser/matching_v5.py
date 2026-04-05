async def compute_matching_v7_5(cv: dict, jd: dict | None):

    if jd is None:
        return {"score": 0, "details": {"reason": "no_jd"}}

    # ---------------------------------------
    # Normalized lists
    # ---------------------------------------
    cv_skills = [s.lower() for s in cv.get("technologies_normalized", [])]
    jd_required = [s.lower() for s in (jd.get("required_skills") or [])]
    jd_tech = [s.lower() for s in (jd.get("tech_stack") or [])]

    # ---------------------------------------
    # 1) TECH MATCH (0–60)
    # ---------------------------------------
    tech_hits = sum(1 for t in jd_tech if t in cv_skills)
    tech_score = (tech_hits / max(len(jd_tech), 1)) * 60 if jd_tech else 0

    # ---------------------------------------
    # 2) ROLE RELEVANCE (0–25)
    # ---------------------------------------
    # Pokud jde o technickou roli (má tech_stack)
    if len(jd_tech) >= 2:
        # technická role → technický kandidát
        if tech_hits > 0:
            role_score = 25
        else:
            role_score = 0
    else:
        # JD není technická → dáme body netechnickým lidem
        if tech_hits == 0:
            role_score = 25
        else:
            role_score = 10

    # ---------------------------------------
    # 3) EXPERIENCE (0–10)
    # ---------------------------------------
    cv_exp = cv.get("years_experience") or 0
    jd_exp = jd.get("min_experience") or 0

    if cv_exp >= jd_exp:
        exp_score = 10
    else:
        exp_score = (cv_exp / max(jd_exp, 1)) * 10

    # ---------------------------------------
    # 4) NOISE REDUCTION
    # ---------------------------------------
    penalty = 0
    # Pokud role je technická, ale kandidát má 0 tech_hits → tvrdá penalizace
    if len(jd_tech) >= 2 and tech_hits == 0:
        penalty = -30

    # ---------------------------------------
    # Final aggregation
    # ---------------------------------------
    final = int(max(0, min(100, tech_score + role_score + exp_score + penalty)))

    return {
        "score": final,
        "details": {
            "tech_score": tech_score,
            "role_score": role_score,
            "experience_score": exp_score,
            "penalty": penalty
        }
    }
