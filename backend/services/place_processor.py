import re
import logging
from typing import List, Dict, Any, Optional

from backend.services.geocoding_service import verify_place
from backend.services.image_service import get_place_image

logger = logging.getLogger("travel_planner.processor")



NON_PLACE_KEYWORDS = [
    "lunch",
    "dinner",
    "breakfast",
    "seafood",
    "street food",
    "food exploration",
    "food stall",
    "food stalls",
    "restaurant",
    "eatery",
    "café",
    "cafe",
    "shack",
    "market & food",
    "market and food",
    "farewell",
    "departure",
    "walk",
    "beach walk",
    "night walk",
    "relax",
    "relaxation",
    "shopping",
    "snack",
    "snacks",
    "hotel check",
    "check-in",
    "check-out",
    "leisure time",
    "free time",
    "rest",
]

# Common aliases/variants for key landmarks
LANDMARK_ALIASES = {
    "thiruvalluvar statue": ["thiruvalluvar monument", "thiruvalluvar", "valluvar statue", "திருவள்ளுவர் சிலை"],
    "vivekananda rock memorial": ["vivekananda rock", "vivekananda memorial", "rock memorial", "விவேகானந்தர் பாறை"],
    "gandhi memorial mandapam": ["gandhi memorial", "mahatma gandhi memorial", "gandhi mandapam", "காந்தி மண்டபம்"],
    "kanyakumari beach": ["cape comorin beach", "kanyakumari sunrise view", "sunset point kanyakumari", "triveni sangam"],
    "padmanabhapuram palace": ["padmanabhapuram fort", "kalkulam palace"],
    "vattakottai fort": ["circular fort", "vattakottai"],
}


def normalize_place_name(name: str) -> str:
    """Normalize place name for reliable matching."""
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r"\([^)]*\)", "", name)
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def is_place_like_entry(name: str) -> bool:
    """
    Determine whether an itinerary entry represents an actual physical sightseeing location
    rather than a generic meal, departure, or leisure activity.
    """
    normalized = normalize_place_name(name)
    if not normalized or len(normalized) < 3:
        return False

    for keyword in NON_PLACE_KEYWORDS:
        kw_norm = normalize_place_name(keyword)
        if kw_norm and kw_norm in normalized:
            return False

    return True


def check_name_match(name1: str, name2: str) -> bool:
    """Check if two place names match using exact, substring, token overlap, or aliases."""
    n1 = normalize_place_name(name1)
    n2 = normalize_place_name(name2)

    if not n1 or not n2:
        return False

    if n1 == n2 or n1 in n2 or n2 in n1:
        return True

    # Check known aliases
    for canonical, aliases in LANDMARK_ALIASES.items():
        all_variants = [canonical] + aliases
        n1_in_group = any(v in n1 or n1 in v for v in all_variants)
        n2_in_group = any(v in n2 or n2 in v for v in all_variants)
        if n1_in_group and n2_in_group:
            return True

    # Token overlap check (significant tokens only)
    tokens1 = {t for t in n1.split() if len(t) > 2}
    tokens2 = {t for t in n2.split() if len(t) > 2}
    if tokens1 and tokens2:
        overlap = tokens1.intersection(tokens2)
        if len(overlap) >= min(len(tokens1), len(tokens2)) and len(overlap) >= 2:
            return True

    return False


def process_places(places: List[Dict[str, Any]], max_places: int = 30) -> List[Dict[str, Any]]:
    """Clean, normalize, and deduplicate places returned by OSM."""
    processed = []
    seen = set()

    for place in places:
        name = place.get("name")
        lat = place.get("latitude")
        lon = place.get("longitude")

        if not name or lat is None or lon is None:
            continue

        norm_name = normalize_place_name(name)
        if norm_name in seen:
            continue

        seen.add(norm_name)
        processed.append({
            "name": name.strip(),
            "latitude": float(lat),
            "longitude": float(lon),
            "type": place.get("type", "attraction"),
        })

        if len(processed) >= max_places:
            break

    return processed


def enrich_itinerary_places(
    travel_plan: Dict[str, Any],
    destination: str,
    osm_places: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Iterate over every AI-generated place in every day of the itinerary.
    Matches against discovered OSM places first, then falls back to targeted Nominatim verification.
    Sets latitude, longitude, and location_verified strictly without fabricating coordinates.
    """
    osm_places = osm_places or []

    for day in travel_plan.get("days", []):
        for place in day.get("places", []):
            place_name = place.get("name", "")

            # Set default unverified state
            place["latitude"] = None
            place["longitude"] = None
            place["location_verified"] = False
            place["image"] = get_place_image(place_name, destination)

            # Check if this is a physical sightseeing location
            if not is_place_like_entry(place_name):
                logger.info(f"Skipping non-sightseeing entry: '{place_name}'")
                continue

            matched_from_osm = False

            # 1. Match against pre-fetched OSM dataset
            for osm_item in osm_places:
                if check_name_match(place_name, osm_item.get("name", "")):
                    place["latitude"] = round(float(osm_item["latitude"]), 6)
                    place["longitude"] = round(float(osm_item["longitude"]), 6)
                    place["location_verified"] = True
                    place["type"] = osm_item.get("type", "Sightseeing Spot")
                    matched_from_osm = True
                    logger.info(f"Matched '{place_name}' from OSM cache: ({place['latitude']}, {place['longitude']})")
                    break

            if matched_from_osm:
                continue

            # 2. Targeted Nominatim verification
            verification = verify_place(place_name, destination)
            if verification.get("location_verified"):
                place["latitude"] = verification.get("latitude")
                place["longitude"] = verification.get("longitude")
                place["location_verified"] = True
                place["type"] = verification.get("type", "Sightseeing Spot")
            else:
                logger.info(f"Could not verify place: '{place_name}'")

    return travel_plan