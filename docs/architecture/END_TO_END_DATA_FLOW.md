# GASTROWISE – END-TO-END DATA FLOW & ARCHITECTURE SPECIFICATION
**Sprint 2 Technical Architecture Audit**  
**Role:** Principal Software Architect & QA Technical Lead  
**Audit Date:** November 2026  
**Status:** VERIFIED AGAINST CODEBASE

---

## 1. SYSTEM ARCHITECTURAL TOPOLOGY

The GastroWise platform is structured into four primary architectural tiers:

```mermaid
graph TB
    subgraph Client Tier
        Mobile["React Native / Expo Router Mobile App<br/>(iOS & Android)"]
        WebFE["Next.js Customer Web Client<br/>(:3000)"]
        AdminFE["Next.js Admin Dashboard<br/>(:3002)"]
    end

    subgraph API Gateway & Business Engine Tier
        NestBE["NestJS API Gateway & Business Engine<br/>(:3001)"]
        JWTAuth["JWT & Roles Guards"]
        MulterEngine["Multer File Processing"]
    end

    subgraph AI Microservices Tier
        FastAPI["Python FastAPI AI Service<br/>(:5000)"]
        HybridEngine["4-Stage Hybrid Recommender<br/>(Content-Based + SVD CF)"]
        RouteSolver["TSPTW Route Optimizer<br/>(Google OR-Tools)"]
        VisionService["YOLOv11 Food Detection<br/>+ CLAHE Preprocessing"]
        NLUCopilot["Copilot Dialogue Manager<br/>(Slot Extraction & Intent)"]
    end

    subgraph Data Tier
        Atlas["MongoDB Atlas Cluster (Cloud)<br/>Database: gastrowise"]
        AtlasRest["Collection: restaurants<br/>(Least-Privilege: find only)"]
        AtlasUsers["Collection: users<br/>(Users, Taste Profiles, Roles)"]
        AtlasItin["Collection: itineraries<br/>(Food Tours & Stops)"]
        AtlasInter["Collection: user_interactions<br/>(Behavior Matrix)"]
        AtlasReviews["Collection: reviews<br/>(Sentiment & Ratings)"]
    end

    Mobile -->|REST / JWT Bearer| NestBE
    WebFE -->|REST / JWT Bearer| NestBE
    AdminFE -->|REST / JWT Bearer| NestBE

    NestBE --> JWTAuth
    NestBE --> MulterEngine
    NestBE -->|Mongoose ODM| Atlas

    NestBE -->|HTTP REST| FastAPI
    FastAPI --> HybridEngine
    FastAPI --> RouteSolver
    FastAPI --> VisionService
    FastAPI --> NLUCopilot

    FastAPI -.->|Direct Read-Only / gastrowise_ai_service| AtlasRest
    Atlas --- AtlasUsers
    Atlas --- AtlasItin
    Atlas --- AtlasInter
    Atlas --- AtlasReviews
```

---

## 2. VERIFIED END-TO-END DATA FLOWS

### FLOW 1: USER AUTHENTICATION & SESSION MANAGEMENT
Handles user registration, credential verification, bcrypt password hashing, dual JWT token generation (Access & Refresh), refresh rotation, and logout.

#### Architecture Components:
- **Client:** `KLTN-123-GastroWise-Mobile/src/store/authStore.ts`
- **Gateway:** `KLTN-123-GastroWise-BE/src/auth/auth.controller.ts` $\rightarrow$ `auth.service.ts`
- **Database:** MongoDB Atlas `gastrowise.users`
- **AI Service:** None (Strictly isolated from auth)

#### Sequence Diagram:
```mermaid
sequenceDiagram
    autonumber
    actor User as Mobile User
    participant Mobile as Mobile App (authStore)
    participant SecStore as Expo SecureStore
    participant Nest as NestJS AuthController / Service
    participant Mongo as MongoDB Atlas (users)

    User->>Mobile: Input Email + Password
    Mobile->>Nest: POST /auth/login { email, password }
    Nest->>Mongo: findOneByEmail(email)
    Mongo-->>Nest: User Document (bcrypt hash, role, status)
    Nest->>Nest: bcrypt.compare(password, user.password)
    alt Password Invalid or User Banned
        Nest-->>Mobile: 401 Unauthorized / 403 Forbidden
        Mobile-->>User: Display error message
    else Credentials Valid
        Nest->>Nest: _generateTokens(userId, email, role)<br/>[Access: 1d, Refresh: 7d]
        Nest->>Nest: bcrypt.hash(refreshToken)
        Nest->>Mongo: updateRefreshToken(userId, hashedRefreshToken)
        Nest-->>Mobile: 200 OK { token, accessToken, refreshToken, user }
        Mobile->>SecStore: setItemAsync(ACCESS_TOKEN, accessToken)
        Mobile->>SecStore: setItemAsync(USER_INFO, user)
        Mobile-->>User: Navigate to (tabs)/index (Explore)
    end
```

#### DTO & Payload Definitions:
- **Request (`LoginDto`):**
  ```json
  {
    "email": "user@gastrowise.vn",
    "password": "SecurePassword123!"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "6724b112988cb148b897824b",
      "email": "user@gastrowise.vn",
      "name": "Nguyễn Văn A",
      "role": "user",
      "tasteProfile": {
        "spicy": 0.8,
        "sweet": 0.3,
        "sour": 0.2,
        "salty": 0.5,
        "umami": 0.9,
        "bitter": 0.1
      }
    }
  }
  ```

---

### FLOW 2: TASTE DNA RETRIEVAL & UPDATE
Allows users to retrieve their 6-dimensional gastronomic taste profile, calibrate radar chart preferences, and submit initial onboarding quiz vectors.

#### Architecture Components:
- **Client:** `KLTN-123-GastroWise-Mobile/src/app/profile/taste-dna.tsx`
- **Gateway:** `KLTN-123-GastroWise-BE/src/taste-dna/taste-dna.controller.ts` $\rightarrow$ `taste-dna.service.ts`
- **Database:** MongoDB Atlas `gastrowise.users` (`tasteProfile` subdocument)
- **AI Service:** None directly (Taste vector is used in Flow 4)

#### Sequence Diagram:
```mermaid
sequenceDiagram
    autonumber
    actor User as Mobile User
    participant Mobile as Mobile App (taste-dna.tsx)
    participant Nest as NestJS TasteDnaController / Service
    participant Mongo as MongoDB Atlas (users)

    User->>Mobile: Open Taste DNA Screen
    Mobile->>Nest: GET /taste-dna/me (Bearer Token)
    Nest->>Nest: JwtAuthGuard validates sub claim
    Nest->>Mongo: findById(userId).select('tasteProfile dietaryPreferences')
    Mongo-->>Nest: User Document
    Nest-->>Mobile: 200 OK { tasteVector: [0.8, 0.3, 0.2, 0.5, 0.9, 0.1], dietary: [...] }
    Mobile-->>User: Render 6-D Radar Chart & Sliders

    User->>Mobile: Drag Slider (e.g. increase Spicy to 0.95)
    Mobile->>Nest: PATCH /taste-dna/me { spicy: 0.95, dietaryPreferences: ["không cay"] }
    Nest->>Nest: UpdateTasteDnaDto Validation
    Nest->>Mongo: findByIdAndUpdate(userId, { 'tasteProfile.spicy': 0.95 })
    Mongo-->>Nest: Updated Document
    Nest-->>Mobile: 200 OK { success: true, profile: { ... } }
```

---

### FLOW 3: RESTAURANT DISCOVERY (GEOJSON 2DSPHERE & TEXT SEARCH)
High-performance spatial querying and full-text restaurant discovery based on device GPS coordinates, maximum distance radius, keyword search, price range, and category tags.

#### Architecture Components:
- **Client:** `KLTN-123-GastroWise-Mobile/src/app/(tabs)/index.tsx`, `explore.tsx`
- **Gateway:** `KLTN-123-GastroWise-BE/src/restaurants/restaurants.controller.ts` $\rightarrow$ `restaurants.service.ts`
- **Database:** MongoDB Atlas `gastrowise.restaurants` (Indexes: `location: "2dsphere"`, `tenQuan_text_diaChi_text_monAnTags_text`)
- **AI Service:** None (Direct DB spatial index query)

#### Sequence Diagram:
```mermaid
sequenceDiagram
    autonumber
    actor User as Mobile User
    participant Mobile as Mobile App (Explore Screen)
    participant Nest as NestJS RestaurantsController
    participant Mongo as MongoDB Atlas (restaurants)

    User->>Mobile: Open Explore / Filter by District / Price
    Mobile->>Nest: GET /restaurants/nearby?lat=10.7769&lon=106.7009&radiusKm=5&limit=20
    Nest->>Nest: Validate lat, lon, radiusKm
    Nest->>Mongo: find({ location: { $nearSphere: { $geometry: Point, $maxDistance: 5000 } } })
    Mongo-->>Nest: List of 20 Restaurant Documents
    Nest->>Nest: mapRestaurantToDTO(rawDocs) + computeDistance()
    Nest-->>Mobile: 200 OK { success: true, total: 20, data: [ ...DTOs ] }
    Mobile-->>User: Render Restaurant Cards with distance & rating badges
```

---

### FLOW 4: HYBRID PERSONALIZED RECOMMENDATIONS (4-STAGE AI PIPELINE)
The primary intelligence pipeline of GastroWise, orchestrating candidate retrieval, 6-D Taste DNA content-based cosine similarity, TruncatedSVD Collaborative Filtering, and contextual weather/distance boosting.

#### Architecture Components:
- **Client:** `KLTN-123-GastroWise-Mobile/src/app/(tabs)/index.tsx`
- **Gateway:** `KLTN-123-GastroWise-BE/src/restaurants/restaurants.service.ts`
- **AI Service:** `KLTN-123-GastroWise-AI/app/api/v1/recommendation.py` $\rightarrow$ `recommender.py` + `collaborative_filter.py`
- **Database:** MongoDB Atlas `gastrowise.restaurants` (Hydration)

#### Sequence Diagram:
```mermaid
sequenceDiagram
    autonumber
    actor User as Mobile User
    participant Mobile as Mobile App
    participant Nest as NestJS RestaurantsService
    participant AI as FastAPI (/recommend/hybrid)
    participant Mongo as MongoDB Atlas (restaurants)

    User->>Mobile: Browse Recommended Section
    Mobile->>Nest: GET /restaurants/recommended?lat=10.7769&lon=106.7009&limit=8
    Nest->>Mongo: Find user taste profile (if JWT present)
    Nest->>AI: POST /recommend/hybrid { user_id, user_gps, taste_vector, weather_type }
    
    rect rgb(240, 248, 255)
        Note over AI: 4-Stage AI Recommendation Pipeline:
        AI->>AI: Stage 1: Candidate Generation & Hard Constraints (Price, Geo, Dietary)
        AI->>AI: Stage 2: Content-Based Taste DNA 6-D Cosine Similarity
        AI->>AI: Stage 3: SVD Collaborative Filtering Scoring
        AI->>AI: Stage 4: Weather Context Boost + Distance Decay Reranking
    end

    AI-->>Nest: 200 OK { total: 8, items: [ { id, score, taste_score, cf_score, match_reasons, explanation } ] }
    Nest->>Mongo: find({ _id: { $in: candidateIds } })
    Mongo-->>Nest: Raw Restaurant Documents
    Nest->>Nest: Hydrate DTOs with aiScore, matchReasons, and localized metadata
    Nest-->>Mobile: 200 OK { success: true, isColdStart: false, data: [ ...HydratedDTOs ] }
    Mobile-->>User: Display Recommended Cards with Explanatory Match Pills
```

> [!WARNING]
> **API Contract Mismatch Identified:** NestJS `restaurants.service.ts:448` currently invokes `${aiBaseUrl}/v1/recommendation/recommend/hybrid`. FastAPI mounts the endpoint at `${aiBaseUrl}/recommend/hybrid`. This discrepancy produces an HTTP 404, which causes NestJS to trigger `getFallbackRecommendations()`, masking the AI recommendation engine with a basic rating-sorted database fallback!

---

### FLOW 5: AI ITINERARY GENERATION (OR-TOOLS TSPTW)
Transforms user time windows, budget limits, transportation modes, and food preferences into an optimized multi-stop gastronomic itinerary using Google OR-Tools.

#### Architecture Components:
- **Client:** `KLTN-123-GastroWise-Mobile/src/app/ai-planner.tsx`
- **Gateway:** `KLTN-123-GastroWise-BE/src/itineraries/itineraries.controller.ts` $\rightarrow$ `itineraries.service.ts`
- **AI Service:** `KLTN-123-GastroWise-AI/app/api/v1/routing.py` $\rightarrow$ `route_optimizer.py`
- **Database:** MongoDB Atlas `gastrowise.itineraries`

#### Sequence Diagram:
```mermaid
sequenceDiagram
    autonumber
    actor User as Mobile User
    participant Mobile as Mobile App (ai-planner.tsx)
    participant Nest as NestJS ItinerariesService
    participant AI as FastAPI (/routes/optimize)
    participant Mongo as MongoDB Atlas (itineraries)

    User->>Mobile: Enter Budget (250k), Mode (Motorbike), Stops (3), Time (11:00)
    Mobile->>Nest: POST /itineraries/generate { prompt, budget, routing_mode, desired_stops, start_time }
    Nest->>Nest: Retrieve candidate restaurants from DB
    Nest->>AI: POST /routes/optimize { start_location, start_time_mins, budget, routing_mode, candidates }
    
    rect rgb(245, 255, 245)
        Note over AI: Route Optimization Engine:
        AI->>AI: Select K Best Candidates (Starter -> Main -> Cafe/Dessert)
        AI->>AI: Build Haversine Distance & Travel Time Matrices
        AI->>AI: Solve TSPTW with Google OR-Tools / Progression Heuristic
        AI->>AI: Compute Arrival, Dwell, Departure Timetable & CO2 Savings
    end

    AI-->>Nest: 200 OK { stops, total_distance_km, total_duration_mins, total_cost, co2_saved_kg }
    Nest->>Nest: Map stops, generate UUIDs, compute remaining budget
    Nest->>Mongo: create(ItineraryDocument)
    Mongo-->>Nest: Saved Itinerary (_id: 6735c02b...)
    Nest-->>Mobile: 201 Created { _id, title, stops, total_distance_km, total_cost, co2SavedKg }
    Mobile-->>User: Navigate to /itinerary/[id] with interactive map & itinerary timeline
```

---

### FLOW 6: ITINERARY MANAGEMENT & RECALCULATION
Empowers users to customize generated itineraries: reordering stops, adding new venues, removing stops, and recalculating routes with dynamic TSP recalculation.

#### Architecture Components:
- **Client:** `KLTN-123-GastroWise-Mobile/src/app/itinerary/[id].tsx`
- **Gateway:** `KLTN-123-GastroWise-BE/src/itineraries/itineraries.controller.ts` $\rightarrow$ `itineraries.service.ts`
- **Database:** MongoDB Atlas `gastrowise.itineraries`

#### Sequence Diagram:
```mermaid
sequenceDiagram
    autonumber
    actor User as Mobile User
    participant Mobile as Mobile App (Itinerary Details)
    participant Nest as NestJS ItinerariesService
    participant Mongo as MongoDB Atlas (itineraries)

    User->>Mobile: Move Stop 3 to Stop 1 (Reorder)
    Mobile->>Nest: PATCH /itineraries/:id/reorder { stop_ids: ["s3", "s1", "s2"] }
    Nest->>Nest: JwtAuthGuard validates sub claim
    Nest->>Mongo: findById(id)
    Mongo-->>Nest: Itinerary Document
    Nest->>Nest: Check Ownership: (itinerary.user_id === actorId || actorRole === 'admin')
    Nest->>Nest: recalculateTimetableAndMetrics(reorderedStops)
    Nest->>Mongo: itinerary.save()
    Mongo-->>Nest: Updated Itinerary
    Nest-->>Mobile: 200 OK (Updated Itinerary with revised arrival/departure times)
    Mobile-->>User: Refresh Timeline View
```

---

### FLOW 7: INTERACTION TRACKING & SVD RETRAINING PIPELINE
Captures user behavioral interactions in the mobile app, batches them in local queues, flushes them to NestJS, and exports the interaction matrix to train the Collaborative Filtering model.

#### Architecture Components:
- **Client:** `KLTN-123-GastroWise-Mobile/src/lib/analytics/tracker.ts`
- **Gateway:** `KLTN-123-GastroWise-BE/src/interactions/interactions.service.ts`
- **Database:** MongoDB Atlas `gastrowise.user_interactions`
- **AI Service:** `KLTN-123-GastroWise-AI/app/api/v1/recommendation.py` $\rightarrow$ `collaborative_filter.py`

#### Sequence Diagram:
```mermaid
sequenceDiagram
    autonumber
    actor User as Mobile User
    participant Mobile as Mobile App (AnalyticsTracker)
    participant Nest as NestJS InteractionsController / Service
    participant Mongo as MongoDB Atlas (user_interactions)
    participant Admin as Admin FE / Cron
    participant AI as FastAPI (/cf/train)

    User->>Mobile: Views restaurant, dwells for 15s, clicks favorite
    Mobile->>Mobile: Enqueue events in memory (Buffer size: 10, Flush interval: 8s)
    Mobile->>Nest: POST /interactions/batch { events: [ { eventType: 'view', durationMs: 15000 }, ... ] }
    Nest->>Mongo: insertMany(events)
    Mongo-->>Nest: Write Result { count: 3 }
    Nest-->>Mobile: 200 OK { success: true, count: 3 }

    Note over Admin,AI: Asynchronous Offline Model Synchronization:
    Admin->>Nest: POST /restaurants/recommender/sync-cf (Requires Admin Role)
    Nest->>Mongo: find({ userId: { $exists: true } }).limit(5000)
    Mongo-->>Nest: Interaction Matrix List
    Nest->>AI: POST /cf/train { interactions }
    AI->>AI: TruncatedSVD(n_components=12).fit(InteractionMatrix)
    AI-->>Nest: 200 OK { success: true, user_count: 142, item_count: 178 }
    Nest-->>Admin: 200 OK { success: true, message: "Model updated" }
```

---

### FLOW 8: AI COPILOT & CHAT DIALOGUE ORCHESTRATION
Processes natural language culinary inquiries, extracts user intent and entities, queries candidate restaurants, and formats response cards with actionable mobile navigation links.

#### Architecture Components:
- **Client:** `KLTN-123-GastroWise-Mobile/src/app/ai-assistant.tsx`
- **Gateway:** `KLTN-123-GastroWise-BE/src/restaurants/restaurants.controller.ts` $\rightarrow$ `restaurants.service.ts`
- **AI Service:** `KLTN-123-GastroWise-AI/app/api/v1/copilot.py` $\rightarrow$ `nlu_service.py`
- **Database:** MongoDB Atlas `gastrowise.restaurants` (Candidate hydration)

#### Sequence Diagram:
```mermaid
sequenceDiagram
    autonumber
    actor User as Mobile User
    participant Mobile as Mobile App (ai-assistant.tsx)
    participant Nest as NestJS RestaurantsService
    participant AI as FastAPI (/copilot/message)
    participant Mongo as MongoDB Atlas (restaurants)

    User->>Mobile: "Tìm quán phở bò gần đây giá dưới 60k"
    Mobile->>Nest: POST /restaurants/chat { message, userLat, userLon }
    Nest->>AI: POST /copilot/message { message, user_gps: [10.7769, 106.7009], taste_vector }
    
    rect rgb(255, 250, 240)
        Note over AI: NLU Dialogue Processing:
        AI->>AI: Classify Intent: search_food
        AI->>AI: Extract Entities: dish='phở bò', max_price=60000, geo='near'
        AI->>AI: Search Matching Candidates & Generate Explanations
        AI->>AI: Construct Action Card ('search_results_action')
    end

    AI-->>Nest: 200 OK { reply, intent, entities, action_card, results: [ { id, name, ... } ] }
    Nest->>Mongo: find({ _id: { $in: candidateIds } })
    Mongo-->>Nest: Restaurant Documents
    Nest->>Nest: Hydrate Results with complete DTOs
    Nest-->>Mobile: 200 OK { reply, intent, action_card, results: [ ...HydratedDTOs ] }
    Mobile-->>User: Render Chat Bubble with interactive Action Card
```

> [!WARNING]
> **API Contract Mismatch Identified:** NestJS `restaurants.service.ts:969` invokes `${aiBaseUrl}/v1/copilot/message`. FastAPI mounts the endpoint at `${aiBaseUrl}/copilot/message`. This discrepancy produces an HTTP 404, prompting NestJS to execute regex-based keyword search fallback!

---

## 3. SUMMARY OF IDENTIFIED CONTRACT & ROUTING MISMATCHES

| Item | Origin Tier | Target Tier | Called Endpoint | Actual Route in Target | Impact | Remediation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MIS-01** | Mobile Client | NestJS Gateway | `${EXPO_PUBLIC_API_URL}/auth/login`<br/>(`.../api/v1/auth/login`) | `POST /auth/login` | Mobile calls return 404 unless `.env` omits `/api/v1` or NestJS adds global prefix. | Set `app.setGlobalPrefix('api/v1')` in NestJS `main.ts` or update Mobile `.env`. |
| **MIS-02** | NestJS Gateway | FastAPI Service | `POST /v1/recommendation/recommend/hybrid` | `POST /recommend/hybrid` | AI Hybrid recommendations return 404 $\rightarrow$ fallback rating sort is always served. | Align FastAPI prefix with `/v1/recommendation` or change BE call to `/recommend/hybrid`. |
| **MIS-03** | NestJS Gateway | FastAPI Service | `POST /v1/recommendation/cf/train` | `POST /cf/train` | Interaction matrix sync returns 404 $\rightarrow$ SVD model is never retrained from BE. | Align FastAPI prefix or update BE call to `/cf/train`. |
| **MIS-04** | NestJS Gateway | FastAPI Service | `POST /v1/copilot/message` | `POST /copilot/message` | AI Copilot returns 404 $\rightarrow$ regex fallback is always returned to user. | Align FastAPI router prefix to `/v1/copilot` or update BE call to `/copilot/message`. |
| **MIS-05** | NestJS Gateway | MongoDB / Mobile | `duration_mins`, `transit_to_next_mins` | `dining_duration_mins`, `transit_time_mins` | Inconsistent naming in `itineraries.service.ts` causes Mongoose default fallbacks. | Normalize property names across `itinerary.schema.ts`, `itineraries.service.ts`, and Mobile UI. |

