# M10.0 — AI Data Readiness & Cross-Service Integration Validation Report

- **AI Repository:** `thienthiencute/KLTN-123-GastroWise-AI`
- **AI Feature Branch:** `feature/m10-ai-data-readiness` (branched from `feature/m7-3-ai-backend-contract-validation` @ `f69f3ea`, 5 commits ahead of AI `main` @ `ea67f95`)
- **Companion BE Repository (`main`):** `maanxx/KLTN-123-GastroWise-BE` @ `7d3d901` (PR #12)
- **Final Verdict:** **`PASS WITH CONDITIONS`**

*(Condition summary: All AI MongoDB readiness statuses, rating normalization rules, 62 unit/contract tests, and live 5-container Docker Compose Core↔Planning↔AI↔Nginx integration with 6 synthetic test restaurant records passed. Production Atlas data profiling (`BLK-11`), BE-side `tags` array defensive handling, `KLTN-123-GastroWise-AI` PR merge order into `main`, and AI push authorization/CI pipeline remain external/follow-up conditions.)*

---

## 1. Repository & Branch Audit (Phase A)

- **AI `origin/main`:** `ea67f95ee9654917894a1d8faf2a9286962b46d1`
- **AI `feature/m7-3-ai-backend-contract-validation` (`f69f3ea`):** 5 commits ahead of `origin/main`:
  1. `a17ccc3` `feat(m2.3): enforce fail-closed internal auth and dual-compatibility routing contract`
  2. `eaee526` `feat: implement rating normalization utility and enhance recommendation sorting logic`
  3. `f4b0e17` `fix(ai): harden recommender quality and regression coverage`
  4. `06c3721` `feat(ai): add recommendation evaluation and benchmarking`
  5. `f69f3ea` `[test](integration): thien validate ai backend planning contracts`
- **Pre-existing Local Uncommitted Changes Preserved onto `feature/m10-ai-data-readiness`:**
  - `app/config.py`: `build_mongo_uri_from_env()` supporting `AI_DB_USER`, `AI_DB_PASSWORD`, `MONGO_HOST`, `MONGO_PORT`, `MONGO_AUTH_SOURCE` and aligning default `DB_NAME="gastro_core"`.
  - `app/db/mongo.py`: Initial M9.4 `DatabaseLoadError`, `PyMongoError` handling, `sanitize_log_message()`, GeoJSON extraction, and `rating_normalizer` wiring.
  - `main.py`: Initial `@app.exception_handler(DatabaseLoadError)` returning `503`.
- **M7.3 Report Alignment:** Verified `docs/progress/M7_3_AI_BACKEND_CONTRACT_VALIDATION_REPORT.md` matches actual code (`verify_internal_ai_key`, `ai_api_v1_router`, 16 FastAPI routes, OpenAPI snapshot, `app/core/rating_normalizer.py`, `app/core/nutrition_data.py` decoupling `cv2`).
- **PR Integration Order Dependency:** `feature/m10-ai-data-readiness` builds on M2.3–M7.3 features (`verify_internal_ai_key`, `rating_normalizer.py`, `tests/contracts/`). Recommended PR sequence:
  1. **PR #1:** `feature/m7-3-ai-backend-contract-validation` $\rightarrow$ `main`
  2. **PR #2:** `feature/m10-ai-data-readiness` $\rightarrow$ `main`

---

## 2. Existing & Hardened Implementation Review (Phase B)

Enhanced `app/db/mongo.py`, `app/core/text_utils.py`, and `main.py`:
- **Explicit Dataset Readiness Statuses Exposed on `GET /` & Error Handlers:**
  - `DATABASE_UNAVAILABLE` (`HTTP 503`): Missing/placeholder `MONGO_URI`, connection timeout, or SCRAM `OperationFailure` (never masked as `EMPTY_DATASET`).
  - `EMPTY_DATASET` (`HTTP 200`): Authenticated MongoDB `ping` succeeded and collection `find({})` returned `0` docs.
  - `DATA_VALIDATION_FAILED` (`HTTP 503`): Collection returned $> 0$ docs, all missing required `_id`/`name` fields.
  - `DATA_READY` (`HTTP 200`): Validated $\ge 1$ restaurant documents loaded and TF-IDF vectorizer fitted.
- **Schema Normalization & Defensive Resilience (`normalize_and_validate_documents`):**
  - Verifies non-empty `id` (`_id`/`id`) and `name` (`tenQuan`/`name`); rejects malformed rows cleanly without crashing valid rows.
  - Deduplicates by `id` and normalized `(name, address)` before counting missing fields.
  - Parses GeoJSON `location.coordinates` `[lon, lat]` and flat `lat`/`lon`, rejects `(0.0, 0.0)` and out-of-range coordinates safely (`coords_valid=False`, `(0.0, 0.0)` fallback).
  - Hardened `clean_price` (`text_utils.py`) to clamp negative numbers (`< 0 -> 0.0`) and `None`/`NaN`, and fixed `_clean_tags` / `_clean_text` so missing `None`/`NaN` become `""` instead of `"None"`.
  - `_fit_vectorizer()` guards against empty/stopword-only tag corpora.
  - `sanitize_log_message()` masks `mongodb(+srv)://user:pass@` URIs and `password=`/`secret=`/`token=` key-value strings.

---

## 3. MongoDB Configuration Verification (Isolated Docker Compose)

Verified directly against `KLTN-123-GastroWise-BE/docker-compose.yml` and running containers (never Atlas):
- `mongo-test`: `mongo:7.0 --auth`, database `gastro_core_test` (`CORE_DB_NAME_STAGING`), persistent volume `kltn-123-gastrowise-be_mongo_test_data` preserved (`CreatedAt: 2026-11-26T05:19:26Z`).
- `core-service`: `MONGO_HOST=mongo-test`, `CORE_DB_NAME=gastro_core_test`, SCRAM `readWrite` user (`CORE_DB_USER`).
- `ai-service`: `MONGO_HOST=mongo-test`, `MONGODB_DB_NAME=gastro_core_test`, `MONGODB_COLLECTION_NAME=restaurants`, `MONGO_AUTH_SOURCE=gastro_core_test`, SCRAM `read`-only user (`AI_DB_USER`).

---

## 4. Restaurant Schema Mapping Verification

| Source MongoDB Field | Fallback Alias(es) | Target AI Column | Transformation / Validation |
|---|---|---|---|
| `_id` | `id` | `id` | Required non-empty string |
| `tenQuan` | `name` | `name` | Required non-empty trimmed string |
| `diemTrungBinh` | `rating` | `rating`, `raw_rating`, `raw_rating_scale`, `_rating_normalized` | Scaled to `[0.0, 5.0]` via `detect_restaurant_rating_scale` + `normalize_rating`; never double-divided |
| `giaCa` | `price`, `avgPrice` | `price` | Cleaned numeric float $\ge 0.0$ |
| `diaChi` | `address` | `address`, `district` | Safe empty string fallback; district extracted via `extract_district_from_address` |
| `location.coordinates` | `lat`, `lon` | `lat`, `lon`, `coords_valid` | Bounds checked `[-90, 90]` / `[-180, 180]`, rejects `[0, 0]` |
| `tags` | — | `tags` | List or string joined cleanly (`""` when missing/null) |

---

## 5. Rating Normalization Review & Test Results (Phase C)

Reviewed `app/core/rating_normalizer.py` and added explicit `ratingScale` / `raw_rating_scale` metadata support plus regression tests in `tests/test_mongo_data_readiness.py`:
- Foody 10-point (`9.4 -> 4.7`, subscores doc `4.0/10 -> 2.0`, `ratingScale: "10_point" -> 2.0`) — **PASS**
- GastroWise 5-point (`reviewsCount > 0`, `4.2 -> 4.2`) — **PASS**
- Missing / `None` / `NaN` / `inf` / non-numeric $\rightarrow$ `DEFAULT_NEUTRAL_RATING` (`3.0`) — **PASS**
- Out-of-range (`-3.5 -> 0.0`, `25.0 -> 5.0`) — **PASS**
- Double normalization prevention (`_rating_normalized=True` / repeated `normalize_restaurant_dict`) preserving `raw_rating` — **PASS**

---

## 6. Dataset Loading & Synthetic Record Results (Phase D)

### Baseline Empty Check (`0` records in `gastro_core_test.restaurants`)
```json
{"status":"GastroWise AI Microservice Running","data_status":"EMPTY_DATASET","restaurants_loaded":0,"validation":{"database":"gastro_core_test","collection":"restaurants","raw_count":0,"loaded_count":0,"rejected_count":0}}
```

### Synthetic Approved Test Seed (`6` records inserted into `gastro_core_test.restaurants` -> cleaned after verification)
- Inserted **6** identifiable synthetic docs (`_id: 674700000000000000000001..06`, `m10SyntheticTest: true`), including Foody 10-point (`8.6`, `4.0`, `9.2`), GastroWise 5-point (`4.5`), missing null fields/coords (`location: null`, `tags: null`, `diaChi: null`), and **1** invalid document missing `tenQuan`/`name`.
- **Observed Live `GET http://127.0.0.1:5000/` in `gastrowise-ai-service`:**
```json
{"status":"GastroWise AI Microservice Running","architecture":"Enterprise Modular Tree (Clean Architecture)","data_status":"DATA_READY","restaurants_loaded":5,"validation":{"database":"gastro_core_test","collection":"restaurants","raw_count":6,"loaded_count":5,"rejected_count":1,"duplicates_skipped":0,"invalid_coordinates_count":1,"missing_tags_count":1,"missing_address_count":1}}
```
- **Synthetic test records loaded cleanly:** **5 valid records loaded out of 6 raw records** (`1` rejected without crashing service).
- **Cleanup verified:** Synthetic test docs removed afterwards (`deletedSynthetic: 4` remaining after Phase D sub-test, `remainingRestaurants: 0`), restoring `EMPTY_DATASET`.

---

## 7. Recommendation & Auth Endpoint Live Results (Docker Network HTTP)

All calls made over live Docker network from `planning-service` to `http://ai-service:5000`:
- Unauthenticated `POST /recommend/hybrid`: **HTTP `401`** (`{"detail":"Missing X-Internal-AI-Key header"}`) — **PASS**
- Invalid key `POST /recommend/hybrid`: **HTTP `403`** (`{"detail":"Invalid internal AI service key"}`) — **PASS**
- `POST /recommend` (`"phở bò"`): **HTTP `200`** returned `674700000000000000000001` (`[M10_TEST] Phở Bò Quận 1`, `distance_km: 0.16`, `price: 65000`) — **PASS**
- `POST /recommend/hybrid` (`dietary_exclusions: ["chay"]`): **HTTP `200`** returned `total: 1`, `674700000000000000000002` (`[M10_TEST] Cơm Chay Quận 3`) — **PASS**
- `POST /cf/train` (`{ interactions: [{ userId, targetId, eventType, rating? }] }`): **HTTP `200`** (`success: true`, `user_count: 3`, `item_count: 4`) — **PASS**
- `POST /weather-recommend` (`temperature: 33.0, weather_condition: "sunny"`): **HTTP `200`**, `weather_type: "hot"`, top pick `[M10_TEST] Trà Sữa Mát Lạnh` — **PASS**
- `POST /routes/optimize`: **HTTP `200`**, ordered 2 stops (`order_index: 1, 2`) — **PASS**
- `POST /copilot/message` (`"tìm quán phở gần quận 1"`): **HTTP `201`/`200`**, `intent: "search_food"`, `district: "Quận 1"` — **PASS**

---

## 8. Cross-Service & Contract Validation Results (Phase D & E)

### Live Full-Stack HTTP Flow (`Nginx Gateway :8080` $\leftrightarrow$ `Core :3001` $\leftrightarrow$ `Planning :3003` $\leftrightarrow$ `AI :5000` $\leftrightarrow$ `MongoDB :27017`)
With canonical BE Restaurant schema documents (string comma-separated `tags`):
- `GET http://nginx-gateway:8080/api/v1/restaurants?search=pho&lat=10.7769&lon=106.7009`: **HTTP `200`**, hydrated `[M10_TEST] Phở Bò Quận 1` with `rating: 4.3` — **PASS**
- `GET http://nginx-gateway:8080/api/v1/restaurants/weather-recommend?lat=10.7769&lon=106.7009`: **HTTP `200`**, `total: 1` — **PASS**
- `POST http://nginx-gateway:8080/api/v1/restaurants/chat`: **HTTP `201`**, `intent: "search_food"`, `resultsCount: 1` — **PASS**
- `GET http://core-service:3001/api/v1/internal/restaurants/candidates?lat=10.7769&lng=106.7009` (`X-Internal-Service-Key`): **HTTP `200`**, `total: 4` — **PASS**

### Confirmed Contract / Schema Drift Findings (BE Repo — Not Modified Here)
1. **BE `tags` Array Crash (`RestaurantsService.mapRestaurantToDTO` & `InternalRestaurantsController.getCandidates`):**
   - **Observed Error:** `TypeError: r.tags.split is not a function` / `doc.tags.split is not a function` (`HTTP 500`) whenever a MongoDB `restaurants` document stores `tags` as a BSON Array instead of a string. AI `mongo.py` handles both `list` and `str`, whereas BE assumes `string` only.
   - **Recommended BE Task:** Support `Array.isArray(doc.tags) ? doc.tags : doc.tags.split(...)` cleanly in a separate BE PR.
2. **BE `InternalRestaurantsController` Raw 10-Point Rating (`internal-restaurants.controller.ts:89`):**
   - Passes `rating: doc.diemTrungBinh || 0` without normalizing 10-point Foody ratings to `[0, 5]`; `ItinerariesService.ts:310` assumes 5-star scale when computing `compositeScore`. `AiApiClient.optimizeRoute()` also omits `name`/`rating`/`avg_price` when mapping `ItinerariesService` items, relying on AI `CandidateStop` defaults (`4.5`, `50000`).
3. **Unused/Stale DTOs in `BE/libs/shared/src/contracts/ai.contracts.ts` & `ReviewsService.analyzeSentiment`:** Previously documented in M7.3 report (unchanged).

---

## 9. Remaining Blockers

- **`BLK-11` (High):** Staging MongoDB Atlas snapshot audit has not been run yet (all tests here used isolated local Docker `gastro_core_test`).
- **BE Defensive Fix Needed (Medium):** `RestaurantsService.mapRestaurantToDTO` and `InternalRestaurantsController.getCandidates` array-type `tags` handling + 10-point rating scaling for Planning.
- **AI Repo Branch Integration (High):** `feature/m7-3-ai-backend-contract-validation` (5 commits) and `feature/m10-ai-data-readiness` must be PR-reviewed and merged into AI `main` (`ea67f95`).

---

## 10. Actual Test Commands & Logs

```bash
# 1. Full Python regression suite (54 existing + 8 new M10.0 tests = 62 tests)
.venv/bin/python -u -m unittest discover -p "test_*.py" -v
# -> Ran 62 tests in 0.282s -> OK

# 2. Live Docker Compose multi-container integration (BE repo)
docker compose up -d --build ai-service
docker compose exec -T ai-service curl -sf http://127.0.0.1:5000/
# -> Verified EMPTY_DATASET (0 docs) -> DATA_READY (5/6 docs) -> EMPTY_DATASET (post-cleanup)
```
