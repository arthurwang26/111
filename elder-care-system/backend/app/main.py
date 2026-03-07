# [檔案用途：系統啟動入口管理] (預設不需更動，全系統的核心啟動點)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import engine, Base
from fastapi.staticfiles import StaticFiles
import os

# Ensure snapshots directory exists
os.makedirs("snapshots", exist_ok=True)

# Create database tables (if they don't exist yet, Alembic will handle migrations later)
Base.metadata.create_all(bind=engine)

from app.api import auth, dashboard, video, residents as residents_router, cameras as cameras_router, events as events_router, tests as tests_router
from contextlib import asynccontextmanager
from app.services.system_health import health_monitor

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load registered residents into CV processor and start background tasks
    health_monitor.start()
    try:
        from app.cv.processor import processor
        from app.db import SessionLocal
        db = SessionLocal()
        processor.refresh_residents(db)
        db.close()
    except Exception as e:
        print(f"[Startup] CV 初始化: {e}")
    yield  # 應用程式運行中
    # Shutdown
    health_monitor.stop()

app = FastAPI(
    title="Elderly Long-term Care API",
    description="長照中心視覺異常偵測系統後端",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(video.router)
app.include_router(residents_router.router)
app.include_router(cameras_router.router)
app.include_router(events_router.router)
app.include_router(tests_router.router)

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
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount React Frontend
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {"status": "ok", "message": "Elderly Care API is running. Frontend build not found."}
