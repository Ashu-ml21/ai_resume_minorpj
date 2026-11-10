import pdfplumber, docx, os
from schemas.resume import ResumeData
from ollama_client import chat_structured, PARSER_MODEL


def extract_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    if ext in (".docx", ".doc"):
        d = docx.Document(path)
        return "\n".join(p.text for p in d.paragraphs)
    if ext == ".txt":
        return open(path, encoding="utf-8").read()
    raise ValueError(f"Unsupported file type: {ext}")


def parse_resume_text(text: str) -> ResumeData:
    prompt = f"Extract structured resume data from the following text:\n\n{text[:12000]}"
    return chat_structured(
        prompt,
        ResumeData,
        system="You are a precise resume parser. Extract only what is explicitly present. Never invent data.",
        model=PARSER_MODEL,
    )


def anonymize(resume: ResumeData) -> ResumeData:
    return resume.model_copy(update={
        "name": "[REDACTED]",
        "email": "[REDACTED]",
        "phone": "[REDACTED]",
    })