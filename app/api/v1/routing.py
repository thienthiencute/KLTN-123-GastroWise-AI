from fastapi import APIRouter
from app.schemas.routing import RouteOptimizeRequest, RouteOptimizeResponse
from app.core.route_optimizer import optimize_food_tour_route

router = APIRouter(prefix="/routes", tags=["Route Optimization"])

@router.post("/optimize", response_model=RouteOptimizeResponse)
async def handle_optimize_route(request_data: RouteOptimizeRequest):
    return optimize_food_tour_route(request_data)

