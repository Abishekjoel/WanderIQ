import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.database import init_db
from backend.routes.travel import router as travel_router
from backend.routes.places import router as places_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("travel_planner")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: initialize database tables automatically on startup."""
    logger.info("Initializing database tables...")
    init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down AI Travel Planner API.")


app = FastAPI(
    title="WanderIQ API",
    description="WanderIQ — AI-powered travel planning application using Groq, OpenStreetMap, and SQLite.",
    version="1.0.0",
    lifespan=lifespan
)

# --------------------------------------------------
# CORS Configuration
# --------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "null",  # For local file:// testing if opened directly in browser
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Core Endpoints
# --------------------------------------------------
@app.get("/")
def root():
    return {
        "service": "AI Travel Planner",
        "project": "AI Travel Planner",
        "status": "running",
        "port": 8001,
        "message": "WanderIQ API is running!",
        "docs": "/docs",
        "health": "/health"
    }



@app.get("/health")
def health():
    return {
        "service": "AI Travel Planner",
        "project": "AI Travel Planner",
        "status": "ok",
        "port": 8001
    }


# --------------------------------------------------
# Feature Routers
# --------------------------------------------------
app.include_router(travel_router)
app.include_router(places_router)