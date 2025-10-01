import asyncio
from dataclasses import dataclass
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent
import os

# Load env vars

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ----------------------------------
# Shared Dependencies
# ----------------------------------

@dataclass
class TravelDeps:
    user_name: str
    origin_city: str

# ----------------------------------
# Shared Data
# ----------------------------------

class TripContext(BaseModel):
    destination: Optional[str] = None
    from_city: Optional[str] = None
    arrival_time: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_location: Optional[str] = None
    hotel_price: Optional[int] = None
    hotel_stars: Optional[int] = None
    activities: Optional[list[str]] = None

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
    system_prompt="Suggest a good hotel near the arrival airport or city center. Consider time of arrival and convenience.",
)

class Activities(BaseModel):
    personalized_for: str
    top_activities: list[str]

activity_agent = Agent(
    "gemini-2.5-flash",
    deps_type=TravelDeps,
    output_type=Activities,
    system_prompt="Suggest local activities close to the hotel and suitable for arrival time (e.g., evening, morning).",
)

# ----------------------------------
# Chain Execution
# ----------------------------------

async def handle_destination(user_input: str, deps: TravelDeps, ctx: TripContext):
    dest_result = await destination_agent.run(user_input, deps=deps)
    ctx.destination = dest_result.output.destination

async def handle_flight(user_input: str, deps: TravelDeps, ctx: TripContext):
    flight_prompt = f"Plan a flight from {deps.origin_city} to {ctx.destination}."
    flight_result = await flight_agent.run(flight_prompt, deps=deps)
    ctx.from_city = flight_result.output.from_city
    ctx.arrival_time = flight_result.output.arrival_time

async def handle_hotel(user_input: str, deps: TravelDeps, ctx: TripContext):
    hotel_prompt = (
        f"Recommend a hotel in {ctx.destination} for a traveler arriving at {ctx.arrival_time}. "
        f"Prefer locations near the airport or city center."
    )
    hotel_result = await hotel_agent.run(hotel_prompt, deps=deps)
    ctx.hotel_name = hotel_result.output.name
    ctx.hotel_location = hotel_result.output.location
    ctx.hotel_price = hotel_result.output.price_per_night_usd
    ctx.hotel_stars = hotel_result.output.stars

async def handle_activities(user_input: str, deps: TravelDeps, ctx: TripContext):
    activities_prompt = (
        f"Suggest activities in {ctx.destination} close to {ctx.hotel_location} "
        f"and suitable for a traveler arriving at {ctx.arrival_time}."
    )
    activity_result = await activity_agent.run(activities_prompt, deps=deps)
    ctx.activities = activity_result.output.top_activities

async def plan_trip(user_input: str, deps: TravelDeps):
    ctx = TripContext()
    chain = [handle_destination, handle_flight, handle_hotel, handle_activities]
    for step in chain:
        await step(user_input, deps, ctx)
    return ctx

# ----------------------------------
# Routes
# ----------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/plan", response_class=HTMLResponse)
async def plan(
    request: Request,
    user_name: str = Form(...),
    origin_city: str = Form(...),
    preferences: str = Form(...),
):
    deps = TravelDeps(user_name=user_name, origin_city=origin_city)
    ctx = await plan_trip(preferences, deps)
    return templates.TemplateResponse("result.html", {"request": request, "deps": deps, "ctx": ctx})
