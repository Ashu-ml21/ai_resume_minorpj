import csv, os
from db import get_conn


def export_scores_csv(out_path: str):
    with get_conn() as c:
        rows = c.execute("""
            SELECT r.filename, j.title, s.total_score, s.created_at
            FROM scores s
            JOIN resumes r ON r.id = s.resume_id
            JOIN jobs j ON j.id = s.job_id
            ORDER BY s.total_score DESC
        """).fetchall()
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["resume", "job", "score", "created_at"])
        for r in rows:
            w.writerow([r["filename"], r["title"], r["total_score"], r["created_at"]])


def compare_candidates(resume_ids: list[int]) -> list[dict]:
    out = []
    with get_conn() as c:
        for rid in resume_ids:
            row = c.execute("""
                SELECT r.filename, s.total_score, s.details_json
                FROM resumes r
                LEFT JOIN scores s ON s.resume_id = r.id
                WHERE r.id = ?
            """, (rid,)).fetchone()
            if row:
                out.append(dict(row))
    return out


def differentiators(candidates: list[dict]) -> list[str]:
    scores = [c["total_score"] or 0 for c in candidates]
    if len(scores) < 2:
        return ["Need at least two candidates to compare."]
    gap = max(scores) - min(scores)
    if gap < 2:
        return ["Candidates are within 2 points — review qualitative strengths."]
    top = candidates[scores.index(max(scores))]
    return [f"Top candidate {top['filename']} leads by {gap:.1f} points."]