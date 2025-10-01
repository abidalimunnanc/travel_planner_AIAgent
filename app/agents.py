import asyncio
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel
from pydantic_ai import Agent

# ----------------------------------
# Shared Dependencies
# ----------------------------------
@dataclass
class TravelDeps:
    user_name: str
    origin_city: str

# ----------------------------------
# Shared Context
# ----------------------------------
class TripContext(BaseModel):
    destination: Optional[str] = None
    from_city: Optional[str] = None
    arrival_time: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_location: Optional[str] = None
    activities: list[str] = []

# ----------------------------------
# Agents
# ----------------------------------
class DestinationOutput(BaseModel):
    destination: str

destination_agent = Agent(
    "gemini-2.5-flash",
    deps_type=TravelDeps,
    output_type=DestinationOutput,
    system_prompt="You help users select an ideal travel destination based on their preferences.",
)

class FlightPlan(BaseModel):
    from_city: str
    to_city: str
    arrival_time: str

flight_agent = Agent(
    "gemini-2.5-flash",
    deps_type=TravelDeps,
    output_type=FlightPlan,
    system_prompt="Plan a realistic flight itinerary for a trip. Include origin city and arrival time.",
)

class HotelOption(BaseModel):
    name: str
    location: str
    price_per_night_usd: int
    stars: int

hotel_agent = Agent(
    "gemini-2.5-flash",
    deps_type=TravelDeps,
    output_type=HotelOption,
    system_prompt="Suggest a good hotel near the arrival airport or city center.",
)

class Activities(BaseModel):
    personalized_for: str
    top_activities: list[str]

activity_agent = Agent(
    "gemini-2.5-flash",
    deps_type=TravelDeps,
    output_type=Activities,
    system_prompt="Suggest local activities close to the hotel and suitable for arrival time.",
)

# ----------------------------------
# Chain Logic
# ----------------------------------
async def plan_trip(user_input: str, deps: TravelDeps, ctx: TripContext):
    # Destination
    dest_result = await destination_agent.run(user_input, deps=deps)
    ctx.destination = dest_result.output.destination

    # Flight
    flight_prompt = f"Plan a flight from {deps.origin_city} to {ctx.destination}."
    flight_result = await flight_agent.run(flight_prompt, deps=deps)
    ctx.from_city = flight_result.output.from_city
    ctx.arrival_time = flight_result.output.arrival_time

    # Hotel
    hotel_prompt = f"Recommend a hotel in {ctx.destination} for arrival at {ctx.arrival_time}."
    hotel_result = await hotel_agent.run(hotel_prompt, deps=deps)
    ctx.hotel_name = hotel_result.output.name
    ctx.hotel_location = hotel_result.output.location

    # Activities
    activities_prompt = f"Suggest activities in {ctx.destination} near {ctx.hotel_location}."
    activity_result = await activity_agent.run(activities_prompt, deps=deps)
    ctx.activities = activity_result.output.top_activities
