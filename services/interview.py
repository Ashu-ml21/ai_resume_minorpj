from schemas.interview import QuestionSet, InterviewTurn, ChatMessage, ChatResponse
from schemas.resume import ResumeData
from ollama_client import chat_structured, chat_with_tools, chat_text, embed, cosine_sim

def generate_questions(resume: ResumeData, jd_text: str) -> QuestionSet:
    prompt = f"""Generate 8 personalized interview questions for this candidate
(technical, behavioral, and gap-probing based on the resume vs. job description).

Job description:
{jd_text[:6000]}

Resume:
{resume.model_dump_json()}"""
    return chat_structured(prompt, QuestionSet, system="You are a hiring manager conducting a structured interview.")

def check_claim(claim: str, resume_text: str) -> str:
    sim = cosine_sim(embed(claim), embed(resume_text))
    if sim > 0.75:
        return "verified"
    if sim < 0.35:
        return "contradicted_or_absent"
    return "unverifiable"

def interview_turn(question: str, answer: str, resume_text: str) -> dict:
    tools = [{
        "type": "function",
        "function": {
            "name": "check_claim",
            "description": "Verify a candidate's claim against their resume.",
            "parameters": {
                "type": "object",
                "properties": {"claim": {"type": "string"}},
                "required": ["claim"],
            },
        },
    }]
    messages = [{
        "role": "user",
        "content": (
            f"Question: {question}\n"
            f"Answer: {answer}\n"
            f"Resume: {resume_text[:6000]}\n\n"
            f"Fact-check the answer using the check_claim tool, then score 0-10 on: "
            f"ownership, technical_competence, problem_solving, collaboration."
        ),
    }]
    resp = chat_with_tools("", tools=tools, messages=messages)
    msg = resp["message"]
    return {
        "content": msg.get("content", ""),
        "tool_calls": msg.get("tool_calls", []),
    }

# --- NEW CHAT FUNCTION ---
def chat_with_resume(resume_text: str, jd_text: str, user_message: str, history: list[ChatMessage]) -> str:
    """Acts as an AI Interview Coach that knows your resume and the JD."""
    
    # Build the system prompt
    system_prompt = f"""You are an expert AI Interview Coach.
You are helping a candidate prepare for an interview.
Here is their resume:
{resume_text[:4000]}

Here is the job description they are applying for:
{jd_text[:4000]}

Answer their questions, give them advice, or simulate an interview response. 
Be encouraging but honest. If they ask you to act as the interviewer, do so.
Keep your responses conversational and concise."""

    # Build the message history (Limit to the last 10 messages for memory)
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add past history
    for msg in history[-10:]:
        messages.append({"role": msg.role, "content": msg.content})
        
    # Add the new user message
    messages.append({"role": "user", "content": user_message})

    # Call Ollama directly with the chat format
    import ollama
    resp = ollama.chat(
        model="qwen2.5:3b",
        messages=messages,
        options={"temperature": 0.7, "num_ctx": 8192},
    )
    
    return resp["message"]["content"]