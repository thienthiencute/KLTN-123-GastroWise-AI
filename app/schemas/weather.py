from pydantic import BaseModel
from typing import List, Optional
from app.schemas.recommendation import TasteScore

class WeatherRecommendRequest(BaseModel):
    user_gps: Optional[List[float]] = None
    temperature: Optional[float] = None
    weather_condition: Optional[str] = None

class WeatherInfo(BaseModel):
    temperature: float
    condition_text: str
    condition_code: int
    banner_title: str
    banner_desc: str
    weather_type: str

class WeatherRecommendResponse(BaseModel):
    weather: WeatherInfo
    scores: List[TasteScore]
