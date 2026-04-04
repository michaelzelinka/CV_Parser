import pdfplumber
from docx import Document
import tempfile

async def extract_text_from_file(upload):
    filename = upload.filename.lower()
    suffix = filename.split(".")[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(await upload.read())
        tmp_path = tmp.name

    if suffix == "pdf":
        text = ""
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
        return text.strip()

    if suffix == "docx":
        doc = Document(tmp_path)
        return "\n".join(p.text for p in doc.paragraphs).strip()

    return ""
