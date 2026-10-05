import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load configuration from THIS project's .env file explicitly, so it cannot be
# affected by the current working directory or a sibling project's .env.
load_dotenv(PROJECT_ROOT / ".env")

# Database configuration.
# Resolve a relative sqlite path against THIS project's root so the app never
# opens a sibling project's database file just because it was started elsewhere.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./travel_planner.db")
if DATABASE_URL.startswith("sqlite:///./"):
    _db_file = DATABASE_URL.replace("sqlite:///./", "", 1)
    DATABASE_URL = f"sqlite:///{(PROJECT_ROOT / _db_file).as_posix()}"
DATABASE_PATH = PROJECT_ROOT / "travel_planner.db"

# External API credentials
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# OpenStreetMap Configuration
NOMINATIM_USER_AGENT = os.getenv(
    "NOMINATIM_USER_AGENT",
    "AI-Travel-Planner/1.0 (contact: travel-planner-app@local.dev)"
)

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]
