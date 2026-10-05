# WanderIQ ✈️✨

A playful, production-quality full-stack AI travel planning application built with **FastAPI**, **Groq LLM**, **OpenStreetMap (Nominatim & Overpass)**, **SQLAlchemy/SQLite**, and **Leaflet.js**.

---

## 🌟 Key Features

- **Playful, Vibrant Travel-Tech UI**: Intuitive steppers, quick preset chips, day tabs, animated progress loader, and interactive Leaflet OpenStreetMap.
- **AI-Powered Itineraries**: Intelligent, day-by-day travel schedules generated using Groq LLM tailored to budget, days, travelers, and interests.
- **Real-World Place Verification**: Every physical sightseeing spot is verified against OpenStreetMap (Nominatim & Overpass).
- **Zero Fake Coordinates**: Coordinates are only attached when verified with high confidence; unverified or non-sightseeing items are marked accordingly.
- **Interactive OpenStreetMap Visualization**: Interactive Leaflet.js map with markers for verified attractions and sequential route polylines.
- **100% Free & Open**: Completely independent of Google Cloud APIs and billing.
- **Persistent Trip Storage**: Automatic trip saving with SQLAlchemy and SQLite.
- **Trip History Management**: Browse, view, and delete previously generated itineraries.
- **Modern UI/UX**: Responsive glassmorphism interface, multi-select interest chips, and real-time step-by-step loading state.

---

## 🏗 System Architecture

```text
User / Browser (HTML5, CSS3, Vanilla JS, Leaflet.js)
       ↓ (HTTP REST API)
FastAPI Backend (backend/main.py)
       ↓
Groq LLM (openai/gpt-oss-120b & fallbacks) ──> AI Itinerary Generation
       ↓
OpenStreetMap Nominatim / Overpass ──────────> Real-World Place Verification
       ↓
SQLAlchemy & SQLite (travel_planner.db) ─────> Trip Persistence & History
```

---

## 📁 Project Structure

```text
AI-Travel-Planner/
├── backend/
│   ├── database/
│   │   ├── __init__.py
│   │   └── database.py        # SQLAlchemy engine, models, and session management
│   ├── models/
│   │   ├── __init__.py
│   │   └── travel.py          # Pydantic models & request validation
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── travel.py          # /api/travel endpoints (plan, history, detail, delete)
│   │   └── places.py          # /api/places endpoints (search, verify)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── groq_service.py    # AI itinerary generation via Groq
│   │   ├── places_service.py  # Nominatim & Overpass place discovery
│   │   ├── place_processor.py # Normalization, filtering, and place matching
│   │   └── geocoding_service.py # Nominatim geocoding & scoring
│   ├── __init__.py
│   ├── config.py              # Environment configuration
│   ├── main.py                # FastAPI app, CORS, lifespan, routes
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── index.html             # Responsive UI with form, timeline & map
│   ├── script.js              # Fetch client, Leaflet map, step loader, history
│   └── style.css              # Modern travel-tech design system
├── .env                       # Environment variables (API keys)
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+
- Groq API Key (from [console.groq.com](https://console.groq.com))

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone <repo-url>
cd AI-Travel-Planner

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables
Create or update `.env` in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=sqlite:///./travel_planner.db
OPENWEATHER_API_KEY=your_optional_openweather_key
```

### 4. Run the Backend API

**Windows (recommended):** from the `AI-Travel-Planner` folder run:
```powershell
./start-backend.ps1
```
This forces the correct working directory, venv and port, and refuses to start if
port 8001 is already taken (so it can never collide with the other AI projects).

Equivalent manual command (run from the `AI-Travel-Planner` folder):
```bash
python -m uvicorn backend.main:app --reload --reload-dir backend --host 127.0.0.1 --port 8001
```
- API is live at `http://127.0.0.1:8001`
- Interactive OpenAPI Docs: `http://127.0.0.1:8001/docs`
- Identity / health check: `http://127.0.0.1:8001/health` -> `{"service": "AI Travel Planner", ...}`

> Port map for the shared parent folder: Travel Planner = **8001**, Recipe Finder = 8000, Home Interior Planner = 8002.

### 5. Launch the Frontend
Open `frontend/index.html` in your browser or run a simple local HTTP server:
```bash
python -m http.server 5500 --directory frontend
```
Navigate to `http://127.0.0.1:5500`.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | API health check (`{"status": "ok"}`) |
| `POST` | `/api/travel/plan` | Generate AI itinerary, verify places, save & return |
| `GET` | `/api/travel/history` | Retrieve saved travel plans |
| `GET` | `/api/travel/{id}` | Retrieve details of a saved trip |
| `DELETE` | `/api/travel/{id}` | Delete a saved trip |
| `GET` | `/api/places/search` | Search OSM attractions in destination |
| `GET` | `/api/places/verify` | Verify a specific place via Nominatim |

---

## 🧪 Testing

Run backend tests:
```bash
python -m pytest
# or run the end-to-end test suite
python test_e2e_flow.py
```
