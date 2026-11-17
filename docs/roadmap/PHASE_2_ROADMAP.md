# GASTROWISE - PHASE 2 MASTER DEVELOPMENT ROADMAP
## Intelligent Personalized Food Recommendation & Journey Optimization Platform

**Author:** Principal Software Architect & AI Technical Lead  
**Target Release:** GastroWise 2.0 (Phase 2)  
**Technology Stack:** React Native (Expo SDK 57), NestJS 10, MongoDB Atlas, Python FastAPI (Port 5000), PyTorch / YOLOv11, Google OR-Tools  

---

## 1. Executive Summary & Architectural Vision

GastroWise Phase 2 transforms the platform from a rule-assisted food discovery directory into a unified, **intelligent culinary intelligence and autonomous travel companion**. The system harmonizes user tastes, physical constraints, environmental context, and multi-stop logistics into cohesive food journeys.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                GASTROWISE ECOSYSTEM                                    │
└────────────────────────────────────────────────────────────────────────────────────────┘
                 ▲                                                       ▲
                 │                                                       │
  Mobile App (React Native Expo 57)                        Admin & Web Portal (Next.js 14/15)
  - Taste DNA Questionnaire & Radar                       - Restaurant & Menu Management
  - AI Food Camera (Vision)                               - Itinerary & Audit Trail Monitor
  - Interactive Smart Journey Map                         - Analytics & AI Sentiment Insights
                 │                                                       │
                 ▼                                                       ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        NESTJS BACKEND GATEWAY (PORT 3001)                              │
│  - JWT Bearer Authentication & RBAC Guards                                             │
│  - Request Validation Pipes & DTO Serialization                                        │
│  - Data Aggregation, Ownership Validation & Business Workflows                         │
│  - Internal AI Microservice Gateway Client (mTLS / API Key)                            │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
┌───────────────────────────────┐     ┌──────────────────────────────────────────────────┐
│     MONGODB ATLAS CLUSTER     │     │       PYTHON FASTAPI AI MICROSERVICE (PORT 5000) │
│  - users & taste_dna_profiles │     │  - P1: Online Taste DNA Vector Scoring           │
│  - restaurants (2dsphere)     │     │  - P2: Hybrid Recommendation (Content + CF + SVD)│
│  - menu_items & nutrition     │     │  - P3: OR-Tools Route Optimizer (VRPTW + CO2)    │
│  - itineraries & stops        │     │  - P4: YOLOv11 Vietnamese Food Vision Pipeline   │
│  - reviews & user_interactions│     │  - P5: Natural Language Intent Copilot           │
└───────────────────────────────┘     └──────────────────────────────────────────────────┘
```

---

## 2. Phase-by-Phase Detailed Task Specifications

---

### PHASE P0: DATA FOUNDATION & TAXONOMY NORMALIZATION

#### [TASK-P0-01] Geospatial & Data Normalization Migration
- **Business Objective:** Enable sub-second geospatial search, radius filtering, and uniform food categorization across all 24 districts of Ho Chi Minh City.
- **Current Status:** PARTIALLY COMPLETED. Lat/lon stored as standalone numbers; district extracted via regex; no `2dsphere` index.
- **Exact Files / Modules Affected:**
  - Backend: `src/restaurants/schemas/restaurant.schema.ts`, `src/restaurants/restaurants.service.ts`
  - AI: `app/db/mongo.py`, `app/config.py`
  - Mobile: `src/app/(tabs)/explore.tsx`
- **Mobile Responsibilities:** Send standard `[longitude, latitude]` array in query parameters when location permission is granted.
- **NestJS Responsibilities:** Add `location: { type: 'Point', coordinates: [number, number] }` with `@Prop({ type: Object, index: '2dsphere' })`; write a safe migration script to backfill `location` from existing `lat`/`lon`.
- **FastAPI / AI Responsibilities:** Update `app/db/mongo.py` dataset loader to read native GeoJSON coordinates and extract distance via MongoDB `$geoNear` instead of custom Python loops.
- **Database Changes:**
  - Collection: `restaurants`
  - Add field: `location: { type: "Point", coordinates: [lon, lat] }`
  - Create index: `{ location: "2dsphere" }`
- **API Contracts:**
  - `GET /restaurants?lng=106.7009&lat=10.7769&radius_km=5`
- **Dependencies:** None. Foundational.
- **Acceptance Criteria:**
  1. `db.restaurants.getIndexes()` contains `location_2dsphere`.
  2. Querying within 3km returns only restaurants located within 3,000m.
  3. All 1,000+ existing restaurants have non-null `location` coordinates.
- **Testing Requirements:** Unit test in NestJS testing `$near` query; integration test verifying MongoDB index creation.
- **Git Branch Suggestion:** `feat/p0-geospatial-normalization`
- **Estimated Effort:** 8 Story Points (2 days)

---

#### [TASK-P0-02] User Interaction Event Collection Pipeline
- **Business Objective:** Capture implicit and explicit user engagement (views, search queries, food tour completions, dish clicks, review likes) to power collaborative filtering and Taste DNA reinforcement.
- **Current Status:** NOT IMPLEMENTED. Currently only explicit reviews and favorites are persisted.
- **Exact Files / Modules Affected:**
  - Backend: `src/interactions/` (New Module), `src/app.module.ts`
  - Mobile: `src/lib/analytics/tracker.ts` (New Utility), `src/app/(tabs)/index.tsx`, `src/app/restaurant/[id].tsx`
- **Mobile Responsibilities:** Fire lightweight async event tracking payload `{ eventType, targetId, durationMs, metadata }` on screen dwell and card taps.
- **NestJS Responsibilities:** Create `UserInteraction` schema; implement high-throughput `POST /interactions/batch` endpoint with throttler guard.
- **FastAPI / AI Responsibilities:** Expose ingestion interface for interaction matrices.
- **Database Changes:**
  - Create collection: `user_interactions`
  - Fields: `userId (ObjectId)`, `eventType (enum)`, `targetType (restaurant|menu_item|itinerary)`, `targetId (ObjectId)`, `durationMs (Number)`, `metadata (Object)`, `createdAt (Date)`
  - Indexes: `{ userId: 1, createdAt: -1 }`, `{ targetId: 1, eventType: 1 }`
- **API Contracts:**
  - `POST /interactions/batch` -> Payload: `{ events: Array<InteractionEventDto> }`
- **Dependencies:** `TASK-P0-01`
- **Acceptance Criteria:**
  1. Interaction events logged within < 20ms response time.
  2. Batch endpoint handles up to 50 events in a single payload.
  3. Unauthenticated events saved with guest session ID.
- **Testing Requirements:** Load test with k6 (500 events/sec); schema validation tests.
- **Git Branch Suggestion:** `feat/p0-interaction-pipeline`
- **Estimated Effort:** 5 Story Points (1.5 days)

---

### PHASE P1: ADVANCED TASTE DNA SYSTEM

#### [TASK-P1-01] Normalized Taste DNA Profiling Engine
- **Business Objective:** Represent each user's taste as a continuous multi-dimensional flavor vector (sweet, sour, salty, spicy, umami, bitter) + dietary rules + cuisine preferences, allowing mathematical similarity matching.
- **Current Status:** PARTIALLY COMPLETED. Mobile stores strings in `User.preferences` (`['Món Việt', 'Vị cay: Cay vừa']`).
- **Exact Files / Modules Affected:**
  - Backend: `src/taste-dna/` (New Module), `src/users/schemas/user.schema.ts`
  - Mobile: `src/app/favorites.tsx`, `src/components/features/taste/TasteRadarChart.tsx`
  - AI: `app/core/taste_dna_service.py` (New Service)
- **Mobile Responsibilities:** Render a radar chart visualizing the 6 flavor dimensions; allow user to fine-tune taste sliders in the profile.
- **NestJS Responsibilities:** Expose `GET /taste-dna/me` and `PATCH /taste-dna/me`; orchestrate taste updates and emit recalculation triggers.
- **FastAPI / AI Responsibilities:** Convert user interactions and questionnaire answers into a normalized 6-dimension vector `[0.0, 1.0]`.
- **Database Changes:**
  - Create collection: `taste_dna_profiles`
  - Fields: `userId (ObjectId, unique)`, `vector: { spicy: Number, sweet: Number, sour: Number, salty: Number, umami: Number, bitter: Number }`, `dietary_constraints: [String]`, `cuisine_weights: Map<String, Number>`, `price_tier: Number`, `updated_at: Date`
- **API Contracts:**
  - `GET /taste-dna/me` -> `{ vector: {...}, dietary_constraints: [...], cuisine_weights: {...} }`
  - `PATCH /taste-dna/me` -> `{ vector?: {...}, dietary_constraints?: [...] }`
- **Dependencies:** `TASK-P0-01`, `TASK-P0-02`
- **Acceptance Criteria:**
  1. Saving questionnaire updates taste profile in MongoDB.
  2. Vector dimensions are strictly clamped between `0.0` and `1.0`.
  3. Mobile radar chart reflects live vector values.
- **Testing Requirements:** Mathematical bounds unit test; API authorization e2e test.
- **Git Branch Suggestion:** `feat/p1-taste-dna-engine`
- **Estimated Effort:** 8 Story Points (2 days)

---

#### [TASK-P1-02] Dynamic Taste DNA Reinforcement Pipeline
- **Business Objective:** Automatically adapt the user's Taste DNA over time as they complete food tours, leave positive reviews, or skip recommendations, applying exponential time decay.
- **Current Status:** NOT IMPLEMENTED.
- **Exact Files / Modules Affected:**
  - Backend: `src/taste-dna/taste-dna.service.ts`, `src/reviews/reviews.service.ts`
  - AI: `app/core/taste_dna_service.py`
- **Mobile Responsibilities:** Receive and display "Taste DNA Updated: +5% Spicy Lover" notification banner after positive dining experiences.
- **NestJS Responsibilities:** When a review with rating >= 4 is posted, invoke AI microservice `POST /v1/taste-dna/reinforce`.
- **FastAPI / AI Responsibilities:** Calculate exponential moving average $\vec{V}_{t} = (1 - \alpha) \vec{V}_{t-1} + \alpha \vec{V}_{\text{restaurant}}$, with decay factor $\alpha = 0.15$.
- **Database Changes:** None (updates existing `taste_dna_profiles`).
- **API Contracts:**
  - `POST /v1/taste-dna/reinforce` -> `{ user_id: string, restaurant_features: {...}, weight: number }`
- **Dependencies:** `TASK-P1-01`
- **Acceptance Criteria:**
  1. Leaving 3 spicy restaurant reviews increases `vector.spicy` measurably.
  2. Negative reviews decrease the corresponding cuisine weight.
- **Testing Requirements:** Algorithmic convergence test in pytest.
- **Git Branch Suggestion:** `feat/p1-taste-dna-reinforcement`
- **Estimated Effort:** 5 Story Points (1.5 days)

---

### PHASE P2: HYBRID AI RECOMMENDATION ENGINE

#### [TASK-P2-01] Multi-Stage Candidate Generation & Content-Based Scorer
- **Business Objective:** Retrieve and rank the top 50 restaurant candidates that match a user's location, Taste DNA, and current ambient context.
- **Current Status:** PARTIALLY COMPLETED. Python AI has TF-IDF cosine similarity on static tags in `recommender.py`.
- **Exact Files / Modules Affected:**
  - AI: `app/core/recommender.py`, `app/api/v1/recommendation.py`
  - Backend: `src/restaurants/restaurants.service.ts`
- **Mobile Responsibilities:** Display personalized "Dành riêng cho khẩu vị của bạn" feed on Home screen.
- **NestJS Responsibilities:** Fetch candidate IDs from AI service, hydrate with real-time restaurant operational status (`isOpen`, `menu`), and deliver to Mobile.
- **FastAPI / AI Responsibilities:** Implement Candidate Retrieval (Stage 1) via Geo/Tag filtering + Content-Based Cosine Match (Stage 2) over Taste DNA and restaurant tag embeddings.
- **Database Changes:** None.
- **API Contracts:**
  - `POST /v1/recommend/hybrid` -> Payload: `{ user_id, user_gps, max_price, current_time, weather }`
- **Dependencies:** `TASK-P0-01`, `TASK-P1-01`
- **Acceptance Criteria:**
  1. Inference latency for 50 candidates is under 80ms.
  2. Completely excludes restaurants that violate user's hard dietary constraints (e.g. non-vegetarian restaurants for strict vegetarians).
- **Testing Requirements:** Pytest benchmark on 10,000 restaurant catalog.
- **Git Branch Suggestion:** `feat/p2-hybrid-candidate-retrieval`
- **Estimated Effort:** 10 Story Points (3 days)

---

#### [TASK-P2-02] Collaborative Filtering & Explainability Layer
- **Business Objective:** Provide recommendations based on "diners like you" patterns and output human-readable explanations ("Được gợi ý vì bạn thích Lẩu Haidilao và trời đang mưa").
- **Current Status:** NOT IMPLEMENTED.
- **Exact Files / Modules Affected:**
  - AI: `app/core/collaborative_filter.py` (New), `app/core/recommender.py`
  - Backend: `src/restaurants/restaurants.service.ts`
  - Mobile: `src/app/(tabs)/index.tsx`, `src/app/restaurant/[id].tsx`
- **Mobile Responsibilities:** Render explanation pill (`✨ Lý do đề xuất: ...`) beneath each recommendation card.
- **NestJS Responsibilities:** Pass explanation text through API contract to mobile UI.
- **FastAPI / AI Responsibilities:** Train TruncatedSVD / Matrix Factorization model on user-restaurant interaction matrix; generate rule-based justification string from dominant feature weights.
- **Database Changes:**
  - Model weights cache in Redis or local pickle artifact `artifacts/svd_model.pkl`.
- **API Contracts:**
  - Response item: `{ id, name, score, match_reasons: ["Hợp khẩu vị cay 85%", "Gần bạn 1.2km"] }`
- **Dependencies:** `TASK-P0-02`, `TASK-P2-01`
- **Acceptance Criteria:**
  1. Every returned recommendation includes at least 1 valid explanation string.
  2. Cold-start users gracefully fall back to Content-Based + Weather explanations.
- **Testing Requirements:** Cold-start unit test; explanation string format test.
- **Git Branch Suggestion:** `feat/p2-collaborative-explainability`
- **Estimated Effort:** 8 Story Points (2 days)

---

### PHASE P3: SMART ROUTE OPTIMIZATION (CORE BUSINESS)

#### [TASK-P3-01] Google OR-Tools Multi-Stop Food Tour Optimizer
- **Business Objective:** Replace naive heuristic stop ordering with a mathematical Traveling Salesperson Problem with Time Windows (TSPTW) solver, minimizing travel distance while respecting restaurant opening hours and stop durations.
- **Current Status:** PARTIALLY COMPLETED. Backend currently sorts by rating and limits to 3 stops without time-window or travel duration optimization.
- **Exact Files / Modules Affected:**
  - AI: `app/core/route_optimizer.py` (New Module), `app/api/v1/routing.py` (New Router)
  - Backend: `src/itineraries/itineraries.service.ts`
  - Mobile: `src/app/ai-planner.tsx`, `src/app/itinerary/[id].tsx`
- **Mobile Responsibilities:** Present step-by-step itinerary with arrival time, dining duration (e.g., 45 mins), and transit time between stops.
- **NestJS Responsibilities:** Forward user prompt, budget, time bounds, and start location to AI route optimizer; persist optimal stop sequence in `itineraries` collection.
- **FastAPI / AI Responsibilities:** Use `ortools.constraint_solver` to solve routing model with distance matrix, time windows, and meal type ordering (Appetizer/Cafe -> Main Meal -> Dessert/Drink).
- **Database Changes:**
  - `ItineraryStop` schema: Add `arrival_time: String`, `dining_duration_mins: Number`, `transit_time_mins: Number`, `distance_to_next_m: Number`.
- **API Contracts:**
  - `POST /v1/routes/optimize` -> Payload: `{ start_location, budget, time_slot, candidate_ids }` -> Response: `{ optimal_stops: [...], total_distance_km, total_time_mins, total_cost }`
- **Dependencies:** `TASK-P0-01`, `TASK-P2-01`
- **Acceptance Criteria:**
  1. OR-Tools solver converges to optimal sequence in < 500ms for 3 to 7 stops.
  2. No stop scheduled outside its `gioMoCua` (opening hours).
  3. Total cost stays within user budget limit.
- **Testing Requirements:** Constraint test suite with conflicting time windows; benchmark test.
- **Git Branch Suggestion:** `feat/p3-ortools-route-optimizer`
- **Estimated Effort:** 13 Story Points (3.5 days)

---

#### [TASK-P3-02] Real-World Distance Matrix & Scientific CO2 Model
- **Business Objective:** Compute true road distances (not bird-flight) and compute verifiable CO₂ savings with documented emission factors.
- **Current Status:** PARTIALLY COMPLETED. Backend uses Haversine formula and flat `0.18 kg CO2/km`.
- **Exact Files / Modules Affected:**
  - AI: `app/core/routing_utils.py`
  - Backend: `src/itineraries/itineraries.service.ts`
  - Mobile: `src/app/itinerary/[id].tsx`
- **Mobile Responsibilities:** Display CO₂ badge with tooltip: *"Dựa trên lộ trình tối ưu xanh: Tiết kiệm 1.8kg CO₂ so với di chuyển ngẫu nhiên"*.
- **NestJS Responsibilities:** Store `co2SavedKg` and routing mode in `Itinerary` schema.
- **FastAPI / AI Responsibilities:** Integrate Open Source Routing Machine (OSRM) table API for road network distance matrix; calculate emission reduction based on baseline detour distance vs optimized sequence using 120g CO₂/km (urban motorbike) and 180g CO₂/km (car).
- **Database Changes:** None.
- **API Contracts:** Documented in `docs/ai/ROUTE_OPTIMIZATION.md`.
- **Dependencies:** `TASK-P3-01`
- **Acceptance Criteria:**
  1. Road distance matches actual street navigation within 10% tolerance.
  2. CO₂ calculation formula documented and tested against baseline.
- **Testing Requirements:** Distance verification tests against Google Maps sample routes.
- **Git Branch Suggestion:** `feat/p3-osrm-co2-scientific`
- **Estimated Effort:** 5 Story Points (1.5 days)

---

### PHASE P4: AI FOOD VISION & NUTRITION RECOGNITION

#### [TASK-P4-01] Expanded Vietnamese Food Dataset & YOLOv11 Fine-Tuning
- **Business Objective:** Expand food visual detection from 5 classes to 20+ prominent Vietnamese dishes with confidence >= 0.70.
- **Current Status:** PARTIALLY COMPLETED. Existing `best.pt` detects 5 dishes (`Banh-Mi`, `Bot Chien`, `Bun`, `Goi-Cuon`, `Pho`).
- **Exact Files / Modules Affected:**
  - AI: `data.yaml`, `app/core/vision_service.py`, `train_yolo.py`
  - Backend: `src/restaurants/restaurants.service.ts`
- **Mobile Responsibilities:** Provide camera / gallery picker in `src/app/ai-nutri.tsx` uploading real image to `POST /restaurants/search-by-image`.
- **NestJS Responsibilities:** Receive multipart image, validate MIME type (`image/jpeg`, `image/png`), proxy to FastAPI `POST /v1/vision/predict`, and search matching restaurants.
- **FastAPI / AI Responsibilities:** Train YOLOv11m on 20 Vietnamese food classes; implement letterbox padding, confidence thresholding (`conf >= 0.65`), and nutrition lookup table.
- **Database Changes:**
  - Collection: `food_nutrition_dictionary` (New collection storing calories, carbs, protein, fat per detected dish).
- **API Contracts:**
  - `POST /v1/vision/predict` -> Response: `{ detected: true, food_name: "Phở Bò", confidence: 0.92, nutrition: { calories: 450, protein: 28, carbs: 55, fat: 12 }, mapped_tags: ["PHỞ", "MÓN NƯỚC"] }`
- **Dependencies:** None. Independent parallel task.
- **Acceptance Criteria:**
  1. mAP@50 >= 0.85 across 20 Vietnamese food classes.
  2. Food camera in mobile correctly identifies dishes and displays nutrition cards.
  3. Low confidence (< 0.65) returns graceful "Chưa nhận diện chính xác món ăn" prompt.
- **Testing Requirements:** Confusion matrix validation; inference speed < 120ms on GPU or < 300ms on CPU.
- **Git Branch Suggestion:** `feat/p4-yolo-food-vision-20class`
- **Estimated Effort:** 13 Story Points (4 days)

---

### PHASE P5: AI NATURAL LANGUAGE FOOD COPILOT

#### [TASK-P5-01] Multi-Intent NLU & Dialogue Orchestrator
- **Business Objective:** Enable users to chat naturally with GastroWise Copilot to search, plan journeys, filter by budget, or book tables with structured intent parsing.
- **Current Status:** PARTIALLY COMPLETED. Simple keyword match in NestJS `chatWithAI` and Python `/chat`.
- **Exact Files / Modules Affected:**
  - AI: `app/core/nlu_service.py` (New), `app/api/v1/copilot.py` (New)
  - Backend: `src/restaurants/restaurants.controller.ts`, `src/restaurants/restaurants.service.ts`
  - Mobile: `src/app/ai-assistant.tsx`
- **Mobile Responsibilities:** Interactive chat interface displaying structured action chips (`[Lên Lộ Trình]`, `[Xem Chi Tiết Quán]`, `[Xác Nhận Đặt Bàn]`).
- **NestJS Responsibilities:** Secure copilot endpoint with user session; validate user confirmation before triggering write actions (e.g. creating itinerary or submitting booking).
- **FastAPI / AI Responsibilities:** Intent classification (`search_food`, `plan_journey`, `ask_nutrition`, `find_nearby`) + Slot filling (cuisine, district, budget, party size) via rule-guided LLM/lightweight transformer.
- **Database Changes:**
  - `chat_sessions` schema: Update `ChatMessage` to support rich action payload.
- **API Contracts:**
  - `POST /restaurants/chat` -> `{ message, history }` -> `{ reply, intent, entities, action_card }`
- **Dependencies:** `TASK-P2-01`, `TASK-P3-01`
- **Acceptance Criteria:**
  1. Correctly classifies intents with > 90% accuracy across 50 test prompts.
  2. Modifying or deleting data ALWAYS requests explicit user confirmation.
- **Testing Requirements:** Dialogue test scenarios in pytest and NestJS Jest e2e.
- **Git Branch Suggestion:** `feat/p5-nlu-copilot-orchestration`
- **Estimated Effort:** 10 Story Points (3 days)

---

### PHASE P6: FEEDBACK LOOP & CONTINUOUS LEARNING

#### [TASK-P6-01] Automated Feedback Processing & Model Monitoring
- **Business Objective:** Continually track recommendation Click-Through Rate (CTR), itinerary completion rate, and model drift without manual interventions.
- **Current Status:** NOT IMPLEMENTED.
- **Exact Files / Modules Affected:**
  - Backend: `src/interactions/interactions.service.ts`
  - AI: `app/core/monitoring.py` (New), `app/tasks/evaluate_models.py`
- **Mobile Responsibilities:** Fire feedback signal when recommendation is tapped vs ignored.
- **NestJS Responsibilities:** Aggregate interaction metrics daily; expose analytics endpoint for Admin Portal.
- **FastAPI / AI Responsibilities:** Compute Precision@K, NDCG@K, and novelty metrics on historical offline logs.
- **Database Changes:**
  - Collection: `recommendation_metrics` (Daily metrics summary).
- **API Contracts:**
  - `GET /admin/analytics/recommendations`
- **Dependencies:** `TASK-P0-02`, `TASK-P2-01`
- **Acceptance Criteria:**
  1. Offline evaluation script executes and generates markdown performance report.
  2. Daily CTR metric computed accurately from `user_interactions`.
- **Testing Requirements:** Synthetic user log evaluation test.
- **Git Branch Suggestion:** `feat/p6-feedback-evaluation-pipeline`
- **Estimated Effort:** 8 Story Points (2 days)

---

### PHASE P7: SYSTEM INTEGRATION, SECURITY & PRODUCTION QA

#### [TASK-P7-01] Internal AI Gateway Security & Service-to-Service Auth
- **Business Objective:** Protect AI Microservice endpoints from unauthorized access and establish encrypted internal communication between NestJS and Python FastAPI.
- **Current Status:** PARTIALLY COMPLETED. AI service has open CORS and no shared secret guard.
- **Exact Files / Modules Affected:**
  - Backend: `src/restaurants/restaurants.service.ts`, `src/reviews/reviews.service.ts`
  - AI: `app/core/security.py` (New), `main.py`
- **Mobile Responsibilities:** None (mobile only talks to NestJS Gateway).
- **NestJS Responsibilities:** Inject `X-Internal-AI-Key: Bearer <secret>` header into all Axios requests directed to AI Microservice.
- **FastAPI / AI Responsibilities:** Implement `Security(api_key_header)` dependency; reject requests missing or possessing invalid internal key with HTTP 403 Forbidden.
- **Database Changes:** None.
- **API Contracts:**
  - Header: `X-Internal-AI-Key: <SECRET_STRING>`
- **Dependencies:** All previous tasks.
- **Acceptance Criteria:**
  1. Direct external curl to FastAPI returns 403.
  2. NestJS requests pass authentication seamlessly.
- **Testing Requirements:** Security penetration test in pytest and Jest.
- **Git Branch Suggestion:** `feat/p7-ai-internal-security`
- **Estimated Effort:** 3 Story Points (1 day)

---

#### [TASK-P7-02] End-to-End Performance & Load Hardening
- **Business Objective:** Ensure the complete ecosystem supports 200 concurrent requests/sec with p95 latency < 250ms under peak weekend dining hours.
- **Current Status:** NOT IMPLEMENTED.
- **Exact Files / Modules Affected:**
  - Backend: All controllers (`ThrottlerModule`, Caching)
  - AI: `main.py`, Gunicorn / Uvicorn worker settings
- **Mobile Responsibilities:** Verify network timeout handling and offline banners.
- **NestJS Responsibilities:** Cache static restaurant and category data in Redis / in-memory cache; tune MongoDB connection pool (min: 10, max: 100).
- **FastAPI / AI Responsibilities:** Run Uvicorn with 4 worker processes; pre-warm PyTorch model weights on startup.
- **Database Changes:** Create compound query indexes on MongoDB.
- **Dependencies:** `TASK-P7-01`
- **Acceptance Criteria:**
  1. k6 load test passes 200 RPS with 0% error rate.
  2. p95 response time under 250ms for recommendation and search.
- **Testing Requirements:** k6 load test script execution.
- **Git Branch Suggestion:** `feat/p7-load-performance-hardening`
- **Estimated Effort:** 5 Story Points (1.5 days)

---

## 3. Dependency Graph & Parallel Development Paths

```
[TASK-P0-01: Geospatial & Schema Normalization]
      │
      ├─────────────────────────────────────────┐
      ▼                                         ▼
[TASK-P0-02: Interaction Pipeline]        [TASK-P4-01: YOLOv11 Food Vision] (Parallel Track A)
      │                                         │
      ▼                                         │
[TASK-P1-01: Taste DNA Profiling]               │
      │                                         │
      ├────────────────────────┐                │
      ▼                        ▼                │
[TASK-P1-02: Taste Reinf.] [TASK-P2-01: Hybrid Reco Engine]
                               │                │
      ┌────────────────────────┤                │
      ▼                        ▼                │
[TASK-P2-02: CF & Explain.] [TASK-P3-01: OR-Tools Route Opt]
      │                        │                │
      │                        ▼                │
      │                  [TASK-P3-02: OSRM & Scientific CO2]
      │                        │                │
      ▼                        ▼                ▼
[TASK-P5-01: AI Natural Language Copilot Orchestration]
      │
      ▼
[TASK-P6-01: Automated Feedback & Model Evaluation]
      │
      ▼
[TASK-P7-01: AI Gateway Security] ──► [TASK-P7-02: Load Hardening]
```

---

## 4. Immediate Development Action: The First 3 Tasks

The following three tasks have zero mutual blockers and can be commenced immediately in parallel:

1. **TASK-P0-01 (Geospatial & Schema Normalization):**
   - **Lead:** Backend Lead
   - **Focus:** Add `location: { type: 'Point', coordinates: [lon, lat] }` with `2dsphere` index to `Restaurant` schema and migrate existing data.
2. **TASK-P4-01 (YOLOv11 20-Class Food Recognition):**
   - **Lead:** AI / Computer Vision Engineer
   - **Focus:** Expand dataset from 5 classes to 20 classes and train `best.pt` with confidence thresholds.
3. **TASK-P1-01 (Taste DNA 6-D Vector Profile):**
   - **Lead:** Mobile & Fullstack Engineer
   - **Focus:** Build normalized `taste_dna_profiles` collection, mobile radar visualizer, and questionnaire synchronization.

