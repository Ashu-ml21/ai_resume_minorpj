import pdfplumber
from pydantic import BaseModel, Field
from schemas.scoring import QualityScore, BulletRewrite, SectionAudit
from schemas.interview import CoverLetter
from schemas.resume import ResumeData
from ollama_client import chat_structured

class _Rewrites(BaseModel):
    items: list[BulletRewrite] = Field(default_factory=list)

class _Audits(BaseModel):
    items: list[SectionAudit] = Field(default_factory=list)

def ats_check(path: str) -> dict:
    issues = []
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                if page.extract_tables():
                    issues.append(f"Page {i+1}: tables detected (ATS may misparse)")
                if page.images:
                    issues.append(f"Page {i+1}: images detected")
    except Exception:
        pass
    return {"issues": issues, "pass": len(issues) == 0}

def quality_score(resume: ResumeData) -> QualityScore:
    prompt = f"""Evaluate this resume. Fill ALL fields with numbers 0-100.
Do NOT leave notes empty. Write at least 3 notes explaining the scores.

Resume:
{resume.model_dump_json()}"""
    return chat_structured(prompt, QualityScore, system="You are a senior resume reviewer. Always provide scores and notes.")

def rewrite_bullets(bullets: list[str]) -> list[BulletRewrite]:
    if not bullets:
        return []
    
    prompt = f"""Rewrite these resume bullets using the STAR format (Situation, Task, Action, Result) with numbers. 
If a bullet is already good, rewrite it to be even more impactful.

Bullets:
{bullets}"""
    try:
        result = chat_structured(prompt, _Rewrites, system="You are an expert resume writer.")
        return result.items
    except Exception:
        return []

def audit_sections(resume: ResumeData) -> list[SectionAudit]:
    prompt = f"""Audit each section of this resume (Summary, Skills, Experience, Education). 
For EACH section, provide at least one strength or issue. Do not leave arrays empty.

Resume:
{resume.model_dump_json()}"""
    try:
        return chat_structured(prompt, _Audits, system="You are a meticulous resume auditor.").items
    except Exception:
        return []

def generate_cover_letter(resume: ResumeData, jd_text: str) -> CoverLetter:
    prompt = f"""Write a 3-paragraph cover letter. 
You MUST fill the 'body' field with the actual letter text. Do not leave it blank.

Job Description:
{jd_text[:3000]}

Resume:
{resume.model_dump_json()}"""
    try:
        return chat_structured(prompt, CoverLetter, system="You are an expert career coach.")
    except Exception:
        return CoverLetter(subject="Application", body="Failed to generate cover letter due to model limits.", highlights=[])