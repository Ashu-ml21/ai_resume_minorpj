from schemas.scoring import ScoreResult, DeepScoreResult, RubricConfig
from schemas.resume import ResumeData
from ollama_client import chat_structured, embed, cosine_sim, DEFAULT_MODEL


def semantic_similarity(resume_text: str, jd_text: str) -> float:
    """Return 0–100 similarity. Never raises."""
    try:
        a = embed(resume_text)
        b = embed(jd_text)
        if not any(a) or not any(b):
            return 0.0
        return round(cosine_sim(a, b) * 100, 2)
    except Exception:
        return 0.0


def score_resume(resume: ResumeData, jd_text: str, rubric: RubricConfig | None = None) -> ScoreResult:
    rubric = rubric or RubricConfig()
    ctx = f"Regional context: {rubric.regional_context}\n" if rubric.regional_context else ""
    prompt = f"""Score this resume against the job description.

{ctx}Must-have skills: {rubric.must_have_skills}
Nice-to-have skills: {rubric.nice_to_have_skills}

Job description:
{jd_text[:8000]}

Resume JSON:
{resume.model_dump_json()}

Return weighted total_score (0-100), must_have_coverage (0-100), nice_to_have_coverage (0-100),
and an evidence list with exact resume quotes proving each match."""
    return chat_structured(prompt, ScoreResult, system="You are a fair, evidence-based recruiter.")


def verify_quotes(result: DeepScoreResult, raw_text: str) -> DeepScoreResult:
    for ev in result.evidence:
        if ev.matched_quote and ev.matched_quote in raw_text:
            ev.quote_verified = True
        elif ev.matched_quote:
            ev.quote_verified = False
            ev.confidence *= 0.5
    return result


def deep_score_resume(
    resume: ResumeData,
    jd_text: str,
    raw_text: str,
    rubric: RubricConfig | None = None,
) -> DeepScoreResult:
    rubric = rubric or RubricConfig()
    ctx = f"Regional context: {rubric.regional_context}\n" if rubric.regional_context else ""
    prompt = f"""Do a deep analysis of this resume against the job description.

{ctx}Must-have skills: {rubric.must_have_skills}
Nice-to-have skills: {rubric.nice_to_have_skills}

Job description:
{jd_text[:8000]}

Resume JSON:
{resume.model_dump_json()}

Steps:
1. For each requirement, classify evidence as EXACT_MATCH, SEMANTIC_INFERENCE, DOMAIN_ANALOGY, or MISSING.
2. Provide the exact resume quote that supports each requirement.
3. Write a reasoning_trace explaining your analysis.
4. Give total_score, must_have_coverage, nice_to_have_coverage.
5. End with self_verification_notes."""
    result = chat_structured(
        prompt,
        DeepScoreResult,
        system="You are a rigorous, evidence-based resume analyst. Never hallucinate quotes.",
        model=DEFAULT_MODEL,
    )
    return verify_quotes(result, raw_text)