
async def compute_matching_v7_5(cv: dict, jd: dict | None):
    """
    UNIVERSAL HR-FRIENDLY SCORING ENGINE (v7.5)
    Fixes:
    - JD skill normalization
    - String match stability
    - Stronger embedding thresholds
    - Fair seniority scoring
    """

    if jd is None:
        return {"score": 0, "details": {"reason": "no_jd"}}

    # Normalize input
    cv_skills = cv.get("technologies_normalized", [])
    jd_req_raw = jd.get("required_skills") or []
    jd_req = [normalize_skill_label(s) for s in jd_req_raw]

    # Precompute CV embeddings
    cv_embs = [await embed(s) for s in cv_skills]

    # ============================================================
    # ✅ 1) STRING MATCH (0–40)
    # exact match only, no substring fuzziness
    # ============================================================
    string_score = 0
    max_string_score = len(jd_req) * 4

    cv_set = {s.lower() for s in cv_skills}

    for req in jd_req:
        if req.lower() in cv_set:
            string_score += 4

    string_score = (string_score / max_string_score * 40) if max_string_score else 0

    # ============================================================
    # ✅ 2) EMBEDDING MATCH (0–40)
    # new thresholds: >0.82 strong, >0.72 medium
    # ============================================================
    embed_score = 0
    embed_max = len(jd_req) * 4

    for req in jd_req:
        req_emb = await embed(req)
        sims = [cos(req_emb, cv_emb) for cv_emb in cv_embs] if cv_embs else []
        sim = max(sims) if sims else 0

        if sim > 0.82:
            embed_score += 4
        elif sim > 0.72:
            embed_score += 2

    embed_score = (embed_score / embed_max * 40) if embed_max else 0

    # ============================================================
    # ✅ 3) EXPERIENCE SCORE (0–10)
    # more fair for unknown JD experience
    # ============================================================
    cv_exp = cv.get("years_experience") or 0
    jd_exp = jd.get("min_experience")

    if not jd_exp:
        exp_score = min(cv_exp / 2, 10)   # up to 10 points
    else:
        ratio = min(cv_exp / jd_exp, 1)
        exp_score = ratio * 10

    # ============================================================
    # ✅ 4) SENIORITY SCORE (0–10)
    # perfect = 10
    # near match (mid ↔ senior) = 5
    # junior ↔ senior = 0
    # ============================================================
    cv_sen = (cv.get("seniority") or "").lower()
    jd_sen = (jd.get("seniority") or "").lower()

    if cv_sen == jd_sen and cv_sen:
        seniority_score = 10
    elif (cv_sen, jd_sen) in [
        ("mid", "senior"),
        ("senior", "mid")
    ]:
        seniority_score = 5
    else:
        seniority_score = 0

    # ============================================================
    # ✅ FINAL AGGREGATION
    # ============================================================
    raw_score = string_score + embed_score + exp_score + seniority_score

    # Hard cap for totally irrelevant candidates
    if string_score == 0 and embed_score == 0:
        final = min(raw_score, 3)
    else:
        final = raw_score

    final = int(max(0, min(100, final)))

    return {
        "score": final,
        "details": {
            "string_score": string_score,
            "embedding_score": embed_score,
            "experience_score": exp_score,
            "seniority_score": seniority_score,
        }
    }
