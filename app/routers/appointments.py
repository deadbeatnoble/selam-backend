from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Appointment, Professional, User
from app.schemas import AppointmentCreate, AppointmentResponse
from app.services.email_service import send_appointment_email
from app.services.patient_summary import build_appointment_email_body, build_patient_summary

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", response_model=AppointmentResponse)
def book_appointment(
    data: AppointmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prof = db.query(Professional).filter(Professional.id == data.professional_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    if not prof.available:
        raise HTTPException(status_code=400, detail="Professional is not available")

    appointment = Appointment(
        user_id=user.id,
        professional_id=data.professional_id,
        appointment_date=data.appointment_date,
        status="pending",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    summary = build_patient_summary(user, db)
    body = build_appointment_email_body(
        patient_name=user.name,
        patient_email=user.email,
        professional_name=prof.name,
        appointment_date=appointment.appointment_date,
        patient_summary=summary,
    )
    email_sent = send_appointment_email(
        to_email=prof.email,
        subject=f"SelamMind: New appointment request from {user.name}",
        body=body,
    )

    return AppointmentResponse(
        id=appointment.id,
        professional_id=prof.id,
        professional_name=prof.name,
        profession=prof.profession,
        appointment_date=appointment.appointment_date,
        status=appointment.status,
        email_sent=email_sent,
    )


@router.get("", response_model=list[AppointmentResponse])
def list_appointments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appointments = (
        db.query(Appointment)
        .filter(Appointment.user_id == user.id)
        .order_by(Appointment.appointment_date.desc())
        .all()
    )
    result = []
    for appt in appointments:
        prof = db.query(Professional).filter(Professional.id == appt.professional_id).first()
        result.append(
            AppointmentResponse(
                id=appt.id,
                professional_id=appt.professional_id,
                professional_name=prof.name if prof else "Unknown",
                profession=prof.profession if prof else "",
                appointment_date=appt.appointment_date,
                status=appt.status,
                email_sent=False,
            )
        )
    return result
