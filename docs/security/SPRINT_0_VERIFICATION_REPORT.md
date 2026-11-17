# GASTROWISE – SPRINT 0: SECURITY & ARCHITECTURE VERIFICATION REPORT
**Sprint 0 Verification & Stabilization Audit**  
**Role:** Principal Software Architect, Senior Security Engineer & AI Technical Lead  
**Audit Date:** November 17, 2026  
**Status:** AUDITED AGAINST CODEBASE & REPOSITORIES

---

## 1. EXECUTIVE SUMMARY & OVERALL VERIFICATION RESULT

This audit was conducted to independently verify the technical and security claims reported at the conclusion of Phase 2 and Sprint 1 remediation.

```
========================================================================================
OVERALL SPRINT 0 VERIFICATION RESULT: CONDITIONALLY COMPLIANT (REMEDIATION REQUIRED)
- Verified Previous Claims        : 7 of 9 Claims Verified True
- Critical Security Findings     : 4 High/Critical Findings Identified
- Architecture Boundary Status   : 1 Mismatch (Dual-entry MongoDB read)
- Recommendation Engine Quality  : 1 Critical Scale Normalization Defect (5.4 Star Bug)
- Test Suite Health              : 10/14 NestJS Specs Passed; 100% Core AI Algorithms Passed
========================================================================================
```

---

## 2. VERIFIED VS. UNVERIFIED PREVIOUS CLAIMS AUDIT

| # | Reported Claim | Audit Target | Verified Status | Evidence & Actual Code Behavior |
| :-: | :--- | :--- | :---: | :--- |
| **1** | Added automatic `.env` loading in `app/config.py` | `KLTN-123-GastroWise-AI/app/config.py:1-20` | **VERIFIED TRUE** | Custom parser checks for `.env` at parent directory, reads without overwriting existing `os.environ` keys, and falls back gracefully if `python-dotenv` is missing. |
| **2** | Added MongoDB error sanitization in `app/db/mongo.py` | `KLTN-123-GastroWise-AI/app/db/mongo.py:12-16` | **VERIFIED TRUE** | `sanitize_log_message()` applies regex `r'mongodb(\+srv)?:\/\/[^@]+@'` to replace credentials with `[REDACTED_AUTH]`. Used in all Atlas error handlers. |
| **3** | Created `verify_mongodb_connection.py` | `KLTN-123-GastroWise-AI/verify_mongodb_connection.py` | **VERIFIED TRUE** | 119-line Python script verifying ping, user identity, authorized find_one, write rejection, and collection boundary. |
| **4** | Created `verify_mongodb_least_privilege.js` | `KLTN-123-GastroWise-AI/verify_mongodb_least_privilege.js` | **VERIFIED TRUE** | 179-line Node.js script using Native MongoDB driver to verify least-privilege RBAC. |
| **5** | Configured MongoDB user `gastrowise_ai_service` | Live Atlas Cluster `cluster01.adts0oq.mongodb.net` | **VERIFIED TRUE** | Successfully connected and authenticated as `gastrowise_ai_service`. |
| **6** | Restricted AI database access to `gastrowise.restaurants` | Atlas RBAC `gastrowiseAiMicroserviceRole` | **VERIFIED TRUE** | Read on `gastrowise.restaurants` succeeded; read on `gastrowise.users` was strictly denied (`code: 8000, codeName: 'AtlasError'`). |
| **7** | Verified write rejection on restaurant data | Atlas RBAC write probe | **VERIFIED TRUE** | `col.insert_one()` probe was strictly rejected by Atlas RBAC (`user is not allowed to do action [insert] on [gastrowise.restaurants]`, `code: 8000`). |
| **8** | Loaded 178 restaurants into memory | `app/db/mongo.py:81` & live Atlas collection count | **VERIFIED TRUE** | Live Atlas `restaurants` collection contains exactly 178 documents. AI dataset successfully loads 178 records. |
| **9** | Successful TF-IDF & Hybrid Recommendation regression tests | `test_hybrid_recommendation.py` | **PARTIALLY TRUE / DEFECT FOUND** | Algorithms pass unit tests, BUT `app/db/mongo.py` fails to normalize raw 10-point `diemTrungBinh` ratings to a 0–5 scale, resulting in invalid "5.4★" star badges in recommendations. |

---

## 3. TASK 1: GIT REPOSITORY & CHANGE AUDIT

All 5 project repositories were audited for uncommitted changes, branches, commit histories, and tracking integrity:

| Repository | Current Branch | Head Commit SHA | Uncommitted Changes | Tracking Status |
| :--- | :--- | :--- | :--- | :--- |
| **KLTN-123-GastroWise-AI** | `main` | `2a9064c` | Modified: `.env.example`, `app/config.py`, `app/db/mongo.py`<br/>Untracked: `verify_mongodb_connection.py`, `verify_mongodb_least_privilege.js` | Changes are intentional, safe, and part of TASK-SEC-01 remediation. |
| **KLTN-123-GastroWise-BE** | `main` | `f6bc66f` | Clean (`working tree clean`) | Clean. Note: `scripts/remediate-config.js` is committed in HEAD. |
| **KLTN-123-GastroWise-Mobile** | `main` | `d9c8251` | Clean (`working tree clean`) | Tracked `.env` in git (Risk flagged). |
| **KLTN-123-GastroWise-FE** | `main` | `8884dca` | Clean (`working tree clean`) | Clean. |
| **KLTN-123-GastroWise-Admin-FE** | `main` | `3ac5471` | Clean (`working tree clean`) | Clean. |

---

## 4. TASK 2: MONGODB SECURITY VERIFICATION (10 VERIFIED CRITERIA)

| # | Security Verification Criterion | Verification Method | Status | Audit Findings & Verification Details |
| :-: | :--- | :--- | :---: | :--- |
| **1** | Environment variables loaded safely | Code audit: `app/config.py:4-20` | **PASS** | Uses `Path(__file__).resolve()` to target `.env` specifically; does not execute untrusted shell code. |
| **2** | System environment variables never overwritten | Code audit: `app/config.py:19` | **PASS** | Checks `if _k and _k not in os.environ:` prior to assignment, preserving container/CI/system overrides. |
| **3** | Missing credentials fail safely | Code audit: `app/db/mongo.py:41-45` | **PASS** | If `MONGO_URI` is unset, prints security notice and initializes an empty DataFrame (`pd.DataFrame(...)`) rather than crashing unhandled. |
| **4** | Placeholder credentials rejected | Code audit: `app/db/mongo.py:41` | **PASS** | Checks for `<username>` and `<password>` placeholders and aborts initialization safely. |
| **5** | Connection errors never expose credentials | Code audit: `app/db/mongo.py:12-16, 84` | **PASS** | Error outputs are filtered through `sanitize_log_message()` replacing credentials with `[REDACTED_AUTH]`. |
| **6** | Database and collection names validated | Code audit: `app/config.py:25-27` | **PASS** | `DB_NAME` defaults to `'gastrowise'`; `COLLECTION_NAME` defaults to `'restaurants'`. |
| **7** | Permissions follow least privilege | Live test with `verify_mongodb_connection.py` | **PASS** | Authenticated as `gastrowise_ai_service`. Role `gastrowiseAiMicroserviceRole` enforces read-only. |
| **8** | AI cannot access unauthorized collections | Live test against `gastrowise.users` | **PASS** | Access to `users` collection throws `AtlasError (code 8000): user is not allowed to do action [find] on [gastrowise.users]`. |
| **9** | AI cannot insert, update, delete restaurant data | Live test `insert_one()` probe | **PASS** | Insert probe strictly blocked: `AtlasError (code 8000): user is not allowed to do action [insert] on [gastrowise.restaurants]`. |
| **10** | No credentials hardcoded in active working tree | Working tree regex audit | **PASS** | Working tree files in `KLTN-123-GastroWise-AI` use `os.getenv("MONGODB_URI")`. (Historical commit exposure audited in Task 3). |

---

## 5. TASK 6: AUTOMATED TEST AND REGRESSION AUDIT

| Test Suite / Command | Scope | Target Tier | Exit Code | Result | Key Metrics & Verification Evidence |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `verify_mongodb_connection.py` | Atlas Least Privilege | AI $\leftrightarrow$ MongoDB | `0` | **PASSED** | Ping: OK, Read: OK, Write Rejection: OK (8000), Collection Boundary: OK (8000). |
| `test_hybrid_recommendation.py` | Hybrid Recommendation Engine | AI Microservice | `0` | **PASSED** | Flavor vector extraction, Cosine similarity, TruncatedSVD CF, Weather context boost. |
| `npm test` (`KLTN-123-GastroWise-BE`) | Unit & Service Specs | NestJS Backend | `1` | **PARTIAL PASS** | 10 Passed, 4 Failed. 55 unit tests passed; 4 suites failed due to incomplete DI mocks in test fixtures. |
| `route_optimizer.py` Execution | TSPTW Route Optimizer | AI Microservice | `0` | **PASSED** | Generates 3-stop gastronomic route (1.5 km, 144 mins, 130,000 VND, CO2 saved) in 12ms. |
| `evaluate_search.py` | Searchbar Accuracy | AI Microservice | - | **BLOCKED** | Requires running Uvicorn server on port 5000. |
| `test_sentiment.py` | ViSoBERT Sentiment | AI Microservice | - | **BLOCKED** | Requires running Uvicorn server on port 5000. |
| `test_nlu_copilot.py` | Copilot Dialogue NLU | AI Microservice | `1` | **FAILED** | Fails with `ModuleNotFoundError: No module named 'cv2'` due to tight coupling in `nlu_service.py:3`. |
| Mobile Test Suite | App Tests | Mobile App | - | **NOT CONFIGURED** | No test runner or spec files exist in `KLTN-123-GastroWise-Mobile`. |
| Web FE Test Suites | Customer / Admin | Next.js Frontends | - | **NOT CONFIGURED** | No test scripts configured in `package.json`. |

---

## 6. TASK 7: PRODUCTION READINESS AUDIT

| Infrastructure / Security Domain | Production Requirement | Current State | Risk / Status | Fix Action (Source Code vs. DBA) |
| :--- | :--- | :--- | :---: | :--- |
| **MongoDB Atlas Network Access** | IP Whitelisting / VPC Peering | Open to `0.0.0.0/0` (All IPs) | **HIGH** | **DBA Action Required:** Restrict Atlas Network Access to production static IPs / NAT gateway. |
| **Containerization (Docker)** | Production Dockerfiles & Compose | Missing across all 5 repos | **MEDIUM** | **Source Code Fix:** Add multi-stage Dockerfiles for NestJS, FastAPI, and Next.js. |
| **AI Internal Authentication** | Mutual `X-Internal-AI-Key` | Completely absent | **CRITICAL** | **Source Code Fix:** Implement API key validation in FastAPI and inject header in NestJS. |
| **Review Mutation RBAC** | JWT Auth & Ownership Guard | Missing in `reviews.controller.ts` | **CRITICAL** | **Source Code Fix:** Add `JwtAuthGuard` and ownership check on review deletions/edits. |
| **CORS Restriction (FastAPI)** | Specific allowed origins | Wildcard `allow_origins=["*"]` | **HIGH** | **Source Code Fix:** Restrict allowed origins to NestJS gateway and internal hosts. |
| **File Upload Validation** | Size limit $\le 5\text{MB}$ & MIME check | Missing in `search-by-image` | **HIGH** | **Source Code Fix:** Add Multer validation in `restaurants.controller.ts:39`. |
| **Rating Scale Normalization** | Normalized 0–5 star scale | Stored as 0–10 in Atlas, not scaled in AI | **HIGH** | **Source Code Fix:** Normalize `rating = raw / 2` in `app/db/mongo.py`. |

---

## 7. FORMAL FINDINGS AUDIT MATRIX

### FINDING S0-01: Invalid "5.4★" Rating Badge Due to Missing 0–10 to 0–5 Scale Normalization
- **Severity:** HIGH
- **Evidence:** [KLTN-123-GastroWise-AI/app/db/mongo.py:58](file:///D:/GastroWise/KLTN-123-GastroWise-AI/app/db/mongo.py#L58), [app/core/recommender.py:423-424](file:///D:/GastroWise/KLTN-123-GastroWise-AI/app/core/recommender.py#L423-L424)
- **Actual Behavior:** MongoDB Atlas stores `diemTrungBinh` on a 0–10 scale. AI microservice renames `diemTrungBinh` to `rating` without dividing by 2. When a restaurant has a raw Foody score of 5.4/10 (equivalent to a mediocre 2.7/5 stars), line 423 evaluates $5.4 \ge 4.7$ and generates `"⭐ Đánh giá xuất sắc (5.4★)"`.
- **Expected Behavior:** Ratings in the AI DataFrame must be normalized to a 0–5 scale (`rating = raw / 2` if $raw > 5.0$). 5.4/10 should become 2.7/5 and must not trigger the "Đánh giá xuất sắc" pill.
- **Business Impact:** Misleads users into believing mediocre restaurants are top-rated; renders impossible rating numbers (5.4 out of 5 stars) in the UI.
- **Recommended Solution:** In `app/db/mongo.py`, normalize `temp_df['rating'] = temp_df['rating'].apply(lambda r: round(float(r) / 2.0, 1) if float(r) > 5.0 else float(r))`.
- **Dependencies:** None.
- **Acceptance Criteria:** Maximum rating in AI DataFrame $\le 5.0$. Restaurant with score 5.4 yields 2.7 stars.
- **Testing Requirements:** Python test verifying rating column transformation.

---

### FINDING S0-02: Tracked Script Containing Hardcoded Connection String in Git HEAD
- **Severity:** HIGH
- **Evidence:** [KLTN-123-GastroWise-BE/scripts/remediate-config.js:9-12](file:///D:/GastroWise/KLTN-123-GastroWise-BE/scripts/remediate-config.js#L9-L12)
- **Actual Behavior:** A helper script used to remediate `config.py` was committed to Git HEAD in `KLTN-123-GastroWise-BE` containing the old database connection string.
- **Expected Behavior:** No scripts containing real credentials or passwords should be tracked in Git.
- **Business Impact:** Anyone with read access to the repository can view historical database credentials.
- **Recommended Solution:** Remove `scripts/remediate-config.js` from Git tracking (`git rm scripts/remediate-config.js`) and ensure the old `thienthien` Atlas user is deleted or rotated.
- **Dependencies:** DBA action to verify `thienthien` user deletion on Atlas.
- **Acceptance Criteria:** File removed from working tree and `.gitignore` updated.
- **Testing Requirements:** Git status verify file is untracked.

---

### FINDING S0-03: Missing Authentication & Authorization on Review Mutation Endpoints
- **Severity:** CRITICAL
- **Evidence:** [KLTN-123-GastroWise-BE/src/reviews/reviews.controller.ts:48-61](file:///D:/GastroWise/KLTN-123-GastroWise-BE/src/reviews/reviews.controller.ts#L48-L61)
- **Actual Behavior:** `DELETE /reviews/:id`, `PATCH /reviews/:id`, and `POST /reviews/migrate-sentiment` have no `JwtAuthGuard`, no `RolesGuard`, and no ownership check.
- **Expected Behavior:** Reviews can only be deleted or updated by their author or an administrator.
- **Business Impact:** Any anonymous user can delete or tamper with all customer reviews across the platform.
- **Recommended Solution:** Add `@UseGuards(JwtAuthGuard)` to all mutation routes and verify author ownership (`review.userId === req.user.sub`) or `admin` role.
- **Dependencies:** `AuthModule`.
- **Acceptance Criteria:** Unauthenticated requests receive 401 Unauthorized; cross-user mutations receive 403 Forbidden.
- **Testing Requirements:** Unit test in `reviews.controller.spec.ts`.

---

### FINDING S0-04: Tight Coupling Causes NLU Dialogue Test Failure on Missing OpenCV
- **Severity:** MEDIUM
- **Evidence:** [KLTN-123-GastroWise-AI/app/core/nlu_service.py:3](file:///D:/GastroWise/KLTN-123-GastroWise-AI/app/core/nlu_service.py#L3)
- **Actual Behavior:** `nlu_service.py` imports `VIETNAMESE_FOOD_NUTRITION` dictionary from `vision_service.py`, which imports `cv2` at line 2. If `opencv-python` is not installed, all NLP/NLU chat features crash with `ModuleNotFoundError`.
- **Expected Behavior:** Text processing and NLP should operate independently of computer vision libraries.
- **Business Impact:** Copilot chat and intent classification fail if computer vision runtime is missing.
- **Recommended Solution:** Move `VIETNAMESE_FOOD_NUTRITION` into a standalone constants module (e.g. `app/core/nutrition_data.py`).
- **Dependencies:** None.
- **Acceptance Criteria:** `test_nlu_copilot.py` passes without requiring `cv2`.
- **Testing Requirements:** Execute `test_nlu_copilot.py` in standalone Python environment.

