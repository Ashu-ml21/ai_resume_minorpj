from pydantic import BaseModel, Field


class Experience(BaseModel):
    title: str
    company: str
    start: str = ""
    end: str = ""
    bullets: list[str] = Field(default_factory=list)


class Education(BaseModel):
    degree: str
    institution: str
    year: str = ""


class ResumeData(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    years_experience: float = 0.0