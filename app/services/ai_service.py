import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = {
    "en": """You are SelamMind, a supportive wellness companion.
RULES:
- Keep every reply to 2-3 short sentences maximum. Never overwhelm the user.
- Never diagnose medical conditions or claim the user has any disorder.
- Offer gentle coping strategies only.
- Respect privacy: do NOT mention professionals unless the user explicitly asks or shows crisis signs.
- Be warm, calm, and brief.""",
    "am": """እርስዎ SelamMind ነዎት፣ ደጋፊ የጤና ጓደኛ።
ደንቦች:
- ሁሉንም ምላሾች በ2-3 አጭር ዓረፍተ ነገሮች ውስጥ ይገባዉ። ተጠቃሚውን አያስቸጥሩ።
- ህክምና ሁኔታዎችን በጭራረት አያድኑ።
- ለስላሳ መቋቋም ስትራቴጂዎችን ብቻ ያቅርቡ።
- ግላዊነትን ያክብሩ፡ ተጠቃሚው ሲጠይቅ ወይም አደጋ ምልክት ካለ ብቻ ባለሙያ ይመልከቱ።
- ሞቅ ያለ፣ ቀላል እና አጭር ይሁኑ።""",
    "om": """Ati SelamMind dha, hiriyaa fayyaa deeggarsaa.
Seerota:
- Deebiin hundi jechoota 2-3 gabaabaa qofa. Fayyadamaa hin ulfachiisin.
- Haala fayyaa hin madaalin.
- Tooftaalee of-qabachuu tasgabbaa'aa qofa kenni.
- Dhuunfaa kabaji: ogummaa osoo hin gaafatin yookaan balaan osoo hin mul'atin hin gorsin.
- Tasgabbaa'aa, salphaa fi gabaabaa ta'i.""",
}

BREATHING_FALLBACK = {
    "en": {
        "reply": "Let's breathe together. Follow the timer below.",
        "structured_data": {
            "type": "breathing",
            "title": "4-7-8 Breathing Exercise",
            "description": "A gentle technique to calm your mind.",
            "steps": [
                {"phase": "inhale", "duration_seconds": 4, "instruction": "Breathe in slowly through your nose"},
                {"phase": "hold", "duration_seconds": 7, "instruction": "Hold your breath gently"},
                {"phase": "exhale", "duration_seconds": 8, "instruction": "Exhale slowly through your mouth"},
            ],
            "cycles": 4,
        },
    },
    "am": {
        "reply": "አብረን እንተንፋፍ። ከታች ያለውን ሰዓት ይከተሉ።",
        "structured_data": {
            "type": "breathing",
            "title": "4-7-8 የመተንፈስ ልምምድ",
            "description": "አእምሮን ለማረጋገጥ ለስላሳ ቴክኒክ።",
            "steps": [
                {"phase": "inhale", "duration_seconds": 4, "instruction": "በአፍንጫዎ በዝግታ ይተንፉ"},
                {"phase": "hold", "duration_seconds": 7, "instruction": "መተንፈስዎን በቀስታ ይያዙ"},
                {"phase": "exhale", "duration_seconds": 8, "instruction": "በአፍዎ በዝግታ ይተንፉ"},
            ],
            "cycles": 4,
        },
    },
    "om": {
        "reply": "Waliin hafuura baafnu. Sa'aatii armaan gadii hordofi.",
        "structured_data": {
            "type": "breathing",
            "title": "Shaakala hafuura baafachuu 4-7-8",
            "description": "Mala tasgabbaa'aa sammuu kee tasgabbeessuuf.",
            "steps": [
                {"phase": "inhale", "duration_seconds": 4, "instruction": "Sanka keetiin suutaan hafuura fudhadhu"},
                {"phase": "hold", "duration_seconds": 7, "instruction": "Hafuura suutaan qabi"},
                {"phase": "exhale", "duration_seconds": 8, "instruction": "Afaan keetiin suutaan hafuura baasi"},
            ],
            "cycles": 4,
        },
    },
}

BOOKS_FALLBACK = {
    "en": {
        "reply": "Here are a few gentle reads that may help.",
        "structured_data": {
            "type": "books",
            "title": "Recommended Reads",
            "books": [
                {"title": "The Gifts of Imperfection", "author": "Brené Brown", "description": "A short guide to self-compassion."},
                {"title": "Reasons to Stay Alive", "author": "Matt Haig", "description": "Hopeful reflections on hard times."},
                {"title": "Mindfulness in Plain English", "author": "Bhante Henepola Gunaratana", "description": "Simple steps to calm your mind."},
            ],
        },
    },
    "am": {
        "reply": "ሊረዱ የሚችሉ ለስላሳ መጽሐፍት።",
        "structured_data": {
            "type": "books",
            "title": "የሚመከሩ መጽሐፍት",
            "books": [
                {"title": "The Gifts of Imperfection", "author": "Brené Brown", "description": "የራስ ላይ ያለን ትላቅነት አጭር መመሪያ።"},
                {"title": "Reasons to Stay Alive", "author": "Matt Haig", "description": "በከባድ ጊዜ ተስፋ የሚሰጡ ሐሳቦች።"},
                {"title": "Mindfulness in Plain English", "author": "Bhante Henepola Gunaratana", "description": "አእምሮን ለማረጋገጥ ቀላል እርምጃዎች።"},
            ],
        },
    },
    "om": {
        "reply": "Kitaabota tasgabbaa'aa si gargaaran.",
        "structured_data": {
            "type": "books",
            "title": "Kitaabota gorfaman",
            "books": [
                {"title": "The Gifts of Imperfection", "author": "Brené Brown", "description": "Qajeelfama gabaabaa of-jalabbii."},
                {"title": "Reasons to Stay Alive", "author": "Matt Haig", "description": "Yaada abdii yeroo rakkisaa keessatti."},
                {"title": "Mindfulness in Plain English", "author": "Bhante Henepola Gunaratana", "description": "Tarkaanfiiwwan salphaa sammuu tasgabbeessuuf."},
            ],
        },
    },
}

STUDY_PLAN_FALLBACK = {
    "en": {
        "reply": "Here's your study plan, organized by priority.",
        "structured_data": {
            "type": "study_plan",
            "title": "Your Study Plan",
            "todos": [
                {"id": 1, "task": "Review Chapter 5 - Biology", "deadline": "Tomorrow", "priority": "high", "completed": False},
                {"id": 2, "task": "Complete Math homework", "deadline": "In 2 days", "priority": "high", "completed": False},
                {"id": 3, "task": "Read essay requirements", "deadline": "In 3 days", "priority": "medium", "completed": False},
            ],
            "tips": ["Start with high-priority tasks", "Take breaks every 45 minutes"],
        },
    },
    "am": {
        "reply": "በቅድሚያ የተዘጋጀ የጥናት ዕቅድዎ።",
        "structured_data": {
            "type": "study_plan",
            "title": "የእርስዎ የጥናት ዕቅድ",
            "todos": [
                {"id": 1, "task": "ምዕራፍ 5 - ባዮሎጂ ይገምግሙ", "deadline": "ነገ", "priority": "high", "completed": False},
                {"id": 2, "task": "የሂሳብ ቤት ሥራ ያጠናቅቁ", "deadline": "በ2 ቀናት", "priority": "high", "completed": False},
                {"id": 3, "task": "የፅሁፍ መስፈርቶችን ያንብቡ", "deadline": "በ3 ቀናት", "priority": "medium", "completed": False},
            ],
            "tips": ["ከፍተኛ ቅድሚያ ተግባሮችን መጀመሪያ ያስሩ", "በየ45 ደቂቃው ዕረፍት ይውሰዱ"],
        },
    },
    "om": {
        "reply": "Karoora barumsaa kee dursaatiin qophaa'e.",
        "structured_data": {
            "type": "study_plan",
            "title": "Karoora barumsaa kee",
            "todos": [
                {"id": 1, "task": "Bo'oo 5 - Baayoloojii ilaali", "deadline": "Boru", "priority": "high", "completed": False},
                {"id": 2, "task": "Hojii herregaa xumuri", "deadline": "Guyyaa 2tti", "priority": "high", "completed": False},
                {"id": 3, "task": "Ibsa barreeffamaa dubbisi", "deadline": "Guyyaa 3tti", "priority": "medium", "completed": False},
            ],
            "tips": ["Hojiiwwan dursa ol kaan jalqabi", "Yeroo 45tti boqonnaa fudhadhu"],
        },
    },
}

SUPPORT_FALLBACK = {
    "en": "I hear you. Take your time — try breathing, a study plan, or book suggestions.",
    "am": "እንደምትሰማህ አስተውያለሁ። ጊዜዎን ይውሰዱ — የመተንፈስ ልምምድ ወይም መጽሐፍት ይሞክሩ።",
    "om": "Sagalee kee dhaga'eera. Yeroo kee fudhadhu — hafuura baafachuu yookaan kitaabota yaali.",
}

HIGH_RISK_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die", "self-harm",
    "ማጥፋት", "መሞት", "ሞት", "ራሴን",
    "of du'uu", "of ajjeesuu", "du'uu barbaada",
]

PROFESSIONAL_REQUEST_KEYWORDS = [
    "professional", "therapist", "psychologist", "psychiatrist", "doctor", "counselor",
    "ባለሙያ", "ሐኪም", "ሐኪም", "ምክር",
    "ogummaa", "saayikoloojistii", "haakim",
]

OLLAMA_TIMEOUT = 60.0
_resolved_model: str | None = None


async def _resolve_ollama_model() -> str:
    global _resolved_model
    if _resolved_model:
        return _resolved_model

    configured = settings.ollama_model
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                if configured in models:
                    _resolved_model = configured
                    return _resolved_model
                for name in models:
                    if name.startswith(configured):
                        _resolved_model = name
                        return _resolved_model
                if models:
                    _resolved_model = models[0]
                    logger.warning("Model %s not found; using %s", configured, _resolved_model)
                    return _resolved_model
    except Exception as exc:
        logger.warning("Could not resolve Ollama model: %s", exc)

    _resolved_model = configured
    return _resolved_model


async def check_ai_status() -> dict:
    available = False
    model = settings.ollama_model
    models: list[str] = []
    error = None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                available = len(models) > 0
                model = await _resolve_ollama_model()
    except Exception as exc:
        error = str(exc)[:120]

    return {
        "ollama_url": settings.ollama_base_url,
        "configured_model": settings.ollama_model,
        "active_model": model,
        "available": available or bool(settings.openai_api_key),
        "ollama_running": available,
        "models": models,
        "error": error,
    }


def _get_system_prompt(language: str) -> str:
    return SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"])


def _truncate_reply(text: str, max_sentences: int = 3) -> str:
    sentences = text.replace("!", ".").replace("?", ".").split(".")
    kept = [s.strip() for s in sentences if s.strip()][:max_sentences]
    return ". ".join(kept) + ("." if kept else "")


async def _check_ollama_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            return resp.status_code == 200 and bool(resp.json().get("models"))
    except Exception as exc:
        logger.debug("Ollama unavailable: %s", exc)
        return False


async def _call_ollama(prompt: str, language: str) -> str | None:
    model = await _resolve_ollama_model()
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": _get_system_prompt(language)},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                return _truncate_reply(content) if content else None
            logger.warning("Ollama chat failed: HTTP %s — %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("Ollama chat error: %s", exc)
    return None


async def _call_openai(prompt: str, language: str) -> str | None:
    if not settings.openai_api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": _get_system_prompt(language)},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 150,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return _truncate_reply(content) if content else None
    except Exception:
        pass
    return None


def _detect_high_risk(message: str) -> bool:
    lower = message.lower()
    return any(kw in lower for kw in HIGH_RISK_KEYWORDS)


def _wants_professional(message: str) -> bool:
    lower = message.lower()
    return any(kw in lower for kw in PROFESSIONAL_REQUEST_KEYWORDS)


async def _generate_study_plan_with_ai(message: str, language: str) -> dict | None:
    lang_labels = {"en": "English", "am": "Amharic", "om": "Oromo"}
    lang_label = lang_labels.get(language, "English")
    prompt = f"""Create a brief study plan. Reply ONLY with valid JSON:
{{"reply": "1 sentence in {lang_label}", "structured_data": {{"type": "study_plan", "title": "...", "todos": [{{"id": 1, "task": "...", "deadline": "...", "priority": "high|medium|low", "completed": false}}], "tips": ["..."]}}}}
User: {message}"""

    reply = await _call_ollama(prompt, language) or await _call_openai(prompt, language)
    if reply:
        try:
            start = reply.find("{")
            end = reply.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(reply[start:end])
        except json.JSONDecodeError:
            pass
    return None


async def generate_chat_response(
    message: str,
    chat_type: str = "support",
    language: str = "en",
) -> dict:
    ai_available = await _check_ollama_available() or bool(settings.openai_api_key)

    if chat_type == "breathing":
        fallback = BREATHING_FALLBACK.get(language, BREATHING_FALLBACK["en"])
        reply_text = fallback["reply"]
        used_ai = False
        if ai_available:
            prompt = f"One calming sentence for someone starting a breathing exercise. User: {message}"
            ai_reply = await _call_ollama(prompt, language) or await _call_openai(prompt, language)
            if ai_reply:
                reply_text = ai_reply
                used_ai = True
        return {
            "reply": reply_text,
            "chat_type": "breathing",
            "structured_data": fallback["structured_data"],
            "ai_available": True,
        }

    if chat_type == "books":
        fallback = BOOKS_FALLBACK.get(language, BOOKS_FALLBACK["en"])
        reply_text = fallback["reply"]
        used_ai = False
        if ai_available:
            prompt = f"One sentence recommending wellness books. User topic: {message}"
            ai_reply = await _call_ollama(prompt, language) or await _call_openai(prompt, language)
            if ai_reply:
                reply_text = ai_reply
                used_ai = True
        return {
            "reply": reply_text,
            "chat_type": "books",
            "structured_data": fallback["structured_data"],
            "ai_available": True,
        }

    if chat_type == "study_plan":
        if ai_available:
            result = await _generate_study_plan_with_ai(message, language)
            if result:
                return {
                    "reply": result.get("reply", ""),
                    "chat_type": "study_plan",
                    "structured_data": result.get("structured_data"),
                    "ai_available": True,
                }
        fallback = STUDY_PLAN_FALLBACK.get(language, STUDY_PLAN_FALLBACK["en"])
        return {
            "reply": fallback["reply"],
            "chat_type": "study_plan",
            "structured_data": fallback["structured_data"],
            "ai_available": True,
        }

    is_high_risk = _detect_high_risk(message)
    wants_professional = _wants_professional(message)

    if ai_available:
        reply = await _call_ollama(message, language) or await _call_openai(message, language)
        if reply:
            structured = None
            if is_high_risk or wants_professional:
                structured = {"high_risk": is_high_risk, "show_professional": True}
            return {
                "reply": reply,
                "chat_type": "support",
                "structured_data": structured,
                "ai_available": True,
            }

    fallback = SUPPORT_FALLBACK.get(language, SUPPORT_FALLBACK["en"])
    structured = None
    if is_high_risk or wants_professional:
        structured = {"high_risk": is_high_risk, "show_professional": True}
    return {
        "reply": fallback,
        "chat_type": "support",
        "structured_data": structured,
        "ai_available": True,
    }
