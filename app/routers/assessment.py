from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Assessment, User
from app.schemas import AssessmentResult, AssessmentSubmit
from app.services.risk_engine import calculate_scores, determine_risk_level, get_recommendation, get_risk_tier

router = APIRouter(prefix="/assessment", tags=["Assessment"])

STANDARD_OPTIONS = {
    "en": [
        {"label": "Not at all", "score": 0},
        {"label": "Several days", "score": 1},
        {"label": "More than half the days", "score": 2},
        {"label": "Nearly every day", "score": 3},
    ],
    "am": [
        {"label": "በጭራረት", "score": 0},
        {"label": "በጥቂት ቀናት", "score": 1},
        {"label": "ከግማሽ በላይ ቀናት", "score": 2},
        {"label": "በየቀኑ ሁሉ", "score": 3},
    ],
    "om": [
        {"label": "Gonkumaa", "score": 0},
        {"label": "Guyyoota muraasa", "score": 1},
        {"label": "Guyyoota walakkaa ol", "score": 2},
        {"label": "Guyyaa guyyaan", "score": 3},
    ],
}

FUNCTIONAL_OPTIONS = {
    "en": [
        {"label": "Not difficult at all", "score": 0},
        {"label": "Somewhat difficult", "score": 1},
        {"label": "Very difficult", "score": 2},
        {"label": "Extremely difficult", "score": 3},
    ],
    "am": [
        {"label": "በጭራረት አስቸጋሪ አይደለም", "score": 0},
        {"label": "በተወሰነ መልኩ አስቸጋሪ", "score": 1},
        {"label": "በጣም አስቸጋሪ", "score": 2},
        {"label": "በጣም በጣም አስቸጋሪ", "score": 3},
    ],
    "om": [
        {"label": "Rakkoo tokkoo malee", "score": 0},
        {"label": "Tokkotti rakkisaa", "score": 1},
        {"label": "Baay'ee rakkisaa", "score": 2},
        {"label": "Baay'ee baay'ee rakkisaa", "score": 3},
    ],
}

QUESTION_TEXT = {
    "en": [
        {"id": 1, "code": "PR_01", "section": "Mood and Engagement", "category": "mood",
         "text": "Over the past 2 weeks, how often have you felt little interest or pleasure in doing things you normally enjoy?"},
        {"id": 2, "code": "PR_02", "section": "Mood and Engagement", "category": "mood",
         "text": "Over the past 2 weeks, how often have you felt down, depressed, or hopeless?"},
        {"id": 3, "code": "PR_03", "section": "Anxiety and Tension", "category": "anxiety",
         "text": "How often have you found yourself feeling nervous, anxious, or on edge?"},
        {"id": 4, "code": "PR_04", "section": "Anxiety and Tension", "category": "anxiety",
         "text": "How often do you find it difficult to control or stop worrying about various aspects of your life?"},
        {"id": 5, "code": "PR_05", "section": "Somatic and Energy", "category": "wellbeing",
         "text": "Have you been experiencing trouble falling asleep, staying asleep, or sleeping too much?"},
        {"id": 6, "code": "PR_06", "section": "Somatic and Energy", "category": "wellbeing",
         "text": "How often have you felt tired, fatigued, or lacking the energy to complete basic daily routines?"},
        {"id": 7, "code": "PR_07", "section": "Cognitive and Self-Perception", "category": "wellbeing",
         "text": "How often do you feel bad about yourself, feel that you are a failure, or feel you have let yourself or your family down?"},
        {"id": 8, "code": "PR_08", "section": "Cognitive and Self-Perception", "category": "wellbeing",
         "text": "Have you noticed trouble concentrating on things, such as reading, work responsibilities, or conversations?"},
        {"id": 9, "code": "PR_09", "section": "Social and Environmental", "category": "wellbeing",
         "text": "How often have you felt isolated or disconnected from your supportive community, friends, or family structures?"},
        {"id": 10, "code": "PR_10", "section": "Functional Impairment", "category": "wellbeing",
         "text": "If you checked off any problems on this list, how difficult have these problems made it for you to do your work, take care of things at home, or get along with other people?"},
    ],
    "am": [
        {"id": 1, "code": "PR_01", "section": "ስሜት እና ተሳትፎ", "category": "mood",
         "text": "ባለፉት 2 ሳምንታት በተለምዶ የሚወዷቸውን ነገሮች ለመስራት ወይም ለመደሰት ትንሽ ፍላጎት ወይም ደስታ ስሜት ምን ያህል ብዙ ጊዜ ተሰማዎታል?"},
        {"id": 2, "code": "PR_02", "section": "ስሜት እና ተሳትፎ", "category": "mood",
         "text": "ባለፉት 2 ሳምንታት ምን ያህል ብዙ ጊዜ ደማቅ፣ ተስፋ ቁርጥራጭ ወይም ተስፋ የሌለው ስሜት ተሰማዎታል?"},
        {"id": 3, "code": "PR_03", "section": "ድብርት እና ጭንቀት", "category": "anxiety",
         "text": "ምን ያህል ብዙ ጊዜ ድብርት፣ ጭንቀት ወይም በጣም ተጨንቀው ስሜት አጋጥመዎታል?"},
        {"id": 4, "code": "PR_04", "section": "ድብርት እና ጭንቀት", "category": "anxiety",
         "text": "ስለ ሕይወትዎ የተለያዩ ገጽታዎች ምን ያህል ብዙ ጊዜ ለመቆጣጠር ወይም ለማቆም ችግር አጋጥመዎታል?"},
        {"id": 5, "code": "PR_05", "section": "አካላዊ እና ኢነርጂ", "category": "wellbeing",
         "text": "ለመተኛት፣ ለመቆየት ወይም በጣም ለመኝታ ችግር አጋጥመዎታል?"},
        {"id": 6, "code": "PR_06", "section": "አካላዊ እና ኢነርጂ", "category": "wellbeing",
         "text": "ምን ያህል ብዙ ጊዜ ድካም፣ ዝቅተኛ ኢነርጂ ወይም መሠረታዊ ዕለታዊ ስራዎችን ለመጨረስ ችግር ተሰማዎታል?"},
        {"id": 7, "code": "PR_07", "section": "እውቀት እና ራስ ግምት", "category": "wellbeing",
         "text": "ምን ያህል ብዙ ጊዜ ስለ ራስዎ መጥፎ ስሜት፣ ውድቀት ወይም ራስዎን ወይም ቤተሰብዎን አሳሳተሁ ስሜት አጋጥመዎታል?"},
        {"id": 8, "code": "PR_08", "section": "እውቀት እና ራስ ግምት", "category": "wellbeing",
         "text": "በንባብ፣ በስራ ወይም በውይይት ላይ ለማተኮር ችግር ልታስተውሉ ይችላሉ?"},
        {"id": 9, "code": "PR_09", "section": "ማህበራዊ እና አካባቢ", "category": "wellbeing",
         "text": "ምን ያህል ብዙ ጊዜ ከማህበረሰብዎ፣ ጓደኞችዎ ወይም ቤተሰብዎ ተለይተው ወይም ተበላሽተው ስሜት ተሰማዎታል?"},
        {"id": 10, "code": "PR_10", "section": "የእንቅስቃሴ ተጽዕኖ", "category": "wellbeing",
         "text": "ከዚህ ዝርዝር ላይ ማንኛውም ችግሮች ካሉ፣ እነዚህ ችግሮች ስራዎን፣ የቤት ነገሮችን ወይም ከሌሎች ጋር መግባባት ምን ያህል አስቸጋሪ አድርገዋል?"},
    ],
    "om": [
        {"id": 1, "code": "PR_01", "section": "Miira fi Hirmaannisa", "category": "mood",
         "text": "Torban 2 darban keessatti wantoota yeroo baay'ee jaallattu gochuuf fedhii yookaan gammachuu xiqqaa yeroo meeqa qabde?"},
        {"id": 2, "code": "PR_02", "section": "Miira fi Hirmaannisa", "category": "mood",
         "text": "Torban 2 darban keessatti yeroo meeqa gadda, gammachuu gadi aanaa yookaan abdii dhabdee jirtu?"},
        {"id": 3, "code": "PR_03", "section": "Yaaddoo fi Dhiphina", "category": "anxiety",
         "text": "Yeroo meeqa yaaddoo, soda yookaan tasgabbaa'uu dhabdee jirtu?"},
        {"id": 4, "code": "PR_04", "section": "Yaaddoo fi Dhiphina", "category": "anxiety",
         "text": "Waa'ee jireenyaa keetii yeroo meeqa yaaddoo to'achuu yookaan dhaabuu rakkisaa ta'e?"},
        {"id": 5, "code": "PR_05", "section": "Qaama fi Annisaa", "category": "wellbeing",
         "text": "Hirriba dhalachuu, tursiisuu yookaan baay'ee hirribuu rakkoo qabdaa?"},
        {"id": 6, "code": "PR_06", "section": "Qaama fi Annisaa", "category": "wellbeing",
         "text": "Yeroo meeqa dadhabbii, annisaa gadi aanaa yookaan hojii guyyaa guyyaa xumuruuf humna dhabdee jirtu?"},
        {"id": 7, "code": "PR_07", "section": "Yaada fi Of-tola", "category": "wellbeing",
         "text": "Yeroo meeqa ofii kee irratti miira gadi aanaa, kufaatii yookaan ofii yookaan maatii kee akka kufe miira qabde?"},
        {"id": 8, "code": "PR_08", "section": "Yaada fi Of-tola", "category": "wellbeing",
         "text": "Dubbisuuf, dubbisuu yookaan hojii irratti xiyyeeffannoo qabachuuf rakkoo qabde?"},
        {"id": 9, "code": "PR_09", "section": "Hawaasa fi Naannoo", "category": "wellbeing",
         "text": "Yeroo meeqa hawaasa kee, hiriyoota yookaan maatii kee irraa adda ta'ee yookaan walqabatee hin jirre?"},
        {"id": 10, "code": "PR_10", "section": "Dhiibbaa Hojii", "category": "wellbeing",
         "text": "Yoo rakkoonni kana keessaa tokko yoo jiraate, rakkoonni kun hojii kee, mana kee yookaan namoota waliin walqunnamtii kee meeqa rakkisaa taasisa?"},
    ],
}


def _build_questions(lang: str) -> list[dict]:
    language = lang if lang in QUESTION_TEXT else "en"
    std_opts = STANDARD_OPTIONS[language]
    func_opts = FUNCTIONAL_OPTIONS[language]
    questions = []
    for q in QUESTION_TEXT[language]:
        questions.append({
            **q,
            "options": func_opts if q["id"] == 10 else std_opts,
        })
    return questions


def _get_questions(lang: str) -> dict:
    language = lang if lang in QUESTION_TEXT else "en"
    questions = _build_questions(language)
    return {
        "questions": questions,
        "options": [o["label"] for o in STANDARD_OPTIONS[language]],
        "scale": "0-3 (frequency scale)",
    }


def _build_result(scores: dict, risk: str, lang: str, assessment_id: str = "", created_at=None):
    from datetime import datetime
    return {
        "id": assessment_id or "guest",
        "total_score": scores["total_score"],
        "stress_score": scores["stress_score"],
        "anxiety_score": scores["anxiety_score"],
        "depression_score": scores["depression_score"],
        "risk_level": risk,
        "risk_tier": get_risk_tier(scores["total_score"]),
        "recommendation": get_recommendation(risk, lang),
        "created_at": created_at or datetime.utcnow(),
    }


@router.get("/questions")
def get_questions(language: str = Query("en")):
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
    risk = determine_risk_level(scores["total_score"])

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

    result = _build_result(scores, risk, user.language, assessment.id, assessment.created_at)
    return AssessmentResult(**result)


@router.post("/submit-guest")
def submit_assessment_guest(
    data: AssessmentSubmit,
    language: str = Query("en"),
):
    answers = [{"question_id": a.question_id, "score": a.score} for a in data.answers]
    scores = calculate_scores(answers)
    risk = determine_risk_level(scores["total_score"])
    lang = language if language in ("en", "am", "om") else "en"
    return _build_result(scores, risk, lang)


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
        total_score=0,
        stress_score=assessment.stress_score,
        anxiety_score=assessment.anxiety_score,
        depression_score=assessment.depression_score,
        risk_level=assessment.risk_level,
        risk_tier=get_risk_tier(0),
        recommendation=get_recommendation(assessment.risk_level, user.language),
        created_at=assessment.created_at,
    )
