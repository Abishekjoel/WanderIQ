import logging
import re
import requests
from typing import Optional, Dict, Any, List

from backend.config import NOMINATIM_USER_AGENT

logger = logging.getLogger("travel_planner.geocoding")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def normalize_text(value: str) -> str:
    """Normalize text for token and substring comparisons."""
    if not value:
        return ""
    value = value.lower().strip()
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def get_headers() -> Dict[str, str]:
    """Return headers including User-Agent required by Nominatim."""
    return {
        "User-Agent": NOMINATIM_USER_AGENT
    }


def get_destination_coordinates(destination: str) -> Optional[Dict[str, Any]]:
    """Convert a destination name into coordinates using Nominatim."""
    if not destination or not destination.strip():
        return None

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": destination.strip(),
                "format": "json",
                "limit": 1,
                "addressdetails": 1,
            },
            headers=get_headers(),
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            return None

        result = results[0]
        return {
            "latitude": float(result["lat"]),
            "longitude": float(result["lon"]),
            "display_name": result.get("display_name", ""),
        }
    except Exception as exc:
        logger.warning(f"Error fetching coordinates for destination '{destination}': {exc}")
        return None


def calculate_match_score(
    place_name: str,
    destination: str,
    result: Dict[str, Any]
) -> int:
    """
    Score a Nominatim search result based on name matching, destination relevance,
    and category appropriateness.
    """
    normalized_place = normalize_text(place_name)
    normalized_dest = normalize_text(destination)

    display_name = normalize_text(result.get("display_name", ""))
    result_name = normalize_text(result.get("name", ""))

    if not result.get("lat") or not result.get("lon"):
        return 0

    score = 0

    # 1. Exact name match
    if result_name == normalized_place:
        score += 100
    elif normalized_place in result_name:
        score += 70
    elif normalized_place in display_name:
        score += 60
    else:
        # Check token intersection
        place_tokens = set(normalized_place.split())
        result_tokens = set(result_name.split())
        display_tokens = set(display_name.split())

        common_result = place_tokens.intersection(result_tokens)
        common_display = place_tokens.intersection(display_tokens)

        # Ignore trivial stopwords
        common_result = {t for t in common_result if len(t) > 2}
        common_display = {t for t in common_display if len(t) > 2}

        if len(common_result) >= max(1, len(place_tokens) // 2):
            score += 40
        elif len(common_display) >= max(1, len(place_tokens) // 2):
            score += 30
        else:
            return 0  # No meaningful name match

    # 2. Destination relevance check
    dest_tokens = {t for t in normalized_dest.split() if len(t) > 2}
    dest_matched = any(t in display_name for t in dest_tokens) if dest_tokens else False

    address = result.get("address", {})
    address_str = normalize_text(" ".join(str(v) for v in address.values()))
    if any(t in address_str for t in dest_tokens):
        dest_matched = True

    if dest_matched:
        score += 40
    else:
        # If destination is completely absent from result, penalize unless exact place name is unique
        score -= 20

    # 3. Category & Type weighting
    category = normalize_text(result.get("category", ""))
    result_type = normalize_text(result.get("type", ""))

    tourist_categories = {"tourism", "historic", "leisure", "amenity", "natural", "boundary"}
    tourist_types = {
        "attraction", "museum", "viewpoint", "monument", "memorial",
        "fort", "castle", "palace", "beach", "place_of_worship",
        "temple", "church", "mosque", "park", "garden", "lighthouse",
        "statue", "ruins", "archaeological_site"
    }

    if category in tourist_categories:
        score += 20
    if result_type in tourist_types:
        score += 20

    return score


def search_nominatim(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Execute search query against Nominatim with timeout and error handling."""
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": query,
                "format": "json",
                "limit": limit,
                "addressdetails": 1,
            },
            headers=get_headers(),
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        return []
    except requests.Timeout:
        logger.warning(f"Nominatim timeout for query: '{query}'")
        return []
    except requests.RequestException as exc:
        logger.warning(f"Nominatim request error for query '{query}': {exc}")
        return []
    except Exception as exc:
        logger.warning(f"Unexpected error in Nominatim search '{query}': {exc}")
        return []


def verify_place(place_name: str, destination: str) -> Dict[str, Any]:
    """
    Verify whether an AI-generated sightseeing location actually exists
    using OpenStreetMap Nominatim.

    Returns structured verification result and prints formatted console logs.
    """
    print(f"\nSearching:\n{place_name}, {destination}\n")

    if not place_name or not place_name.strip():
        print(f"Result:\nNone\n\nCoordinates:\nNone, None\n\nVerified:\nfalse\n")
        return {
            "name": place_name or "",
            "latitude": None,
            "longitude": None,
            "location_verified": False,
        }

    queries = [
        f"{place_name.strip()}, {destination.strip()}",
        place_name.strip()
    ]

    best_match = None
    highest_score = 0

    for query in queries:
        results = search_nominatim(query, limit=5)
        if not results:
            continue

        for res in results:
            score = calculate_match_score(place_name, destination, res)
            if score > highest_score and score >= 50:
                highest_score = score
                best_match = res

        # If high-confidence match found with destination in query, stop early
        if highest_score >= 90:
            break

    if best_match and best_match.get("lat") and best_match.get("lon"):
        matched_name = best_match.get("name") or place_name
        lat = round(float(best_match["lat"]), 6)
        lon = round(float(best_match["lon"]), 6)

        print(f"Result:\n{matched_name}\n\nCoordinates:\n{lat}, {lon}\n\nVerified:\ntrue\n")

        return {
            "name": place_name,
            "latitude": lat,
            "longitude": lon,
            "location_verified": True,
            "matched_name": matched_name,
            "display_name": best_match.get("display_name", "")
        }

    print(f"Result:\nNone\n\nCoordinates:\nNone, None\n\nVerified:\nfalse\n")
    return {
        "name": place_name,
        "latitude": None,
        "longitude": None,
        "location_verified": False,
    }
