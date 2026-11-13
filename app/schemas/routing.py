from pydantic import BaseModel
from typing import List, Optional

class CandidateStop(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    meal_type: Optional[str] = 'main'  # 'starter' | 'main' | 'dessert' | 'cafe'
    open_time: Optional[str] = '08:00'
    close_time: Optional[str] = '22:00'
    dining_duration_mins: Optional[int] = 45
    avg_price: Optional[int] = 50000
    rating: Optional[float] = 4.5
    tags: Optional[str] = None
    district: Optional[str] = None

class RouteOptimizeRequest(BaseModel):
    start_location: List[float]  # [lat, lon]
    start_time_mins: Optional[int] = 660  # Mặc định 11:00 AM (11 * 60)
    budget: Optional[int] = 250000
    routing_mode: Optional[str] = 'motorbike'  # 'motorbike' | 'car' | 'walking'
    desired_stops: Optional[int] = 3
    max_duration_mins: Optional[int] = None
    candidates: List[CandidateStop]

class OptimizedStop(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    order_index: int
    meal_type: str
    arrival_time: str
    departure_time: str
    dining_duration_mins: int
    transit_time_mins: int
    distance_to_next_km: float
    estimated_cost: int
    tags: Optional[str] = None

class RouteOptimizeResponse(BaseModel):
    stops: List[OptimizedStop]
    total_distance_km: float
    total_duration_mins: int
    total_cost: int
    remaining_budget: int
    co2_saved_kg: float
    status: str
    message: str
    algorithm_used: str = 'OR-Tools TSPTW'
    routing_mode: str = 'motorbike'


