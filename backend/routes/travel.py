import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.database import get_db, TravelPlanDB
from backend.models.travel import TravelRequest
from backend.services.groq_service import generate_travel_plan
from backend.services.places_service import search_places, get_destination_coordinates
from backend.services.place_processor import enrich_itinerary_places

logger = logging.getLogger("travel_planner.routes.travel")

router = APIRouter(
    prefix="/api/travel",
    tags=["Travel"],
)


@router.post("/plan", status_code=status.HTTP_200_OK)
def create_travel_plan(
    request: TravelRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Generate an AI itinerary using Groq, enrich sightseeing locations with
    verified OpenStreetMap coordinates, save the trip to the database, and return.
    """
    try:
        logger.info(f"Generating travel plan for: {request.destination}, {request.days} days, budget: ₹{request.budget}")

        # 1. Generate itinerary using Groq LLM
        travel_plan = generate_travel_plan(
            destination=request.destination,
            days=request.days,
            budget=request.budget,
            travelers=request.travelers,
            interests=request.interests,
        )

        # 2. Query broad OpenStreetMap dataset for the destination
        osm_places = search_places(request.destination, limit=25)

        # 3. Enrich & verify each sightseeing place in the itinerary
        enriched_plan = enrich_itinerary_places(
            travel_plan=travel_plan,
            destination=request.destination,
            osm_places=osm_places
        )

        # 4. Save to Database
        interests_str = json.dumps(request.interests)
        itinerary_str = json.dumps(enriched_plan)

        db_plan = TravelPlanDB(
            destination=request.destination,
            days=request.days,
            budget=request.budget,
            travelers=request.travelers,
            interests=interests_str,
            summary=enriched_plan.get("summary", ""),
            itinerary_json=itinerary_str
        )
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)

        # 5. Format response
        response_data = {
            "id": db_plan.id,
            "destination": enriched_plan.get("destination", request.destination),
            "summary": enriched_plan.get("summary", ""),
            "days": enriched_plan.get("days", []),
            "travel_tips": enriched_plan.get("travel_tips", []),
            "created_at": db_plan.created_at.isoformat() if db_plan.created_at else None,
        }

        return {
            "success": True,
            "data": response_data
        }

    except ValueError as exc:
        logger.warning(f"Validation error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc)
        ) from exc

    except RuntimeError as exc:
        logger.error(f"Service runtime error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to generate the itinerary right now: {exc}"
        ) from exc

    except Exception as exc:
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating your travel plan. Please try again."
        ) from exc


@router.get("/history", status_code=status.HTTP_200_OK)
def get_travel_history(
    limit: int = 20,
    db: Session = Depends(get_db)
) -> dict:
    """Retrieve previously generated and saved travel plans."""
    try:
        plans = db.query(TravelPlanDB).order_by(TravelPlanDB.created_at.desc()).limit(limit).all()
        return {
            "success": True,
            "count": len(plans),
            "data": [plan.to_dict() for plan in plans]
        }
    except Exception as exc:
        logger.error(f"Failed to fetch travel history: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve travel history."
        ) from exc


@router.get("/{travel_plan_id}", status_code=status.HTTP_200_OK)
def get_travel_plan(
    travel_plan_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Retrieve a single saved travel plan by its ID."""
    plan = db.query(TravelPlanDB).filter(TravelPlanDB.id == travel_plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Travel plan with ID {travel_plan_id} not found."
        )
    return {
        "success": True,
        "data": plan.to_dict()
    }


@router.delete("/{travel_plan_id}", status_code=status.HTTP_200_OK)
def delete_travel_plan(
    travel_plan_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Delete a saved travel plan by its ID."""
    plan = db.query(TravelPlanDB).filter(TravelPlanDB.id == travel_plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Travel plan with ID {travel_plan_id} not found."
        )
    db.delete(plan)
    db.commit()
    return {
        "success": True,
        "message": f"Travel plan {travel_plan_id} deleted successfully."
    }