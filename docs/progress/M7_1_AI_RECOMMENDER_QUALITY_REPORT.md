# M7.1 — GastroWise AI Recommender Quality Audit & Improvement Report

## 1. Executive Summary
- **Target Repository:** `KLTN-123-GastroWise-AI`
- **Reference Backend Repository:** `KLTN-123-GastroWise-BE` (branch: `fix/m2.3-backend-integration-security`)
- **Working Branch:** `feature/m7-1-ai-recommender-quality`
- **Final Verdict:** **`PASS — M7.1 VERIFIED`** ✅
- **Objective:** Audit and improve GastroWise AI recommendation quality, fix rating scale normalization (ISSUE-06), resolve OpenCV import fragility (ISSUE-11), eliminate candidate duplicates, ensure ranking determinism, enforce strict dietary constraint handling, and verify microservice contract compatibility without breaking changes.

---

## 2. Architecture & Recommendation Algorithm Review

### 2.1 Current Microservice Architecture
- **Framework:** FastAPI (Python 3.9/3.12 compatible) with Clean Modular Architecture.
- **Service Ingress:** Mounted behind Nginx API Gateway (`:8080`) -> Proxied exclusively via Backend Core Service (`:3001`) and Planning Service (`:3003`). AI Service (`:5000`) is internal-only.
- **Security:** Fail-closed `X-Internal-AI-Key` header authentication enforced via `verify_internal_ai_key` dependency on all `/api/v1` routes.

### 2.2 Recommendation Engine Pipeline
1. **Content-Based & Search Recommender (`/recommend`):**
   - Query parsing, Vietnamese food dish tag extraction, TF-IDF cosine similarity between query tags and restaurant tags.
   - Taste DNA 6-D vector boosting (`[spicy, sweet, sour, salty, umami, bitter]`).
   - Dynamic sorting modes: `relevance`, `distance`, `price`, `rating`.
2. **4-Stage Industrial Hybrid Engine (`/recommend/hybrid`):**
   - **Stage 1 (Hard Filtering):** GPS radius candidate pool, price ceiling, strict dietary exclusions (`chay`, `không cay`, `halal`).
   - **Stage 2 (Content-Based Taste Matching):** Cosine similarity between 6-D user Taste DNA vector and restaurant flavor profile vector.
   - **Stage 3 (Collaborative Filtering):** TruncatedSVD Matrix Factorization predicting user-restaurant affinity $\hat{R}(u, r) = \mu + b_u + b_r + p_u^T q_r$, sigmoid-normalized to $[0.0, 1.0]$.
   - **Stage 4 (Contextual Ranking & Explainability):** Environmental weather boosting ($S_{\text{env}}$), distance logarithmic decay penalty ($\lambda_{\text{dist}} \cdot \ln(1 + D)$), rating quality prior bonus, explainable justification pills.

---

## 3. ISSUE-06 — Rating Scale Audit & Normalization Strategy

### 3.1 Root Cause & Source Identification
Audit revealed two distinct rating scales coexisting in the GastroWise ecosystem:
1. **Foody/ShopeeFood Crawled Catalog (Raw Scale: 10-point):**
   - Seeded restaurants store `diemTrungBinh` (and subscores `diemChatLuong`, `diemViTri`, `diemPhucVu`, `diemGiaCa`) on a $[0.0, 10.0]$ scale.
2. **GastroWise User Reviews (Scale: 5-star):**
   - Mobile client UI (`WriteReviewScreen`) submits 1 to 5 star ratings.
   - Core Service review aggregation updates `diemTrungBinh` to the average of `diemReview` ($[1.0, 5.0]$) and sets `reviewsCount`.

### 3.2 Threshold Flaw in Prior Implementation
The previous implementation applied a naive threshold check:
```python
if r > 5.0:
    return round(r / 2.0, 1)
return round(r, 1)
```
- A poor Foody restaurant with $4.0/10$ ($40\%$) was treated as $\le 5.0$, returning $4.0/5$ ($80\%$).
- A good Foody restaurant with $7.0/10$ ($70\%$) was $> 5.0$, returning $3.5/5$.
- Result: Lower-rated Foody restaurants were ranked *higher* than better-rated ones.

### 3.3 Implemented Solution (`app/core/rating_normalizer.py`)
- Created dedicated normalizer with explicit scale support (`SCALE_10`, `SCALE_5`, `AUTO`).
- **Scale Detection:** Inspects document metadata. Documents with Foody sub-scores and `reviewsCount == 0` are recognized as 10-point even when $\le 5.0$. Documents with `reviewsCount > 0` are recognized as 5-star.
- **Double Normalization Prevention:** Preserves `raw_rating`, records `raw_rating_scale`, and flags `_rating_normalized = True`. Normalized ratings are never divided by 2 again.
- **Boundary & Out-of-Range Handling:**
  - Negative values clamped to $0.0$.
  - Values $> 10.0$ clamped to $5.0$.
  - Missing, `None`, `NaN`, empty string, and non-numeric inputs map to neutral default ($3.0$).
- **Integrated Across:**
  - MongoDB loader (`app/db/mongo.py`).
  - SVD interaction trainer (`app/core/collaborative_filter.py`).
  - Route Optimizer (`app/core/route_optimizer.py`).
  - Recommenders (`app/core/recommender.py`).

---

## 4. ISSUE-11 — OpenCV (CV2) Import & Environment Resilience

### 4.1 Root Cause
- Top-level unconditional `import cv2` in `app/core/vision_service.py` caused entire service and test suite initialization to crash if native shared libraries (e.g. `libGL.so.1`, `libglib-2.0.0`) were absent in headless environments.
- Top-level unused imports in `main.py` (`get_yolo_model`, `get_sentiment_pipeline`) caused unnecessary eager module loading during startup and test collection.

### 4.2 Implemented Solution
- **Resilient Fallback Import in `app/core/vision_service.py`:**
  ```python
  try:
      import cv2
  except (ImportError, Exception):
      cv2 = None
  ```
- **Safe CLAHE Preprocessing:** `preprocess_image_clahe` safely checks `if cv2 is None: return image` without throwing unhandled exceptions.
- **Cleaned `main.py`:** Removed unused top-level vision and sentiment imports so recommendation and core services boot independently of computer vision libraries.

---

## 5. Recommendation Quality & Behavioral Improvements

1. **Deduplication:**
   - Added candidate deduplication by `id` as well as composite `(name, address)` in both `recommend_restaurants` and `recommend_hybrid`. Duplicate candidate cards are completely eliminated.
2. **Determinism:**
   - Implemented stable, deterministic tie-breaking sorting across all sort modes:
     `by=['s_composite', 's_taste', 'rating', 'id'], ascending=[False, False, False, True]`.
   - Repeated requests with identical inputs and dataset state produce identical ordered rankings.
3. **Strict Dietary Constraint Enforcement:**
   - When users specify dietary restrictions (e.g., `chay`, `vegan`, `không cay`, `halal`), filtering is strictly applied. If no matching restaurants exist, an empty list is safely returned rather than silently falling back to meat/non-compliant dishes.
4. **Rating Quality Factor in Composite Ranking:**
   - Added a normalized quality prior bonus (`+0.05 * (rating / 5.0)`) into the hybrid composite formula, giving higher-rated restaurants a natural, mathematically bounded edge when taste match is equal.
5. **Missing & NaN Data Safety:**
   - Handled `NaN` prices, coordinates, and ratings with safe conversions, preventing `ValueError: cannot convert float NaN to integer`.

---

## 6. Test Suite & Verification Evidence

All tests executed with Python 3.9 in the local virtual environment (`.venv/bin/python -m unittest discover -p "test_*.py" -v`):

### 6.1 Quality, Normalization & Resilience Tests (`test_m7_recommender_quality.py`)
- `test_ten_point_scale_normalization`: ✅ PASS
- `test_five_point_scale_preservation`: ✅ PASS
- `test_auto_detection_scale`: ✅ PASS
- `test_missing_and_null_ratings`: ✅ PASS (`None`, `NaN`, `inf`, `-inf`, `bool`, empty string, non-numeric)
- `test_invalid_and_out_of_range_ratings`: ✅ PASS
- `test_boundary_values`: ✅ PASS
- `test_double_normalization_prevention`: ✅ PASS
- `test_restaurant_doc_scale_detection`: ✅ PASS (Foody 4.0/10 -> 2.0/5, 8.0/10 -> 4.0/5, GastroWise 4.0/5 -> 4.0/5, heterogeneous pandas `NaN` handling, idempotency)
- `test_clahe_preprocessing_with_cv2`: ✅ PASS
- `test_clahe_preprocessing_without_cv2`: ✅ PASS
- `test_main_and_vision_import_without_cv2`: ✅ PASS
- `test_deduplication_filters_duplicate_restaurants`: ✅ PASS
- `test_deterministic_ranking_results`: ✅ PASS
- `test_strict_dietary_restrictions_vegetarian`: ✅ PASS (excludes `"lẩu gà nấm"` / meat dishes with mushroom/vegetables)
- `test_empty_candidate_pool_handling`: ✅ PASS
- `test_empty_dataset_handling`: ✅ PASS
- `test_missing_data_resilience`: ✅ PASS (`NaN` rating, price, and coordinates)
**Result:** 17/17 PASS

### 6.2 Full Repository Test Execution
```bash
.venv/bin/python -m unittest discover -p "test_*.py" -v
```
- `test_internal_auth.py`: 4/4 PASS (fail-closed `X-Internal-AI-Key` verification)
- `test_m7_recommender_quality.py`: 17/17 PASS
- `test_routing_contract.py`: 3/3 PASS (canonical + legacy request compatibility + dual `stops`/`ordered_stops` response)
**Total:** 24/24 PASS (0 failures, 0 errors, 0 skipped, 2.180s)

---

## 7. Independent Audit & Hardening Fixes (M7.1 Verification)

During independent audit, 4 subtle defects were identified and hardened:
1. **Vision Service Startup Coupling (`app/core/vision_service.py`):** Top-level `from ultralytics import YOLO` internally triggered `import cv2`, crashing `main.py` when OpenCV was absent. Moved `YOLO` import lazily inside `get_yolo_model()`.
2. **Pandas `NaN` & Precedence in Rating Scale Detection (`app/core/rating_normalizer.py`):**
   - `float('nan')` values from heterogeneous MongoDB DataFrames (`to_dict()`) bypassed `is not None` and `or 0` checks in `detect_restaurant_rating_scale`, causing Foody documents with `NaN` `reviewsCount` and rating $\le 5.0$ to fall back to `AUTO`.
   - When `_rating_normalized=True`, `rating` now takes precedence over `diemTrungBinh`.
   - Added `bool` rejection in `normalize_rating`.
3. **NaN Coordinate Propagation & Price Column Guard (`app/core/text_utils.py`, `app/core/recommender.py`):**
   - `calculate_distance` now guards against `NaN`/`Inf` coordinates (returns `999.0` instead of propagating `NaN` into JSON responses).
   - `recommend_hybrid` and `recommend_restaurants` safely coerce/default missing `price` columns before `max_price` filtering.
4. **Strict Vegetarian Filter Hardening (`app/core/recommender.py`):**
   - Removed `'nấm|rau củ'` from the vegetarian regex `'chay|vegan|vegetarian'` so meat dishes containing mushrooms or vegetables (e.g., `"lẩu gà nấm"`) are never returned for strict vegetarian requests.

| File | Type | Purpose |
|---|:---:|---|
| `app/core/rating_normalizer.py` | Modified | Hardened `NaN`/`Inf`/`bool` checks, normalized precedence, and Foody subscore detection |
| `app/core/vision_service.py` | Modified | Lazy `YOLO` import inside `get_yolo_model()` so service boots without `cv2` |
| `app/core/text_utils.py` | Modified | Guard `calculate_distance` against `NaN`/`Inf` coordinates |
| `app/core/recommender.py` | Modified | Strict vegetarian filter + safe `price` column coercion |
| `test_m7_recommender_quality.py` | Modified | Added regression tests for all confirmed bugs and 12 required scenarios |

---

## 8. Known Limitations & Proposed M7.2 Tasks
1. **Static Dataset in Dev:** In local dev without MongoDB Atlas credentials, fallback mock dataset is used. Model training should be tested with production replica data in staging.
2. **Cold-Start Collaborative Filtering:** Users with $< 2$ interactions rely on Content-Based + Weather boosting. M7.2 can explore popular/trending fallback weighting.
3. **Proposed M7.2 Tasks:**
   - Multi-criteria rating weighting (food vs service vs atmosphere vs price).
   - Automated offline eval pipeline measuring Precision@k, Recall@k, and NDCG@k on historical user interaction logs.
