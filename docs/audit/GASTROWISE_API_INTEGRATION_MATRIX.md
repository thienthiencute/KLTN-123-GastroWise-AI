# GASTROWISE – API INTEGRATION & CONTRACT MATRIX

**Audit Date:** November 14, 2026  
**Auditor:** Principal Software Architect, Senior Backend Engineer & API Architect  
**Scope:** Complete Cross-Repository API Contracts & Integration Points (Client $\leftrightarrow$ Gateway $\leftrightarrow$ AI Microservices)

---

## 1. INTEGRATION ARCHITECTURE OVERVIEW

```
                                      [ CLIENT LAYER ]
                                              │
                      ┌───────────────────────┼───────────────────────┐
                      │                       │                       │
             Mobile App (Expo)         Customer FE (Next)      Admin FE (Next)
                      │                       │                       │
                      └───────────────────────┬───────────────────────┘
                                              │
                                 HTTP / JSON (REST + JWT)
                                 Port 3001 (Gateway)
                                              ▼
                                 [ NESTJS API GATEWAY ]
                                (KLTN-123-GastroWise-BE)
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      │                                               │
               Mongoose Driver                                HTTP / JSON (Internal)
               Port 27017 / Cloud                             Port 5000
                      ▼                                               ▼
             [ MONGODB DATABASE ]                           [ FASTAPI AI ENGINE ]
                                                           (KLTN-123-GastroWise-AI)
```

---

## 2. BREAKING INTEGRATION DISCREPANCIES (CRITICAL)

The audit discovered **three major contract mismatches** that disrupt live platform operations:

### Discrepancy 1: Personalized Recommendation Route 404
- **Caller Location:** `KLTN-123-GastroWise-BE/src/restaurants/restaurants.service.ts` (Line 448)
  ```typescript
  const response = await axios.post(`${aiBaseUrl}/v1/recommendation/recommend/hybrid`, payload);
  ```
- **Callee Location:** `KLTN-123-GastroWise-AI/main.py` & `app/api/v1/router.py`
  - In `main.py`: `app.include_router(api_router)` without `/v1` prefix.
  - In `app/api/v1/router.py`: `router.include_router(recommendation.router, prefix="/recommend", tags=["recommendation"])`
  - Resulting Live AI Route: `POST /recommend/hybrid`
- **Failure Mode:** NestJS makes HTTP request to `http://localhost:5000/v1/recommendation/recommend/hybrid` $\rightarrow$ FastAPI responds with **404 Not Found**.
- **Impact:** NestJS catches the 404 in a try-catch block and silently executes fallback database sorting. **AI personalization is completely bypassed in production!**

### Discrepancy 2: AI Food Copilot Route 404
- **Caller Location:** `KLTN-123-GastroWise-BE/src/restaurants/restaurants.service.ts` (Line 969)
  ```typescript
  const response = await axios.post(`${aiBaseUrl}/v1/copilot/message`, { query, history, tasteProfile });
  ```
- **Callee Location:** `KLTN-123-GastroWise-AI/main.py`
  - In `main.py`: `app.include_router(copilot_router, prefix="/copilot", tags=["Copilot"])`
  - Resulting Live AI Route: `POST /copilot/message` (missing `/v1` prefix)
- **Failure Mode:** NestJS dispatches to `http://localhost:5000/v1/copilot/message` $\rightarrow$ FastAPI responds with **404 Not Found**.
- **Impact:** NestJS catches 404 and falls back to naive regex keyword matching. **NLU and intent classification are completely bypassed!**

### Discrepancy 3: Mobile Base URL Prefix Mismatch
- **Mobile Configuration:** `KLTN-123-GastroWise-Mobile/.env`
  ```bash
  EXPO_PUBLIC_API_URL=http://10.161.30.252:3001/api/v1
  ```
- **Backend Configuration:** `KLTN-123-GastroWise-BE/src/main.ts`
  - Does **NOT** configure `app.setGlobalPrefix('api/v1')`.
  - All controllers listen on root: `/auth`, `/restaurants`, `/itineraries`, etc.
- **Failure Mode:** Mobile requests send URLs like `http://...:3001/api/v1/auth/login` $\rightarrow$ NestJS returns **404 Cannot POST /api/v1/auth/login**.
- **Remediation Requirement:** Standardize API versioning by adding `app.setGlobalPrefix('api/v1')` to NestJS `main.ts`, or standardize client environments.

---

## 3. CLIENT $\leftrightarrow$ BACKEND GATEWAY API CONTRACTS

### 3.1 Authentication & User Management
| Method | Gateway Endpoint | Auth Required | Request Body / Query Params | Expected Response | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Public | `{ email, password, name, role? }` | `{ accessToken, refreshToken, user }` | Verified |
| `POST` | `/auth/login` | Public | `{ email, password }` | `{ accessToken, refreshToken, user }` | Verified |
| `POST` | `/auth/refresh` | Bearer (Refresh) | `{}` | `{ accessToken, refreshToken }` | Verified |
| `POST` | `/auth/forgot-password` | Public | `{ email }` | `{ message: string }` | Verified (Email OTP) |
| `POST` | `/auth/reset-password` | Public | `{ email, otp, newPassword }` | `{ message: string }` | Verified (Plaintext OTP) |
| `GET` | `/users/profile` | Bearer (Access) | None | `{ _id, email, name, avatar, tasteProfile, dietaryPreferences }` | Verified |
| `PATCH`| `/users/profile` | Bearer (Access) | `{ name?, dietaryPreferences?, allergies? }` | `{ user }` | Verified |
| `POST` | `/users/avatar` | Bearer (Access) | `multipart/form-data` (`file`) | `{ avatarUrl: string }` | Defect (hardcoded localhost) |

### 3.2 Restaurants & Menus
| Method | Gateway Endpoint | Auth Required | Request Body / Query Params | Expected Response | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/restaurants` | Public | `?page=1&limit=20&search=...&cuisine=...` | `{ data: Restaurant[], total, page }` | Verified |
| `GET` | `/restaurants/nearby` | Public | `?latitude=...&longitude=...&radiusKm=5` | `Restaurant[]` (with distanceKm) | Verified |
| `GET` | `/restaurants/:id` | Public | None | `Restaurant` (with menuItems, reviews) | Verified |
| `GET` | `/restaurants/recommendations/for-you` | Bearer (Access) | `?latitude=...&longitude=...&limit=10` | `Restaurant[]` (with matchScore) | Degraded (404 to AI $\rightarrow$ DB sort fallback) |
| `POST` | `/restaurants/search-by-image` | Public | `multipart/form-data` (`image`) | `{ detectedDish, confidence, restaurants: [] }` | Degraded (Security risk: unvalidated upload) |
| `POST` | `/restaurants/chat-copilot` | Bearer (Access) | `{ query: string, history: [] }` | `{ reply: string, intent: string, recommendations: [] }` | Degraded (404 to AI $\rightarrow$ regex fallback) |

### 3.3 Itineraries & Smart Food Journeys
| Method | Gateway Endpoint | Auth Required | Request Body / Query Params | Expected Response | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/itineraries/generate` | Bearer (Access) | `{ title, startDate, startLocation, preferences, mealSlots }` | `Itinerary` (optimized stops, time windows, distance) | Verified (Calls AI `/route/optimize`) |
| `GET` | `/itineraries` | Bearer (Access) | `?status=...&page=1` | `{ data: Itinerary[], total }` | Verified |
| `GET` | `/itineraries/:id` | Bearer (Access) | None | `Itinerary` (full stops breakdown) | Verified |
| `PATCH`| `/itineraries/:id` | Bearer (Access) | `{ stops?, status?, title? }` | `Itinerary` | Verified |
| `DELETE`| `/itineraries/:id` | Bearer (Access) | None | `{ success: true }` | Verified |

### 3.4 Reviews & Favorites
| Method | Gateway Endpoint | Auth Required | Request Body / Query Params | Expected Response | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/reviews` | Bearer (Access) | `{ restaurantId, rating, comment, photos?, tasteScores? }` | `Review` (with AI sentiment analysis) | Verified |
| `GET` | `/reviews/restaurant/:id` | Public | `?page=1&limit=10` | `{ data: Review[], averageRating, ratingBreakdown }` | Verified |
| `POST` | `/favorites/toggle` | Bearer (Access) | `{ restaurantId }` | `{ isFavorite: boolean }` | Verified |
| `GET` | `/favorites/collections` | Bearer (Access) | None | `FavoriteCollection[]` | Verified |
| `POST` | `/favorites/collections` | Bearer (Access) | `{ name, description? }` | `FavoriteCollection` | Verified |

---

## 4. GATEWAY $\leftrightarrow$ FASTAPI AI MICROSERVICES CONTRACTS

| Gateway Caller Service | Target AI Endpoint | Expected HTTP Method | Payload Contract | AI Service Actual Route | Status & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `restaurants.service.ts:448` | `/v1/recommendation/recommend/hybrid` | `POST` | `{ userId, userTasteProfile, userLocation, candidateRestaurants, weatherContext }` | `/recommend/hybrid` | **404 MISMATCH** (Missing `/v1/recommendation`) |
| `restaurants.service.ts:969` | `/v1/copilot/message` | `POST` | `{ query, history, tasteProfile }` | `/copilot/message` | **404 MISMATCH** (Missing `/v1`) |
| `restaurants.service.ts:512` | `/vision/detect` | `POST` | `multipart/form-data` (`image: binary`) | `/vision/detect` | Verified (200 OK for 5 classes) |
| `itineraries.service.ts:182` | `/route/optimize` | `POST` | `{ stops: [{ id, lat, lng, timeWindow, duration }], startLocation, departureTime }` | `/route/optimize` | Verified (200 OK via OR-Tools) |
| `reviews.service.ts:114` | `/sentiment/analyze` | `POST` | `{ text: string }` | `/sentiment/analyze` | Verified (200 OK via ViSoBERT) |

---

## 5. DTO & PAYLOAD VALIDATION DEFICIENCIES

1. **ValidationPipe Configuration:**
   - In `KLTN-123-GastroWise-BE/src/main.ts`:
     ```typescript
     app.useGlobalPipes(new ValidationPipe());
     ```
   - **Vulnerability:** Lacks `{ whitelist: true, forbidNonWhitelisted: true, transform: true }`. Clients can inject arbitrary unvalidated properties into MongoDB models via request payloads.
2. **Missing `X-Internal-AI-Key` Propagation:**
   - Neither NestJS `Axios` instances nor FastAPI route handlers include internal authorization headers. Any host on the local network or container network can hit the AI microservices directly without authentication.

---
*Report certified by Principal Software Architect & QA Lead.*

