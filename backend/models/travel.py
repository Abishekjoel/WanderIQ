from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TravelRequest(BaseModel):
    destination: str = Field(
        ...,
        min_length=1,
        description="Travel destination name"
    )
    days: int = Field(
        ...,
        ge=1,
        le=30,
        description="Number of travel days (1 to 30)"
    )
    budget: float = Field(
        ...,
        gt=0,
        description="Total trip budget in INR"
    )
    travelers: int = Field(
        ...,
        ge=1,
        le=50,
        description="Number of travelers"
    )
    interests: List[str] = Field(
        default_factory=list,
        description="List of travel interests"
    )

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Destination cannot be empty.")
        return trimmed


class PlaceItem(BaseModel):
    name: str
    description: Optional[str] = None
    activity: Optional[str] = None
    estimated_duration_hours: Optional[float] = None
    best_time: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_verified: bool = False


class DayPlan(BaseModel):
    day: int
    places: List[PlaceItem] = []


class TravelPlanResponse(BaseModel):
    id: Optional[int] = None
    destination: str
    summary: Optional[str] = None
    days: List[DayPlan] = []
    travel_tips: List[str] = []
