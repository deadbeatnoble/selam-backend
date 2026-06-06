from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Assessment, MoodLog, User


MOOD_LABELS = {
    "en": {"great": "Great", "fine": "Fine", "stressed": "Stressed", "overwhelmed": "Overwhelmed"},
    "am": {"great": "በጣም ጥሩ", "fine": "ጥሩ", "stressed": "ተጭነቅ", "overwhelmed": "ተጭበርባሪ"},
    "om": {"great": "Baay'ee gaarii", "fine": "Gaarii", "stressed": "Dhiphina qaba", "overwhelmed": "Garmalee ulfaataa"},
}


def build_patient_summary(user: User, db: Session) -> str:
    lang = user.language if user.language in MOOD_LABELS else "en"
    mood_labels = MOOD_LABELS[lang]

    latest_mood = (
        db.query(MoodLog)
        .filter(MoodLog.user_id == user.id)
        .order_by(MoodLog.created_at.desc())
        .first()
    )

    latest_assessment = (
        db.query(Assessment)
        .filter(Assessment.user_id == user.id)
        .order_by(Assessment.created_at.desc())
        .first()
    )

    lines = [
        f"Patient: {user.name}",
        f"Email: {user.email}",
        f"Language: {user.language}",
    ]

    if latest_mood:
        mood_text = mood_labels.get(latest_mood.mood, latest_mood.mood)
        lines.append(f"Latest mood: {mood_text} ({latest_mood.created_at.strftime('%Y-%m-%d %H:%M')} UTC)")
        if latest_mood.notes:
            lines.append(f"Mood notes: {latest_mood.notes}")

    if latest_assessment:
        lines.extend([
            f"Assessment risk: {latest_assessment.risk_level.upper()}",
            f"Stress: {latest_assessment.stress_score}/100",
            f"Anxiety: {latest_assessment.anxiety_score}/100",
            f"Low mood: {latest_assessment.depression_score}/100",
            f"Assessment date: {latest_assessment.created_at.strftime('%Y-%m-%d %H:%M')} UTC",
        ])

    if not latest_mood and not latest_assessment:
        lines.append("No mood or assessment data recorded yet.")

    return "\n".join(lines)


def build_appointment_email_body(
    *,
    patient_name: str,
    patient_email: str,
    professional_name: str,
    appointment_date: datetime,
    patient_summary: str,
) -> str:
    formatted_date = appointment_date.strftime("%A, %B %d, %Y at %I:%M %p UTC")
    return f"""New SelamMind Appointment Request
================================

Professional: {professional_name}
Requested time: {formatted_date}

Patient overview
----------------
{patient_summary}

---
This notification was sent automatically by SelamMind when a patient booked an appointment.
Please contact the patient at {patient_email} to confirm.
"""
