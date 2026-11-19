import sys
import os

# Ensure standard output/error use UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import create_tables
from app.routers.analysis import router as analysis_router
from app.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    os.makedirs(settings.REPOS_DIR, exist_ok=True)
    await create_tables()
    yield

app = FastAPI(title="RepoDoctor AI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)

@app.get("/")
async def root():
    return {"message": "RepoDoctor AI API", "version": "1.0.0"}

@app.get("/api/health")
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "RepoDoctor AI"}
