# AI CV Parser & Matching Assistant

A lightweight AI-powered tool for parsing CVs (PDF/DOCX), extracting structured information, generating candidate summaries, and evaluating candidate–role compatibility using Job Descriptions (JD).


## Overview
This tool helps HR teams quickly understand whether a candidate is a good fit for a role by:

- parsing CV files,
- extracting key fields,
- analyzing skills and experience,
- comparing them with a Job Description,
- generating a match score and candidate summary.

Ideal for recruitment teams, HR assistants, and hiring managers looking to reduce manual CV screening time.


## Features
- **Upload CV** (PDF/DOCX)
- **Extract structured fields**:  
  name, email, phone, years of experience, seniority, technologies, languages
- **Upload Job Description (JD)** or paste job posting text
- **AI-based Matching Score (0–100%)**
- **3–5 sentence candidate summary**
- **JSON / PDF-ready output**
- **Streamlit UI** for HR-friendly interaction
- **FastAPI backend** (API-first design)


## Tech Stack
**Backend:**  
FastAPI, OpenAI API, pdfplumber, python-docx, pydantic, uvicorn  

**Frontend:**  
Streamlit  

**Deployment:**  
Render (API), Streamlit Cloud / HuggingFace Spaces (UI)


## Project Structure
```
cv_parser/
├── api/
│   ├── main.py
│   ├── routes.py
│   ├── models.py
│
├── parser/
│   ├── extract_text.py
│   ├── llm_extractor.py
│   ├── matching.py
│
├── frontend/
│   └── app.py
│
├── prompts/
│   ├── cv_extract_prompt.json
│   ├── matching_prompt.txt
│   └── summary_prompt.txt
│
├── requirements.txt
└── README.md
```

## Installation
1. Clone the repository:
```bash
git clone https://github.com/<michaelzelinka>/cv-parser.git
cd cv-parser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Add `.env` with your API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Start backend:
```bash
uvicorn api.main:app --reload
```

5. Start Streamlit UI:
```bash
streamlit run frontend/app.py
```


## API Example

### **POST /parse**
Uploads CV + optional Job Description text.

```
POST http://localhost:8000/parse
Content-Type: multipart/form-data

file=@cv.pdf
jd="Job description text here..."
```

### Example Response
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+420111222333",
  "years_experience": 5,
  "technologies": ["Python", "SQL"],
  "languages": ["English B2", "Czech C1"],
  "summary": "A backend engineer with strong Python experience...",
  "match_score": 82
}
```


## Roadmap
- Improved JD analysis (NER + scoring logic)
- Multi-candidate comparison
- One-click PDF report generation
- ATS export integrations (CSV/JSON/XML)
- SaaS version (login, project workspace, credits)
- Role-specific scoring models


## License
MIT License


## Contributing
Pull requests, improvements, or issue reports are welcome!


## Contact
**Michael Zelinka**  
GitHub: https://github.com/michaelzelinka 
Email: michaelzelinka9823@gmail.com

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal)
![License: MIT](https://img.shields.io/badge/License-MIT-green)
