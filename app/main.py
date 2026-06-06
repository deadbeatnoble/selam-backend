from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import Base, engine
from app.routers import assessment, appointments, auth, chat, mood, professionals
from app.seed import seed_professionals
from app.services.ai_service import check_ai_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE professionals ADD COLUMN IF NOT EXISTS email VARCHAR(100)"))
            conn.execute(
                text(
                    "UPDATE professionals SET email = LOWER(REPLACE(name, ' ', '.')) || '@selammind.et' "
                    "WHERE email IS NULL OR email = ''"
                )
            )
    except Exception:
        pass
    seed_professionals()
    yield


app = FastAPI(
    title="SelamMind API",
    description="Mental Wellness Platform for Ethiopia",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(mood.router)
app.include_router(assessment.router)
app.include_router(chat.router)
app.include_router(professionals.router)
app.include_router(appointments.router)


@app.get("/")
def root():
    return {"message": "SelamMind API", "status": "running"}


@app.get("/health")
async def health():
    db_status = "disconnected"
    db_name = "unknown"
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT current_database()")).scalar()
            db_status = "connected"
            db_name = row
    except Exception as e:
        db_status = f"error: {str(e)[:120]}"
    ai_status = await check_ai_status()
    return {
        "api": "running",
        "database": db_status,
        "database_name": db_name,
        "ai": ai_status,
    }
