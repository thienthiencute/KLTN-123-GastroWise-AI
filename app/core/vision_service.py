import io
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
from fastapi import HTTPException, UploadFile
from typing import Dict, Any, List, Optional
from app.config import EN_VI_MAPPING
from app.schemas.vision import VisionPredictResponse, FoodDetectionItem, BoundingBox, NutritionInfo

_yolo_model = None

# Bảng tra cứu dinh dưỡng chuẩn hóa cho các món ăn Việt Nam phổ biến
VIETNAMESE_FOOD_NUTRITION: Dict[str, Dict[str, Any]] = {
    'bánh mì': {'calories': 385, 'protein_g': 12.5, 'carbs_g': 55.0, 'fat_g': 14.0, 'serving_desc': '1 ổ bánh mì kẹp thịt chả'},
    'banh mi': {'calories': 385, 'protein_g': 12.5, 'carbs_g': 55.0, 'fat_g': 14.0, 'serving_desc': '1 ổ bánh mì kẹp thịt chả'},
    'phở': {'calories': 460, 'protein_g': 24.0, 'carbs_g': 62.0, 'fat_g': 11.5, 'serving_desc': '1 tô phở bò tái chín'},
    'pho': {'calories': 460, 'protein_g': 24.0, 'carbs_g': 62.0, 'fat_g': 11.5, 'serving_desc': '1 tô phở bò tái chín'},
    'bún': {'calories': 440, 'protein_g': 22.0, 'carbs_g': 58.0, 'fat_g': 12.0, 'serving_desc': '1 tô bún nước'},
    'bun': {'calories': 440, 'protein_g': 22.0, 'carbs_g': 58.0, 'fat_g': 12.0, 'serving_desc': '1 tô bún nước'},
    'bún bò huế': {'calories': 530, 'protein_g': 28.0, 'carbs_g': 60.0, 'fat_g': 18.0, 'serving_desc': '1 tô bún bò Huế đầy đủ'},
    'bun bo hue': {'calories': 530, 'protein_g': 28.0, 'carbs_g': 60.0, 'fat_g': 18.0, 'serving_desc': '1 tô bún bò Huế đầy đủ'},
    'bún chả': {'calories': 510, 'protein_g': 25.0, 'carbs_g': 65.0, 'fat_g': 15.0, 'serving_desc': '1 suất bún chả nướng than hoa'},
    'bún đậu mắm tôm': {'calories': 580, 'protein_g': 26.0, 'carbs_g': 54.0, 'fat_g': 24.0, 'serving_desc': '1 mẹt bún đậu thập cẩm'},
    'bún riêu': {'calories': 420, 'protein_g': 18.0, 'carbs_g': 56.0, 'fat_g': 13.0, 'serving_desc': '1 tô bún riêu cua đồng'},
    'cơm tấm': {'calories': 650, 'protein_g': 32.0, 'carbs_g': 78.0, 'fat_g': 21.0, 'serving_desc': '1 đĩa cơm sườn bì chả'},
    'com tam': {'calories': 650, 'protein_g': 32.0, 'carbs_g': 78.0, 'fat_g': 21.0, 'serving_desc': '1 đĩa cơm sườn bì chả'},
    'cơm gà': {'calories': 590, 'protein_g': 34.0, 'carbs_g': 68.0, 'fat_g': 18.0, 'serving_desc': '1 đĩa cơm gà xé / luộc'},
    'gỏi cuốn': {'calories': 180, 'protein_g': 9.0, 'carbs_g': 28.0, 'fat_g': 2.5, 'serving_desc': '3 cuốn tôm thịt chấm tương'},
    'goi cuon': {'calories': 180, 'protein_g': 9.0, 'carbs_g': 28.0, 'fat_g': 2.5, 'serving_desc': '3 cuốn tôm thịt chấm tương'},
    'bột chiên': {'calories': 480, 'protein_g': 11.0, 'carbs_g': 52.0, 'fat_g': 24.0, 'serving_desc': '1 đĩa bột chiên 2 trứng'},
    'bot chien': {'calories': 480, 'protein_g': 11.0, 'carbs_g': 52.0, 'fat_g': 24.0, 'serving_desc': '1 đĩa bột chiên 2 trứng'},
    'bánh xèo': {'calories': 420, 'protein_g': 14.0, 'carbs_g': 46.0, 'fat_g': 20.0, 'serving_desc': '1 cái bánh xèo giòn rụm'},
    'bánh cuốn': {'calories': 320, 'protein_g': 12.0, 'carbs_g': 48.0, 'fat_g': 8.0, 'serving_desc': '1 đĩa bánh cuốn nóng chả lụa'},
    'hủ tiếu': {'calories': 450, 'protein_g': 21.0, 'carbs_g': 64.0, 'fat_g': 10.0, 'serving_desc': '1 tô hủ tiếu Nam Vang'},
    'mì quảng': {'calories': 480, 'protein_g': 22.0, 'carbs_g': 60.0, 'fat_g': 14.0, 'serving_desc': '1 tô mì Quảng tôm thịt'},
    'nem nướng': {'calories': 390, 'protein_g': 19.0, 'carbs_g': 35.0, 'fat_g': 16.0, 'serving_desc': '1 phần nem nướng bánh tráng'},
    'cà phê sữa đá': {'calories': 140, 'protein_g': 2.5, 'carbs_g': 22.0, 'fat_g': 4.0, 'serving_desc': '1 ly cà phê sữa đá pha phin'},
    'chè thái': {'calories': 280, 'protein_g': 3.0, 'carbs_g': 52.0, 'fat_g': 7.0, 'serving_desc': '1 ly chè Thái sầu riêng'},
}

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

def get_nutrition_for_dish(dish_name: str) -> Optional[NutritionInfo]:
    if not dish_name:
        return None
    lower = dish_name.lower().strip()
    
    # 1. Exact match
    if lower in VIETNAMESE_FOOD_NUTRITION:
        data = VIETNAMESE_FOOD_NUTRITION[lower]
        return NutritionInfo(**data)
        
    # 2. Substring match
    for key, data in VIETNAMESE_FOOD_NUTRITION.items():
        if key in lower or lower in key:
            return NutritionInfo(**data)
            
    # 3. Default fallback
    return NutritionInfo(
        calories=450,
        protein_g=18.0,
        carbs_g=55.0,
        fat_g=12.0,
        serving_desc=f'1 khẩu phần {dish_name}'
    )

def preprocess_image_clahe(image: Image.Image) -> Image.Image:
    """
    Áp dụng cân bằng sáng cục bộ thích nghi (CLAHE) để cải thiện độ tương phản
    cho ảnh chụp trong điều kiện ánh sáng yếu tại quán ăn.
    """
    try:
        img_np = np.array(image.convert('RGB'))
        # Chuyển sang không gian màu LAB
        lab = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # Áp dụng CLAHE lên kênh độ sáng L
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        
        merged_lab = cv2.merge((cl, a, b))
        enhanced_rgb = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2RGB)
        return Image.fromarray(enhanced_rgb)
    except Exception:
        return image

async def predict_food_image(file: UploadFile) -> VisionPredictResponse:
    model = get_yolo_model()
    if not model:
        raise HTTPException(status_code=503, detail="Model AI chưa sẵn sàng")
    
    try:
        contents = await file.read()
        raw_image = Image.open(io.BytesIO(contents))
        
        # Cân bằng ánh sáng CLAHE
        enhanced_image = preprocess_image_clahe(raw_image)
        
        # Chạy suy luận với YOLOv11
        results = model(enhanced_image, conf=0.25)
        
        detected_items: List[FoodDetectionItem] = []
        max_conf = 0.0
        primary_name = ""
        primary_original = ""
        
        if results and len(results) > 0:
            result = results[0]
            if result.boxes and len(result.boxes) > 0:
                # Sắp xếp các box theo độ tin cậy giảm dần
                sorted_boxes = sorted(result.boxes, key=lambda x: float(x.conf), reverse=True)
                
                for box in sorted_boxes:
                    conf = float(box.conf)
                    cls_id = int(box.cls)
                    raw_cls_name = result.names[cls_id]
                    
                    # Làm sạch tên món
                    clean_name = raw_cls_name.lower().replace("_", " ").replace("-", " ").strip()
                    vi_name = EN_VI_MAPPING.get(clean_name, EN_VI_MAPPING.get(raw_cls_name.lower(), clean_name))
                    vi_title = vi_name.title()
                    
                    xyxy = box.xyxy[0].tolist() if hasattr(box, 'xyxy') else [0, 0, 0, 0]
                    bbox = BoundingBox(x1=round(xyxy[0], 1), y1=round(xyxy[1], 1), x2=round(xyxy[2], 1), y2=round(xyxy[3], 1))
                    
                    nutri = get_nutrition_for_dish(vi_title)
                    
                    item = FoodDetectionItem(
                        food_name=vi_title,
                        vietnamese_name=vi_title,
                        confidence=round(conf, 4),
                        bbox=bbox,
                        nutrition=nutri
                    )
                    detected_items.append(item)
                    
                if detected_items:
                    primary_name = detected_items[0].vietnamese_name
                    primary_original = detected_items[0].food_name
                    max_conf = detected_items[0].confidence

        # Out-Of-Distribution Rejection Threshold: theta = 0.45
        CONFIDENCE_THRESHOLD = 0.45
        if not primary_name or max_conf < CONFIDENCE_THRESHOLD:
            return VisionPredictResponse(
                food_name=None,
                confidence=round(max_conf, 4) if max_conf > 0 else 0.0,
                is_confident=False,
                detections=detected_items,
                message="Hình ảnh chưa đủ rõ nét hoặc món ăn nằm ngoài danh mục nhận diện hiện tại. Vui lòng chụp gần hơn hoặc chọn góc đủ sáng."
            )

        primary_nutrition = get_nutrition_for_dish(primary_name)
        print(f"✅ [YOLO Vision] Phát hiện: '{primary_name}' (Độ tin cậy: {max_conf:.2%})")

        return VisionPredictResponse(
            food_name=primary_name,
            original_name=primary_original,
            confidence=round(max_conf, 4),
            is_confident=True,
            detections=detected_items,
            nutrition=primary_nutrition,
            message="Nhận diện món ăn thành công"
        )

    except Exception as e:
        print(f"❌ Lỗi dự đoán ảnh: {e}")
        raise HTTPException(status_code=500, detail=str(e))
