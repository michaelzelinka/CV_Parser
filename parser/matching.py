def compute_match_score(cv, jd):
    if not jd:
        return 50  # neutral score

    score = 0

    # 30% - skills overlap
    cv_skills = set(cv.get("technologies", []))
    jd_skills = set(jd.get("required_skills", []))
    if jd_skills:
        overlap = len(cv_skills & jd_skills) / len(jd_skills)
        score += overlap * 30

    # 30% - years of experience
    required_exp = jd.get("min_experience", 0)
    cv_exp = cv.get("years_experience", 0)
    if required_exp:
        exp_score = min(cv_exp / required_exp, 1) * 30
        score += exp_score

    # 40% - seniority match
    if cv.get("seniority") == jd.get("seniority"):
        score += 40

    return round(score)
