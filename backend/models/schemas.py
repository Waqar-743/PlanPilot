from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from enum import Enum


class Modality(str, Enum):
    TEXT = "text"
    VOICE = "voice"


class BudgetLevel(str, Enum):
    LOW = "low"
    MED = "med"
    HIGH = "high"


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    modality: Modality = Modality.TEXT


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    travel_requirements: Optional[dict] = None
    phase: str = "gathering"


class TravelRequirements(BaseModel):
    destination: Optional[str] = None
    origin: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_level: Optional[BudgetLevel] = None
    duration_days: Optional[int] = None
    has_all_requirements: bool = False


class WeatherRequest(BaseModel):
    destination: str
    dates: str  # "YYYY-MM-DD to YYYY-MM-DD"


class FlightRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: str
    budget_level: str


class HotelRequest(BaseModel):
    destination: str
    check_in: str
    check_out: str
    budget_level: str


class LocalExpertRequest(BaseModel):
    destination: str
    duration_days: int
    weather_context: str
    hotel_location: str


class ConversationCreate(BaseModel):
    modality: Modality = Modality.TEXT
    user_id: Optional[str] = "anonymous"
