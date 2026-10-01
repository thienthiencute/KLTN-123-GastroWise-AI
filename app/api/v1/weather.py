from fastapi import APIRouter
from app.schemas.weather import WeatherRecommendRequest, WeatherRecommendResponse
from app.core.weather_service import process_weather_recommendation

router = APIRouter(tags=["Weather AI"])

@router.post("/weather-recommend", response_model=WeatherRecommendResponse)
async def handle_weather_recommend(request_data: WeatherRecommendRequest):
    return await process_weather_recommendation(request_data)
