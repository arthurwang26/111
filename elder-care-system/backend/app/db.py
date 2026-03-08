# [檔案用途：資料庫連線設定 Engine] (請勿更動)
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://elder_admin:elder_password@localhost:5432/elder_care")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# PostgreSQL does not need check_same_thread
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# [檔案用途：資料表結構定義 SQLAlchemy] (若需新增資料庫欄位可改)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Resident(Base):
    __tablename__ = "residents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    room = Column(String(50), nullable=True)
    family_line_id = Column(String(100), nullable=True)
    face_embedding = Column(JSON, nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    events = relationship("Event", back_populates="resident", cascade="all, delete-orphan")
    daily_activities = relationship("DailyActivity", back_populates="resident", cascade="all, delete-orphan")
    abnormal_events = relationship("AbnormalEvent", back_populates="resident", cascade="all, delete-orphan")

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    source = Column(String(255), nullable=False) # URL, RTSP, or device index
    location = Column(String(100), nullable=True)
    status = Column(String(20), default="offline") # online, offline, error
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    events = relationship("Event", back_populates="camera", cascade="all, delete-orphan")

class Event(Base): # General behavior/interaction events
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"), nullable=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    activity_type = Column(String(50), nullable=False) # walk, sit, lay, eat, play, watch_tv
    object_interaction = Column(String(100), nullable=True) # wheelchair, cup, cane, etc.
    description = Column(Text, nullable=True)

    resident = relationship("Resident", back_populates="events")
    camera = relationship("Camera", back_populates="events")

class DailyActivity(Base):
    __tablename__ = "daily_activity"
    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    walking_mins = Column(Float, default=0.0)
    sitting_mins = Column(Float, default=0.0)
    sleeping_mins = Column(Float, default=0.0)
    interaction_mins = Column(Float, default=0.0)
    health_score = Column(Float, default=0.0)
    summary_text = Column(Text, nullable=True) # AI summary
    
    resident = relationship("Resident", back_populates="daily_activities")

class AbnormalEvent(Base):
    __tablename__ = "abnormal_events"
    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    level = Column(Integer, nullable=False) # 1, 2, 3
    type = Column(String(50), nullable=False) # fall, inactivity_20m, night_activity, dangerous_object
    description = Column(Text, nullable=True)
    snapshot_path = Column(String(255), nullable=True)
    video_path = Column(String(255), nullable=True)
    ai_summary = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False)
    
    resident = relationship("Resident", back_populates="abnormal_events")

class SystemHealthLog(Base):
    __tablename__ = "system_health_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    module = Column(String(50), nullable=False) # camera, cv_model, line_bot, database
    status = Column(String(20), nullable=False) # ok, warning, error
    message = Column(Text, nullable=True)
class SystemMetric(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    ai_latency_ms = Column(Float, default=0.0) # AI 推論延遲
    camera_fps = Column(Float, default=0.0)    # 實際讀取幀率
    active_tracks = Column(Integer, default=0) # 追蹤中的目標數量
    cpu_usage_percent = Column(Float, default=0.0) # 系統 CPU 使用率
