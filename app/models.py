import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    assessments: Mapped[list["Assessment"]] = relationship(back_populates="user")
    mood_logs: Mapped[list["MoodLog"]] = relationship(back_populates="user")
    chats: Mapped[list["Chat"]] = relationship(back_populates="user")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="user")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    stress_score: Mapped[int] = mapped_column(Integer)
    anxiety_score: Mapped[int] = mapped_column(Integer)
    depression_score: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="assessments")


class MoodLog(Base):
    __tablename__ = "mood_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    mood: Mapped[str] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="mood_logs")


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    user_message: Mapped[str] = mapped_column(Text)
    ai_response: Mapped[str] = mapped_column(Text)
    chat_type: Mapped[str] = mapped_column(String(50), default="support")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="chats")


class Professional(Base):
    __tablename__ = "professionals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100))
    profession: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(100))
    available: Mapped[bool] = mapped_column(Boolean, default=True)


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    professional_id: Mapped[str] = mapped_column(String(36), ForeignKey("professionals.id"))
    appointment_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(50), default="pending")

    user: Mapped["User"] = relationship(back_populates="appointments")
    professional: Mapped["Professional"] = relationship()
