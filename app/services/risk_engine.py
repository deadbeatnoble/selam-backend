def calculate_scores(answers: list[dict]) -> dict:
    """Calculate stress, anxiety, depression scores from assessment answers."""
    stress_ids = {1, 2, 3, 4}
    anxiety_ids = {5, 6, 7, 8}
    depression_ids = {9, 10, 11, 12}

    stress = sum(a["score"] for a in answers if a["question_id"] in stress_ids) * 5
    anxiety = sum(a["score"] for a in answers if a["question_id"] in anxiety_ids) * 5
    depression = sum(a["score"] for a in answers if a["question_id"] in depression_ids) * 5

    return {
        "stress_score": min(stress, 100),
        "anxiety_score": min(anxiety, 100),
        "depression_score": min(depression, 100),
    }


def determine_risk_level(stress: int, anxiety: int, depression: int) -> str:
    composite = max(stress, anxiety, depression)
    if composite < 30:
        return "green"
    if composite <= 60:
        return "yellow"
    return "red"


def get_recommendation(risk_level: str, language: str = "en") -> str:
    recommendations = {
        "en": {
            "green": "You're doing well! Explore wellness content, breathing exercises, and meditation.",
            "yellow": "Consider weekly monitoring and a personalized wellness plan. Check in with your mood regularly.",
            "red": "We recommend professional support. Please consider booking an appointment with a mental health professional.",
        },
        "am": {
            "green": "በጣም ጥሩ ነው! የጤና ይዘቶችን፣ የመተንፈስ ልምምዶችን እና ማሰላሰልን ይሞክሩ።",
            "yellow": "ሳምንታዊ ክትትል እና የግል ዕቅድ ያስቡ። የስሜትዎን በየጊዜው ይመዝግቡ።",
            "red": "የሙያዊ ድጋፍ እንመክራለን። ከአእምሮ ጤና ባለሙያ ጋር ቀጠሮ ለመያዝ ያስቡ።",
        },
        "om": {
            "green": "Baay'ee gaarii! Qabiyyee fayyaa, hafuura baafachuu fi yaada qabachuu yaali.",
            "yellow": "Sakatta'insa torbanii fi karoora fayyaa ofii keetii yaadi. Miira kee yeroo hunda galmeessi.",
            "red": "Deeggarsa ogummaa gorsina. Beellama ogummaa fayyaa sammuu qabsiisuu yaadi.",
        },
    }
    return recommendations.get(language, recommendations["en"]).get(risk_level, "")
