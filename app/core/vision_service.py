import io
from PIL import Image
from ultralytics import YOLO
from fastapi import HTTPException, UploadFile
from app.config import EN_VI_MAPPING
from app.schemas.vision import VisionPredictResponse

_yolo_model = None

def get_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        try:
            print("-> [YOLO Loader] Đang tải và khởi tạo YOLOv11m (Medium)...")
            _yolo_model = YOLO("best.pt")
            print("-> [YOLO Loader] Load YOLO model thành công!")
        except Exception as e:
            print(f"!!! Lỗi load YOLO: {e}")
            _yolo_model = False
    return _yolo_model if _yolo_model is not False else None

async def predict_food_image(file: UploadFile) -> VisionPredictResponse:
    model = get_yolo_model()
    if not model:
        raise HTTPException(status_code=503, detail="Model AI chưa sẵn sàng")
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        results = model(image)
        
        detected_name = ""
        max_conf = 0.0
        
        if results and len(results) > 0:
            result = results[0]
            if result.boxes:
                top_box = sorted(result.boxes, key=lambda x: x.conf, reverse=True)[0]
                max_conf = float(top_box.conf)
                cls_id = int(top_box.cls)
                detected_name = result.names[cls_id] 

        if not detected_name:
            return VisionPredictResponse(food_name=None, message="Không nhận diện được món ăn")

        # Smart name translation & cleaning
        name_clean = detected_name.lower().replace("_", " ").replace("-", " ").strip()
        
        translated_name = EN_VI_MAPPING.get(name_clean)
        
        if not translated_name:
            translated_name = EN_VI_MAPPING.get(detected_name.lower())
            
        if not translated_name:
            translated_name = name_clean 
            for k, v in EN_VI_MAPPING.items():
                if k in name_clean or name_clean in k:
                    translated_name = v
                    break

        final_name = translated_name.title()

        print(f"AI Detected: '{detected_name}' -> Clean: '{name_clean}' -> Final: '{final_name}'")

        return VisionPredictResponse(
            food_name=final_name, 
            original_name=detected_name,
            confidence=max_conf
        )

    except Exception as e:
        print(f"Lỗi dự đoán ảnh: {e}")
        raise HTTPException(status_code=500, detail=str(e))
