# GastroWise AI Microservice — API Contract Inventory

- **Service:** GastroWise AI Microservice (`KLTN-123-GastroWise-AI`, FastAPI `1.0.0`, OpenAPI `3.1.0`)
- **Base Bind / Port:** `http://ai-service:5000` (Docker Compose) / `http://127.0.0.1:5000` (local)
- **Authentication Mechanism:** Fail-closed shared secret via `X-Internal-AI-Key` header enforced by `verify_internal_ai_key` on `api_v1_router` (`401` missing header, `403` invalid key, `500` unset server `INTERNAL_AI_KEY`).
- **Exception:** `GET /` (Docker health check) is intentionally unauthenticated.

---

## 1. Registered Endpoints Summary

| Route | HTTP Method | Auth | Request Schema | Response Schema | Confirmed Callers (`KLTN-123-GastroWise-BE`) |
|---|---|---|---|---|---|
| `/` | `GET` | Public (Health) | None | JSON health object | Docker `HEALTHCHECK` |
| `/recommend` | `POST` | `X-Internal-AI-Key` | `RecommendRequest` | `RecommendResponse` | Core Service (`RestaurantsService.findAll`) |
| `/recommend/hybrid` | `POST` | `X-Internal-AI-Key` | `HybridRecommendRequest` | `HybridRecommendResponse` | Core Service (`RestaurantsService.getPersonalizedRecommendations`) |
| `/cf/train` | `POST` | `X-Internal-AI-Key` | `TrainCFRequest` | `TrainCFResponse` | Core Service (`RestaurantsService.syncInteractionsToAi`) |
| `/chat` | `POST` | `X-Internal-AI-Key` | `ChatRequest` | `ChatResponse` | Legacy endpoint (no active BE caller) |
| `/weather-recommend` | `POST` | `X-Internal-AI-Key` | `WeatherRecommendRequest` | `WeatherRecommendResponse` | Core Service (`RestaurantsService.getWeatherRecommendation`) |
| `/sentiment` | `POST` | `X-Internal-AI-Key` | `SentimentRequest` | `SentimentResponse` | Offline script / optional caller |
| `/analyze-sentiment` | `POST` | `X-Internal-AI-Key` | `SentimentRequest` | `AdvancedSentimentResponse` | Core Service (`ReviewsService.analyzeSentiment`) |
| `/predict-food` | `POST` | `X-Internal-AI-Key` | `multipart/form-data` (`file`) | `VisionPredictResponse` | Core Service (`RestaurantsService.searchByImage`) |
| `/routes/optimize` | `POST` | `X-Internal-AI-Key` | `RouteOptimizeRequest` (canonical + legacy aliases) | `RouteOptimizeResponse` | Planning Service (`AiApiClient.optimizeRoute`) |
| `/copilot/message` | `POST` | `X-Internal-AI-Key` | `CopilotChatRequest` | `CopilotChatResponse` | Core Service (`RestaurantsService.chatWithAI`) |
| `/v1/recommendation/recommend` | `POST` | `X-Internal-AI-Key` | `RecommendRequest` | `RecommendResponse` | Dual-route ADR-07 compatibility |
| `/v1/recommendation/recommend/hybrid` | `POST` | `X-Internal-AI-Key` | `HybridRecommendRequest` | `HybridRecommendResponse` | Dual-route ADR-07 compatibility |
| `/v1/recommendation/cf/train` | `POST` | `X-Internal-AI-Key` | `TrainCFRequest` | `TrainCFResponse` | Dual-route ADR-07 compatibility |
| `/v1/recommendation/chat` | `POST` | `X-Internal-AI-Key` | `ChatRequest` | `ChatResponse` | Dual-route ADR-07 compatibility |
| `/v1/copilot/message` | `POST` | `X-Internal-AI-Key` | `CopilotChatRequest` | `CopilotChatResponse` | Dual-route ADR-07 compatibility |

---

## 2. Detailed Schemas, Field Requirements & Defaults

### 2.1 `RecommendRequest` / `RecommendResponse` (`POST /recommend`)
- **Request Required:** `query: str`
- **Request Optional (Defaults):** `candidate_ids: Optional[List[str]] = []`, `user_gps: Optional[List[float]] = None`, `city_filter: Optional[str] = None`, `taste_vector: Optional[List[float]] = None`, `dietary_exclusions: Optional[List[str]] = []`
- **Response Required:** `sort_by: str`, `scores: List[TasteScore]`
  - `TasteScore`: required `{id: str, name: str, tags: str, S_taste: float, distance_km: float, price: int}`, optional `{explanation: Optional[str] = None}`

### 2.2 `HybridRecommendRequest` / `HybridRecommendResponse` (`POST /recommend/hybrid`)
- **Request Required:** *(None — all fields optional)*
- **Request Optional (Defaults):** `user_id: Optional[str] = None`, `user_gps: Optional[List[float]] = None`, `taste_vector: Optional[List[float]] = None`, `dietary_exclusions: Optional[List[str]] = []`, `weather_type: Optional[str] = None`, `temperature: Optional[float] = None`, `max_price: Optional[int] = None`, `limit: Optional[int] = 10`
- **Response Required:** `total: int`, `is_cold_start: bool`, `applied_weights: Dict[str, float]`, `items: List[HybridRecommendItem]`
  - `HybridRecommendItem`: `{id: str, name: str, tags: str, score: float, taste_score: float, cf_score: float, env_score: float, distance_km: float, price: int, match_reasons: List[str], explanation: str}`

### 2.3 `RouteOptimizeRequest` / `RouteOptimizeResponse` (`POST /routes/optimize`)
- **Request Required (Canonical):** `start_location: List[float]`, `candidates: List[CandidateStop]`
  - `CandidateStop` required: `id: str`, `name: str` *(validator falls back to `Restaurant {id}` if empty/missing)*, `lat: float`, `lon: float`
  - `CandidateStop` optional: `meal_type='main'`, `open_time='08:00'`, `close_time='22:00'`, `dining_duration_mins=45`, `avg_price=50000`, `rating=4.5`, `tags=None`, `district=None`
- **Request Optional (Defaults):** `start_time_mins=660`, `budget=250000`, `routing_mode='motorbike'`, `desired_stops=3`, `max_duration_mins=None`
- **Documented Legacy Aliases (`model_validator(mode='before')`):**
  - `restaurants` -> `candidates`
  - `start_lat`, `start_lng` -> `start_location`
  - `budget_vnd` -> `budget`
  - `start_time` (`"HH:MM"` or numeric) -> `start_time_mins`
  - CandidateStop: `lng` -> `lon`, `open` -> `open_time`, `close` -> `close_time`, `duration_mins` -> `dining_duration_mins`
- **Response Required:** `stops: List[OptimizedStop]`, `total_distance_km: float`, `total_duration_mins: int`, `total_cost: int`, `remaining_budget: int`, `co2_saved_kg: float`, `status: str`, `message: str`
- **Response Optional/Default:** `ordered_stops: Optional[List[OptimizedStop]]` (auto-populated from `stops` via post-validator), `algorithm_used='OR-Tools TSPTW'`, `routing_mode='motorbike'`

### 2.4 `WeatherRecommendRequest` / `WeatherRecommendResponse` (`POST /weather-recommend`)
- **Request Optional:** `user_gps=None`, `temperature=None`, `weather_condition=None`
- **Response Required:** `weather: WeatherInfo` (`temperature`, `condition_text`, `condition_code`, `banner_title`, `banner_desc`, `weather_type`), `scores: List[TasteScore]`

### 2.5 `TrainCFRequest` / `TrainCFResponse` (`POST /cf/train`)
- **Request Required:** `interactions: List[Dict[str, Any]]`
- **Response Required:** `success: bool`, `message: str`, `user_count: int`, `item_count: int`

### 2.6 `SentimentRequest` / `SentimentResponse` & `AdvancedSentimentResponse`
- **Request Required:** `review: str`
- **`POST /sentiment` Response:** `label: str`, `score: float`
- **`POST /analyze-sentiment` Response:** `label: str`, `score: float`, `hashtags: List[str]`

### 2.7 `CopilotChatRequest` / `CopilotChatResponse` (`POST /copilot/message`)
- **Request Required:** `message: str`, optional `user_gps=None`, `taste_vector=None`
- **Response Required:** `reply: str`, `intent: str`, `entities: Dict[str, Any]`, optional `action_card=None`, `results: List[Dict[str, Any]] = []`

### 2.8 `VisionPredictResponse` (`POST /predict-food`)
- **Request Required:** Multipart form upload field `file: UploadFile`
- **Response:** `food_name=None`, `original_name=None`, `confidence=None`, `is_confident=True`, `detections=[]`, `nutrition=None`, `message=None`

---

## 3. Error Responses & Internal Dependencies

- **Authentication Errors (`verify_internal_ai_key`):**
  - `401 Unauthorized`: `{"detail": "Missing X-Internal-AI-Key header"}`
  - `403 Forbidden`: `{"detail": "Invalid internal AI service key"}`
  - `500 Internal Server Error`: `{"detail": "Internal configuration error: INTERNAL_AI_KEY is not configured"}`
- **Request Validation Errors (FastAPI / Pydantic):**
  - `422 Unprocessable Entity`: `{"detail": [{"type": ..., "loc": [...], "msg": ..., "input": ...}]}` (also triggered on malformed JSON bodies)
- **Model/Vision Errors (`/predict-food`):**
  - `503 Service Unavailable`: `{"detail": "Model AI chưa sẵn sàng"}` if `best.pt` / YOLO fails to load
  - `500 Internal Server Error`: `{"detail": "..."}` on corrupted image decode
- **Internal Dependencies:**
  - MongoDB (`app/db/mongo.py`) for initial catalog load & TF-IDF vectorizer fit (`df`, `tfidf_vectorizer`).
  - Open-Meteo (`https://api.open-meteo.com/v1/forecast`, 3s timeout, safe fallback `28.0°C, code=0`).
  - Google OR-Tools (`ortools`) optional for TSPTW (`solve_with_ortools` falls back to `solve_greedy_gastronomic` when absent/unsolved).
  - YOLOv11 (`best.pt`) and `cv2` lazy/fallback-guarded (`predict_food_image`).
  - ViSoBERT (`5CD-AI/Vietnamese-Sentiment-visobert`) lazy-loaded for `/sentiment`; rule-based engine for `/analyze-sentiment`.
