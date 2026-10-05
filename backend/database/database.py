import json
from datetime import datetime
from collections.abc import Generator

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.config import DATABASE_URL

# SQLite configuration
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TravelPlanDB(Base):
    """SQLAlchemy model for storing generated travel itineraries."""
    __tablename__ = "travel_plans"

    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String(255), nullable=False, index=True)
    days = Column(Integer, nullable=False)
    budget = Column(Float, nullable=False)
    travelers = Column(Integer, nullable=False)
    interests = Column(Text, nullable=True)  # JSON-encoded list or string
    summary = Column(Text, nullable=True)
    itinerary_json = Column(Text, nullable=False)  # Complete JSON payload
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        """Convert database entity to dictionary."""
        try:
            parsed_itinerary = json.loads(self.itinerary_json)
        except Exception:
            parsed_itinerary = {}

        try:
            parsed_interests = json.loads(self.interests) if self.interests else []
        except Exception:
            parsed_interests = [i.strip() for i in (self.interests or "").split(",") if i.strip()]

        return {
            "id": self.id,
            "destination": self.destination,
            "days": self.days,
            "budget": self.budget,
            "travelers": self.travelers,
            "interests": parsed_interests,
            "summary": self.summary,
            "days_plan": parsed_itinerary.get("days", []),
            "travel_tips": parsed_itinerary.get("travel_tips", []),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def init_db():
    """Create all database tables automatically on startup."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

