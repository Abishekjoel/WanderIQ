import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.services.places_service import search_places
from backend.services.place_processor import process_places
from backend.services.geocoding_service import verify_place

logger = logging.getLogger("travel_planner.routes.places")

router = APIRouter(
    prefix="/api/places",
    tags=["Places"]
)


@router.get("/search", status_code=status.HTTP_200_OK)
def search_destination_places(
    destination: Optional[str] = Query(None, description="Destination city/region name"),
    query: Optional[str] = Query(None, description="Alternative query parameter for destination")
):
    """
    Search and discover tourist attractions for a destination using OpenStreetMap.
    """
    dest_name = (destination or query or "").strip()
    if not dest_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Destination query parameter cannot be empty."
        )

    try:
        raw_places = search_places(dest_name, limit=25)
        clean_places = process_places(raw_places, max_places=20)

        return {
            "success": True,
            "destination": dest_name,
            "count": len(clean_places),
            "places": clean_places
        }
    except Exception as error:
        logger.error(f"Error searching places for '{dest_name}': {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve places for destination '{dest_name}'."
        ) from error


@router.get("/verify", status_code=status.HTTP_200_OK)
def verify_place_endpoint(
    place: str = Query(..., min_length=1, description="Sightseeing place name to verify"),
    destination: str = Query("", description="Destination context for disambiguation")
):
    """
    Verify whether a specific sightseeing place exists using Nominatim geocoding.
    """
    place_name = place.strip()
    if not place_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Place parameter cannot be empty."
        )

    try:
        result = verify_place(place_name, destination.strip())
        return {
            "success": True,
            "data": result
        }
    except Exception as error:
        logger.error(f"Error verifying place '{place_name}': {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying place '{place_name}'."
        ) from error