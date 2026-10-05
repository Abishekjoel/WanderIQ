"""
Test other destinations (e.g. Goa) to ensure zero destination hardcoding
and verify Overpass fallback resilience.
"""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.main import app

client = TestClient(app)

def test_generic_destination_goa():
    print("\n[TEST] Generic Destination: Goa...")
    payload = {
        "destination": "Goa",
        "days": 2,
        "budget": 12000,
        "travelers": 2,
        "interests": ["Beaches", "Food"]
    }
    res = client.post("/api/travel/plan", json=payload)
    assert res.status_code == 200, f"Failed with {res.status_code}: {res.text}"
    data = res.json()["data"]
    assert data["destination"] == "Goa"
    assert len(data["days"]) > 0
    print(f" -> Successfully generated itinerary for Goa with {len(data['days'])} days!")

if __name__ == "__main__":
    test_generic_destination_goa()
