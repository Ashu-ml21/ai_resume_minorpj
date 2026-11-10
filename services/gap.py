from schemas.scoring import GapAnalysis
from schemas.resume import ResumeData
from ollama_client import chat_structured


def analyze_gaps(resume: ResumeData, jd_text: str) -> GapAnalysis:
    prompt = f"""Compare this resume to the job description and identify gaps.

Job description:
{jd_text[:8000]}

Resume:
{resume.model_dump_json()}

Return:
- missing_keywords: important keywords in the JD absent from the resume
- missing_skills: skills the JD requires but the resume lacks
- suggested_projects: 3-5 concrete project ideas to bridge the gaps
- prioritized_feedback: list of objects {{priority: high|medium|low, issue: ..., suggestion: ...}}"""
    return chat_structured(prompt, GapAnalysis, system="You are a career coach focused on actionable advice.")