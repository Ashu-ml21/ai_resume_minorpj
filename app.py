import os, shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from db import init_db, get_conn
from schemas.resume import ResumeData
from schemas.scoring import RubricConfig, GapAnalysis
from schemas.analytics import AnalyticsPayload, GapSeverity
from services.parser import extract_text, parse_resume_text, anonymize
from services.scorer import score_resume, deep_score_resume, semantic_similarity
from services.gap import analyze_gaps
from services.ats import (
    ats_check, quality_score, rewrite_bullets, audit_sections, generate_cover_letter
)

from services.interview import generate_questions, interview_turn, chat_with_resume
from schemas.interview import ChatRequest, ChatResponse

from services.batch import export_scores_csv, compare_candidates, differentiators
from services.analytics import (
    compute_benchmarks, evidence_breakdown, gap_severity, score_history,
    generate_bullet_metrics, generate_timeline, generate_completeness,
    calculate_ideal_match, generate_confidence_distribution, generate_keyword_density
)
from services.suggestions import stream_analysis

app = FastAPI(title="AI Resume Analyser")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    text = extract_text(path)
    parsed = parse_resume_text(text)
    anon = anonymize(parsed)
    with get_conn() as c:
        cur = c.execute("INSERT INTO resumes(filename, raw_text, parsed_json) VALUES(?,?,?)", (file.filename, text, parsed.model_dump_json()))
        rid = cur.lastrowid
    return {"resume_id": rid, "parsed": parsed.model_dump(), "anonymized": anon.model_dump()}

class ScoreReq(BaseModel):
    resume_id: int
    job_description: str
    rubric: RubricConfig | None = None
    deep: bool = False

def _load_resume(resume_id: int):
    with get_conn() as c:
        row = c.execute("SELECT raw_text, parsed_json, filename FROM resumes WHERE id=?", (resume_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Resume not found")
    return row

@app.post("/api/score")
def score(req: ScoreReq):
    row = _load_resume(req.resume_id)
    resume = ResumeData.model_validate_json(row["parsed_json"])
    sim = semantic_similarity(row["raw_text"], req.job_description)

    if req.deep:
        result = deep_score_resume(resume, req.job_description, row["raw_text"], req.rubric)
    else:
        result = score_resume(resume, req.job_description, req.rubric)

    with get_conn() as c:
        cur = c.execute("INSERT INTO jobs(title, description) VALUES(?,?)", ("uploaded", req.job_description))
        jid = cur.lastrowid
        c.execute("INSERT INTO scores(resume_id, job_id, total_score, details_json) VALUES(?,?,?,?)", (req.resume_id, jid, result.total_score, result.model_dump_json()))
    return {"semantic_similarity": sim, "score": result.model_dump()}

@app.post("/api/gaps")
def gaps(req: ScoreReq):
    row = _load_resume(req.resume_id)
    resume = ResumeData.model_validate_json(row["parsed_json"])
    return analyze_gaps(resume, req.job_description).model_dump()

@app.post("/api/quality")
def quality(req: ScoreReq):
    row = _load_resume(req.resume_id)
    resume = ResumeData.model_validate_json(row["parsed_json"])
    bullets = [b for e in resume.experience for b in e.bullets][:10]
    
    qual = quality_score(resume)
    sections = audit_sections(resume)
    rewrites = rewrite_bullets(bullets)
    cover = generate_cover_letter(resume, req.job_description)
    
    return {
        "quality": qual.model_dump(),
        "sections": [s.model_dump() for s in sections],
        "rewrites": [r.model_dump() for r in rewrites],
        "cover_letter": cover.model_dump(),
    }

@app.post("/api/ats/{resume_id}")
def ats(resume_id: int):
    row = _load_resume(resume_id)
    return ats_check(os.path.join(UPLOAD_DIR, row["filename"]))

@app.post("/api/interview/questions")
def iq(req: ScoreReq):
    row = _load_resume(req.resume_id)
    resume = ResumeData.model_validate_json(row["parsed_json"])
    return generate_questions(resume, req.job_description).model_dump()

class TurnReq(BaseModel):
    resume_id: int
    question: str
    answer: str

@app.post("/api/interview/turn")
def iturn(req: TurnReq):
    row = _load_resume(req.resume_id)
    return interview_turn(req.question, req.answer, row["raw_text"])

@app.get("/api/export/csv")
def export_csv():
    out = os.path.join(UPLOAD_DIR, "scores.csv")
    export_scores_csv(out)
    return FileResponse(out, media_type="text/csv", filename="scores.csv")

@app.post("/api/compare")
def compare(ids: list[int]):
    cands = compare_candidates(ids)
    return {"candidates": cands, "differentiators": differentiators(cands)}

class StreamReq(BaseModel):
    resume_id: int
    job_description: str

@app.post("/api/analyse/stream")
async def analyse_stream(req: StreamReq):
    row = _load_resume(req.resume_id)
    resume = ResumeData.model_validate_json(row["parsed_json"])
    async def gen():
        async for tok in stream_analysis(resume, req.job_description):
            yield f"data: {tok}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")

@app.post("/api/analytics")
def analytics(req: ScoreReq):
    row = _load_resume(req.resume_id)
    resume = ResumeData.model_validate_json(row["parsed_json"])

    # 1. Use the fast scoring function (instantly returns data)
    score_result = score_resume(resume, req.job_description) 
    
    # 2. Use the fast empty gaps object (avoids AI timeouts)
    gaps_result = GapAnalysis()
    
    # 3. Check ATS
    ats_result = ats_check(os.path.join(UPLOAD_DIR, row["filename"]))

    # 4. Calculate Benchmarks (Fast Python math)
    bench = compute_benchmarks(resume, row["raw_text"], score_result, gaps_result, deep=None, ats_pass=ats_result["pass"])

    # 5. Generate Charts (FIXED: Passing row["raw_text"])
    ideal_match = calculate_ideal_match(resume, req.job_description)
    bullet_metrics = generate_bullet_metrics(resume, row["raw_text"])
    timeline = generate_timeline(resume, row["raw_text"])
    completeness = generate_completeness(resume, row["raw_text"])
    conf_dist = generate_confidence_distribution(score_result)
    kw_density = generate_keyword_density(resume, gaps_result)

    payload = AnalyticsPayload(
        benchmarks=bench,
        must_have_coverage=score_result.must_have_coverage or 50.0, 
        nice_to_have_coverage=score_result.nice_to_have_coverage or 30.0,
        evidence_breakdown=evidence_breakdown(score_result, score_result),
        gap_severity=gap_severity(gaps_result),
        score_history=score_history(req.resume_id),
        ideal_match=ideal_match,
        bullet_metrics=bullet_metrics,
        timeline=timeline,
        completeness=completeness,
        confidence_distribution=conf_dist,
        keyword_density=kw_density
    )
    return payload.model_dump()

@app.post("/api/interview/chat", response_model=ChatResponse)
def chat_interview(req: ChatRequest):
    row = _load_resume(req.resume_id)
    reply_text = chat_with_resume(
        resume_text=row["raw_text"],
        jd_text="", 
        user_message=req.message,
        history=req.history
    )
    return ChatResponse(reply=reply_text)