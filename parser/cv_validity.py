import re

def is_probably_cv(text: str, cv_data: dict) -> bool:
    """
    Heuristický CV checker.
    Vrací True = dokument vypadá jako CV.
    Vrací False = dokument je s velkou pravděpodobností smlouva, legal nebo šum.
    """

    if not text or len(text) < 200:
        return False

    text_low = text.lower()

    # ---------------------------------------------------------
    # ❌ 1) Detekce dokumentů, které NIKDY nejsou CV
    # ---------------------------------------------------------
    legal_keywords = [
        "smlouva", "nájemní", "pronajímatel", "nájemce",
        "ustanovení", "uzavřeli", "strany se dohodly", 
        "závazek", "dlužník", "věřitel", "plátce",
        "agreement", "whereas", "hereby",
        "invoice", "factura", "účtenka",
        "podmínky", "lhůta", "úhrada", "povinnost",
        "článek", "odstavec", "ustanovení", "příloha"
    ]
    if any(k in text_low for k in legal_keywords):
        return False

    # ---------------------------------------------------------
    # ✅ 2) Pozitivní signály že jde o CV (alespoň 2)
    # ---------------------------------------------------------
    positive_signals = 0

    # Name must not be empty and not look like one word
    name = cv_data.get("name")
    if name and len(name.split()) >= 2:
        positive_signals += 1

    # Email valid
    email = cv_data.get("email")
    if email and "@" in email:
        positive_signals += 1

    # Phone number pattern
    phone = cv_data.get("phone")
    if phone and re.search(r"\+?\d{9,12}", phone):
        positive_signals += 1

    # Position hints in extracted text
    cv_keywords = [
        "experience", "work history", "professional summary",
        "skills", "technologies", "languages", "certifications",
        "education", "projects",
        "praxe", "zkušenosti", "vzdělání", "znalosti", "technologie"
    ]
    if any(k in text_low for k in cv_keywords):
        positive_signals += 1

    # Must meet at least 2 positive signals
    return positive_signals >= 2
