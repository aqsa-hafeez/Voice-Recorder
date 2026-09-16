from datetime import datetime, timezone

import os

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, LargeBinary
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.core.config import settings

# For local SQLite, make sure the folder for the .db file actually exists
# (e.g. "sqlite:////tmp/storage/app.db" needs a "tmp/storage" folder).
# Postgres URLs are untouched by this.
if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "", 1)
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="Untitled Conversation")
    language_detected = Column(String, nullable=True)
    duration_sec = Column(Float, nullable=True)
    status = Column(String, default="processing")  # processing | done | failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Audio saved directly in the database (bytea/blob) so playback works
    # even on serverless deployments where local disk (/tmp) doesn't persist.
    audio_data = Column(LargeBinary, nullable=True)
    audio_mime_type = Column(String, nullable=True)

    segments = relationship(
        "Segment", back_populates="conversation", cascade="all, delete-orphan"
    )

    @property
    def has_audio(self) -> bool:
        return self.audio_data is not None


class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    speaker_label = Column(String)   
    text = Column(String)
    start_time = Column(Float)
    end_time = Column(Float)

    conversation = relationship("Conversation", back_populates="segments")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
