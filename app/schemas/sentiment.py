from pydantic import BaseModel
from typing import List, Optional

class SentimentRequest(BaseModel):
    review: str

class SentimentResponse(BaseModel):
    label: str
    score: float

class AdvancedSentimentResponse(BaseModel):
    label: str
    score: float
    hashtags: List[str]
