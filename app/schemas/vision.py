from pydantic import BaseModel
from typing import Optional

class VisionPredictResponse(BaseModel):
    food_name: Optional[str] = None
    original_name: Optional[str] = None
    confidence: Optional[float] = None
    message: Optional[str] = None
