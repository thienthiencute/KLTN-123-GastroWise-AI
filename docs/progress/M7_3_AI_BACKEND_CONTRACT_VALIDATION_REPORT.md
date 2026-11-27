# M7.3 — AI ↔ Backend ↔ Planning Contract Validation Report

- **Primary Repository:** `thienthiencute/KLTN-123-GastroWise-AI`
- **Inspected Companion Repository (Read-Only):** `KLTN-123-GastroWise-BE` (Core Service + Planning Service + Nginx Gateway)
- **Branch:** `feature/m7-3-ai-backend-contract-validation` (branched from M7.2 commit `06c3721debbbdcc06b6863febc9e2a827fda81db`)
- **Final Verdict:** **`CONDITIONAL PASS — PARTIAL LIVE INTEGRATION`** *(all 20 HTTP-layer contract tests and 54 total repository tests pass via FastAPI `TestClient` / `httpx.ASGITransport` with fixture datasets; full multi-container live Core + Planning + MongoDB Atlas stack execution was not run in this offline session, and non-blocking BE contract drift was identified in read-only inspection)*

---

## 1. Service Architecture & Actual Communication Paths

Verified from `KLTN-123-GastroWise-BE/docker-compose.yml` and NestJS source code:
- **Ingress:** Client/Mobile $\rightarrow$ Nginx API Gateway (`:8080`) $\rightarrow$ Core Service (`:3001`) & Planning Service (`:3003`). AI Service (`:5000`) is **internal-only** on `gastrowise_network`.
- **Core Service $\rightarrow$ AI Service (`http://ai-service:5000`):**
  - `RestaurantsService.findAll` $\rightarrow$ `POST /recommend`
  - `RestaurantsService.getPersonalizedRecommendations` $\rightarrow$ `POST /recommend/hybrid`
  - `RestaurantsService.syncInteractionsToAi` $\rightarrow$ `POST /cf/train`
  - `RestaurantsService.getWeatherRecommendation` $\rightarrow$ `POST /weather-recommend`
  - `RestaurantsService.searchByImage` $\rightarrow$ `POST /predict-food`
  - `RestaurantsService.chatWithAI` $\rightarrow$ `POST /copilot/message`
  - `ReviewsService.analyzeSentiment` $\rightarrow$ `POST /analyze-sentiment`
- **Planning Service $\rightarrow$ AI Service (`http://ai-service:5000`):**
  - `AiApiClient.optimizeRoute` $\rightarrow$ `POST /routes/optimize` (with 3500ms timeout, `X-Correlation-Id`, and circuit-breaker greedy fallback, never falling back on `401`/`403`/`400`/`422`).

---

## 2. API Inventory

Full OpenAPI `3.1.0` specification (`16` paths, `29` schemas) documented in [`docs/contracts/AI_API_CONTRACT_INVENTORY.md`](../contracts/AI_API_CONTRACT_INVENTORY.md) and snapshotted in [`tests/contracts/fixtures/contract_snapshot.json`](../../tests/contracts/fixtures/contract_snapshot.json).

---

## 3. Backend-to-AI Contract Findings

- **Runtime Callers (`restaurants.service.ts`, `reviews.service.ts`):** All outbound payloads and response field consumers match FastAPI Pydantic schemas exactly (`user_gps`, `taste_vector`, `dietary_exclusions`, `weather_type`, `temperature`, `max_price`, `limit`, `items`, `is_cold_start`, `applied_weights`, `review`, `hashtags`, `message`, `action_card`).
- **Hydration Design:** AI `/recommend` and `/recommend/hybrid` do not return `rating` in JSON; Core Service receives ranked `id`s and hydrates `rating`/`diemTrungBinh` from MongoDB via `mapRestaurantToDTO`.

---

## 4. AI-to-Planning Contract Findings

- **`AiApiClient.mapToCanonicalAiRequest` (`apps/planning-service/src/acl/ai-api.client.ts`):** Sends canonical `RouteOptimizeRequest` (`start_location`, `start_time_mins`, `budget`, `routing_mode`, `desired_stops`, `candidates`) and reads `stops || ordered_stops`, `algorithm_used`, `total_distance_km`, `total_duration_mins`.
- **Legacy Alias Compatibility:** Verified over HTTP (`test_legacy_aliases_payload_via_http`) for `restaurants` $\rightarrow$ `candidates`, `start_lat`/`start_lng` $\rightarrow$ `start_location`, `budget_vnd` $\rightarrow$ `budget`, `start_time` $\rightarrow$ `start_time_mins`, `lng` $\rightarrow$ `lon`, `open`/`close` $\rightarrow$ `open_time`/`close_time`, and `duration_mins` $\rightarrow$ `dining_duration_mins`.

---

## 5. Authentication Verification

- All `/api_v1_router` routes enforce `verify_internal_ai_key` (`X-Internal-AI-Key`, timing-safe `secrets.compare_digest`):
  - Missing header $\rightarrow$ `HTTP 401`
  - Wrong key $\rightarrow$ `HTTP 403`
  - Unset server `INTERNAL_AI_KEY` $\rightarrow$ `HTTP 500` (fail-closed)
  - Valid key $\rightarrow$ `HTTP 200`
  - `GET /` (Docker health check) $\rightarrow$ `HTTP 200` without auth.

---

## 6. Request / Response Compatibility Matrix

| Integration Pair | Endpoint | Auth | Request Compat | Response Compat | Notes |
|---|---|---|---|---|---|
| Core `findAll` $\leftrightarrow$ AI | `POST /recommend` | `X-Internal-AI-Key` | PASS | PASS | Dual-mounted at `/v1/recommendation/recommend` |
| Core `getPersonalizedRecommendations` $\leftrightarrow$ AI | `POST /recommend/hybrid` | `X-Internal-AI-Key` | PASS | PASS | Matches `items[]`, `is_cold_start`, `applied_weights` |
| Core `syncInteractionsToAi` $\leftrightarrow$ AI | `POST /cf/train` | `X-Internal-AI-Key` | PASS | PASS | `{interactions}` $\rightarrow$ `{success, user_count, item_count}` |
| Core `getWeatherRecommendation` $\leftrightarrow$ AI | `POST /weather-recommend` | `X-Internal-AI-Key` | PASS | PASS | `{user_gps}` $\rightarrow$ `{weather, scores}` |
| Core `searchByImage` $\leftrightarrow$ AI | `POST /predict-food` | `X-Internal-AI-Key` | PASS | PASS | Multipart `file` $\rightarrow$ `503` if model unavailable |
| Core `chatWithAI` $\leftrightarrow$ AI | `POST /copilot/message` | `X-Internal-AI-Key` | PASS | PASS | Matches `reply`, `intent`, `entities`, `action_card`, `results` |
| Core `analyzeSentiment` $\leftrightarrow$ AI | `POST /analyze-sentiment` | Conditional Header | PASS | PASS | `ReviewsService` skips header if env unset (falls back on 401) |
| Planning `AiApiClient` $\leftrightarrow$ AI | `POST /routes/optimize` | `X-Internal-AI-Key` | PASS | WARN | Response `order_index` is 1-based; Planning adds `+1` |
| Unused BE `ai.contracts.ts` DTOs $\leftrightarrow$ AI | N/A (Unused TS classes) | N/A | DRIFT | DRIFT | `HybridRecommendationRequest`/`SentimentAnalysisRequest` stale |

---

## 7. Test Cases & Execution Evidence

- **Test Dependencies:** Added [`requirements-dev.txt`](../../requirements-dev.txt) containing `-r requirements.txt` and `httpx>=0.27.0` (installed in local `.venv` without bloating production `requirements.txt` / `Dockerfile`). Install dev dependencies via:
  ```bash
  pip install -r requirements-dev.txt
  ```
- **Contract Tests Executed (`20/20 PASS` via FastAPI `TestClient` + `httpx.ASGITransport`):**
  - `tests/contracts/test_ai_auth_contract.py` (`6` tests): public `GET /`, `401` across 7 protected endpoints, `403`, `500` unset env, `200` valid key, OpenAPI snapshot regression check.
  - `tests/contracts/test_recommendation_contract.py` (`5` tests): Core `/recommend/hybrid`, null optionals & empty results, invalid/extreme GPS & budget boundary, `/recommend` + `/v1/recommendation/recommend` dual route, `/cf/train` + `/weather-recommend` + `/analyze-sentiment` + `/copilot/message`.
  - `tests/contracts/test_planning_contract.py` (`4` tests): Planning `AiApiClient` canonical payload, all legacy aliases, empty candidates (`EMPTY`), `422` validation errors.
  - `tests/contracts/test_error_contract.py` (`5` tests): missing required fields (`422`), invalid types (`422`), malformed JSON (`422`), `/predict-food` model unavailable (`503`), full ASGI HTTP round-trip via `httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app))`.
- **Full Regression Suite Command & Output:**
  ```bash
  .venv/bin/python -m unittest discover -p "test_*.py" -v
  ```
  - **Result:** **54 passed / 0 failed / 0 skipped** (`0.292s`) — combining 20 contract tests + 17 M7.1 tests + 10 M7.2 tests + 4 auth unit tests + 3 routing contract tests.
- **M7.2 Benchmark Reproducibility:**
  ```bash
  .venv/bin/python -m evaluation.runners.run_evaluation
  .venv/bin/python -m evaluation.runners.compare_baselines
  ```
  - **Result:** Reproduced identically (`NDCG@10 = 0.9161`, `MAP@10 = 0.7781`, `10/10` scenarios passing).

---

## 8. Live vs. Mocked Integration Results

- **HTTP Protocol Layer (`TestClient` / `httpx.ASGITransport`):** **Executed & Passed (20/20)** — exercises real Starlette/FastAPI routing, header middleware, auth dependency, Pydantic validation, JSON serialization, and error formatting.
- **Live TCP Socket & Multi-Container Stack (`Core` + `Planning` + `AI` + `MongoDB`):** **Not Executed in This Session** — standard sandbox disallows binding host TCP sockets and Core/Planning (`:3001`, `:3003`, `mongod`) were not running locally; DB & Open-Meteo were mocked with fixture DataFrames.

---

## 9. Confirmed Contract Mismatches (Companion BE Repo — Read-Only Inspection)

*(Not modified here per single-repo scope rules; documented for coordinated BE follow-up)*
1. **Stale TypeScript DTOs in `KLTN-123-GastroWise-BE/libs/shared/src/contracts/ai.contracts.ts`:** `HybridRecommendationRequest`, `HybridRecommendationResponse`, `SentimentAnalysisRequest`, and `CopilotMessageRequest` do not match actual FastAPI schemas or Core Service callers. **Correction:** Synchronize `ai.contracts.ts` with `AI_API_CONTRACT_INVENTORY.md`.
2. **`order_index` Double Offset (`itineraries.service.ts:328`):** AI returns 1-based `order_index` (`1, 2, ...`), while `ItinerariesService` applies `s.order_index + 1` (producing `2, 3, ...`) because its greedy fallback is 0-based. **Correction:** Normalize `AiApiClient.optimizeRoute` to return 0-based `order_index` or remove `+ 1` in `ItinerariesService` when `solver !== 'Gastronomic Greedy Fallback'`.
3. **`ReviewsService.analyzeSentiment` Optional Auth Key (`reviews.service.ts:34-36`):** Only attaches `X-Internal-AI-Key` if env var is set instead of failing fast at startup like `RestaurantsService` and `AiApiClient`.

---

## 10. Remaining Limitations & 11. Recommendations for M8

1. Run full Docker Compose E2E integration across `Core (:3001)`, `Planning (:3003)`, `AI (:5000)`, and isolated `mongo-test` in CI (M8 / GitHub Actions).
2. Add GitHub Actions contract regression step running `unittest discover -s tests/contracts` against `requirements-dev.txt`.
3. Harmonize `KLTN-123-GastroWise-BE/libs/shared/src/contracts/ai.contracts.ts` and `order_index` handling in a dedicated BE PR.
