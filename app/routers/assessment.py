from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Assessment, User
from app.schemas import AssessmentResult, AssessmentSubmit
from app.services.risk_engine import calculate_scores, determine_risk_level, get_recommendation

router = APIRouter(prefix="/assessment", tags=["Assessment"])

ASSESSMENT_QUESTIONS = {
    "en": [
        {"id": 1, "category": "stress", "text": "How often do you feel overwhelmed by your responsibilities?"},
        {"id": 2, "category": "stress", "text": "How often do you have trouble relaxing?"},
        {"id": 3, "category": "stress", "text": "How often do you feel under pressure?"},
        {"id": 4, "category": "stress", "text": "How often do you feel irritable or angry?"},
        {"id": 5, "category": "anxiety", "text": "How often do you feel nervous or anxious?"},
        {"id": 6, "category": "anxiety", "text": "How often do you worry about things you can't control?"},
        {"id": 7, "category": "anxiety", "text": "How often do you feel restless?"},
        {"id": 8, "category": "anxiety", "text": "How often do you have difficulty concentrating?"},
        {"id": 9, "category": "depression", "text": "How often do you feel sad or down?"},
        {"id": 10, "category": "depression", "text": "How often do you lose interest in activities you enjoy?"},
        {"id": 11, "category": "depression", "text": "How often do you feel hopeless?"},
        {"id": 12, "category": "depression", "text": "How often do you feel tired or have low energy?"},
    ],
    "am": [
        {"id": 1, "category": "stress", "text": "በኃላፊነትዎ ምክንያት ምን ያህል ብዙ ጊዜ ተጭበርባሪ ስሜት ይሰማዎታል?"},
        {"id": 2, "category": "stress", "text": "ምን ያህል ብዙ ጊዜ ለመዝናናት ችግር ይገጥምዎታል?"},
        {"id": 3, "category": "stress", "text": "ምን ያህል ብዙ ጊዜ በግፊት ስሜት ይሰማዎታል?"},
        {"id": 4, "category": "stress", "text": "ምን ያህል ብዙ ጊዜ ተበሳጭተው ወይም ተናደዱ ይሰማዎታል?"},
        {"id": 5, "category": "anxiety", "text": "ምን ያህል ብዙ ጊዜ ድብርት ወይም ጭንቀት ይሰማዎታል?"},
        {"id": 6, "category": "anxiety", "text": "ምን ያህል ብዙ ጊዜ ስለ መቆጣጠር የማይችሉት ነገሮች ይጨንቃሉ?"},
        {"id": 7, "category": "anxiety", "text": "ምን ያህል ብዙ ጊዜ ያለምነት ስሜት ይሰማዎታል?"},
        {"id": 8, "category": "anxiety", "text": "ምን ያህል ብዙ ጊዜ ለማተኮር ችግር ይገጥምዎታል?"},
        {"id": 9, "category": "depression", "text": "ምን ያህል ብዙ ጊዜ ደማቅ ወይም ዝቅተኛ ስሜት ይሰማዎታል?"},
        {"id": 10, "category": "depression", "text": "ምን ያህል ብዙ ጊዜ ከሚወዷቸው ነገሮች ፍላጎት ይጣላሉ?"},
        {"id": 11, "category": "depression", "text": "ምን ያህል ብዙ ጊዜ ተስፋ ቁርጥራጭ ስሜት ይሰማዎታል?"},
        {"id": 12, "category": "depression", "text": "ምን ያህል ብዙ ጊዜ ድካም ወይም ዝቅተኛ ኢነርጂ ይሰማዎታል?"},
    ],
    "om": [
        {"id": 1, "category": "stress", "text": "Yeroo meeqa itti gahee keetiin ulfaataa jiraachuu si dhukkubsa?"},
        {"id": 2, "category": "stress", "text": "Yeroo meeqa boqochuuf rakkoo qabda?"},
        {"id": 3, "category": "stress", "text": "Yeroo meeqa miira dhiibbaa qabda?"},
        {"id": 4, "category": "stress", "text": "Yeroo meeqa aaree yookaan aaree jirta?"},
        {"id": 5, "category": "anxiety", "text": "Yeroo meeqa yaaddoo yookaan soda qabda?"},
        {"id": 6, "category": "anxiety", "text": "Yeroo meeqa wantoota to'achuu hin dandeenye irratti yaadda?"},
        {"id": 7, "category": "anxiety", "text": "Yeroo meeqa tasgabbaa'uu dhabdee jirta?"},
        {"id": 8, "category": "anxiety", "text": "Yeroo meeqa xiyyeeffannoo qabachuuf rakkoo qabda?"},
        {"id": 9, "category": "depression", "text": "Yeroo meeqa gammachuu gadi aanaa yookaan gadda qabda?"},
        {"id": 10, "category": "depression", "text": "Yeroo meeqa wantoota jaallattu irratti fedhii dhabda?"},
        {"id": 11, "category": "depression", "text": "Yeroo meeqa abdii dhabdee jirta?"},
        {"id": 12, "category": "depression", "text": "Yeroo meeqa dadhabbii yookaan annisaa gadi aanaa qabda?"},
    ],
}

OPTIONS = {
    "en": ["Never", "Rarely", "Sometimes", "Often", "Always"],
    "am": ["በጭራረት", "አልፎ አልፎ", "አንዳንድ ጊዜ", "ብዙ ጊዜ", "ሁልጊዜ"],
    "om": ["Gonkumaa", "Yeroo muraasa", "Yeroo tokko tokko", "Yeroo baay'ee", "Yeroo hunda"],
}


def _get_questions(lang: str) -> dict:
    language = lang if lang in ASSESSMENT_QUESTIONS else "en"
    return {
        "questions": ASSESSMENT_QUESTIONS[language],
        "options": OPTIONS[language],
        "scale": "0-4 (Never to Always)",
    }


@router.get("/questions")
def get_questions(language: str = Query("en")):
    """Public assessment questions — no login required."""
    return _get_questions(language)


@router.get("/start")
def start_assessment(user: User = Depends(get_current_user)):
    return _get_questions(user.language)


@router.post("/submit", response_model=AssessmentResult)
def submit_assessment(
    data: AssessmentSubmit,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    answers = [{"question_id": a.question_id, "score": a.score} for a in data.answers]
    scores = calculate_scores(answers)
    risk = determine_risk_level(scores["stress_score"], scores["anxiety_score"], scores["depression_score"])

    assessment = Assessment(
        user_id=user.id,
        stress_score=scores["stress_score"],
        anxiety_score=scores["anxiety_score"],
        depression_score=scores["depression_score"],
        risk_level=risk,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return AssessmentResult(
        id=assessment.id,
        stress_score=assessment.stress_score,
        anxiety_score=assessment.anxiety_score,
        depression_score=assessment.depression_score,
        risk_level=assessment.risk_level,
        recommendation=get_recommendation(risk, user.language),
        created_at=assessment.created_at,
    )


@router.post("/submit-guest")
def submit_assessment_guest(
    data: AssessmentSubmit,
    language: str = Query("en"),
):
    """Score assessment without saving — for guests before login."""
    answers = [{"question_id": a.question_id, "score": a.score} for a in data.answers]
    scores = calculate_scores(answers)
    risk = determine_risk_level(scores["stress_score"], scores["anxiety_score"], scores["depression_score"])
    lang = language if language in ("en", "am", "om") else "en"
    return {
        "stress_score": scores["stress_score"],
        "anxiety_score": scores["anxiety_score"],
        "depression_score": scores["depression_score"],
        "risk_level": risk,
        "recommendation": get_recommendation(risk, lang),
    }


@router.get("/result", response_model=AssessmentResult | None)
def get_latest_result(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assessment = (
        db.query(Assessment)
        .filter(Assessment.user_id == user.id)
        .order_by(Assessment.created_at.desc())
        .first()
    )
    if not assessment:
        return None
    return AssessmentResult(
        id=assessment.id,
        stress_score=assessment.stress_score,
        anxiety_score=assessment.anxiety_score,
        depression_score=assessment.depression_score,
        risk_level=assessment.risk_level,
        recommendation=get_recommendation(assessment.risk_level, user.language),
        created_at=assessment.created_at,
    )
