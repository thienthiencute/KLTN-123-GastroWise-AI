# GASTROWISE - API CONTRACT SPECIFICATION
## End-to-End API Architecture, DTOs & Service-to-Service Integration

**Gateway:** NestJS 10 (Port 3001)  
**AI Microservice:** Python FastAPI (Port 5000)  
**Security Model:** JWT Bearer (User <-> Gateway) + `X-Internal-AI-Key` (Gateway <-> AI Microservice)  
**Standard Format:** JSON (UTF-8), Content-Type: `application/json` (or `multipart/form-data` for vision)  

---

## 1. Gateway Security & Global Error Contract

### 1.1. Client to Gateway Headers
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json
Accept: application/json
X-Client-Platform: android | ios | web
X-Client-Version: 1.0.0
```

### 1.2. Gateway to AI Microservice Internal Headers
```http
X-Internal-AI-Key: Bearer <ENV_AI_SERVICE_SECRET>
Content-Type: application/json
```

### 1.3. Standard Error Envelope (RFC 7807 Compatible)
```json
{
  "statusCode": 400,
  "message": "Validation failed",
  "error": "Bad Request",
  "errors": [
    {
      "field": "budget",
      "rule": "min",
      "message": "Budget must be greater than or equal to 50,000 VND"
    }
  ],
  "timestamp": "2026-11-05T10:30:00.000Z",
  "path": "/api/v1/itineraries/generate"
}
```

---

## 2. Phase 2 Client <-> Gateway Endpoints (NestJS)

### 2.1. Taste DNA & Preferences

#### `GET /taste-dna/me`
- **Auth:** Required (User JWT)
- **Description:** Retrieve current authenticated user's 6-D Taste vector and preferences.
- **Response (200 OK):**
```json
{
  "userId": "66f00112233445566778899a",
  "vector": {
    "spicy": 0.75,
    "sweet": 0.40,
    "sour": 0.30,
    "salty": 0.55,
    "umami": 0.85,
    "bitter": 0.15
  },
  "dietary_constraints": ["no_msg", "low_carb"],
  "cuisine_weights": {
    "vietnamese": 0.90,
    "bbq": 0.80,
    "japanese": 0.65
  },
  "preferred_price_tier": 2,
  "updated_at": "2026-11-05T08:00:00.000Z"
}
```

#### `PATCH /taste-dna/me`
- **Auth:** Required (User JWT)
- **Description:** Update taste questionnaire preferences and manual slider adjustments.
- **Request Body:**
```json
{
  "cuisines": ["Món Việt Truyền Thống", "Lẩu & Nướng Hàn/Nhật"],
  "spice_tolerance": "Cay vừa",
  "dietary_constraints": ["Ăn thuần chay (Vegan)"],
  "price_tier": 2
}
```
- **Response (200 OK):** Updated `TasteDnaProfile` document.

---

### 2.2. Interaction Event Logging

#### `POST /interactions/batch`
- **Auth:** Optional (Accepts Authenticated User or Guest Session)
- **Description:** Log implicit and explicit user behaviors for recommendation reinforcement.
- **Request Body:**
```json
{
  "sessionId": "sess_9f823a-bc12",
  "events": [
    {
      "eventType": "VIEW_RESTAURANT",
      "targetType": "restaurant",
      "targetId": "66df87a1c890123456789abc",
      "dwellTimeMs": 14500,
      "context": {
        "lat": 10.7769,
        "lon": 106.7009,
        "weather_type": "hot"
      }
    },
    {
      "eventType": "CLICK_RECOMMENDATION",
      "targetType": "restaurant",
      "targetId": "66df87a1c890123456789def",
      "dwellTimeMs": 0,
      "context": {
        "recommendation_algorithm": "hybrid_v1"
      }
    }
  ]
}
```
- **Response (201 Created):**
```json
{
  "success": true,
  "processed": 2
}
```

---

### 2.3. Smart Food Journey Routing & Optimization (TASK-BIZ-02)

#### `POST /itineraries/generate`
- **Auth:** Required (User JWT)
- **Description:** Generate OR-Tools optimized multi-stop food tour matching prompt, location, budget, stop count, and routing mode.
- **Request Body:**
```json
{
  "prompt": "Food Tour lẩu nướng & trà sữa Gò Vấp",
  "budget": 350000,
  "start_time": "18:00",
  "end_time": "21:30",
  "stop_count": 3,
  "routing_mode": "motorbike",
  "lat": 10.8354,
  "lng": 106.6660
}
```
- **Response (201 Created):**
```json
{
  "_id": "672901a1bc33445566778899",
  "title": "Lộ trình ẩm thực tại Gò Vấp",
  "status": "generated",
  "budget": 350000,
  "total_cost": 210000,
  "remaining_budget": 140000,
  "desired_stops": 3,
  "routing_mode": "motorbike",
  "co2SavedKg": 1.8,
  "total_distance_km": 4.6,
  "total_duration_mins": 195,
  "optimizedBy": "OR-Tools TSPTW Solver",
  "stops": [
    {
      "stop_id": "stop-1-uuid",
      "restaurant_id": "66e112233445566778899001",
      "restaurant_name": "Nhà Hàng Lẩu Nướng King BBQ",
      "restaurant_lat": 10.8220,
      "restaurant_lng": 106.6870,
      "order_index": 1,
      "meal_type": "main",
      "arrival_time": "18:15",
      "departure_time": "19:00",
      "dining_duration_mins": 45,
      "transit_time_mins": 15,
      "distance_to_next_km": 1.2,
      "estimated_cost": 120000
    },
    {
      "stop_id": "stop-2-uuid",
      "restaurant_id": "66e112233445566778899002",
      "restaurant_name": "Phúc Long Coffee & Tea",
      "restaurant_lat": 10.8310,
      "restaurant_lng": 106.6950,
      "order_index": 2,
      "meal_type": "cafe",
      "arrival_time": "19:15",
      "departure_time": "20:00",
      "dining_duration_mins": 45,
      "transit_time_mins": 10,
      "distance_to_next_km": 1.5,
      "estimated_cost": 45000
    }
  ]
}
```

#### `PATCH /itineraries/:id/reorder`
- **Auth:** Required (User JWT - Owner or Admin)
- **Description:** Reorder stops in an itinerary and dynamically recalculate distances, transit times, arrival/departure schedules, and carbon savings.
- **Request Body:**
```json
{
  "stop_ids": ["stop-2-uuid", "stop-1-uuid"]
}
```
- **Response (200 OK):** Updated `Itinerary` document with recalculated timetable and metrics.

#### `POST /itineraries/:id/stops`
- **Auth:** Required (User JWT - Owner or Admin)
- **Description:** Add a new restaurant stop to the itinerary and recalculate schedule and budget.
- **Request Body:**
```json
{
  "restaurant_id": "66e112233445566778899003",
  "insert_after_order": 2
}
```
- **Response (200 OK):** Updated `Itinerary` document with inserted stop and updated schedule.

#### `DELETE /itineraries/:id/stops/:stopId`
- **Auth:** Required (User JWT - Owner or Admin)
- **Description:** Remove a stop from the itinerary, re-index remaining stops, and recalculate timetables and remaining budget.
- **Response (200 OK):** Updated `Itinerary` document.

#### `POST /itineraries/:id/recalculate`
- **Auth:** Required (User JWT - Owner or Admin)
- **Description:** Recalculate route optimization when constraints (budget, transport mode, start time, location) change.
- **Request Body:**
```json
{
  "budget": 500000,
  "routing_mode": "car",
  "start_time": "18:30"
}
```
- **Response (200 OK):** Updated `Itinerary` document with newly optimized metrics.

#### `PATCH /itineraries/:id`
- **Auth:** Required (User JWT - Owner or Admin)
- **Description:** Update itinerary lifecycle status (`confirmed`, `cancelled`, `completed`). When `completed`, automatically records interaction and triggers Taste DNA EMA reinforcement.
- **Request Body:**
```json
{
  "status": "completed"
}
```

#### `DELETE /itineraries/:id`
- **Auth:** Required (User JWT - Owner or Admin)
- **Description:** Delete an itinerary document.

---

### 2.4. Food Vision & Nutrition Camera

#### `POST /restaurants/search-by-image`
- **Auth:** Optional
- **Headers:** `Content-Type: multipart/form-data`
- **Body:** Form Data: `file: <binary image file (jpg/png)>`
- **Response (200 OK):**
```json
{
  "detected": true,
  "food_name": "Phở Bò",
  "confidence": 0.94,
  "nutrition": {
    "calories": 450,
    "protein_g": 28,
    "carbs_g": 55,
    "fat_g": 12,
    "advice": "Món ăn giàu protein, cung cấp năng lượng đầy đủ."
  },
  "matching_restaurants": [
    {
      "_id": "66a0123...",
      "tenQuan": "Phở Gia Truyền Bát Đàn",
      "diaChi": "12 Nguyễn Văn Bảo, Gò Vấp",
      "diemTrungBinh": 4.9,
      "giaCa": "50.000đ - 85.000đ"
    }
  ]
}
```

---

## 3. Internal Service-to-Service Endpoints (NestJS <-> Python FastAPI)

### 3.1. Hybrid Recommendation

#### `POST /v1/recommend/hybrid`
- **Invoked By:** NestJS `RestaurantsService`
- **Headers:** `X-Internal-AI-Key: Bearer <SECRET>`
- **Request Body:**
```json
{
  "user_id": "66f00112233445566778899a",
  "user_gps": [10.7769, 106.7009],
  "taste_vector": {
    "spicy": 0.75,
    "sweet": 0.40,
    "sour": 0.30,
    "salty": 0.55,
    "umami": 0.85,
    "bitter": 0.15
  },
  "dietary_constraints": ["low_carb"],
  "weather_type": "hot",
  "current_time_slot": "lunch",
  "limit": 20
}
```
- **FastAPI Response (200 OK):**
```json
{
  "sort_by": "hybrid_taste_context",
  "candidates": [
    {
      "restaurant_id": "66df87a1c890123456789abc",
      "score": 0.934,
      "relevance_factors": {
        "taste_match": 0.88,
        "context_weather": 0.95,
        "distance_penalty": 0.05
      },
      "explanation": "Đặc biệt phù hợp vị giác đậm đà & món thanh mát ngày nắng"
    }
  ]
}
```

---

### 3.2. Google OR-Tools Route Optimizer

#### `POST /routes/optimize`
- **Invoked By:** NestJS `ItinerariesService`
- **Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "start_location": [10.8354, 106.6660],
  "start_time_mins": 1080,
  "budget": 350000,
  "routing_mode": "motorbike",
  "desired_stops": 3,
  "candidates": [
    {
      "id": "66e112233445566778899001",
      "name": "Nhà Hàng Lẩu Nướng King BBQ",
      "lat": 10.8220,
      "lon": 106.6870,
      "meal_type": "main",
      "open_time": "10:00",
      "close_time": "22:00",
      "dining_duration_mins": 45,
      "avg_price": 120000,
      "rating": 4.6,
      "tags": "Lẩu, Nướng"
    },
    {
      "id": "66e112233445566778899002",
      "name": "Phúc Long Coffee & Tea",
      "lat": 10.8310,
      "lon": 106.6950,
      "meal_type": "cafe",
      "open_time": "08:00",
      "close_time": "22:30",
      "dining_duration_mins": 45,
      "avg_price": 50000,
      "rating": 4.5,
      "tags": "Trà sữa, Cafe"
    }
  ]
}
```
- **FastAPI Response (200 OK):**
```json
{
  "stops": [
    {
      "id": "66e112233445566778899001",
      "name": "Nhà Hàng Lẩu Nướng King BBQ",
      "lat": 10.8220,
      "lon": 106.6870,
      "order_index": 1,
      "meal_type": "main",
      "arrival_time": "18:15",
      "departure_time": "19:00",
      "dining_duration_mins": 45,
      "transit_time_mins": 15,
      "distance_to_next_km": 1.2,
      "estimated_cost": 120000,
      "tags": "Lẩu, Nướng"
    },
    {
      "id": "66e112233445566778899002",
      "name": "Phúc Long Coffee & Tea",
      "lat": 10.8310,
      "lon": 106.6950,
      "order_index": 2,
      "meal_type": "cafe",
      "arrival_time": "19:15",
      "departure_time": "20:00",
      "dining_duration_mins": 45,
      "transit_time_mins": 10,
      "distance_to_next_km": 1.5,
      "estimated_cost": 50000,
      "tags": "Trà sữa, Cafe"
    }
  ],
  "total_distance_km": 2.7,
  "total_duration_mins": 115,
  "total_cost": 170000,
  "remaining_budget": 180000,
  "co2_saved_kg": 0.5,
  "status": "SUCCESS",
  "message": "Tối ưu thành công lộ trình ẩm thực (OR-Tools TSPTW Optimal Solution)",
  "algorithm_used": "OR-Tools TSPTW",
  "routing_mode": "motorbike"
}
```

---

### 3.3. YOLOv11 Food Vision Inference

#### `POST /v1/vision/predict`
- **Invoked By:** NestJS `RestaurantsService`
- **Headers:** `X-Internal-AI-Key: Bearer <SECRET>`, `Content-Type: multipart/form-data`
- **Request Body:** Binary form-data image file
- **FastAPI Response (200 OK):**
```json
{
  "detected": true,
  "class_name": "pho_bo",
  "vietnamese_name": "Phở Bò",
  "confidence": 0.942,
  "bounding_box": {
    "x_min": 0.12,
    "y_min": 0.18,
    "x_max": 0.88,
    "y_max": 0.82
  },
  "nutrition": {
    "calories": 450,
    "protein_g": 28,
    "carbs_g": 55,
    "fat_g": 12
  },
  "mapped_tags": ["PHỞ", "MÓN NƯỚC", "BÒ"]
}
```

