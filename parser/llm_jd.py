from openai import AsyncOpenAI

client = AsyncOpenAI()

SYSTEM_PROMPT = """
You are an expert HR analyst. 
Your task is to extract clear, structured, universal job requirements from ANY job description.

This MUST work for ALL job types:
- manufacturing / warehouse / blue-collar
- healthcare / social care
- customer support / office admin / HR
- finance / accounting
- sales / marketing
- engineering / IT / dev / data
- managerial roles
- junior / senior / trainee

RULES:
1. ALWAYS extract concrete skill keywords even if mentioned implicitly.
2. Extract only meaningful skills, not generic fluff ("motivated", "nice", "friendly").
3. If the job implies domain knowledge, extract it as a skill. Example:
   - "we use forklifts" → skill: "forklift operation"
   - "we write internal tools" → skill: "internal tools development"
   - "clean code" → skill: "code quality"
   - "communication with clients" → skill: "client communication"
   - "working in hospital wards" → skill: "clinical operations"
4. For IT roles, extract technologies (python, fastapi, sql, kubernetes…) ONLY if explicitly present.
5. For healthcare roles, extract clinical competencies ONLY if relevant.
6. For warehouse roles, extract physical and logistics tasks.
7. For sales, extract communication, CRM, negotiation.
8. For marketing, extract PPC, SEO, content writing etc.
9. REQUIRED skills = MUST-HAVE skills (core tasks).
10. NICE-TO-HAVE skills = optional or "advantage".
11. Seniority must be "Senior", "Mid", "Junior", "Trainee".
    If unclear, infer based on phrases:
       - "we expect ownership", "architect", "lead" → Senior
       - "independent", "experience needed" → Mid
       - "junior", "entry-level" → Junior
       - "we teach you", "you will learn" → Trainee
12. Extract minimum years of experience:
    - If explicitly stated, use it.
    - If implied:
        "experienced" → 3
        "junior" → 0
        "senior" → 5
        "mid" → 2
        "trainee" → 0

OUTPUT STRICTLY AS JSON:
{
  "role": string,
  "required_skills": [ ... ],
  "nice_to_have_skills": [ ... ],
  "seniority": "Senior|Mid|Junior|Trainee",
  "min_experience": number
}
"""

async def extract_structured_jd(jd_text: str) -> dict:
    """
    Universal JD extractor (v7).
    Works for ALL industries and job types.
    Produces structured JSON for scoring.
    """

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": jd_text}
    ]

    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0
        )
        return resp.choices[0].message.parsed
    except Exception as e:
        # fallback
        return {
            "role": "Unknown",
            "required_skills": [],
            "nice_to_have_skills": [],
            "seniority": "Junior",
            "min_experience": 0
        }
