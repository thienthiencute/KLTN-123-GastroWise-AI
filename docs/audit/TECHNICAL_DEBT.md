# GASTROWISE – TECHNICAL DEBT & RISK REGISTER

**Audit Date:** 2026-11-10  
**Lead Auditor:** Independent Principal Software Architect  
**Scope:** Architecture, Code Quality, Security, Scalability & Maintainability

---

## 1. Top 10 Technical Risks

| # | Risk Description | Affected Subsystem | Severity | Impact | Mitigation Strategy |
| :-: | :--- | :--- | :---: | :--- | :--- |
| **1** | **Database Credential Exposure** | AI (`app/config.py`) | **CRITICAL** | Cleartext Atlas credentials committed in code allow arbitrary database tampering. | Rotate Atlas password immediately; remove fallback from code; mandate `.env`. |
| **2** | **Authorization Bypass on Admin Endpoints** | BE (`users`, `itineraries`) | **CRITICAL** | `GET /users`, `PATCH /users/:id`, `GET /itineraries/all`, `PATCH /itineraries/:id` have 0 guards. | Add `JwtAuthGuard` and `RolesGuard` checking `req.user.role === 'admin'`. |
| **3** | **Full Collection Scans on High-Traffic Queries** | Database / BE | **HIGH** | Missing indexes on `reviews.restaurantId`, `itineraries.user_id`, and regex search causes $O(N)$ slowdown. | Add compound indexes `reviews(restaurantId, createdAt)`, `itineraries(user_id, createdAt)`. |
| **4** | **Silent Degradation of Route Optimizer** | AI (`requirements.txt`) | **HIGH** | `ortools` is not in `requirements.txt`. Fresh deployments silently downgrade to naive heuristic sequence. | Add `ortools>=9.8.0` to `requirements.txt` and add CI import verification test. |
| **5** | **Food Recognition Class Discrepancy** | AI (`best.pt`, `data.yaml`) | **MEDIUM** | Model only recognizes 5 dishes (`Banh-Mi`, `Bot Chien`, `Bun`, `Goi-Cuon`, `Pho`) despite 20-dish nutrition dictionary. | Retrain YOLOv11m on expanded 20-class Vietnamese food dataset; update `data.yaml`. |
| **6** | **Lack of Automated Offline Feedback Loop** | AI / BE | **MEDIUM** | P6 offline NDCG@K, Precision@K, and drift monitoring cronjobs do not exist in code. | Implement automated daily aggregation script in `interactions.service.ts` or Python task. |
| **7** | **Wildcard CORS with Credentials** | BE (`main.ts`) | **MEDIUM** | Browser rejects `origin: "*"` with `credentials: true`; potential CSRF risk. | Whitelist exact allowed origins (e.g. `http://localhost:3000,http://localhost:8081`). |
| **8** | **Unrestricted File Upload on Image Vision** | BE (`restaurants.controller.ts`) | **MEDIUM** | File upload lacks MIME filtering and size caps; vulnerable to Denial of Service via memory exhaustion. | Configure Multer with 10MB limit and JPEG/PNG/WEBP filter. |
| **9** | **Zero Automated Mobile Test Harness** | Mobile | **MEDIUM** | React Native app has 0 unit/component tests; regressions can break checkout/itinerary navigation silently. | Introduce Jest + React Native Testing Library for critical screens. |
| **10**| **Absolute Path Imports Breaking Jest** | BE (`src/auth`) | **LOW** | Imports like `from 'src/users/...'` break Jest runner unless custom alias mapper is configured. | Standardize all internal imports to relative paths (`../users/...`). |

---

## 2. Top 10 Technical Debt Items

### TD-01: Duplicate/Orphan Schema `user-interaction.schema.ts`
- **Location:** `KLTN-123-GastroWise-BE/src/users/schemas/user-interaction.schema.ts`
- **Issue:** Specifies `@Schema({ collection: 'user_interactions' })`, which conflicts conceptually with `src/interactions/schemas/interaction.schema.ts`. It is not imported in `UsersModule` and represents legacy dead code.
- **Action:** Delete `src/users/schemas/user-interaction.schema.ts`.

### TD-02: Inconsistent Import Aliases in Backend Auth Module
- **Location:** `src/auth/auth.controller.ts`, `src/auth/auth.module.ts`, `src/auth/auth.service.ts`
- **Issue:** Uses `from 'src/users/...'` instead of relative paths `from '../users/...'`.
- **Action:** Convert to relative imports to restore Jest compatibility across all spec files.

### TD-03: Missing Dependency in AI `requirements.txt`
- **Location:** `KLTN-123-GastroWise-AI/requirements.txt`
- **Issue:** `ortools` is imported in `route_optimizer.py` inside a `try/except` block, but omitted from `requirements.txt`.
- **Action:** Add `ortools>=9.8.0` to `requirements.txt`.

### TD-04: Geometric Detour Factor instead of Live OSRM Road Distance
- **Location:** `KLTN-123-GastroWise-AI/app/core/route_optimizer.py`
- **Issue:** Route optimization calculates Haversine $\times 1.35$ rather than requesting an actual road routing table from OSRM or Mapbox. In dense urban networks with one-way streets, estimated travel times can vary by up to 25%.
- **Action:** Implement an OSRM Table API client with fallback to the existing 1.35x geometric factor.

### TD-05: Hardcoded Default Fallback URLs
- **Location:** `restaurants.service.ts`, `reviews.service.ts`, `constants/index.ts`
- **Issue:** Services contain hardcoded fallbacks (`http://127.0.0.1:5000`, `http://10.0.2.2:3001`). If environment variables fail to load in Docker/Kubernetes, requests silently fall back to local addresses.
- **Action:** Centralize environment variable validation using `@nestjs/config` and fail loudly on startup if `AI_SERVICE_URL` is missing.

### TD-06: Fixed GPS Fallback on Location Permission Denial
- **Location:** `explore.tsx`, `ai-planner.tsx`, `ai-assistant.tsx`
- **Issue:** When location permission is denied or running in emulator, app silently defaults to `[10.7769, 106.7009]` (District 1, HCMC) without notifying the user that location services are inactive.
- **Action:** Surface an explicit UI banner when GPS is unavailable, prompting user to manually select their district.

### TD-07: Monolithic Responsibilities in `RestaurantsController`
- **Location:** `KLTN-123-GastroWise-BE/src/restaurants/restaurants.controller.ts`
- **Issue:** Single controller handles basic CRUD, menu management, image search, weather recommendations, personalized hybrid recommendations, and chatbot copilot.
- **Action:** Split into sub-controllers (`RestaurantsRecommendationController`, `RestaurantsMenuController`, `RestaurantsCopilotController`).

### TD-08: Legacy Spec Files Failing in Jest
- **Location:** `restaurants.controller.spec.ts`, `reviews.service.spec.ts`, `itineraries.controller.spec.ts`
- **Issue:** Default Nest CLI generated specs lack mocks for Mongoose models, causing `npm test` to fail 8 out of 12 suites despite core features functioning.
- **Action:** Provide mock providers for Mongoose models across all legacy spec files or remove unmaintained boilerplate specs.

### TD-09: Inconsistent API Response Envelopes
- **Location:** Backend controllers
- **Issue:** Some endpoints return raw arrays (`GET /restaurants`), some return `{ success, data, total }` (`GET /restaurants/recommended`), and some return custom objects (`POST /restaurants/chat`).
- **Action:** Implement a global NestJS `TransformInterceptor` that wraps all successful responses in standard `{ success: true, statusCode: 200, data: T, meta: {...} }`.

### TD-10: Remote Image Caching Deficiency on Mobile
- **Location:** `index.tsx`, `explore.tsx`, `ai-assistant.tsx`
- **Issue:** App uses standard React Native `<Image>` without disk caching, causing repeated image downloads on feed scrolling.
- **Action:** Upgrade to `expo-image` with automatic disk caching and memory management.

