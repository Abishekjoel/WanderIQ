import logging
import requests
from typing import Optional

from backend.config import PEXELS_API_KEY

logger = logging.getLogger("travel_planner.images")

DEFAULT_FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=600&q=80",
]


def get_place_image(place_name: str, destination: str = "") -> str:
    """
    Search for a high-quality photo of a sightseeing place using Pexels API.
    Returns image URL or safe scenic travel photo fallback.
    """
    if PEXELS_API_KEY and PEXELS_API_KEY.strip():
        query = f"{place_name} {destination}".strip()
        try:
            headers = {"Authorization": PEXELS_API_KEY.strip()}
            response = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params={"query": query, "per_page": 1, "orientation": "landscape"},
                timeout=6
            )
            if response.status_code == 200:
                data = response.json()
                photos = data.get("photos", [])
                if photos:
                    return photos[0].get("src", {}).get("medium") or photos[0].get("src", {}).get("small")
        except Exception as exc:
            logger.warning(f"Pexels search failed for '{query}': {exc}")

    # Fallback to deterministic unsplash travel image
    idx = (abs(hash(place_name)) % len(DEFAULT_FALLBACK_IMAGES))
    return DEFAULT_FALLBACK_IMAGES[idx]
