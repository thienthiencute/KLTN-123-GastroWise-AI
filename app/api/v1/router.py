from fastapi import APIRouter, Depends
from app.core.auth import verify_internal_ai_key
from app.api.v1.recommendation import router as rec_router
from app.api.v1.weather import router as weather_router
from app.api.v1.sentiment import router as sentiment_router
from app.api.v1.vision import router as vision_router
from app.api.v1.routing import router as routing_router
from app.api.v1.copilot import router as copilot_router

api_v1_router = APIRouter(dependencies=[Depends(verify_internal_ai_key)])

# Primary canonical routes
api_v1_router.include_router(rec_router)
api_v1_router.include_router(weather_router)
api_v1_router.include_router(sentiment_router)
api_v1_router.include_router(vision_router)
api_v1_router.include_router(routing_router)
api_v1_router.include_router(copilot_router, prefix="/copilot")

# ADR-07: Dual-route compatibility mounts to eliminate 404s during transition
api_v1_router.include_router(rec_router, prefix="/v1/recommendation")
api_v1_router.include_router(copilot_router, prefix="/v1/copilot")
