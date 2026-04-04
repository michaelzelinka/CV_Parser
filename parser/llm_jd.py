from openai import AsyncOpenAI

client = AsyncOpenAI()

SYSTEM_PROMPT = """
You are an expert HR analyst and job‑description interpreter.

Your task:
➡️ Extract REAL, CONCRETE job requirements from ANY job description text.
➡️ MUST work for ALL job types (industry‑agnostic).

This includes:
- manufacturing, warehouse, logistics
- healthcare, social care
- administration, HR, customer support
- sales, marketing, finance, accounting
- IT, engineering, QA, devops, data
- junior, mid, senior, trainee roles
- management and leadership roles

---------------------------------------
### ✅ RULES FOR REQUIRED SKILLS
---------------------------------------
Extract **only measurable, concrete skills or technologies**.

Examples:
- “vývoj aplikací” → "application development"
- “Python” → "python"
- “FastAPI” → "fastapi"
- “řízení VZV” → "forklift operation"
- “péče o pacienty” → "patient care"
- “účtování DPH” → "tax accounting"
- “komunikace se zákazníky” → "customer communication"
- “práce s pokladnou” → "cash register operation"
- “plánování směn” → "shift planning"
- “analýza dat” → "data analysis"
- “marketingové kampaně” → "marketing campaigns"
- “produktové myšlení” → "product thinking"

Extract **implicit skills** too:
- If JD mentions “we build internal tools”, extract "internal tools development".
- If JD mentions “automatizace”, extract "process automation".
- If JD mentions AI usage, extract "ai automation".

NEVER extract fluff:  
❌ team player  
❌ motivated  
❌ friendly  
❌ enthusiasm  

---------------------------------------
### ✅ RULES FOR NICE‑TO‑HAVE SKILLS
---------------------------------------
Extract optional or “advantage” items.
Only concrete skills, not personality traits.

---------------------------------------
### ✅ SENIORITY
---------------------------------------
Must be EXACTLY one of:
- "Senior"
- "Mid"
- "Junior"
- "Trainee"

Infer from language:
- “samostatný, zodpovědnost, ownership, senior” → Senior
- “praxe X let, zkušenost” → Mid
- “junior, vhodné pro absolventy” → Junior
- “naučíme vás, trainee program” → Trainee

If unclear:  
→ classify based on tasks complexity  
→ default = “Mid”

---------------------------------------
### ✅ MIN EXPERIENCE (years)
---------------------------------------
If JD mentions explicit number → use it.
If implicit:
- Senior → 5
- Mid → 2
- Junior → 0
- Trainee → 0

---------------------------------------
### ✅ OUTPUT FORMAT (STRICT JSON!)
---------------------------------------
{
  "role": string,
  "required_skills": [string],
  "nice_to_have_skills": [string],
  "seniority": "Senior | Mid | Junior | Trainee",
  "min_experience": number
}

Only output JSON. No prose.
"""

FALLBACK_PROMPT = """
Extract REQUIRED skills from the job description ONLY as a flat list of keywords.
Use simple noun phrases like:
- python
- fastapi
- api design
- customer communication
- forklift operation
- patient care
- data entry
- accounting

Output JSON:
{ "required_skills": [ ... ] }
"""


async def extract_structured_jd(jd_text: str) -> dict:
    """
    Universal JD extractor v7.1
    with intelligent fallback if the main extractor returns empty skills.
    """

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": jd_text},
    ]

    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0
        )

        jd_data = resp.choices[0].message.parsed

        # ✅ If extractor failed to identify skills, use fallback
        if not jd_data.get("required_skills"):
            fb = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": FALLBACK_PROMPT},
                    {"role": "user", "content": jd_text},
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            fallback = fb.choices[0].message.parsed
            jd_data["required_skills"] = fallback.get("required_skills", [])

        return jd_data

    except Exception:
        # Safe fallback for absolutely anything
        return {
            "role": "Unknown",
            "required_skills": [],
            "nice_to_have_skills": [],
            "seniority": "Mid",
            "min_experience": 0
        }
