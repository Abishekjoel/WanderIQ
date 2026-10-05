"""
Step 3 Test Script: Real Place Verification using Nominatim.
Tests the place verification service against required places and invalid places.
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.services.geocoding_service import verify_place

def run_tests():
    test_cases = [
        ("Vivekananda Rock Memorial", "Kanyakumari", True),
        ("Thiruvalluvar Statue", "Kanyakumari", True),
        ("Gandhi Memorial", "Kanyakumari", True),
        ("Fake NonExistent Atlantis Citadel 9999", "Kanyakumari", False),
    ]

    print("=" * 60)
    print("RUNNING STEP 3 TESTS: NOMINATIM PLACE VERIFICATION")
    print("=" * 60)

    all_passed = True

    for place_name, destination, expected_verified in test_cases:
        res = verify_place(place_name, destination)
        verified = res.get("location_verified", False)
        lat = res.get("latitude")
        lon = res.get("longitude")

        print(f"TEST: '{place_name}' in '{destination}'")
        print(f" -> Verified: {verified} (Expected: {expected_verified})")
        print(f" -> Coordinates: ({lat}, {lon})")

        if verified != expected_verified:
            print(" [FAIL] Verification status did not match expected result!")
            all_passed = False
        else:
            if expected_verified:
                if lat is None or lon is None:
                    print(" [FAIL] Verified is True but coordinates are missing!")
                    all_passed = False
                else:
                    print(" [PASS]")
            else:
                if lat is not None or lon is not None:
                    print(" [FAIL] Verified is False but coordinates were returned!")
                    all_passed = False
                else:
                    print(" [PASS]")
        print("-" * 60)

    if all_passed:
        print("\nALL STEP 3 TESTS PASSED SUCCESSFULLY!")
    else:
        print("\nSOME STEP 3 TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
