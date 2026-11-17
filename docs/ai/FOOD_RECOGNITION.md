# GASTROWISE - AI FOOD VISION & RECOGNITION SPECIFICATION
## YOLOv11 Multi-Food Detection, Vietnamese Food Dataset & Nutrition Mapping

**Module:** `KLTN-123-GastroWise-AI / app/core/vision_service.py`  
**Vision Architecture:** Ultralytics YOLOv11m (Medium Architecture, 40.5MB)  
**Target Taxonomy:** 20 Iconic Vietnamese Culinary Dishes  

---

## 1. Dataset Evaluation & Model Selection

### 1.1. Why Global Datasets (Food-101) Fail in Vietnam
Standard open-source benchmarks like **Food-101** contain Western dishes (Hamburgers, Pizzas, Donuts, French Fries) but lack authentic Vietnamese culinary signatures (Cơm Tấm, Bún Đậu Mắm Tôm, Bánh Mì Chả Cá, Hủ Tiếu Nam Vang). Testing Food-101 on Vietnamese food images results in severe misclassification (e.g., misidentifying Phở as Ramen or Bánh Mì as Sub Sandwich).

### 1.2. Existing Baseline vs Phase 2 Expansion
- **Phase 1 Baseline (Existing `best.pt`):** 5 classes: `['Banh-Mi', 'Bot Chien', 'Bun', 'Goi-Cuon', 'Pho']`.
- **Phase 2 Target (20 Expanded Classes):**
```python
EXPANDED_CLASSES = [
    'Banh-Mi',            # 0: Bánh mì kẹp thịt / pate
    'Banh-Xeo',           # 1: Bánh xèo miền Tây / giòn rụm
    'Banh-Cuon',          # 2: Bánh cuốn nóng chả lụa
    'Bot-Chien',          # 3: Bột chiên trứng
    'Bun-Bo-Hue',         # 4: Bún bò Huế cay nồng
    'Bun-Cha',            # 5: Bún chả Hà Nội than hoa
    'Bun-Dau-Mam-Tom',    # 6: Bún đậu mắm tôm thập cẩm
    'Bun-Rieu',           # 7: Bún riêu cua đồng
    'Com-Tam',            # 8: Cơm tấm sườn bì chả
    'Com-Ga',             # 9: Cơm gà xé / cơm gà Hải Nam
    'Goi-Cuon',           # 10: Gỏi cuốn tôm thịt
    'Hu-Tieu',            # 11: Hủ tiếu Nam Vang / hủ tiếu Mỹ Tho
    'Mi-Quang',           # 12: Mì Quảng gà / tôm thịt
    'Cao-Lau',            # 13: Cao lầu Hội An
    'Nem-Nuong',          # 14: Nem nướng Nha Trang
    'Oc-Xao-Me',          # 15: Ốc xào me / nghêu hấp sả
    'Lau-Thai',           # 16: Lẩu Thái hải sản Tom Yum
    'Ca-Phe-Sua-Da',      # 17: Cà phê sữa đá pha phin
    'Ca-Phe-Trung',       # 18: Cà phê trứng béo ngậy
    'Che-Thai'            # 19: Chè Thái sầu riêng thạch dừa
]
```

### 1.3. Architecture Comparison: YOLOv11 vs Pure Classifier (ViT / MobileNet)
| Evaluation Metric | Pure Classifier (ViT / EfficientNet) | YOLOv11m Object Detection (Selected) |
| :--- | :--- | :--- |
| **Multi-Dish Detection** | ❌ Fails when a meal has multiple items (Bánh mì + Cafe). | ✅ Detects each item individually with discrete bounding boxes. |
| **Inference Latency** | ~280ms on CPU | **~95ms on GPU, ~210ms on CPU** |
| **Restaurant Setting** | Distracted by tables, bowls, utensils. | ✅ Bounding box isolates food region from tableware. |
| **Model Footprint** | ~140MB | **~40.5MB (Fits within mobile microservice budget)** |

---

## 2. Image Preprocessing & Augmentation Pipeline

### 2.1. Preprocessing Flow
```
[Raw Camera Image (Any resolution)]
           │
           ▼
[CLAHE Enhancement] - Normalizes poor restaurant ambient lighting
           │
           ▼
[Letterbox Padding] - Preserves original aspect ratio without distortion
           │
           ▼
[RGB 640x640 Input Tensor] -> [YOLOv11 Backbone & Head]
```

```python
import cv2
import numpy as np

def preprocess_food_image(image_bytes: bytes) -> np.ndarray:
    # 1. Decode byte stream to OpenCV BGR image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 2. Contrast Limited Adaptive Histogram Equalization (CLAHE) on L-channel
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    return enhanced_bgr
```

### 2.2. Training Augmentations (to combat restaurant glare and steam)
- **Mosaic Augmentation (prob = 1.0):** Stitches 4 images to train small-scale dishes.
- **Mixup (prob = 0.15):** Blends two dish images.
- **HSV Color Jitter:** `hgain=0.015`, `sgain=0.7`, `vgain=0.4` (simulates warm vs cold restaurant lamps).
- **Random Flips:** `fliplr=0.5`.

---

## 3. Confidence Thresholding & Unknown Food Fallback

### 3.1. Dual-Threshold Policy
- **Detection Acceptance Threshold:** $\theta_{\text{conf}} \ge 0.65$.
- **NMS IoU Threshold:** $\theta_{\text{iou}} = 0.45$.

### 3.2. Unknown Food Fallback Flow
```
                      [YOLO Detections Output]
                                 │
                     ┌───────────┴───────────┐
                     ▼                       ▼
            Max Confidence >= 0.65       Max Confidence < 0.65
                     │                       │
                     ▼                       ▼
        [Class Confirmed: "Phở Bò"]  [Graceful Fallback Mode]
        - Query Nutrition Table      - Prompt: "Chưa nhận diện chính xác món"
        - Query Matching Restaurants - Offer: "Bạn có muốn tìm kiếm theo từ khóa?"
```

---

## 4. Nutrition Facts Mapping Engine

Upon identifying a food class, GastroWise maps the detected item to the `food_nutrition_dictionary` collection:

| Class Key | Display Name | Serving Size | Calories (kcal) | Protein (g) | Carbs (g) | Fat (g) | Dietary Advice |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `pho_bo` | Phở Bò Tái Nạm | 1 Tô (550g) | 480 | 28 | 58 | 14 | Giàu đạm, bổ sung năng lượng tốt. |
| `com_tam`| Cơm Tấm Sườn Bì | 1 Dĩa (450g) | 680 | 34 | 72 | 28 | Năng lượng cao; nên ăn kèm nhiều dưa leo. |
| `bun_cha`| Bún Chả Hà Nội | 1 Phần (400g)| 520 | 26 | 62 | 18 | Cân bằng chất xơ khi dùng kèm rau sống. |
| `banh_mi`| Bánh Mì Thịt Nguội | 1 Ổ (200g) | 390 | 16 | 48 | 15 | Bữa sáng tiện lợi, giàu tinh bột. |
| `goi_cuon`| Gỏi Cuốn Tôm Thịt| 3 Cuốn (210g)| 220 | 18 | 26 | 4 | Thích hợp ăn kiêng (Low-fat / Clean eating). |

---

## 5. End-to-End Mobile Flow Integration

1. User opens **AI Nutri Camera** (`src/app/ai-nutri.tsx`).
2. Mobile captures photo or selects from gallery, uploads to NestJS `POST /restaurants/search-by-image`.
3. NestJS proxies multipart stream to FastAPI `POST /v1/vision/predict`.
4. FastAPI outputs detected dish `food_name` + bounding box + nutrition macros.
5. NestJS queries MongoDB for restaurants with `tags: { $regex: food_name }`.
6. Mobile renders interactive Nutrition Card overlay + carousel of nearby restaurants serving the detected dish.

