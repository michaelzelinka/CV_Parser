import re
from datetime import datetime

# ----------------------------------------------------
# ✅ Normalize experience (float)
# ----------------------------------------------------
def normalize_experience(value):
    """
    Handles cases like:
    5, "5", "5 years", "pět let", "2-4 years", "2020-2025",
    "around 3", "recent graduate", "some experience"
    """

    if value is None:
        return None

    text = str(value).lower().strip()

    # Case 1: pure number
    try:
        return float(text)
    except:
        pass

    # Case 2: year range e.g. 2020–2025
    match = re.match(r"(\d{4})\s*[-–]\s*(\d{4})", text)
    if match:
        y1, y2 = map(int, match.groups())
        if y2 >= y1:
            return float(y2 - y1)

    # Case 3: extract number from text
    num = re.search(r"(\d+(?:\.\d+)?)", text)
    if num:
        return float(num.group(1))

    # Case 4: Czech number words
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

    # Case 5: English words
    english_map = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }
    for word, num in english_map.items():
        if word in text:
            return float(num)

    # No extractable number
    return None


# ----------------------------------------------------
# ✅ Normalize list-like fields (technologies, languages)
# ----------------------------------------------------
def normalize_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value]
    if isinstance(value, str):
        return [v.strip() for v in re.split(r"[,;/•]", value) if v.strip()]

    return []


# ----------------------------------------------------
# ✅ Normalize email
# ----------------------------------------------------
def normalize_email(value):
    if not value:
        return None
    if "@" not in str(value):
        return None
    return value.strip()


# ----------------------------------------------------
# ✅ Normalize seniority
# ----------------------------------------------------
def normalize_seniority(value):
    if not value:
        return None

    v = value.lower()

    if "junior" in v:
        return "Junior"
    if "mid" in v or "medior" in v or "střední" in v:
        return "Mid"
    if "senior" in v:
        return "Senior"
    
    # fallback: capitalize first letter
    return value.strip().title()
