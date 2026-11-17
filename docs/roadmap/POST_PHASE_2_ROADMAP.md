# GASTROWISE – POST-PHASE 2 IMPLEMENTATION ROADMAP & PRODUCTION HARDENING

**Document Version:** 1.0.0  
**Status:** PROPOSED & READY FOR APPROVAL  
**Author:** Principal Software Architect & QA Lead  
**Governing Rule:** No development shall commence on post-Phase 2 tasks without explicit stakeholder authorization.

---

## 1. Overview & Classification of Remaining Work

Based on the Phase 2 zero-trust architectural audit, the remaining requirements are categorized into:
- **Category A: Mandatory Security & Scalability Fixes (P0 - Immediate Blockers)**
- **Category B: Core Functional Completion (P1 - Algorithm & Model Scope)**
- **Category C: Observability & Quality Assurance (P2 - CI/CD & Client Polish)**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       POST-PHASE 2 DEPENDENCY GRAPH                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [TASK-SEC-01] Credential Scrub ──┐                                         │
│                                    ▼                                        │
│  [TASK-SEC-02] RBAC & Guard Fix ──────► [Production Gateway Deployment]    │
│                                    ▲                                        │
│  [TASK-PERF-01] Database Indexes ──┘                                        │
│                                                                             │
│  [TASK-DEP-01] requirements.txt ─────► [TASK-P3-03] OSRM Road Matrix        │
│                                                                             │
│  [TASK-P4-02] YOLO 20-Class Dataset ─► [TASK-P4-03] Vision Model Training   │
│                                                                             │
│  [TASK-P6-02] Metrics Aggregation ───► [Admin Portal Analytics Dashboard]   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Granular Task Breakdown

### CATEGORY A: MANDATORY SECURITY & SCALABILITY FIXES

#### [TASK-SEC-01] Cleartext MongoDB Credential Scrub & Config Hardening
- **Objective:** Eliminate hardcoded Atlas credentials from code and enforce strict environment injection.
- **Affected Files:**
  - AI: `KLTN-123-GastroWise-AI/app/config.py`
  - Documentation: `.env.example` across all services
- **Implementation:**
  1. Rotate database password on MongoDB Atlas.
  2. Remove fallback URI from `app/config.py`. If `MONGODB_URI` is unset, raise `RuntimeError("MONGODB_URI environment variable is required")`.
- **Acceptance Criteria:**
  - Zero plain-text credentials exist across all Git tracked files.
  - Service boots safely when environment variables are injected.
- **Effort Estimate:** 2 Story Points (0.5 day)
- **Execution Mode:** Sequential (Pre-requisite for all deployments).

---

#### [TASK-SEC-02] Authentication & Role-Based Access Control (RBAC) Hardening
- **Objective:** Secure unprotected administrative and mutation endpoints across all backend controllers.
- **Affected Files:**
  - BE: `src/auth/roles.guard.ts` (New), `src/auth/roles.decorator.ts` (New)
  - BE: `src/users/users.controller.ts`
  - BE: `src/restaurants/restaurants.controller.ts`
  - BE: `src/itineraries/itineraries.controller.ts`
  - BE: `src/main.ts` (CORS origin whitelist)
- **Implementation:**
  1. Create `@Roles('admin', 'owner', 'user')` decorator and `RolesGuard`.
  2. Protect `GET /users`, `PATCH /users/:id`, `DELETE /users/:id` with `@UseGuards(JwtAuthGuard, RolesGuard)` and `@Roles('admin')`.
  3. Protect `GET /itineraries/all`, `PATCH /itineraries/:id`, `DELETE /itineraries/:id` with admin authorization.
  4. Protect `POST /restaurants`, `PATCH /restaurants/:id`, `DELETE /restaurants/:id` with owner/admin checks.
  5. Replace wildcard CORS `origin: "*"` with environment variable whitelist.
- **Acceptance Criteria:**
  - Unauthenticated requests to user listing, restaurant mutation, and itinerary deletion return `401 Unauthorized`.
  - Non-admin requests to administrative routes return `403 Forbidden`.
- **Testing Requirements:** NestJS e2e controller integration tests.
- **Effort Estimate:** 5 Story Points (1.5 days)
- **Execution Mode:** Sequential.

---

#### [TASK-PERF-01] Database Foreign Key & Search Index Remediation
- **Objective:** Eliminate full collection scans ($O(N)$) on restaurant reviews, user itineraries, and restaurant searches.
- **Affected Files:**
  - BE: `src/reviews/schemas/review.schema.ts`
  - BE: `src/itineraries/schemas/itinerary.schema.ts`
  - BE: `src/restaurants/schemas/restaurant.schema.ts`
- **Implementation:**
  1. Add `ReviewSchema.index({ restaurantId: 1, createdAt: -1 })`.
  2. Add `ItinerarySchema.index({ user_id: 1, createdAt: -1 })`.
  3. Add `RestaurantSchema.index({ status: 1, diemTrungBinh: -1 })`.
  4. Add compound text index `RestaurantSchema.index({ tenQuan: 'text', tags: 'text' })`.
- **Acceptance Criteria:**
  - `explain("executionStats")` shows `IXSCAN` (Index Scan) rather than `COLLSCAN` for review lookups by restaurant and itinerary lookups by user.
- **Effort Estimate:** 3 Story Points (1 day)
- **Execution Mode:** Can run in parallel with `TASK-SEC-02`.

---

#### [TASK-DEP-01] Dependency Pruning & Path Alias Normalization
- **Objective:** Ensure reproducible clean environment builds and fix Jest import errors.
- **Affected Files:**
  - BE: `src/auth/auth.controller.ts`, `src/auth/auth.module.ts`, `src/auth/auth.service.ts`
  - BE: `src/users/schemas/user-interaction.schema.ts` (Delete orphan)
  - AI: `KLTN-123-GastroWise-AI/requirements.txt`
- **Implementation:**
  1. Add `ortools>=9.8.0` to `requirements.txt`.
  2. Normalize `from 'src/users/...'` to `from '../users/...'` in `src/auth`.
  3. Remove legacy orphan schema `user-interaction.schema.ts`.
- **Acceptance Criteria:**
  - `pip install -r requirements.txt` installs Google OR-Tools.
  - `npm test` runs auth spec files without path alias resolution errors.
- **Effort Estimate:** 2 Story Points (0.5 day)
- **Execution Mode:** Independent.

---

### CATEGORY B: CORE FUNCTIONAL COMPLETION

#### [TASK-P4-02] 20-Class Vietnamese Food Recognition Dataset & Training
- **Objective:** Bridge the gap between the 5 classes currently in `best.pt` and the 20 classes defined in `VIETNAMESE_FOOD_NUTRITION`.
- **Affected Files:**
  - AI: `data.yaml`, `train_yolo.py`, `app/core/vision_service.py`
  - Model weights: `best.pt` (Updated weights)
- **Implementation:**
  1. Expand annotation dataset in `datasets/train` and `datasets/valid` to include all 20 classes.
  2. Update `data.yaml` with `nc: 20` and class names array.
  3. Fine-tune YOLOv11m for 50 epochs with letterbox augmentation and CLAHE preprocessing.
- **Acceptance Criteria:**
  - Model achieves mAP@50 $\ge 0.82$ across 20 Vietnamese food classes.
  - Prediction API accurately classifies Bún Chả, Cơm Tấm, Bánh Xèo, Hủ Tiếu, etc.
- **Effort Estimate:** 8 Story Points (3 days)
- **Execution Mode:** Independent.

---

#### [TASK-P3-03] Open Source Routing Machine (OSRM) Live Distance Matrix
- **Objective:** Replace geometric detour factor ($1.35\times$) with live turn-by-turn road distance tables.
- **Affected Files:**
  - AI: `app/core/route_optimizer.py`
  - AI: `app/core/osrm_client.py` (New)
- **Implementation:**
  1. Integrate OSRM `/table/v1/driving/{coords}` API to fetch exact road network transit time and distance.
  2. Implement fallback to the existing 1.35x Haversine model when OSRM is unreachable.
- **Acceptance Criteria:**
  - Route distance matches Google Maps street directions within $10\%$ tolerance.
- **Effort Estimate:** 5 Story Points (1.5 days)
- **Execution Mode:** Depends on `TASK-DEP-01`.

---

#### [TASK-P6-02] Automated Daily Metrics Aggregation & Continuous Evaluation
- **Objective:** Track recommendation Click-Through Rate (CTR), itinerary completion rate, and offline Precision@K / NDCG@K.
- **Affected Files:**
  - BE: `src/interactions/interactions.service.ts`
  - AI: `app/tasks/evaluate_recommender.py` (New)
  - BE: `src/tasks/metrics.cron.ts` (New)
- **Implementation:**
  1. Schedule daily cronjob at 02:00 UTC to compute:
     $$\text{CTR} = \frac{\sum \text{Clicks}}{\sum \text{Views}}, \quad \text{CompletionRate} = \frac{\sum \text{CompletedTours}}{\sum \text{GeneratedTours}}$$
  2. Compute offline NDCG@K on historical user sessions.
- **Acceptance Criteria:**
  - Metrics are written to `recommendation_metrics` collection daily.
  - Admin Portal can query historical trend data via `GET /interactions/metrics/summary`.
- **Effort Estimate:** 5 Story Points (2 days)
- **Execution Mode:** Independent.

---

### CATEGORY C: CLIENT POLISH & AUTOMATION

#### [TASK-MOB-01] Mobile Image Optimization with `expo-image`
- **Objective:** Improve scroll performance and reduce cellular data consumption on mobile feeds.
- **Affected Files:**
  - Mobile: `src/app/(tabs)/index.tsx`, `src/app/(tabs)/explore.tsx`, `src/app/restaurant/[id].tsx`
- **Implementation:**
  1. Install `expo-image`.
  2. Replace React Native `<Image>` with `<Image priority="high" cachePolicy="memory-disk" />`.
- **Effort Estimate:** 3 Story Points (1 day)

---

#### [TASK-QA-01] Mobile Unit Testing Harness (Jest + RTL)
- **Objective:** Establish automated regression testing for critical mobile user journeys.
- **Affected Files:**
  - Mobile: `package.json`, `jest.config.js`, `__tests__/`
- **Implementation:**
  1. Configure Jest with `jest-expo` and `@testing-library/react-native`.
  2. Write unit tests for Auth login, Taste DNA radar chart, and Copilot chat screen.
- **Effort Estimate:** 5 Story Points (1.5 days)

---

## 3. Top Three Immediate Development Tasks Recommended

Upon stakeholder approval, execute these three prioritized foundational tasks:

1. **`TASK-SEC-01` (Immediate):** Rotate MongoDB Atlas credentials and remove cleartext fallback from `app/config.py`.
2. **`TASK-SEC-02` (Immediate):** Implement `RolesGuard` and attach `@UseGuards(JwtAuthGuard, RolesGuard)` to all unprotected mutation and admin endpoints.
3. **`TASK-PERF-01` (Immediate):** Create missing MongoDB indexes on `reviews.restaurantId`, `itineraries.user_id`, and `restaurants` text search.

