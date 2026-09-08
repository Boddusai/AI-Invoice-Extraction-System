from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.invoices import router as invoices_router
from app.database.database import engine
from app.config import settings


app = FastAPI(
    title="AI Invoice Extraction API",
    description="AI-powered invoice data extraction and validation system",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(invoices_router)


@app.get("/")
def root():
    return {
        "message": "AI Invoice Extraction API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Invoice Extraction API"
    }


@app.get("/database-health")
def database_health():

    try:

        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        return {
            "status": "connected",
            "database": "PostgreSQL"
        }

    except Exception as error:

        return {
            "status": "disconnected",
            "error": str(error)
        }

@app.get("/api-info")
def api_info():
    return {
        "name": "AI Invoice Extraction API",
        "version": "1.0.0",
        "status": "running",
        "frontend": "React",
        "backend": "FastAPI",
        "database": "PostgreSQL",
    }