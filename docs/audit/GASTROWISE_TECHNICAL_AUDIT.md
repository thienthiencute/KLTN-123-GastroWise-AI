# GASTROWISE – COMPREHENSIVE TECHNICAL AUDIT REPORT

**Date:** November 14, 2026  
**Auditor:** Principal Software Architect, Senior Backend Engineer, AI Engineer & QA Lead  
**Audit Scope:** Full Monorepo / Multi-Repository Architecture (5 Repositories)  
**Governance:** Independent Technical Review (Phase 2 Post-Implementation)

---

## 1. EXECUTIVE SUMMARY

An independent technical audit was conducted across all five repositories comprising the **GastroWise** platform:
1. `KLTN-123-GastroWise-BE` (NestJS REST API Gateway & Business Engine)
2. `KLTN-123-GastroWise-AI` (Python FastAPI AI Microservices)
3. `KLTN-123-GastroWise-Mobile` (React Native / Expo Mobile Application)
4. `KLTN-123-GastroWise-FE` (Next.js Customer Web Application)
5. `KLTN-123-GastroWise-Admin-FE` (Next.js Admin Management Portal)

### Key Verdict:
- **Build Integrity:** TypeScript compilation (`tsc --noEmit`) passes cleanly (0 errors) across all TypeScript repositories (BE, Mobile, FE, Admin-FE).
- **Architecture Health:** The layered microservices-gateway design (Client $\rightarrow$ NestJS Gateway $\rightarrow$ MongoDB / FastAPI) is sound in design, but **severely degraded in runtime execution** due to two breaking route mismatches between NestJS and FastAPI, causing the backend to silently fall back to non-AI heuristics.
- **Security Posture:** **CRITICAL RISKS IDENTIFIED**. The FastAPI service has zero authentication (`X-Internal-AI-Key` is missing) and wildcard CORS (`*`). Unauthenticated file uploads lack MIME/size validation. OTP password resets lack expiration timestamps.
- **Automated Testing:** Weak test coverage (~42% in BE with 4 failing test suites; 0% automated coverage in Mobile, Customer FE, and Admin-FE).

---

## 2. REPOSITORY INVENTORY & CONFIGURATION

### 2.1 Backend Gateway (`KLTN-123-GastroWise-BE`)

| Metric | Ground Truth Value | Notes |
| :--- | :--- | :--- |
| **Current Branch** | `main` | Clean working tree |
| **Commit SHA** | `d9f1e40` | Merge PR #8 (`feat/man-be-ai-weather`) |
| **Branch Deviation** | Ahead of `develop` by 14 commits | Unmerged code on `main` needs sync |
| **Runtime & Framework** | Node.js v18/v20, NestJS `^10.0.0` | Production standard |
| **Database Driver** | `@nestjs/mongoose` `^10.0.4`, `mongoose` `^8.4.1` | MongoDB Atlas / Local |
| **Auth & Crypto** | `passport-jwt` `^4.0.1`, `bcrypt` `^5.1.1` | Access + Refresh JWT |
| **Port Configuration** | `3001` (Default) | Configured in `main.ts` |
| **Build Status** | **PASSED** (`tsc --noEmit` $\rightarrow$ 0 errors) | Verified via compiler |
| **Test Status** | **10 Passed, 4 Failed** (61 tests total, 51 passed) | 4 unit test suites broken |

#### Environment Configuration (`.env` vs `.env.example`)
- Monitored Variables: `PORT`, `MONGODB_URI`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `AI_SERVICE_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `INTERNAL_API_KEY`.
- Status: `.env` is properly listed in `.gitignore`. No raw credentials leaked.
- Defect: `INTERNAL_API_KEY` is defined in config, but **never attached** as an authorization header when dispatching HTTP requests to `KLTN-123-GastroWise-AI`.

---

### 2.2 AI Microservices (`KLTN-123-GastroWise-AI`)

| Metric | Ground Truth Value | Notes |
| :--- | :--- | :--- |
| **Current Branch** | `main` | Clean working tree |
| **Commit SHA** | `6c2a513` | Merge PR #1 (`feat/man-ai-weather`) |
| **Active Branches** | `main`, `feat/man-ai-weather` | All features merged into main |
| **Runtime & Framework** | Python 3.10+, FastAPI `0.111.0`, Uvicorn `0.30.1` | ASGI High Performance |
| **Computer Vision** | `ultralytics` `8.2.31` (YOLOv11), `opencv-python` `4.10.0.84` | Model: `best.pt` (40.5 MB) |
| **ML & Recommendation** | `scikit-learn` `1.5.0`, `numpy` `1.26.4` | TruncatedSVD + Cosine |
| **NLP & LLM** | `transformers` `4.41.2`, `torch` `2.3.1` | ViSoBERT + Intent Parser |
| **Missing Dependency** | `ortools` **MISSING from `requirements.txt`** | Used in `route_optimizer.py`! |
| **Port Configuration** | `5000` | Configured in `main.py` |
| **Test Suite** | 5 standalone test scripts in `tests/` | No automated `pytest` runner |

#### Environment Configuration (`.env` vs `.env.example`)
- Monitored Variables: `PORT`, `HOST`, `AI_SECRET_KEY`, `WEATHER_API_KEY`.
- Status: `.env` is gitignored.
- Defect: `AI_SECRET_KEY` is loaded in `core/config.py` but **no authentication dependency/middleware** enforces it on incoming routes!

---

### 2.3 Mobile Application (`KLTN-123-GastroWise-Mobile`)

| Metric | Ground Truth Value | Notes |
| :--- | :--- | :--- |
| **Current Branch** | `main` | Clean working tree |
| **Commit SHA** | `a418b98` | Latest production branch commit |
| **Framework** | React Native `0.74.5`, Expo `~51.0.38` | Expo Managed Workflow |
| **Navigation** | Expo Router `~3.5.23` | File-based routing (`app/`) |
| **State Management** | `zustand` `^4.5.2`, `@tanstack/react-query` `^5.39.0` | Token & Server Cache |
| **Networking** | `axios` `^1.7.2` | Configured via `src/services/api.ts` |
| **Build Status** | **PASSED** (`npx tsc --noEmit` $\rightarrow$ 0 errors) | Verified TypeScript check |
| **Automated Tests** | **0 tests** | No Jest/RNTL tests found |

#### Critical Environment Mismatch:
- In `.env`: `EXPO_PUBLIC_API_URL=http://10.161.30.252:3001/api/v1`
- In Backend `main.ts`: No `setGlobalPrefix('api/v1')` exists!
- **Impact:** All mobile HTTP calls hitting `/api/v1/*` result in HTTP 404 Cannot GET / Cannot POST when targeting standard NestJS backend!

---

### 2.4 Customer Web Frontend (`KLTN-123-GastroWise-FE`)

| Metric | Ground Truth Value | Notes |
| :--- | :--- | :--- |
| **Current Branch** | `main` | Clean working tree |
| **Commit SHA** | `8884dca` | Merge PR #12 (`feat/man-fe-weather`) |
| **Framework** | Next.js `14.2.3`, React `18` | App Router (`src/app`) |
| **Styling & UI** | Tailwind CSS `^3.4.1`, `lucide-react` `^0.378.0` | Responsive Desktop/Mobile Web |
| **Build Status** | **PASSED** (`tsc --noEmit` $\rightarrow$ 0 errors) | Verified clean compile |
| **Automated Tests** | **0 tests** | No unit or Cypress/Playwright tests |

---

### 2.5 Admin Portal Frontend (`KLTN-123-GastroWise-Admin-FE`)

| Metric | Ground Truth Value | Notes |
| :--- | :--- | :--- |
| **Current Branch** | `main` | Clean working tree |
| **Commit SHA** | `3ac5471` | Production admin release commit |
| **Framework** | Next.js `14.2.4`, React `18` | App Router |
| **UI Components** | Ant Design / Radix UI, Tailwind CSS | Management tables & charts |
| **Build Status** | **PASSED** (`tsc --noEmit` $\rightarrow$ 0 errors) | Clean TypeScript compile |
| **Automated Tests** | **0 tests** | No automated tests |

---

## 3. INFRASTRUCTURE & ARCHITECTURAL TOPOLOGY

```
               ┌────────────────────────────────────────────────────────┐
               │                     CLIENT TIER                        │
               │  Mobile (Expo)  │  Customer FE (Next)  │  Admin (Next) │
               └────────────┬───────────────┬───────────────────┬───────┘
                            │               │                   │
                            ▼               ▼                   ▼
               ┌────────────────────────────────────────────────────────┐
               │           API GATEWAY / BUSINESS ENGINE                │
               │         KLTN-123-GastroWise-BE (NestJS :3001)          │
               │  - Authentication, JWT & RBAC (Guards)                 │
               │  - Input Validation (class-validator)                  │
               │  - Business Orchestration & Fallback Logic             │
               └─────────────┬───────────────────────────┬──────────────┘
                             │                           │
                             ▼                           ▼
               ┌───────────────────────────┐ ┌──────────────────────────┐
               │      PERSISTENCE TIER     │ │     AI MICROSERVICES     │
               │       MongoDB Atlas       │ │  FastAPI Engine (:5000)  │
               │  - Users & Taste DNA      │ │  - YOLOv11 Food Vision   │
               │  - Restaurants & Menus    │ │  - SVD + Taste Recom     │
               │  - Reviews & Sentiment    │ │  - OR-Tools TSPTW Route  │
               │  - Itineraries & History  │ │  - ViSoBERT & Copilot    │
               └───────────────────────────┘ └──────────────────────────┘
```

### Architectural Principles Compliance
1. **Client Isolation:** React Native Mobile and Frontends never communicate directly with FastAPI. All traffic flows through NestJS Gateway. (**Compliant**)
2. **Authority of Gateway:** NestJS owns authentication, user authorization, and data persistence. (**Compliant**)
3. **AI Service Role:** FastAPI functions as a stateless compute engine for inference and mathematical optimization. (**Compliant**)
4. **Resilience & Fallbacks:** NestJS includes heuristic fallback blocks if AI services timeout or fail. (**Compliant, but masks active 404 routing bugs!**)

---

## 4. AUDIT SUMMARY TABLE OF REPOSITORIES

| Repository | Tech Stack | Branch / Commit | TS Compile | Unit Tests | Critical Findings |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GastroWise-BE** | NestJS 10, Mongoose 8 | `main` (`d9f1e40`) | 100% Pass | 10 Pass / 4 Fail | Route mismatch to AI (404); Unvalidated upload; No API rate limit |
| **GastroWise-AI** | FastAPI, PyTorch, YOLO | `main` (`6c2a513`) | N/A (Python) | 5 scripts (no runner) | Wildcard CORS; Missing auth middleware; `ortools` not in requirements |
| **GastroWise-Mobile**| React Native, Expo 51 | `main` (`a418b98`) | 100% Pass | 0 tests | Base URL prefix mismatch (`/api/v1` vs `/`) |
| **GastroWise-FE** | Next.js 14, Tailwind | `main` (`8884dca`) | 100% Pass | 0 tests | Zero automated test coverage; relies on server-side rendering |
| **GastroWise-Admin-FE**| Next.js 14, AntD | `main` (`3ac5471`) | 100% Pass | 0 tests | Missing permission gate checks on certain client views |

---
*Report certified by Principal Software Architect & QA Lead.*

