from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Professional
from app.schemas import ProfessionalResponse

router = APIRouter(prefix="/professionals", tags=["Professionals"])


@router.get("", response_model=list[ProfessionalResponse])
def list_professionals(db: Session = Depends(get_db)):
    return db.query(Professional).filter(Professional.available == True).all()


@router.get("/{professional_id}", response_model=ProfessionalResponse)
def get_professional(professional_id: str, db: Session = Depends(get_db)):
    prof = db.query(Professional).filter(Professional.id == professional_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    return prof
