from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.database import engine, Base
from .db import models
from fastapi.staticfiles import StaticFiles
import os

# Ensure snapshots directory exists
os.makedirs("snapshots", exist_ok=True)

# Create database tables (if they don't exist yet, Alembic will handle migrations later)
models.Base.metadata.create_all(bind=engine)

from app.api import auth, dashboard, video, elders as elders_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # 啟動時刷新 CV 長者快取
    try:
        from app.cv.processor import processor
        from app.db.database import SessionLocal
        db = SessionLocal()
        processor.refresh_elders(db)
        db.close()
    except Exception as e:
        print(f"[Startup] CV 初始化: {e}")
    yield  # 應用程式運行中

app = FastAPI(
    title="Elderly Long-term Care API",
    description="長照中心視覺異常偵測系統後端",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(video.router)
app.include_router(elders_router.router)

app.mount("/static/snapshots", StaticFiles(directory="snapshots"), name="snapshots")

# Allow React frontend to access the API
origins = [
    "http://localhost:5173", # Vite default
    "http://localhost:5174", # Vite fallback
    "http://0.0.0.0:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Elderly Care API is running"}
