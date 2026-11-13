from pydantic import BaseModel
from typing import Optional, List

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class NutritionInfo(BaseModel):
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    serving_desc: str

class FoodDetectionItem(BaseModel):
    food_name: str
    vietnamese_name: str
    confidence: float
    bbox: Optional[BoundingBox] = None
    nutrition: Optional[NutritionInfo] = None

class VisionPredictResponse(BaseModel):
    food_name: Optional[str] = None
    original_name: Optional[str] = None
    confidence: Optional[float] = None
    is_confident: bool = True
    detections: List[FoodDetectionItem] = []
    nutrition: Optional[NutritionInfo] = None
    message: Optional[str] = None
