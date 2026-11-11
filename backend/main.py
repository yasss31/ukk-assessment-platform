"""
main.py - Entry point FastAPI UKK Assessment Platform
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.storage import storage
from app.routers import (
    auth_routes,
    dashboard_routes,
    participant_routes,
    rubric_routes,
    assessment_routes,
    auto_play_routes,
    sheets_routes
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ukk-assessment-main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Inisialisasi storage & rubric default
    logger.info("Memulai UKK Assessment Platform Backend...")
    rubrics = storage.list_rubrics()
    participants = storage.list_participants()
    logger.info(f"Loaded {len(rubrics)} profil rubrik dan {len(participants)} peserta.")
    logger.info(f"Google Sheets status: {storage.sheets.get_status()['status']}")
    yield
    # Shutdown
    logger.info("Menghentikan UKK Assessment Platform Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Web Penilaian Otomatis Uji Kompetensi Keahlian (UKK) Cloud Engineer dengan Rubrik Dinamis & Safe AWS Auto Play",
    lifespan=lifespan
)

# CORS Middleware
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(participant_routes.router)
app.include_router(rubric_routes.router)
app.include_router(assessment_routes.router)
app.include_router(auto_play_routes.router)
app.include_router(sheets_routes.router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "OPERATIONAL",
        "docs_url": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "google_sheets": storage.sheets.get_status(),
        "storage_mode": "local_fallback" if not storage.sheets.is_connected else "sheets_synced"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
