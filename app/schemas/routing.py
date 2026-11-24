from pydantic import BaseModel, model_validator
from typing import List, Optional, Any, Dict

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

    @model_validator(mode='before')
    @classmethod
    def normalize_candidate(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Support lng as alias for lon
            if 'lon' not in data and 'lng' in data:
                data['lon'] = data['lng']
            # Support name fallback
            if 'name' not in data or not data['name']:
                data['name'] = f"Restaurant {data.get('id', '')}"
            # Support open / close aliases
            if 'open_time' not in data and 'open' in data:
                data['open_time'] = data['open']
            if 'close_time' not in data and 'close' in data:
                data['close_time'] = data['close']
            # Support duration_mins alias
            if 'dining_duration_mins' not in data and 'duration_mins' in data:
                data['dining_duration_mins'] = data['duration_mins']
        return data

class RouteOptimizeRequest(BaseModel):
    start_location: List[float]  # [lat, lon]
    start_time_mins: Optional[int] = 660  # Mặc định 11:00 AM (11 * 60)
    budget: Optional[int] = 250000
    routing_mode: Optional[str] = 'motorbike'  # 'motorbike' | 'car' | 'walking'
    desired_stops: Optional[int] = 3
    max_duration_mins: Optional[int] = None
    candidates: List[CandidateStop]

    @model_validator(mode='before')
    @classmethod
    def normalize_request(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Support candidates from restaurants
            if 'candidates' not in data and 'restaurants' in data:
                data['candidates'] = data['restaurants']
            # Support start_location from start_lat, start_lng
            if 'start_location' not in data and 'start_lat' in data and 'start_lng' in data:
                data['start_location'] = [data['start_lat'], data['start_lng']]
            # Support budget from budget_vnd
            if 'budget' not in data and 'budget_vnd' in data:
                data['budget'] = data['budget_vnd']
            # Support start_time string "HH:MM" -> start_time_mins
            if 'start_time_mins' not in data and 'start_time' in data:
                st = data['start_time']
                if isinstance(st, str) and ':' in st:
                    parts = st.split(':')
                    try:
                        data['start_time_mins'] = int(parts[0]) * 60 + int(parts[1])
                    except ValueError:
                        data['start_time_mins'] = 660
                elif isinstance(st, (int, float)):
                    data['start_time_mins'] = int(st)
        return data

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
    ordered_stops: Optional[List[OptimizedStop]] = None
    total_distance_km: float
    total_duration_mins: int
    total_cost: int
    remaining_budget: int
    co2_saved_kg: float
    status: str
    message: str
    algorithm_used: str = 'OR-Tools TSPTW'
    routing_mode: str = 'motorbike'

    @model_validator(mode='after')
    def populate_ordered_stops(self) -> 'RouteOptimizeResponse':
        if not self.ordered_stops:
            self.ordered_stops = self.stops
        return self


