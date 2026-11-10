import ollama
from schemas.resume import ResumeData
from ollama_client import MODELS


async def stream_analysis(resume: ResumeData, jd_text: str):
    """Yield analysis tokens live, one by one."""
    prompt = f"""You are a senior resume coach. Analyse this candidate's resume against the job
description. Structure your output with markdown section headers:

## Overall Impression
(2-3 sentences)

## Strengths
- one bullet per strength

## Critical Gaps
- one bullet per gap

## Top 5 Action Items
1. numbered, specific, measurable action

Be concrete. Reference exact resume phrasing. Never invent facts.

Job Description:
{jd_text[:6000]}

Resume:
{resume.model_dump_json()}"""

    stream = await ollama.AsyncClient().chat(
        model=MODELS["default"],
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        options={"temperature": 0.3, "num_ctx": 8192},
    )
    async for chunk in stream:
        piece = chunk["message"]["content"]
        if piece:
            yield piece