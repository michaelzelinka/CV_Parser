def compute_match_score(cv, jd):
    if not jd:
        return 50

    score = 0

    # 40% - skills overlap
    cv_skills = set(cv.get("technologies", []))
    jd_skills = set(jd.get("required_skills", []))

    if jd_skills:
        overlap = len(cv_skills & jd_skills) / len(jd_skills)
        score += overlap * 40

    # 30% - experience
    required = jd.get("min_experience", 0)
    cv_exp = cv.get("years_experience", 0)

    if required:
        score += min(cv_exp / required, 1) * 30

    # 30% - seniority
    if cv.get("seniority") == jd.get("seniority"):
        score += 30

    return round(score)
