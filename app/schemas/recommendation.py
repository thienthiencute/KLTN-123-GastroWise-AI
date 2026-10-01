from pydantic import BaseModel
from typing import List, Optional

class RecommendRequest(BaseModel):
    query: str 
    candidate_ids: Optional[List[str]] = [] 
    user_gps: Optional[List[float]] = None
    city_filter: Optional[str] = None

class TasteScore(BaseModel):
    id: str             
    name: str 
    tags: str  
    S_taste: float
    distance_km: float
    price: int

class RecommendResponse(BaseModel):
    sort_by: str 
    scores: List[TasteScore] 

class ChatRequest(BaseModel):
    message: str
    user_gps: Optional[List[float]] = None

class ChatResponse(BaseModel):
    reply_text: str
    data: List[TasteScore]
