from fastapi import APIRouter, File, UploadFile
from app.schemas.vision import VisionPredictResponse
from app.core.vision_service import predict_food_image

router = APIRouter(tags=["Computer Vision"])

@router.post("/predict-food", response_model=VisionPredictResponse)
async def handle_predict_food(file: UploadFile = File(...)):
    return await predict_food_image(file)
