MOOD_IDS = {1, 2}
ANXIETY_IDS = {3, 4}
WELLBEING_IDS = {5, 6, 7, 8, 9, 10}


def _section_percent(total: int, max_possible: int) -> int:
    if max_possible == 0:
        return 0
    return min(round(total / max_possible * 100), 100)


def calculate_scores(answers: list[dict]) -> dict:
    """Calculate section scores and total from psychological risk assessment."""
    total = sum(a["score"] for a in answers)
    mood = sum(a["score"] for a in answers if a["question_id"] in MOOD_IDS)
    anxiety = sum(a["score"] for a in answers if a["question_id"] in ANXIETY_IDS)
    wellbeing = sum(a["score"] for a in answers if a["question_id"] in WELLBEING_IDS)

    return {
        "total_score": min(total, 30),
        "stress_score": _section_percent(mood, 6),
        "anxiety_score": _section_percent(anxiety, 6),
        "depression_score": _section_percent(wellbeing, 18),
    }


def determine_risk_level(total_score: int) -> str:
    if total_score <= 7:
        return "green"
    if total_score <= 21:
        return "yellow"
    return "red"


def get_risk_tier(total_score: int) -> str:
    if total_score <= 7:
        return "low"
    if total_score <= 14:
        return "mild"
    if total_score <= 21:
        return "moderate"
    return "severe"


def get_recommendation(risk_level: str, language: str = "en") -> str:
    recommendations = {
        "en": {
            "green": "You're doing well. Explore wellness articles, lifestyle tips, and routine self-care tracking.",
            "yellow": "Consider targeted wellness modules, peer support, or scheduling a consultation with a care provider.",
            "red": "We recommend immediate support. Please reach out to a professional and use our priority helpline resources.",
        },
        "am": {
            "green": "በጣም ጥሩ ነው። የጤና መጣጥሞችን፣ የኑሮ ምክሮችን እና የራስ እንክብካቤ መከታተያ ይሞክሩ።",
            "yellow": "የተመረጡ የጤና መሳሪያዎችን ይሞክሩ ወይም ከባለሙያ ጋር ምክክር ያስቡ።",
            "red": "ወዲያውኑ ድጋፍ እንመክራለን። ወደ ባለሙያ ያግኙ እና የአስቸኳይ እገዛ መስመሮቻችንን ይጠቀሙ።",
        },
        "om": {
            "green": "Baay'ee gaarii. Qabiyyee fayyaa, gorsa jireenyaa fi hordoffii of-eegumsaa yaali.",
            "yellow": "Meeshaalee fayyaa filataman yookaan marii ogummaa qabsiisuu yaadi.",
            "red": "Deeggarsa ariifataa gorsina. Ogummaa qunnamiifi sarara gargaarsa dursaatiif fayyadami.",
        },
    }
    return recommendations.get(language, recommendations["en"]).get(risk_level, "")
