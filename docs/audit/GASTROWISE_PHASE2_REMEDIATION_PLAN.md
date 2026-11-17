# GASTROWISE – PHASE 2 REMEDIATION & STABILIZATION PLAN

**Date:** November 14, 2026  
**Auditor:** Principal Software Architect, Senior Backend Engineer, AI Engineer & QA Lead  
**Scope:** Actionable Implementation Plan to Resolve All Audit Deficiencies across 5 Repositories

---

## 1. REMEDIATION ROADMAP OVERVIEW

This plan organizes all remediation tasks into **four prioritized sprints**, guaranteeing that breaking runtime defects and security vulnerabilities are eliminated before feature expansion.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ SPRINT 1: CRITICAL INTEGRATION & ROUTING (P0 - Immediate)               │
│ - Fix 404 Route Mismatches (Recommendation & Copilot)                    │
│ - Standardize API Gateway Global Prefix (/api/v1)                        │
│ - Add ortools to AI requirements.txt                                     │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ SPRINT 2: ZERO-TRUST SECURITY & INPUT VALIDATION (P0 / P1)               │
│ - Implement Internal AI Key Authentication & Restrict AI CORS            │
│ - Enforce Secure File Upload Validation (MIME + Size limits)             │
│ - Secure OTP Storage with Expiration & Brute-Force Throttling            │
│ - Replace Hardcoded Localhost URLs with Dynamic Config                   │
│ - Add NestJS ThrottlerModule Rate Limiting                               │
│ - Whitelist ValidationPipe & Add DB Indexes                              │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ SPRINT 3: TEST SUITE STABILIZATION & QA (P1)                             │
│ - Fix 4 Failing NestJS Unit Test Suites                                  │
│ - Configure Pytest Automated Harness for AI Microservices                │
│ - Establish Unit Testing Harness for Mobile (Jest + RNTL)                │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ SPRINT 4: ARCHITECTURE & BUSINESS HARDENING (P2)                         │
│ - Sync BE develop branch with main (14 unmerged commits)                 │
│ - Implement Asynchronous Interaction Analytics (BullMQ/Redis)            │
│ - Background Taste DNA Preference Decay Job                              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. DETAILED SPRINT BREAKDOWN

### SPRINT 1: Critical Integration & Routing (P0)

| Task ID | Severity | Objective | Affected Repository & Files | Dependencies | Est. Hours | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TASK-REM-01** | **P0** | Fix AI Recommendation Route Mismatch | `KLTN-123-GastroWise-BE/src/restaurants/restaurants.service.ts` | None | 1.0 h | NestJS calls `${aiBaseUrl}/recommend/hybrid`; returns 200 with personalized results; no 404 fallback. |
| **TASK-REM-02** | **P0** | Fix AI Copilot Route Mismatch | `KLTN-123-GastroWise-BE/src/restaurants/restaurants.service.ts` | None | 1.0 h | NestJS calls `${aiBaseUrl}/copilot/message`; returns 200 with ViSoBERT parsed intents; no 404 fallback. |
| **TASK-REM-03** | **P0** | Add `ortools` to AI Requirements | `KLTN-123-GastroWise-AI/requirements.txt` | None | 0.5 h | Clean `pip install -r requirements.txt` succeeds and `import ortools` runs without error. |
| **TASK-REM-04** | **P0** | Standardize Gateway API Prefix | `KLTN-123-GastroWise-BE/src/main.ts`<br>`KLTN-123-GastroWise-Mobile/.env` | None | 1.5 h | Set `app.setGlobalPrefix('api/v1')` in NestJS; Mobile requests to `/api/v1/*` connect successfully. |

---

### SPRINT 2: Zero-Trust Security & Input Validation (P0 / P1)

| Task ID | Severity | Objective | Affected Repository & Files | Dependencies | Est. Hours | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TASK-REM-05** | **P0** | FastAPI Internal Authentication & CORS | `KLTN-123-GastroWise-AI/main.py`<br>`KLTN-123-GastroWise-AI/core/auth.py` | None | 2.5 h | AI endpoints reject requests without valid `X-Internal-AI-Key` header with 401 Unauthorized; CORS restricted. |
| **TASK-REM-06** | **P0** | Attach `X-Internal-AI-Key` in Gateway | `KLTN-123-GastroWise-BE/src/restaurants/restaurants.service.ts`<br>`src/itineraries/itineraries.service.ts`<br>`src/reviews/reviews.service.ts` | TASK-REM-05 | 2.0 h | All NestJS outbound HTTP requests to AI microservices include `X-Internal-AI-Key: <SECRET>` from config. |
| **TASK-REM-07** | **P0** | Secure `search-by-image` File Upload | `KLTN-123-GastroWise-BE/src/restaurants/restaurants.controller.ts` | None | 1.5 h | Max 5MB limit; reject non-image MIME types; check file magic bytes before dispatching to AI. |
| **TASK-REM-08** | **P0** | Secure OTP Reset Password | `KLTN-123-GastroWise-BE/src/auth/auth.service.ts`<br>`src/users/schemas/user.schema.ts` | None | 2.0 h | `UserSchema` adds `otpExpiresAt: Date`; OTP hashed with SHA-256; reject OTP after 15 minutes or 3 failed tries. |
| **TASK-REM-09** | **P1** | Dynamic Avatar Storage URL | `KLTN-123-GastroWise-BE/src/users/users.controller.ts` | None | 1.0 h | Replace `http://localhost:3001` with `APP_BASE_URL` from ConfigService; loads cleanly on physical phones. |
| **TASK-REM-10** | **P1** | Install & Configure Rate Limiting | `KLTN-123-GastroWise-BE/src/app.module.ts`<br>`src/auth/auth.controller.ts` | None | 2.0 h | `ThrottlerModule` configured; `/auth/*` throttled to 5 req/min per IP. |
| **TASK-REM-11** | **P1** | Enable ValidationPipe Whitelist | `KLTN-123-GastroWise-BE/src/main.ts` | None | 0.5 h | `{ whitelist: true, forbidNonWhitelisted: true }` enabled; unmodeled properties rejected with 400 Bad Request. |
| **TASK-REM-12** | **P1** | Add Index on `FavoriteCollection.userId` | `KLTN-123-GastroWise-BE/src/favorites/schemas/favorite-collection.schema.ts` | None | 0.5 h | `userId` field marked `{ index: true }`; full collection scan eliminated. |

---

### SPRINT 3: Test Suite Stabilization & QA (P1)

| Task ID | Severity | Objective | Affected Repository & Files | Dependencies | Est. Hours | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TASK-REM-13** | **P1** | Fix 4 Broken NestJS Unit Test Suites | `KLTN-123-GastroWise-BE/src/restaurants/*.spec.ts`<br>`src/reviews/*.spec.ts` | None | 3.0 h | All 14 backend test suites pass with 0 failures (`npm test` returns 14 passed). |
| **TASK-REM-14** | **P1** | Configure Pytest Runner for AI Engine | `KLTN-123-GastroWise-AI/pytest.ini`<br>`tests/conftest.py` | TASK-REM-03 | 2.0 h | `pytest tests/` runs automatically and passes in CI/CD pipeline. |
| **TASK-REM-15** | **P1** | Setup Mobile Testing Baseline | `KLTN-123-GastroWise-Mobile/package.json`<br>`src/__tests__/*` | None | 4.0 h | Jest + React Native Testing Library configured; basic store & auth screen render tests pass. |

---

### SPRINT 4: Architecture & Business Hardening (P2)

| Task ID | Severity | Objective | Affected Repository & Files | Dependencies | Est. Hours | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TASK-REM-17** | **P2** | Sync Git Branches (Develop $\leftrightarrow$ Main) | `KLTN-123-GastroWise-BE` (git branch merge) | None | 1.0 h | `develop` branch fast-forwarded or merged with `main` to reconcile 14 diverging commits. |
| **TASK-REM-18** | **P2** | Background Taste DNA Decay Job | `KLTN-123-GastroWise-BE/src/users/users.service.ts` | None | 3.0 h | Cron job decays inactive user preference extremes gradually over 30 days. |
| **TASK-REM-19** | **P2** | Expand YOLO Dataset / Zero-Shot | `KLTN-123-GastroWise-AI/app/services/vision_service.py` | None | 8.0 h | Integrate FoodCLIP / Zero-Shot classifier for dishes outside the core 5 classes. |
| **TASK-REM-20** | **P2** | Async Analytics Queue (Redis) | `KLTN-123-GastroWise-BE/src/analytics/` | None | 4.0 h | Telemetry interaction writes buffered via Redis BullMQ queue to preserve API response latency. |

---

## 3. TOTAL ESTIMATED EFFORT

| Sprint | Focus Area | Total Est. Hours |
| :--- | :--- | :--- |
| **Sprint 1** | Critical Integration & Routing (P0) | **4.0 hours** |
| **Sprint 2** | Zero-Trust Security & Input Validation (P0/P1) | **12.0 hours** |
| **Sprint 3** | Test Suite Stabilization & QA (P1) | **9.0 hours** |
| **Sprint 4** | Architecture & Business Hardening (P2) | **16.0 hours** |
| **TOTAL** | **Full Stabilization to Production Readiness** | **41.0 hours** |

---
*Report certified by Principal Software Architect & QA Lead.*

