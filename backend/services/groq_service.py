import json
import logging
import re
from groq import Groq

from backend.config import GROQ_API_KEY

logger = logging.getLogger("travel_planner.groq")

# Model priorities
CANDIDATE_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "llama-3.1-8b-instant"
]


def extract_json(content: str) -> dict:
    """Safely extract JSON dictionary from model output."""
    cleaned = content.strip()

    # Remove Markdown code blocks if present
    if "```" in cleaned:
        # Match ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if match:
            cleaned = match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try finding the first '{' and last '}'
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            json_slice = cleaned[start:end+1]
            return json.loads(json_slice)
        raise ValueError("Could not parse valid JSON from AI response.")


def generate_travel_plan(
    destination: str,
    days: int,
    budget: float,
    travelers: int,
    interests: list[str]
) -> dict:
    """
    Generate travel itinerary using Groq LLM API.
    Enforces strict rules: no fake coordinates, no fake ticket prices, valid JSON output only.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured in .env")

    client = Groq(api_key=GROQ_API_KEY)

    interests_str = ", ".join(interests) if interests else "General Sightseeing, Culture, Food"

    prompt = f"""
You are an expert travel planner.

Create a detailed, realistic, and budget-conscious travel itinerary.

Trip details:
- Destination: {destination}
- Number of days: {days}
- Total budget: ₹{budget}
- Number of travelers: {travelers}
- Interests: {interests_str}

Return ONLY valid JSON with this exact structure:
{{
    "destination": "{destination}",
    "summary": "Concise overview of the travel experience",
    "days": [
        {{
            "day": 1,
            "places": [
                {{
                    "name": "Exact real place/landmark name",
                    "description": "Why this place is worth visiting",
                    "activity": "What the traveler can do here",
                    "estimated_duration_hours": 2.0,
                    "best_time": "09:00 AM"
                }}
            ]
        }}
    ],
    "travel_tips": [
        "Useful local travel tip 1",
        "Useful local travel tip 2"
    ]
}}

CRITICAL RULES:
1. Recommend real, existing physical places and landmarks in or near {destination}.
2. Do not invent fake attractions.
3. Avoid repeating places across days.
4. Keep the itinerary realistic with sensible pacing.
5. Consider the budget (₹{budget}) and travelers count ({travelers}).
6. Align activities with user interests ({interests_str}).
7. DO NOT include ticket prices, admission fees, or ticket details.
8. DO NOT generate latitude, longitude, coordinates, distances, travel times, ratings, or photos.
9. Return JSON ONLY with no commentary or markdown outside the JSON.
"""

    last_error = None

    for model in CANDIDATE_MODELS:
        try:
            logger.info(f"Requesting itinerary generation with model: {model}")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional travel planning assistant. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )

            content = response.choices[0].message.content
            if not content:
                continue

            travel_plan = extract_json(content)
            if "days" in travel_plan and isinstance(travel_plan["days"], list):
                return travel_plan

        except Exception as exc:
            logger.warning(f"Failed with model {model}: {exc}")
            last_error = exc
            continue

    raise RuntimeError(f"Unable to generate itinerary via Groq: {last_error or 'No response'}")
