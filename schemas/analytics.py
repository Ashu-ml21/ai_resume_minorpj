from pydantic import BaseModel, Field

class Benchmarks(BaseModel):
    ats_parseability: float = 0.0
    keyword_match: float = 0.0
    impact_density: float = 0.0
    seniority_alignment: float = 0.0
    evidence_integrity: float = 0.0

class GapSeverity(BaseModel):
    skill: str
    severity: float

class BulletMetric(BaseModel):
    text: str
    word_count: int
    has_metric: bool
    impact_score: float

class TimelineItem(BaseModel):
    company: str
    title: str
    start_year: int = 0
    end_year: int = 0
    duration_years: float = 0.0

class Completeness(BaseModel):
    summary: float = 0.0
    experience: float = 0.0
    education: float = 0.0
    skills: float = 0.0
    certifications: float = 0.0

class AnalyticsPayload(BaseModel):
    benchmarks: Benchmarks
    must_have_coverage: float = 0.0
    nice_to_have_coverage: float = 0.0
    evidence_breakdown: dict = Field(default_factory=dict)
    gap_severity: list[GapSeverity] = Field(default_factory=list)
    score_history: list[dict] = Field(default_factory=list)
    
    # Extreme Analytics Additions
    ideal_match: float = 0.0
    bullet_metrics: list[BulletMetric] = Field(default_factory=list)
    timeline: list[TimelineItem] = Field(default_factory=list)
    completeness: Completeness = Field(default_factory=Completeness)
    confidence_distribution: list[int] = Field(default_factory=lambda: [0]*5)
    keyword_density: dict = Field(default_factory=dict)