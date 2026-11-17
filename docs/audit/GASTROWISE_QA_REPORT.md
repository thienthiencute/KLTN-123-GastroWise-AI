# GASTROWISE – QA & STATIC ANALYSIS AUDIT REPORT

**Audit Date:** November 14, 2026  
**Auditor:** QA Technical Lead & Principal Software Architect  
**Scope:** Static Type Compilation, Automated Unit Testing, Test Suite Health, and Code Coverage across all 5 Repositories

---

## 1. STATIC COMPILATION & TYPE-CHECKING RESULTS

Static type checks were performed across all TypeScript repositories using clean compiler configurations (`tsc --noEmit --incremental false`):

| Repository | Tech Stack | Type-Check Command | Exit Code | TypeScript Errors | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **KLTN-123-GastroWise-BE** | NestJS / TypeScript 5.1 | `npx tsc --noEmit` | `0` | **0 errors** | **PASSED** |
| **KLTN-123-GastroWise-Mobile**| React Native / Expo 51 | `npx tsc --noEmit` | `0` | **0 errors** | **PASSED** |
| **KLTN-123-GastroWise-FE** | Next.js 14 / TypeScript | `npx tsc --noEmit` | `0` | **0 errors** | **PASSED** |
| **KLTN-123-GastroWise-Admin-FE**| Next.js 14 / TypeScript | `npx tsc --noEmit` | `0` | **0 errors** | **PASSED** |
| **KLTN-123-GastroWise-AI** | Python 3.10 / FastAPI | Python syntax / ast | `0` | N/A | **PASSED** |

### Static Analysis Verdict:
The TypeScript type safety across all four front-end and back-end repositories is **in excellent syntactic condition**, with zero compiler errors or broken import paths.

---

## 2. AUTOMATED UNIT TEST EXECUTION LOG

### 2.1 Backend Gateway (`KLTN-123-GastroWise-BE`)
- **Test Runner:** Jest `^29.5.0`
- **Total Test Suites:** 14
- **Passed Suites:** 10
- **Failed Suites:** 4
- **Total Tests:** 61 (51 Passed, 10 Failed)

```
Test Suites: 4 failed, 10 passed, 14 total
Tests:       10 failed, 51 passed, 61 total
Snapshots:   0 total
Time:        4.812 s
Ran all test suites.
```

#### Detailed Suite Breakdown:
| Test Suite File | Status | Tests | Root Cause of Failure |
| :--- | :--- | :--- | :--- |
| `src/auth/auth.service.spec.ts` | **PASS** | 8 passed | None (Mocks configured) |
| `src/auth/auth.controller.spec.ts` | **PASS** | 6 passed | None |
| `src/users/users.service.spec.ts` | **PASS** | 7 passed | None |
| `src/users/users.controller.spec.ts` | **PASS** | 5 passed | None |
| `src/itineraries/itineraries.service.spec.ts` | **PASS** | 6 passed | None |
| `src/itineraries/itineraries.controller.spec.ts`| **PASS** | 5 passed | None |
| `src/favorites/favorites.service.spec.ts` | **PASS** | 5 passed | None |
| `src/favorites/favorites.controller.spec.ts` | **PASS** | 4 passed | None |
| `src/analytics/analytics.service.spec.ts` | **PASS** | 3 passed | None |
| `src/app.controller.spec.ts` | **PASS** | 2 passed | None |
| `src/restaurants/restaurants.controller.spec.ts`| **FAIL** | 3 failed | `Nest can't resolve dependencies of RestaurantsController...` Missing `getModelToken('Restaurant')` provider in `Test.createTestingModule`. |
| `src/restaurants/restaurants.service.spec.ts` | **FAIL** | 3 failed | `Nest can't resolve dependencies of RestaurantsService...` Missing Mongoose `RestaurantModel` mock. |
| `src/reviews/reviews.controller.spec.ts` | **FAIL** | 2 failed | `Nest can't resolve dependencies of ReviewsController...` Missing `getModelToken('Review')` mock. |
| `src/reviews/reviews.service.spec.ts` | **FAIL** | 2 failed | `Nest can't resolve dependencies of ReviewsService...` Missing Mongoose `ReviewModel` mock. |

---

### 2.2 AI Microservices (`KLTN-123-GastroWise-AI`)
- **Automated Test Runner:** None configured (no `pytest` command in CI or scripts).
- **Standalone Test Scripts:** 5 standalone integration scripts located in `tests/`:
  1. `tests/test_vision_food.py` $\rightarrow$ Validates YOLOv11 detection on sample images.
  2. `tests/test_hybrid_recommendation.py` $\rightarrow$ Validates TruncatedSVD and Taste DNA Cosine calculation.
  3. `tests/test_route_optimizer.py` $\rightarrow$ Validates Google OR-Tools TSPTW solver.
  4. `tests/test_nlu_copilot.py` $\rightarrow$ Validates ViSoBERT intent and entity parser.
  5. `tests/test_weather_service.py` $\rightarrow$ Validates Open-Meteo API fetching.
- **Deficiency:** Tests cannot be executed collectively via `pytest` without manual script invocation due to missing `pytest.ini` and relative import setup.

---

### 2.3 Mobile & Web Applications
- `KLTN-123-GastroWise-Mobile`: **0 Automated Tests.** No Jest or React Native Testing Library setup.
- `KLTN-123-GastroWise-FE`: **0 Automated Tests.** No unit or E2E tests.
- `KLTN-123-GastroWise-Admin-FE`: **0 Automated Tests.** No unit or E2E tests.

---

## 3. CODE COVERAGE ESTIMATION

| Subproject | Automated Unit Coverage | Integration Test Coverage | E2E Test Coverage | Quality Gate Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Backend Gateway (BE)** | ~42% (Core modules tested, restaurants/reviews broken) | Low (Mock-only) | None | **FAIL** (4 Broken Suites) |
| **AI Microservices (AI)** | ~35% (Ad-hoc scripts) | Medium | None | **WARN** (No Pytest runner) |
| **Mobile App (Mobile)** | **0%** | **0%** | **0%** | **FAIL** (Zero tests) |
| **Customer Web (FE)** | **0%** | **0%** | **0%** | **FAIL** (Zero tests) |
| **Admin Web (Admin-FE)** | **0%** | **0%** | **0%** | **FAIL** (Zero tests) |

---

## 4. ROOT CAUSE OF BACKEND UNIT TEST FAILURES

The 4 failing backend test suites (`restaurants.controller.spec.ts`, `restaurants.service.spec.ts`, `reviews.controller.spec.ts`, `reviews.service.spec.ts`) are boilerplate test files generated by `@nestjs/cli`. When Mongoose `@InjectModel(Restaurant.name)` and `@InjectModel(Review.name)` were introduced into the respective controllers and services, the corresponding test harnesses were not updated with mock providers.

### Exact Fix Required:
In `restaurants.service.spec.ts`:
```typescript
const module: TestingModule = await Test.createTestingModule({
  providers: [
    RestaurantsService,
    {
      provide: getModelToken(Restaurant.name),
      useValue: {
        find: jest.fn().mockReturnThis(),
        findById: jest.fn().mockResolvedValue(mockRestaurant),
        create: jest.fn().mockResolvedValue(mockRestaurant),
        exec: jest.fn(),
      },
    },
    // add ConfigService and HttpService mocks
  ],
}).compile();
```

---
*Report certified by QA Technical Lead.*

