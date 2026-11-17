# GASTROWISE – SPRINT 1 REMEDIATION & STABILIZATION PLAN
**Prioritized Engineering Roadmap**  
**Role:** Principal Software Architect & QA Lead  
**Planning Date:** November 17, 2026  
**Scope:** Immediate stabilization prior to Sprint 1 Business Feature rollout

---

## 1. SPRINT 1 OBJECTIVES & DEPENDENCY TOPOLOGY

Sprint 1 focuses on eliminating critical security vulnerabilities, repairing cross-tier API contracts, fixing the 5.4★ rating normalization defect, and establishing robust test automation across all repositories.

```mermaid
graph TD
    subgraph Stream A: Backend Security & Gateway (Independent)
        T1["TASK-BE-01 (P0): Secure Reviews Mutation & Matrix Export<br/>(reviews.controller.ts, interactions.controller.ts)"]
        T2["TASK-BE-02 (P0): Align AI Gateway URLs & Global Prefix<br/>(restaurants.service.ts, main.ts)"]
        T3["TASK-BE-03 (P1): Untrack remediate-config.js<br/>(scripts/remediate-config.js, .gitignore)"]
    end

    subgraph Stream B: AI Microservice Engine & Security (Independent)
        T4["TASK-AI-01 (P0): Normalize Rating Scale in Mongo Loader<br/>(app/db/mongo.py, test_hybrid_recommendation.py)"]
        T5["TASK-AI-02 (P0): Enforce Internal AI Key & Restrict CORS<br/>(main.py, app/api/v1/router.py)"]
        T6["TASK-AI-03 (P1): Decouple Nutrition Data from OpenCV<br/>(app/core/nlu_service.py, nutrition_data.py)"]
    end

    subgraph Stream C: Mobile & Web Client Alignment (Independent)
        T7["TASK-MOB-01 (P1): Normalize Stop Properties & Untrack .env<br/>(itinerary/[id].tsx, .gitignore)"]
    end

    subgraph Stream D: Manual DBA Operations (Independent of Source Code)
        T8["TASK-DBA-01: Invalidate Historical Atlas User 'thienthien'"]
        T9["TASK-DBA-02: Configure IP Access List on MongoDB Atlas"]
    end

    T1 --> T2
    T4 --> T5
    T8 -.-> T3
```

---

## 2. DETAILED TASK SPECIFICATIONS

### TASK-BE-01: Fix Broken Access Control on Reviews & User Interaction Matrix
- **Priority:** P0 (Critical Security Blocker)
- **Component:** `KLTN-123-GastroWise-BE`
- **Files Affected:** 
  - `src/reviews/reviews.controller.ts`
  - `src/reviews/reviews.service.ts`
  - `src/interactions/interactions.controller.ts`
- **Objectives:**
  1. Add `@UseGuards(JwtAuthGuard)` to `DELETE /reviews/:id` and `PATCH /reviews/:id`.
  2. Implement author ownership validation: verify `review.userId.toString() === req.user.sub` or `req.user.role === 'admin'`.
  3. Add `@UseGuards(JwtAuthGuard, RolesGuard)` and `@Roles('admin')` to `POST /reviews/migrate-sentiment` and `GET /interactions/matrix`.
- **Dependencies:** None.
- **Estimated Effort:** 2.0 hours.
- **Acceptance Criteria:** Unauthenticated requests receive 401 Unauthorized; cross-tenant review deletions receive 403 Forbidden.
- **Verification Method:** Jest integration test in `reviews.controller.spec.ts`.

---

### TASK-BE-02: Fix Cross-Tier API Routing Discrepancies & Global Prefix
- **Priority:** P0 (Critical Architecture Blocker)
- **Component:** `KLTN-123-GastroWise-BE`
- **Files Affected:**
  - `src/restaurants/restaurants.service.ts:448, 547, 969`
  - `src/main.ts`
- **Objectives:**
  1. Update line 448 from `${aiBaseUrl}/v1/recommendation/recommend/hybrid` to `${aiBaseUrl}/recommend/hybrid`.
  2. Update line 547 from `${aiBaseUrl}/v1/recommendation/cf/train` to `${aiBaseUrl}/cf/train`.
  3. Update line 969 from `${aiBaseUrl}/v1/copilot/message` to `${aiBaseUrl}/copilot/message`.
  4. In `main.ts`, add `app.setGlobalPrefix('api/v1', { exclude: ['uploads/(.*)'] })`.
- **Dependencies:** None.
- **Estimated Effort:** 1.5 hours.
- **Acceptance Criteria:** `GET /restaurants/recommended` returns genuine AI scores from FastAPI with zero 404 fallbacks.
- **Verification Method:** Integration test calling `RestaurantsService.getRecommendations()`.

---

### TASK-AI-01: Normalize Foody 0–10 Rating Scale in AI Dataset Loader
- **Priority:** P0 (Quality & Algorithmic Blocker)
- **Component:** `KLTN-123-GastroWise-AI`
- **Files Affected:**
  - `app/db/mongo.py:58`
  - `test_hybrid_recommendation.py`
- **Objectives:**
  1. In `load_dataset_from_mongo()`, normalize `diemTrungBinh` to a 0–5 scale:
     ```python
     temp_df['rating'] = temp_df['diemTrungBinh'].apply(
         lambda r: round(float(r) / 2.0, 1) if float(r) > 5.0 else float(r)
     )
     ```
  2. Clip composite score in `recommender.py` to $[0.0, 1.0]$.
  3. Add regression assertions to `test_hybrid_recommendation.py`.
- **Dependencies:** None.
- **Estimated Effort:** 1.0 hour.
- **Acceptance Criteria:** `df['rating'].max() <= 5.0`. Restaurant with rating 5.4 becomes 2.7★ and does NOT receive "Đánh giá xuất sắc".
- **Verification Method:** Execute `test_hybrid_recommendation.py`.

---

### TASK-AI-02: Enforce Internal AI Mutual Authentication & Restrict CORS
- **Priority:** P0 (Critical Security Blocker)
- **Component:** `KLTN-123-GastroWise-AI` & `KLTN-123-GastroWise-BE`
- **Files Affected:**
  - `KLTN-123-GastroWise-AI/main.py`
  - `KLTN-123-GastroWise-AI/app/core/auth.py` (new)
  - `KLTN-123-GastroWise-BE/src/restaurants/restaurants.service.ts`
- **Objectives:**
  1. Create FastAPI dependency `verify_internal_key` validating header `X-Internal-AI-Key: Bearer <secret>` using `hmac.compare_digest`.
  2. Apply dependency to all FastAPI v1 routers.
  3. Restrict `allow_origins` in `main.py` to trusted backend IPs/hosts.
  4. Inject `X-Internal-AI-Key` in NestJS `HttpService` outbound requests.
- **Dependencies:** `AI_SECRET_KEY` in `.env`.
- **Estimated Effort:** 2.5 hours.
- **Acceptance Criteria:** Requests to FastAPI without matching key return 401 Unauthorized.
- **Verification Method:** Test client request with invalid vs valid key.

---

### TASK-AI-03: Decouple NLP Dialogue Service from OpenCV Dependency
- **Priority:** P1 (High Quality)
- **Component:** `KLTN-123-GastroWise-AI`
- **Files Affected:**
  - `app/core/nutrition_data.py` (new)
  - `app/core/vision_service.py`
  - `app/core/nlu_service.py`
- **Objectives:**
  1. Extract `VIETNAMESE_FOOD_NUTRITION` dictionary into `app/core/nutrition_data.py`.
  2. Import dictionary in both `vision_service.py` and `nlu_service.py`.
  3. Ensure `nlu_service.py` imports no computer vision packages.
- **Dependencies:** None.
- **Estimated Effort:** 0.5 hour.
- **Acceptance Criteria:** `test_nlu_copilot.py` passes without `cv2` installed.
- **Verification Method:** Run `python test_nlu_copilot.py`.

---

### TASK-MOB-01: Normalize Itinerary Stop Properties & Untrack Mobile `.env`
- **Priority:** P1 (Data Consistency)
- **Component:** `KLTN-123-GastroWise-Mobile` & `KLTN-123-GastroWise-BE`
- **Files Affected:**
  - `KLTN-123-GastroWise-Mobile/src/app/itinerary/[id].tsx`
  - `KLTN-123-GastroWise-Mobile/.gitignore`
  - `KLTN-123-GastroWise-BE/src/itineraries/itineraries.service.ts:366`
- **Objectives:**
  1. Standardize stop property names across BE and Mobile to `dining_duration_mins` and `transit_time_mins`.
  2. Untrack `.env` in `KLTN-123-GastroWise-Mobile` and add `.env` to `.gitignore`.
- **Dependencies:** None.
- **Estimated Effort:** 1.0 hour.
- **Acceptance Criteria:** Itinerary stops save and render accurate custom dining and transit durations without falling back to schema defaults.
- **Verification Method:** Create and inspect itinerary in mobile emulator.

---

## 3. MANUAL DBA OPERATIONS (ATLAS CLOUD CONSOLE)

These operations cannot be performed via code changes and require DBA intervention on MongoDB Atlas:

1. **TASK-DBA-01: Invalidate Historical Database User `thienthien`**
   - **Console Location:** MongoDB Atlas Console $\rightarrow$ Security $\rightarrow$ Database Access.
   - **Action:** Delete user `thienthien` or rotate its password to prevent exploitation of historical Git commit leaks.
   - **Verification:** Run connection test using old credentials; verify Atlas rejects connection with code 18.

2. **TASK-DBA-02: Configure IP Access List Restrictions**
   - **Console Location:** MongoDB Atlas Console $\rightarrow$ Security $\rightarrow$ Network Access.
   - **Action:** Replace wildcard `0.0.0.0/0` with static production gateway IP addresses and developer VPN/NAT CIDRs.
   - **Verification:** Confirm connections from unauthorized public IPs are blocked at TCP/TLS handshake.

---

## 4. THREE INDEPENDENT TASKS READY FOR PARALLEL EXECUTION

The following three tasks have zero overlapping files and can be assigned to three separate engineers immediately:

| Stream | Task ID | Engineer Role | Files Owned | Acceptance Condition |
| :--- | :--- | :--- | :--- | :--- |
| **Stream 1** | **TASK-BE-01** | Backend Security Engineer | `KLTN-123-GastroWise-BE/src/reviews/*`<br/>`KLTN-123-GastroWise-BE/src/interactions/*` | Anonymous review deletion & matrix export return 401/403. |
| **Stream 2** | **TASK-AI-01** | AI Recommendation Engineer | `KLTN-123-GastroWise-AI/app/db/mongo.py`<br/>`KLTN-123-GastroWise-AI/test_hybrid_recommendation.py` | Maximum rating $\le 5.0$; 5.4 rating converts to 2.7★. |
| **Stream 3** | **TASK-MOB-01** | Mobile Frontend Engineer | `KLTN-123-GastroWise-Mobile/src/app/itinerary/*`<br/>`KLTN-123-GastroWise-Mobile/.gitignore` | Stop durations render properly; `.env` is removed from Git tracking. |

