# [檔案用途：資料庫連線設定 Engine] (請勿更動)
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database file path
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./elder_care.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# [檔案用途：資料表結構定義 SQLAlchemy] (若需新增資料庫欄位可改)
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Elder(Base):
    __tablename__ = "elders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    # Face embeddings stored as JSON string/list for easy cosine similarity in python
    face_embedding = Column(JSON, nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    activity_logs = relationship("ActivityLog", back_populates="elder", cascade="all, delete-orphan")
    baselines = relationship("Baseline", back_populates="elder", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="elder", cascade="all, delete-orphan")

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("elders.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    activity_level = Column(Float, nullable=False) # e.g. 0.0 to 1.0 (movement intensity)
    posture = Column(String(50), nullable=True) # e.g. standing, sitting, lying
    location = Column(String(50), nullable=True) # future proofing (e.g. bed, living room if multiple cams)

    elder = relationship("Elder", back_populates="activity_logs")

class Baseline(Base):
    __tablename__ = "baselines"

    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("elders.id"), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now()) # Repesents the date this baseline aggregates
    avg_activity_level = Column(Float, nullable=False)
    sedentary_duration_mins = Column(Float, nullable=False, default=0.0)
    
    elder = relationship("Elder", back_populates="baselines")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("elders.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    type = Column(String(50), nullable=False) # e.g. "FALL", "INACTIVITY", "DEVIATION"
    severity = Column(String(20), nullable=False) # e.g. "HIGH", "MEDIUM"
    description = Column(Text, nullable=True)
    snapshot_path = Column(String(255), nullable=True) # local path to the saved image frame
    is_resolved = Column(Integer, server_default="0", nullable=False) # 0 for false, 1 for true

    elder = relationship("Elder", back_populates="events")
