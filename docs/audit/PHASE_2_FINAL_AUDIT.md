# GASTROWISE – PHASE 2 FINAL ARCHITECTURE & IMPLEMENTATION AUDIT REPORT

**Audit Date:** 2026-11-10  
**Lead Auditor:** Independent Principal Software Architect & QA Lead  
**Scope:** `KLTN-123-GastroWise-Mobile`, `KLTN-123-GastroWise-BE`, `KLTN-123-GastroWise-AI`  
**Standard:** Zero-Trust Ground-Truth Verification against actual code, schemas, and test execution.

---

## 1. Executive Summary

GastroWise is an AI-powered personalized food recommendation and food tour journey optimization platform. The system operates on a 3-tier architecture:
- **Mobile Client:** React Native (Expo SDK 57, Expo Router 57, Zustand 5, Svg)
- **Gateway Backend:** NestJS 10, Mongoose, Express, JWT, Multer
- **AI Microservice:** Python 3.12, FastAPI, PyTorch, YOLOv11, Scikit-Learn, Google OR-Tools

### Key Audit Findings:
1. **Architectural Governance:** Mobile communicates **strictly** through NestJS gateway APIs; no direct calls to Python AI microservice exist in mobile code.
2. **Ground-Truth Implementation Reality vs Prior Claims:**
   - **`TASK-P0-01` (GeoJSON & 2dsphere):** **VERIFIED_COMPLETE**. Native Point schema, 2dsphere index, `$geoNear` aggregation pipeline, and boot migration verified.
   - **`TASK-P0-02` (Telemetry Pipeline):** **VERIFIED_COMPLETE**. `user_interactions` collection with compound indexes, batch flush API, and mobile queueing tracker verified.
   - **`TASK-P1-01` (Taste DNA Profile Engine):** **VERIFIED_COMPLETE**. Continuous 6-D vector $[0.0, 1.0]$, SVG Hexagonal Radar Chart, onboarding quiz, and sliders verified.
   - **`TASK-P1-02` (Dynamic EMA Reinforcement):** **VERIFIED_COMPLETE**. Reviews $\ge 4\star$ and itinerary completion dynamically update Taste DNA vector via EMA ($\alpha = 0.12 - 0.15$). Tested with Jest (5/5 passed).
   - **`TASK-P2-01` & `TASK-P2-02` (Hybrid Recommender & Collaborative Filtering):** **VERIFIED_COMPLETE**. 4-stage funnel (Geo/dietary hard filter $\to$ Taste DNA 6-D cosine $\to$ TruncatedSVD collaborative filtering $\to$ Environmental context boost) with explainability pills and Mobile carousel. Tested in Python (5/5 passed) and NestJS (6/6 passed).
   - **`TASK-P3-01` (OR-Tools Route Optimizer):** **VERIFIED_COMPLETE**. TSPTW solver with time windows, dining durations, meal sequencing (Starter $\to$ Main $\to$ Dessert), and blended CO₂ model (0.104 kg/km). Tested with Jest (3/3 passed).
   - **`TASK-P3-02` (Real-World Distance Matrix):** **PARTIALLY_COMPLETE**. Uses geometric detour factor ($1.35\times$ Haversine) and mathematical CO₂ calculations rather than live OSRM table API.
   - **`TASK-P4-01` (Food Recognition & Nutrition):** **PARTIALLY_COMPLETE**. Vision pipeline, CLAHE contrast enhancement, OOD rejection ($\theta = 0.45$), and 20-dish nutrition dictionary are fully implemented. **However**, the actual YOLO weights `best.pt` and `data.yaml` are only trained on 5 classes (`Banh-Mi`, `Bot Chien`, `Bun`, `Goi-Cuon`, `Pho`), not 20 classes.
   - **`TASK-P5-01` (AI Food Copilot):** **VERIFIED_COMPLETE**. NLU 5-intent classification, slot filling (district, budget), structured Action Cards (Nutrition breakdown, Tour Planner, Map Explore), and Mobile interactive UI verified.
   - **`TASK-P6-01` (Continuous Feedback & Metrics):** **PARTIALLY_COMPLETE**. Interaction telemetry collection and online EMA updates exist, but automated offline NDCG@K, Precision@K, daily CTR calculations, and cronjobs are **NOT_IMPLEMENTED**.
   - **`TASK-P7-01` (Production Hardening & QA):** **PARTIALLY_COMPLETE**. Unit tests for P0-P5 exist and pass (14/14 BE tests), but critical security gaps exist in RBAC and endpoint ownership protection.

---

## 2. Granular Task Verification Matrix (P0–P7)

| Task ID | Task Objective | Expected Deliverable | Actual Code Verification | Verified Status |
| :--- | :--- | :--- | :--- | :---: |
| **`TASK-P0-01`** | Geospatial GeoJSON Normalization | GeoJSON Point `{ type, coordinates: [lon, lat] }`, 2dsphere index, `$geoNear` query | `restaurant.schema.ts` (L21-36, L72), `restaurants.service.ts` (`findNearby`, `ensureGeoJsonLocations`), `explore.tsx`. | **VERIFIED_COMPLETE** |
| **`TASK-P0-02`** | Interaction Telemetry Pipeline | `user_interactions` schema, batch API, client tracker | `interaction.schema.ts`, `interactions.service.ts` (`recordBatch`, `getMatrixExport`), `tracker.ts`. | **VERIFIED_COMPLETE** |
| **`TASK-P1-01`** | Normalized Taste DNA 6-D Profile | Continuous vector $[0.0, 1.0]$, Radar chart UI, Quiz mapping | `taste-dna.schema.ts`, `taste-dna.service.ts`, `taste-dna.tsx` (SVG Polygon, sliders, confidence). | **VERIFIED_COMPLETE** |
| **`TASK-P1-02`** | Dynamic Taste DNA Reinforcement | Online EMA updates on positive review and itinerary finish | `reviews.service.ts` (L147), `itineraries.service.ts` (L385). Tested in `taste-dna.service.spec.ts`. | **VERIFIED_COMPLETE** |
| **`TASK-P2-01`** | Candidate Generation & Content Scorer | Hard filtering (dietary, price, geo), 6-D cosine similarity | `recommender.py` (`compute_restaurant_flavor_vector`, `compute_env_context`, `recommend_hybrid`). | **VERIFIED_COMPLETE** |
| **`TASK-P2-02`** | Collaborative Filtering & Explanations | TruncatedSVD matrix factorization, explainability pills | `collaborative_filter.py`, `recommender.py`, `GET /restaurants/recommended`, `(tabs)/index.tsx`. | **VERIFIED_COMPLETE** |
| **`TASK-P3-01`** | Google OR-Tools Food Tour Optimizer | TSPTW solver, time windows, dining durations, CO₂ model | `route_optimizer.py`, `routing.py`, `itineraries.service.ts`, `itinerary/[id].tsx`. | **VERIFIED_COMPLETE** |
| **`TASK-P3-02`** | Real-World Distance Matrix & CO₂ | Live OSRM distance matrix, scientific CO₂ validation | Uses $1.35\times$ urban detour factor; blended CO₂ factor (0.104 kg/km) implemented. Live OSRM API missing. | **PARTIALLY_COMPLETE** |
| **`TASK-P4-01`** | YOLOv11 20-Class Food Recognition | YOLOv11m trained on 20 dishes, CLAHE, nutrition facts | Pipeline & nutrition table (20 dishes) complete; `best.pt` model weights and `data.yaml` only cover 5 classes. | **PARTIALLY_COMPLETE** |
| **`TASK-P5-01`** | Multi-Intent NLU & Dialogue Copilot | 5-intent NLU, slot filling, interactive Action Cards | `nlu_service.py`, `copilot.py`, `POST /restaurants/chat`, `ai-assistant.tsx` Action Cards. | **VERIFIED_COMPLETE** |
| **`TASK-P6-01`** | Continuous Learning & Metric Jobs | Offline NDCG@K, Precision@K, CTR cronjobs, drift alert | Interaction collection & EMA updates exist. Offline evaluation scripts and cron jobs are missing. | **PARTIALLY_COMPLETE** |
| **`TASK-P7-01`** | Security, RBAC & Production QA | RBAC guards, ownership check, internal AI auth, E2E | JWT auth & 14 unit tests pass. RBAC guards, ownership checks, and AI internal secret are missing. | **PARTIALLY_COMPLETE** |

---

## 3. Cross-Service Architecture Assessment

| Architecture Dimension | Score (0–10) | Evaluation & Evidence |
| :--- | :---: | :--- |
| **1. Mobile Architecture** | **8.5 / 10** | Clean Expo Router file-system structure, Zustand store, atomic UI constants, robust Axios interceptors with SecureStore persistence. Strict compliance with Gateway boundary (0 direct calls to AI microservice). Weakness: Lacks automated unit/component test harness. |
| **2. Backend Architecture** | **8.0 / 10** | Modular NestJS tree, clear separation of concerns, DTOs with `class-validator`, Mongoose schemas, graceful fallback logic when AI is offline. Weakness: Critical security gaps in authorization/RBAC guards on administrative and mutation routes. |
| **3. AI Microservice Architecture** | **8.0 / 10** | High-performance FastAPI setup, modular `/app/core` separation (recommender, route_optimizer, nlu_service, collaborative_filter, vision_service), graceful error handling. Weakness: No internal service authentication, missing `ortools` in `requirements.txt`. |
| **4. Database Design** | **8.0 / 10** | GeoJSON Point with `2dsphere` index, compound indexes on `user_interactions`, unique constraints on users and taste profiles. Weakness: Missing indexes on foreign keys (`Review.restaurantId`, `Itinerary.user_id`) causing collection scans. |
| **5. API Contract Consistency** | **8.5 / 10** | Pydantic schemas in FastAPI mirror TypeScript DTOs in NestJS. Unified response structure across search, recommendation, routing, and chat. |
| **6. AI Recommendation Quality** | **8.5 / 10** | Production-grade 4-stage funnel. Real mathematical formulation (Cosine Similarity + TruncatedSVD + Weather boost - Distance penalty). Human-readable explainability pills. |
| **7. Route Optimization Correctness** | **8.5 / 10** | Mathematical formulation of TSPTW using Google OR-Tools constraint solver. Time window satisfaction, dwell durations, and gastronomic progression (Starter $\to$ Main $\to$ Dessert). |
| **8. Security Maturity** | **5.0 / 10** | **POOR**. Unprotected routes in `users.controller.ts` (`GET /users`, `PATCH /users/:id`, `DELETE /users/:id`) and `itineraries.controller.ts` (`GET /all`, `PATCH /:id`, `DELETE /:id`). Hardcoded MongoDB Atlas connection string with cleartext credentials in `config.py`. Wildcard CORS with credentials enabled. |
| **9. Testing Maturity** | **6.5 / 10** | Phase 2 features have verified unit tests in NestJS (14/14 tests pass) and Python (7 tests pass). However, legacy boilerplate spec files fail, Mobile has 0 unit tests, and no E2E pipeline exists. |
| **10. Production Readiness** | **6.5 / 10** | Core algorithms and mobile experience are operational and attractive. However, production deployment is **BLOCKED** until critical security vulnerabilities (auth bypass, hardcoded DB credentials, missing RBAC) are patched. |

---

## 4. Business Flow Verification & Traceability

### Flow 1: Registration → Taste DNA Quiz → Personalized Recommendations
1. **Registration:** `KLTN-123-GastroWise-Mobile/src/app/(auth)/register.tsx` $\to$ `POST /auth/register` $\to$ Bcrypt hash $\to$ JWT generated $\to$ Saved in SecureStore.
2. **Taste DNA Survey:** `src/app/profile/taste-dna.tsx` $\to$ `POST /taste-dna/quiz` $\to$ `TasteDnaService.submitQuiz()` maps responses into 6-D vector $\to$ Persisted in `taste_dna_profiles`.
3. **Personalized Feed:** `src/app/(tabs)/index.tsx` $\to$ `GET /restaurants/recommended?lat=...&lon=...` $\to$ NestJS extracts vector $\to$ FastAPI `POST /v1/recommendation/recommend/hybrid` $\to$ 4-Stage scoring $\to$ Hydrated with MongoDB data $\to$ Rendered in Mobile carousel with `% Hợp gu` and explainability pills.
- **Traceability Status:** **VERIFIED & OPERATIONAL**.

### Flow 2: Route Optimization & Food Tour Generation
1. **User Input:** `src/app/ai-planner.tsx` takes start location, budget, district, meal count $\to$ `POST /itineraries/generate`.
2. **AI Routing:** `ItinerariesService` calls FastAPI `POST /v1/routing/routes/optimize` $\to$ OR-Tools solves TSPTW with time windows $\to$ Generates timetable (arrival, dining, transit) $\to$ Computes CO₂ saved ($0.104 \text{ kg/km}$).
3. **Mobile Display & Execution:** `src/app/itinerary/[id].tsx` displays route, stops, timetable badges, and CO₂ savings. User taps "Hoàn thành chuyến đi" $\to$ `PATCH /itineraries/:id` $\to$ Kích hoạt `applyFeedbackEma` tăng cường Taste DNA profile.
- **Traceability Status:** **VERIFIED & OPERATIONAL**.

### Flow 3: AI Food Copilot Dialogue & Action Execution
1. **Chat Input:** `src/app/ai-assistant.tsx` sends prompt to `POST /restaurants/chat`.
2. **NLU Processing:** FastAPI `nlu_service.py` classifies intent (`ask_nutrition`, `plan_journey`, `find_nearby`, `search_food`), extracts slots (district, budget, dish) $\to$ Builds structured Action Card.
3. **Action Card UI:** Mobile renders rich interactive cards (Nutrition macro card with calories/protein/carbs/fat; Tour Planner card with direct navigation button).
- **Traceability Status:** **VERIFIED & OPERATIONAL**.

