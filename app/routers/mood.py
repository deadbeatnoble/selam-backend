from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import MoodLog, User
from app.schemas import MoodCreate, MoodResponse

router = APIRouter(prefix="/mood", tags=["Mood Tracking"])


@router.post("", response_model=MoodResponse)
def log_mood(data: MoodCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log = MoodLog(user_id=user.id, mood=data.mood, notes=data.notes)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/history", response_model=list[MoodResponse])
def mood_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(MoodLog).filter(MoodLog.user_id == user.id).order_by(MoodLog.created_at.desc()).limit(30).all()
