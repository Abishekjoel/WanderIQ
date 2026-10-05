import logging
import requests
from typing import Optional, Dict, Any, List

from backend.config import NOMINATIM_USER_AGENT, OVERPASS_ENDPOINTS
from backend.services.geocoding_service import (
    verify_place,
    get_destination_coordinates,
    search_nominatim,
)

logger = logging.getLogger("travel_planner.places")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def get_headers() -> Dict[str, str]:
    """Return standard headers for OSM requests."""
    return {
        "User-Agent": NOMINATIM_USER_AGENT
    }


def query_overpass_places(lat: float, lon: float, radius_meters: int = 15000) -> List[Dict[str, Any]]:
    """
    Query real tourist and cultural places around a coordinate using OpenStreetMap Overpass API.
    Attempts multiple fallback Overpass endpoints to handle 504 / gateway timeouts gracefully.
    """
    overpass_query = f"""
    [out:json][timeout:15];
    (
      node["tourism"~"attraction|museum|viewpoint|gallery|theme_park|zoo"](around:{radius_meters},{lat},{lon});
      way["tourism"~"attraction|museum|viewpoint|gallery|theme_park|zoo"](around:{radius_meters},{lat},{lon});
      relation["tourism"~"attraction|museum|viewpoint|gallery|theme_park|zoo"](around:{radius_meters},{lat},{lon});
      
      node["historic"](around:{radius_meters},{lat},{lon});
      way["historic"](around:{radius_meters},{lat},{lon});
      relation["historic"](around:{radius_meters},{lat},{lon});
      
      node["amenity"="place_of_worship"](around:{radius_meters},{lat},{lon});
      way["amenity"="place_of_worship"](around:{radius_meters},{lat},{lon});
      
      node["leisure"~"park|nature_reserve|beach_resort"](around:{radius_meters},{lat},{lon});
      way["leisure"~"park|nature_reserve|beach_resort"](around:{radius_meters},{lat},{lon});
    );
    out center tags 40;
    """

    headers = {
        "User-Agent": NOMINATIM_USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    for endpoint in OVERPASS_ENDPOINTS:
        try:
            logger.info(f"Querying Overpass endpoint: {endpoint}")
            response = requests.post(
                endpoint,
                data={"data": overpass_query},
                headers=headers,
                timeout=12
            )

            if response.status_code == 200:
                data = response.json()
                elements = data.get("elements", [])
                places = []

                for el in elements:
                    tags = el.get("tags", {})
                    name = tags.get("name") or tags.get("name:en")
                    if not name or not name.strip():
                        continue

                    # Determine coordinates (nodes have lat/lon, ways/relations have center)
                    item_lat = el.get("lat") or (el.get("center", {}).get("lat"))
                    item_lon = el.get("lon") or (el.get("center", {}).get("lon"))

                    if item_lat is None or item_lon is None:
                        continue

                    place_type = (
                        tags.get("tourism")
                        or tags.get("historic")
                        or tags.get("leisure")
                        or tags.get("amenity")
                        or "attraction"
                    )

                    places.append({
                        "name": name.strip(),
                        "latitude": float(item_lat),
                        "longitude": float(item_lon),
                        "type": place_type,
                        "tags": tags,
                    })

                logger.info(f"Retrieved {len(places)} places from Overpass endpoint: {endpoint}")
                return places

            else:
                logger.warning(f"Overpass endpoint {endpoint} returned HTTP {response.status_code}")

        except Exception as exc:
            logger.warning(f"Overpass query error on {endpoint}: {exc}")
            continue

    logger.warning("All Overpass endpoints failed or timed out. Falling back to Nominatim.")
    return []


def search_places(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Discover real places in a destination using coordinates + Overpass,
    with fallback to Nominatim.
    """
    coords = get_destination_coordinates(query)
    places = []

    if coords:
        places = query_overpass_places(coords["latitude"], coords["longitude"])

    if not places:
        # Fallback to Nominatim search
        nominatim_results = search_nominatim(f"attractions in {query}", limit=limit)
        if not nominatim_results:
            nominatim_results = search_nominatim(query, limit=limit)

        for r in nominatim_results:
            if r.get("lat") and r.get("lon"):
                name = r.get("name") or r.get("display_name", "").split(",")[0]
                places.append({
                    "name": name.strip(),
                    "latitude": float(r["lat"]),
                    "longitude": float(r["lon"]),
                    "type": r.get("type") or r.get("category") or "attraction",
                    "display_name": r.get("display_name", "")
                })

    return places


def search_specific_place(place_name: str, destination: str) -> Optional[Dict[str, Any]]:
    """Verify and look up a specific place using Nominatim."""
    result = verify_place(place_name, destination)
    if result.get("location_verified"):
        return result
    return None