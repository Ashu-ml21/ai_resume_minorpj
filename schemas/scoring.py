from pydantic import BaseModel, Field


class Evidence(BaseModel):
    requirement: str
    matched_quote: str = ""
    confidence: float = 0.0
    met: bool = False


class DeepEvidence(BaseModel):
    requirement: str
    reasoning_type: str = "EXACT_MATCH"   # EXACT_MATCH / SEMANTIC_INFERENCE / DOMAIN_ANALOGY / MISSING
    matched_quote: str = ""
    quote_verified: bool = False
    confidence: float = 0.0
    met: bool = False


class ScoreResult(BaseModel):
    total_score: float
    must_have_coverage: float
    nice_to_have_coverage: float
    evidence: list[Evidence] = Field(default_factory=list)
    reasoning: str = ""


class DeepScoreResult(BaseModel):
    reasoning_trace: str = ""
    total_score: float
    must_have_coverage: float
    nice_to_have_coverage: float
    evidence: list[DeepEvidence] = Field(default_factory=list)
    self_verification_notes: str = ""


class GapAnalysis(BaseModel):
    missing_keywords: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    suggested_projects: list[str] = Field(default_factory=list)
    prioritized_feedback: list[dict] = Field(default_factory=list)


class QualityScore(BaseModel):
    structure_score: float
    bullet_quality_score: float
    seniority_score: float
    keyword_score: float
    composite_score: float
    notes: list[str] = Field(default_factory=list)


class BulletRewrite(BaseModel):
    original: str
    rewritten: str
    reason: str = ""


class SectionAudit(BaseModel):
    section: str
    strengths: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class RubricConfig(BaseModel):
    role_level: str = "mid"
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    competency_matrix: dict = Field(default_factory=dict)
    score_threshold: float = 60.0
    regional_context: str = ""