from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    language: Literal["en", "am", "om"] = "en"


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    language: Literal["en", "am", "om"] | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    language: str
    created_at: datetime

    class Config:
        from_attributes = True


class MoodCreate(BaseModel):
    mood: Literal["great", "fine", "stressed", "overwhelmed"]
    notes: str | None = None


class MoodResponse(BaseModel):
    id: str
    mood: str
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AssessmentAnswer(BaseModel):
    question_id: int
    score: int = Field(..., ge=0, le=3)


class AssessmentSubmit(BaseModel):
    answers: list[AssessmentAnswer]


class AssessmentResult(BaseModel):
    id: str
    total_score: int = 0
    stress_score: int
    anxiety_score: int
    depression_score: int
    risk_level: Literal["green", "yellow", "red"]
    risk_tier: str = "low"
    recommendation: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    chat_type: Literal["support", "breathing", "study_plan", "books"] = "support"
    language: Literal["en", "am", "om"] = "en"
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    chat_type: str
    structured_data: dict | None = None
    ai_available: bool = True


class ProfessionalResponse(BaseModel):
    id: str
    name: str
    profession: str
    city: str
    phone: str
    email: str
    available: bool

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    professional_id: str
    appointment_date: datetime


class AppointmentResponse(BaseModel):
    id: str
    professional_id: str
    professional_name: str
    profession: str
    appointment_date: datetime
    status: str
    email_sent: bool = False

    class Config:
        from_attributes = True
