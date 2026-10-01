from fastapi import APIRouter
from app.api.v1.recommendation import router as rec_router
from app.api.v1.weather import router as weather_router
from app.api.v1.sentiment import router as sentiment_router
from app.api.v1.vision import router as vision_router

api_v1_router = APIRouter()
api_v1_router.include_router(rec_router)
api_v1_router.include_router(weather_router)
api_v1_router.include_router(sentiment_router)
api_v1_router.include_router(vision_router)
