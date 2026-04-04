import re
from datetime import datetime


# ----------------------------------------------------
# ✅ Normalize experience (float)
# ----------------------------------------------------
def normalize_experience(value):
    """
    Handles:
    - 5
    - "5"
    - "5 years"
    - "pět let"
    - "five years"
    - "2–4 years"
    - "around 3"
    - "2020–2025", "2018-2021"
    - "recent graduate" -> None
    """
    if value is None:
        return None

    text = str(value).lower().strip()

    # Case 1: raw number
    try:
        return float(text)
    except:
        pass

    # Case 2: year range "2018–2023"
    match = re.match(r"(\d{4})\s*[-–]\s*(\d{4})", text)
    if match:
        y1, y2 = map(int, match.groups())
        if y2 >= y1:
            return float(y2 - y1)

    # Case 3: explicit number in text
    number = re.search(r"(\d+(?:\.\d+)?)", text)
    if number:
        return float(number.group(1))

    # Case 4: Czech words → number
    czech_map = {
        "jeden": 1, "jedna": 1,
        "dva": 2, "dvě": 2,
        "tři": 3,
        "čtyři": 4,
        "pět": 5,
        "šest": 6,
        "sedm": 7,
        "osm": 8,
        "devět": 9,
        "deset": 10,
    }
    for word, num in czech_map.items():
        if word in text:
            return float(num)

    # Case 5: English words → number
    english_map = {
        "one": 1, "two": 2, "three": 3,
        "four": 4, "five": 5,
        "six": 6, "seven": 7,
        "eight": 8, "nine": 9,
        "ten": 10,
    }
    for word, num in english_map.items():
        if word in text:
            return float(num)

    return None


# ----------------------------------------------------
# ✅ Normalize list-like fields
# ----------------------------------------------------
def normalize_list(value):
    """
    Accepts:
    - None
    - "Python, SQL, Docker"
    - ["Python", "SQL"]
    - "Python / SQL / Docker"
    """
    if value is None:
        return []

    if isinstance(value, list):
        return [str(v).strip() for v in value if v]

    if isinstance(value, str):
        return [
            v.strip()
            for v in re.split(r"[;,/•|\n]", value)
            if v.strip()
        ]

    return []


# ----------------------------------------------------
# ✅ Normalize language entries (CZ/EN, dicts)
# ----------------------------------------------------
def normalize_language_items(value):
    """
    Handles:
    - ["English", "German"]
    - "English, Czech"
    - [{"language": "čeština", "level": "native"}]
    - [{"language": "angličtina", "level": "B2"}]
    """
    if value is None:
        return []

    # Already a flat string
    if isinstance(value, str):
        return normalize_list(value)

    normalized = []

    if isinstance(value, list):
        for item in value:

            # Case 1: dict style {"language": "...", "level": "..."}
            if isinstance(item, dict):
                lang = item.get("language") or item.get("lang")
                level = item.get("level")

                if lang and level:
                    normalized.append(f"{lang} ({level})")
                elif lang:
                    normalized.append(str(lang))
                continue

            # Case 2: plain string
            if isinstance(item, str):
                normalized.append(item.strip())

    return normalized


# ----------------------------------------------------
# ✅ Normalize email
# ----------------------------------------------------
def normalize_email(value):
    if not value:
        return None
    v = str(value).strip()
    return v if "@" in v else None


# ----------------------------------------------------
# ✅ Normalize seniority
# ----------------------------------------------------
def normalize_seniority(value):
    if not value:
        return None

    v = str(value).lower()

    if "trainee" in v or "graduate" in v:
        return "Trainee"
    if "junior" in v or "asistent" in v:
        return "Junior"
    if "mid" in v or "medior" in v or "střední" in v:
        return "Mid"
    if "senior" in v:
        return "Senior"

    return value.strip().title()


# ----------------------------------------------------
# ✅ Bilingual CZ→EN skill normalizer
# ----------------------------------------------------
def normalize_skill_label(skill: str) -> str:
    """
    Converts Czech skills to English equivalents so scoring works.
    Example:
    - "datová analýza" → "data analysis"
    - "projektové řízení" → "project management"
    """

    if not skill:
        return ""

    s = skill.lower().strip()

    mapping = {
        "datová analýza": "data analysis",
        "analýza dat": "data analysis",
        "projektové řízení": "project management",
        "řízení projektů": "project management",
        "analýza požadavků": "requirements analysis",
        "testování": "software testing",
        "biometrická data": "biometrics",
        "aplikace": "application support",
        "správa klientského portfolia": "customer portfolio management",
        "bezpečnost": "security",
        "it bezpečnost": "it security",
        "sociální sítě": "social media",
        "marketing": "marketing",
    }

    if s in mapping:
        return mapping[s]

    return skill.strip().lower()
