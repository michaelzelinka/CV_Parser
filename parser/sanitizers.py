import re
from datetime import datetime


# =====================================================================
# ✅ EXPERIENCE NORMALIZATION (CZ/EN + ranges + text numbers)
# =====================================================================
def normalize_experience(value):
    """
    Handles all cases:
    - 5
    - "5"
    - "5 years"
    - "pět let"
    - "five years"
    - "2–4 years"
    - "around 3"
    - "2020–2025"
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

    # Case 2: year range "2018-2023"
    match = re.match(r"(\d{4})\s*[-–]\s*(\d{4})", text)
    if match:
        y1, y2 = map(int, match.groups())
        if y2 >= y1:
            return float(y2 - y1)

    # Case 3: explicit number inside text
    number = re.search(r"(\d+(?:\.\d+)?)", text)
    if number:
        return float(number.group(1))

    # Case 4: Czech text numbers
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

    # Case 5: English text numbers
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


# =====================================================================
# ✅ LIST NORMALIZATION
# =====================================================================
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


# =====================================================================
# ✅ LANGUAGES NORMALIZATION
# =====================================================================
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

    if isinstance(value, str):
        return normalize_list(value)

    normalized = []

    if isinstance(value, list):
        for item in value:
            # dict style {"language": "...", "level": "..."}
            if isinstance(item, dict):
                lang = item.get("language") or item.get("lang")
                level = item.get("level")

                if lang and level:
                    normalized.append(f"{lang} ({level})")
                elif lang:
                    normalized.append(str(lang))
                continue

            # plain string
            if isinstance(item, str):
                normalized.append(item.strip())

    return normalized


# =====================================================================
# ✅ EMAIL NORMALIZATION
# =====================================================================
def normalize_email(value):
    if not value:
        return None
    v = str(value).strip()
    return v if "@" in v else None


# =====================================================================
# ✅ SENIORITY NORMALIZATION
# =====================================================================
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


# =====================================================================
# ✅ SKILL NORMALIZER v2.0 (CZ→EN + unification + tech mapping)
# =====================================================================
def normalize_skill_label(skill: str) -> str:
    """
    Converts Czech skills and technology-specific labels into
    unified English "core skills" to allow proper scoring & embeddings.

    Example:
    - "datová analýza" → "data analysis"
    - "python" → "software development"
    - "power bi" → "data analysis"
    - "elk" → "system analysis"
    """

    if not skill:
        return ""

    s = skill.lower().strip()

    # ----------------------------------------
    # ✅ Direct CZ → EN translations
    # ----------------------------------------
    cz_to_en = {
        "datová analýza": "data analysis",
        "analýza dat": "data analysis",
        "projektové řízení": "project management",
        "řízení projektů": "project management",
        "umělá inteligence": "ai",
        "automatizace": "automation",
        "procesní automatizace": "automation",
        "správa klientského portfolia": "customer portfolio management",
        "testování": "software testing",
        "testování softwaru": "software testing",
        "analýza požadavků": "requirements analysis",
        "it bezpečnost": "it security",
        "bezpečnost": "security",
        "sociální sítě": "social media",
        "marketing": "marketing",
    }

    if s in cz_to_en:
        return cz_to_en[s]

    # ----------------------------------------
    # ✅ Technical keyword → core category
    # ----------------------------------------
    tech_map = {
        # Programming
        "python": "software development",
        "fastapi": "software development",
        "javascript": "software development",
        "typescript": "software development",
        "java": "software development",
        "c#": "software development",
        "c++": "software development",
        "php": "software development",

        # Data & BI
        "sql": "data analysis",
        "power bi": "data analysis",
        "tableau": "data analysis",
        "excel": "data analysis",

        # Systems
        "elk": "system analysis",
        "elasticsearch": "system analysis",
        "kibana": "system analysis",
        "logstash": "system analysis",

        # AI & Automation
        "ai": "ai",
        "ai/llm integrations": "ai",
        "llm": "ai",
        "chatbot": "ai",
        "chatbots": "ai",
        "automation": "automation",
        "process automation": "automation",

        # Enterprise
        "sap": "sap",
        "sap fiori": "sap",
        "application support": "application support",

        # Project
        "api": "software development",
        "git": "software development",
        "docker": "software development",
        "kubernetes": "software development",
        "project management": "project management",
        "scrum": "project management",
        "agile": "project management"
    }

    # ✅ partial keyword match
    for key, normalized in tech_map.items():
        if key in s:
            return normalized

    # fallback: lowercase raw skill
    return s
