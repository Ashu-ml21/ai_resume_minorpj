from pydantic import BaseModel, Field

class InterviewQuestion(BaseModel):
    question: str
    category: str = "technical"
    rationale: str = ""

class QuestionSet(BaseModel):
    questions: list[InterviewQuestion] = Field(default_factory=list)

class InterviewTurn(BaseModel):
    question: str
    answer: str
    fact_check: str = ""
    scores: dict = Field(default_factory=dict)

class CoverLetter(BaseModel):
    subject: str = ""
    body: str = ""
    highlights: list[str] = Field(default_factory=list)

# --- NEW CHAT MODELS ---
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    resume_id: int
    message: str
    history: list[ChatMessage] = Field(default_factory=list)

class ChatResponse(BaseModel):
    reply: str