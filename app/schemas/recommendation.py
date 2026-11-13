from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class RecommendRequest(BaseModel):
    query: str 
    candidate_ids: Optional[List[str]] = [] 
    user_gps: Optional[List[float]] = None
    city_filter: Optional[str] = None
    taste_vector: Optional[List[float]] = None # [TASK-P1-01] 6-D Vector [spicy, sweet, sour, salty, umami, bitter]
    dietary_exclusions: Optional[List[str]] = []

class TasteScore(BaseModel):
    id: str             
    name: str 
    tags: str  
    S_taste: float
    distance_km: float
    price: int
    explanation: Optional[str] = None # [TASK-P2-01] Explainable justification

class RecommendResponse(BaseModel):
    sort_by: str 
    scores: List[TasteScore] 

class ChatRequest(BaseModel):
    message: str
    user_gps: Optional[List[float]] = None
    taste_vector: Optional[List[float]] = None

class ChatResponse(BaseModel):
    reply_text: str
    data: List[TasteScore]

# --- [TASK-P2-01 & TASK-P2-02] HYBRID RECOMMENDATION SCHEMAS ---

class HybridRecommendRequest(BaseModel):
    user_id: Optional[str] = None
    user_gps: Optional[List[float]] = None
    taste_vector: Optional[List[float]] = None # 6-D Vector [spicy, sweet, sour, salty, umami, bitter] in [0.0, 1.0]
    dietary_exclusions: Optional[List[str]] = [] # e.g. ["chay", "vegetarian", "không cay", "halal"]
    weather_type: Optional[str] = None # "rainy", "hot", "cool", "neutral"
    temperature: Optional[float] = None # in Celsius
    max_price: Optional[int] = None
    limit: Optional[int] = 10

class HybridRecommendItem(BaseModel):
    id: str
    name: str
    tags: str
    score: float # Final Composite Score
    taste_score: float # S_taste
    cf_score: float # R_cf
    env_score: float # S_env
    distance_km: float
    price: int
    match_reasons: List[str]
    explanation: str

class HybridRecommendResponse(BaseModel):
    total: int
    is_cold_start: bool
    applied_weights: Dict[str, float]
    items: List[HybridRecommendItem]

class TrainCFRequest(BaseModel):
    interactions: List[Dict[str, Any]]

class TrainCFResponse(BaseModel):
    success: bool
    message: str
    user_count: int
    item_count: int
