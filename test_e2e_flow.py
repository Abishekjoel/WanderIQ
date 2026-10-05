"""
End-to-End Test Suite for AI Travel Planner
Tests FastAPI endpoints, Groq integration, Nominatim/Overpass verification,
Database persistence, and edge case resilience.
"""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.main import app

client = TestClient(app)


def test_health_check():
    print("\n[TEST] Health Check...")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print(" -> Health check passed!")


def test_input_validation():
    print("\n[TEST] Input Validation Errors (422)...")
    # Empty destination
    res1 = client.post("/api/travel/plan", json={"destination": "   ", "days": 3, "budget": 10000, "travelers": 2})
    assert res1.status_code == 422, f"Expected 422, got {res1.status_code}"

    # Zero days
    res2 = client.post("/api/travel/plan", json={"destination": "Goa", "days": 0, "budget": 10000, "travelers": 2})
    assert res2.status_code == 422, f"Expected 422, got {res2.status_code}"

    # Negative budget
    res3 = client.post("/api/travel/plan", json={"destination": "Goa", "days": 3, "budget": -500, "travelers": 2})
    assert res3.status_code == 422, f"Expected 422, got {res3.status_code}"
    print(" -> Input validation tests passed!")


def test_places_search_and_verify():
    print("\n[TEST] Places Search & Verification...")
    # Search
    search_res = client.get("/api/places/search?destination=Kanyakumari")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["success"] is True
    assert len(search_data["places"]) > 0
    print(f" -> Found {len(search_data['places'])} OSM places for Kanyakumari")

    # Verify existing place
    verify_res = client.get("/api/places/verify?place=Vivekananda Rock Memorial&destination=Kanyakumari")
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["data"]["location_verified"] is True
    assert v_data["data"]["latitude"] is not None

    # Verify nonexistent place
    verify_fake = client.get("/api/places/verify?place=Fake Underwater Citadel 9999&destination=Kanyakumari")
    assert verify_fake.status_code == 200
    vf_data = verify_fake.json()
    assert vf_data["data"]["location_verified"] is False
    assert vf_data["data"]["latitude"] is None
    print(" -> Places search & verification tests passed!")


def test_full_itinerary_generation_and_history():
    print("\n[TEST] Full Itinerary Generation (Kanyakumari)...")
    payload = {
        "destination": "Kanyakumari",
        "days": 2,
        "budget": 8000,
        "travelers": 2,
        "interests": ["Beaches", "History"]
    }

    res = client.post("/api/travel/plan", json=payload)
    assert res.status_code == 200, f"Failed with {res.status_code}: {res.text}"
    data = res.json()
    assert data["success"] is True
    plan = data["data"]
    plan_id = plan["id"]
    assert plan_id is not None
    assert plan["destination"] == "Kanyakumari"
    assert len(plan["days"]) > 0

    verified_count = 0
    total_places = 0
    for day in plan["days"]:
        for place in day.get("places", []):
            total_places += 1
            if place.get("location_verified"):
                verified_count += 1
                assert place.get("latitude") is not None
                assert place.get("longitude") is not None
            else:
                assert place.get("latitude") is None
                assert place.get("longitude") is None

    print(f" -> Itinerary generated successfully! Verified {verified_count}/{total_places} places.")

    # Test History
    print("\n[TEST] Travel History API...")
    hist_res = client.get("/api/travel/history")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["success"] is True
    assert any(p["id"] == plan_id for p in hist_data["data"])

    # Test Get Single Trip
    single_res = client.get(f"/api/travel/{plan_id}")
    assert single_res.status_code == 200
    assert single_res.json()["data"]["id"] == plan_id

    # Test Delete Trip
    del_res = client.delete(f"/api/travel/{plan_id}")
    assert del_res.status_code == 200
    print(" -> Travel History, Single Get, and Delete passed!")


def run_all_tests():
    print("=" * 60)
    print("AI TRAVEL PLANNER — END-TO-END TEST SUITE")
    print("=" * 60)
    test_health_check()
    test_input_validation()
    test_places_search_and_verify()
    test_full_itinerary_generation_and_history()
    print("\n" + "=" * 60)
    print("ALL END-TO-END TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
