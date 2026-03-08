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
    poll_thread = None
    running = [True]
    try:
        from app.cv.processor import processor
        from app.cv.capture import pipeline
        from app.db import SessionLocal, Camera
        import cv2, threading, time
        
        # 啟動非阻塞影像擷取
        pipeline.start()
        
        db = SessionLocal()
        processor.refresh_residents(db)
        db.close()

        # Background Camera Poller
        def poll_cameras():
            while running[0]:
                try:
                    with SessionLocal() as db_session:
                        cameras = db_session.query(Camera).all()
                        for cam in cameras:
                            if not running[0]: break
                            if cam.id == pipeline.active_camera_id:
                                continue # Main pipeline updates this
                            
                            idx_or_str = cam.source
                            try: idx_or_str = int(idx_or_str)
                            except: pass

                            cap = cv2.VideoCapture(idx_or_str)
                            is_opened = cap.isOpened()
                            if is_opened:
                                if cam.status != "active":
                                    cam.status = "active"
                                    db_session.commit()
                                cap.release()
                            else:
                                if cam.status != "offline":
                                    cam.status = "offline"
                                    db_session.commit()
                except Exception as e:
                    print(f"[Poller] Error: {e}")
                time.sleep(15)

        poll_thread = threading.Thread(target=poll_cameras, daemon=True)
        poll_thread.start()

    except Exception as e:
        print(f"[Startup] CV 初始化: {e}")
    yield  # 應用程式運行中
    # Shutdown
    health_monitor.stop()
    running[0] = False
    if poll_thread: poll_thread.join(timeout=2)

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

app.mount("/snapshots", StaticFiles(directory="snapshots"), name="snapshots")

# Allow React frontend to access the API
origins = [
    "http://localhost:5173", # Vite default
    "http://localhost:5174", # Vite fallback
    "http://0.0.0.0:5173",
    "http://127.0.0.1:5173",
    "https://*.ngrok-free.app",  # Ngrok public URL
    "https://*.ngrok.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開放全部，方便同學分享
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount React Frontend static assets
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    from fastapi.responses import FileResponse
    from fastapi import Request

    # Mount static assets (JS/CSS/images)
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    # Serve index.html for all non-API routes (React SPA catch-all)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str, request: Request):
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend not built"}
else:
    @app.get("/")
    def read_root():
        return {"status": "ok", "message": "Elderly Care API is running. Frontend build not found."}

