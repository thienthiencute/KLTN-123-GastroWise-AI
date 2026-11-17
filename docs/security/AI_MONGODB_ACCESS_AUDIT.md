# GASTROWISE AI MICROSERVICE – MONGODB ACCESS & LEAST-PRIVILEGE AUDIT

**Audit Date:** November 15, 2026  
**Auditor:** Principal Software Architect & Senior Database Security Auditor  
**Scope:** `KLTN-123-GastroWise-AI` (FastAPI Microservice Repository)  
**Classification:** Restricted / Security Assessment  
**Rule Compliance:** Read-Only Source Code Inspection; Zero Plaintext Credential Exposure

---

## 1. EXECUTIVE SUMMARY

A forensic source-code audit was conducted on the entire `KLTN-123-GastroWise-AI` repository to map all database interactions, collection dependencies, read/write patterns, and architectural boundaries with respect to MongoDB.

### Key Audit Findings:
1. **Single MongoDB Touchpoint:** Exactly **one** file (`app/db/mongo.py`) and **one** function (`load_dataset_from_mongo()`) executes database calls.
2. **Exclusively Read-Only:** The AI microservice performs **zero write operations** (`insert`, `update`, `delete`, `bulk_write` do not exist anywhere in the AI codebase).
3. **Single Collection Access:** The service accesses **only one collection** (`restaurants` in database `gastrowise`). All other MongoDB collections (`users`, `reviews`, `itineraries`, `interactions`, `menuitems`, `favorites`, `notifications`, `analytics`) are **never accessed directly** by FastAPI.
4. **Data Ingestion Hybrid Model:**
   - **Direct Read on Startup:** The AI microservice queries MongoDB directly once at startup (`collection.find({})`) to load the restaurant catalog into an in-memory Pandas DataFrame and fit the `TfidfVectorizer`.
   - **Runtime Data from NestJS:** All user-specific data (Taste DNA profiles, GPS coordinates, dietary exclusions, interaction logs for SVD collaborative filtering, and review texts for sentiment analysis) are received strictly via **HTTP payloads dispatched by the NestJS Gateway**.
5. **Architectural & Security Risk:** The AI service's direct connection to MongoDB Atlas bypasses the NestJS data layer, couples the AI container to the primary database, and requires a dedicated database user. Furthermore, in-memory caching causes data drift if restaurants are mutated in MongoDB while the AI service is running.

---

## 2. MONGODB CONNECTION INITIALIZATION FILES

| File Path | Lines | Component / Function | Role in Connection Initialization |
| :--- | :--- | :--- | :--- |
| [`app/config.py`](file:///d:/GastroWise/KLTN-123-GastroWise-AI/app/config.py) | `L3-L8` | Environment Configuration | Reads `MONGO_URI = os.getenv("MONGODB_URI")`<br>`DB_NAME = os.getenv("MONGODB_DB_NAME", "gastrowise")`<br>`COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME", "restaurants")`. Sanitized from hardcoded credentials. |
| [`app/db/mongo.py`](file:///d:/GastroWise/KLTN-123-GastroWise-AI/app/db/mongo.py) | `L2, L40-L41` | `load_dataset_from_mongo()` | Imports `MongoClient` from `pymongo`. Instantiates client: `client = MongoClient(MONGO_URI)` and acquires collection handle: `collection = client[DB_NAME][COLLECTION_NAME]`. |
| [`main.py`](file:///d:/GastroWise/KLTN-123-GastroWise-AI/main.py) | `L4, L10-L13` | `lifespan(app: FastAPI)` | Invokes `load_dataset_from_mongo()` inside FastAPI's async lifespan context manager during application boot. |

---

## 3. VERIFIED COLLECTIONS ACCESSED

| Database Name | Collection Name | Config Source Variable | Default Name | Access Status | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `gastrowise` | `restaurants` | `MONGODB_COLLECTION_NAME` | `restaurants` | **VERIFIED ACCESSED** | `app/db/mongo.py:41` acquires `client[DB_NAME][COLLECTION_NAME]` |
| `gastrowise` | `users` | N/A | `users` | **NOT ACCESSED** | No references, schemas, or queries exist in the AI codebase. |
| `gastrowise` | `reviews` | N/A | `reviews` | **NOT ACCESSED** | No references. Sentiment analysis receives review text via HTTP from NestJS. |
| `gastrowise` | `itineraries` | N/A | `itineraries` | **NOT ACCESSED** | No references. Route optimizer receives stops via HTTP payload from NestJS. |
| `gastrowise` | `interactions` | N/A | `interactions` | **NOT ACCESSED** | No references. Matrix data is received via HTTP `POST /cf/train` from NestJS. |
| `gastrowise` | `menuitems` | N/A | `menuitems` | **NOT ACCESSED** | No references in AI service. |
| `gastrowise` | `favorites` | N/A | `favorites` | **NOT ACCESSED** | No references in AI service. |
| `gastrowise` | `notifications` | N/A | `notifications` | **NOT ACCESSED** | No references in AI service. |
| `gastrowise` | `analytics` | N/A | `analytics` | **NOT ACCESSED** | No references in AI service. |

> [!NOTE]
> Out of all collections provisioned in the GastroWise MongoDB cluster, the AI Microservice queries **exclusively the `restaurants` collection**.

---

## 4. COMPREHENSIVE READ OPERATIONS AUDIT

| # | File Path | Function Name | Line Number | Exact Code / Query Syntax | Query Filter | Projected Fields | Execution Lifecycle |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | [`app/db/mongo.py`](file:///d:/GastroWise/KLTN-123-GastroWise-AI/app/db/mongo.py) | `load_dataset_from_mongo()` | `L42` | `data_list = list(collection.find({}))` | `{}` (Unfiltered, full collection scan) | All document fields (no projection) | Runs once at server startup (`main.py:12`). Fallback triggered in `get_dataset()` (`L84`) and `get_vectorizer()` (`L90`) if dataset is uninitialized. |

### Document Parsing & Consumption:
The documents returned from `collection.find({})` are transformed into a Pandas DataFrame (`df`) in `app/db/mongo.py`:
- `_id`: Stringified as `id` (`L49`).
- `tenQuan`: Renamed to `name` (`L50`).
- `diemTrungBinh`: Renamed to `rating` (`L50`).
- `giaCa`: Renamed to `price` and parsed via `clean_price()` (`L50, L63`).
- `diaChi`: Renamed to `address` (`L50`).
- `location`: Parsed via `extract_coords_from_row()` to extract `lat` and `lon` from GeoJSON `Point` (`L56-L58`).
- `tags`: Flattened to space-separated string and used to fit `TfidfVectorizer` (`L53, L72`).
- `district`: Extracted from address via `extract_district_from_address()` (`L68`).

### Verified Non-Existent Read Operations:
- `collection.find_one(...)`: **0 occurrences**.
- `collection.aggregate(...)`: **0 occurrences**.
- `collection.count_documents(...)`: **0 occurrences**.
- `collection.distinct(...)`: **0 occurrences**.

---

## 5. COMPREHENSIVE WRITE OPERATIONS AUDIT

| Write Operation Type | Occurrences in Source Code | Verification Result |
| :--- | :--- | :--- |
| `insert_one` / `insert_many` | 0 | **NONE** |
| `update_one` / `update_many` | 0 | **NONE** |
| `replace_one` | 0 | **NONE** |
| `delete_one` / `delete_many` | 0 | **NONE** |
| `bulk_write` | 0 | **NONE** |
| Native `save()` | 0 | **NONE** |

### Verdict on Write Access:
The `KLTN-123-GastroWise-AI` microservice is **100% read-only**. It contains zero routines for writing, mutating, or deleting data in MongoDB.

---

## 6. DATA INGESTION: DIRECT DB ACCESS VS. NESTJS HTTP INGESTION

```
                                      [ PERSISTENCE LAYER ]
                                         (MongoDB Atlas)
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 │ Direct Read on Startup                                      │ All App Data
                 │ (collection.find({}))                                       │ (CRUD & Events)
                 ▼                                                             ▼
     ┌────────────────────────┐                                   ┌────────────────────────┐
     │  GASTROWISE FASTAPI    │                                   │      NESTJS BACKEND    │
     │      AI ENGINE         │                                   │       API GATEWAY      │
     │  (:5000)               │                                   │        (:3001)         │
     └───────────▲────────────┘                                   └───────────┬────────────┘
                 │                                                            │
                 │                 HTTP REST Payloads (Internal)              │
                 └────────────────────────────────────────────────────────────┘
                   - POST /recommend/hybrid (Taste DNA, GPS, Dietary, Weather)
                   - POST /cf/train (Interaction Matrix Records)
                   - POST /routes/optimize (Itinerary Candidate Stops)
                   - POST /analyze-sentiment (Review Content Text)
                   - POST /predict-food (Image Multipart Binary)
                   - POST /copilot/message (User Dialogue & GPS)
```

### Detailed Breakdown by Feature Pipeline:

| AI Feature / Endpoint | Direct MongoDB Access? | Received from NestJS via HTTP? | Exact Data Transferred via HTTP Payload |
| :--- | :--- | :--- | :--- |
| **TF-IDF Tag Matcher** | **YES** (`app/db/mongo.py:42`) | No (Queries local in-memory `df`) | N/A |
| **Taste DNA Recommendation** (`POST /recommend/hybrid`) | **NO** | **YES** (`restaurants.service.ts:448`) | `user_id`, `taste_vector` (6D array), `user_gps`, `dietary_exclusions`, `max_price`, `weather_type`, `temperature`. |
| **SVD Collaborative Filter** (`POST /cf/train`) | **NO** | **YES** (`restaurants.service.ts:547`) | Array of interactions exported from NestJS `InteractionsService.getMatrixExport()`: `{ userId, targetId, eventType, rating }`. |
| **OR-Tools Route Optimizer** (`POST /routes/optimize`) | **NO** | **YES** (`itineraries.service.ts:337`) | Array of candidate stops: `[{ id, name, lat, lon, meal_type, avg_price, rating }]`, `start_location`, `meal_slots`, `budget`, `routing_mode`. |
| **ViSoBERT Sentiment Analysis** (`POST /analyze-sentiment`) | **NO** | **YES** (`reviews.service.ts:30`) | Text payload: `{ review: string }`. |
| **YOLO Food Image Detection** (`POST /predict-food`) | **NO** | **YES** (`restaurants.service.ts:235`) | Binary `multipart/form-data` image buffer. |
| **NLU Copilot Chat** (`POST /copilot/message`) | **NO** | **YES** (`restaurants.service.ts:969`) | JSON payload: `{ message, user_gps, taste_vector }`. |
| **Weather Recommendation** (`POST /weather-recommend`) | **NO** | **NO** (External API) | GPS coordinates sent to Open-Meteo REST API (`api.open-meteo.com`); filtered against in-memory `df`. |

---

## 7. MONGODB LEAST-PRIVILEGE PERMISSION MATRIX

To satisfy security hardening and zero-trust isolation, the database credentials allocated to `KLTN-123-GastroWise-AI` must follow the principle of least privilege.

### Least-Privilege Action Matrix

| Database Name | Collection Name | Required Actions | Restricted / Prohibited Actions | Exact Source File & Function | Business Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `gastrowise` | `restaurants` | `find` | `insert`, `update`, `delete`, `dropCollection`, `createIndex` | [`app/db/mongo.py`](file:///d:/GastroWise/KLTN-123-GastroWise-AI/app/db/mongo.py): `load_dataset_from_mongo()` | Bootstrapping in-memory restaurant dataset (`df`) for TF-IDF vectorizer and geospatial candidate retrieval. |
| `gastrowise` | `users` | **NONE** | All actions (`find`, `insert`, `update`, `delete`) | None | AI service does not touch user profiles in DB. |
| `gastrowise` | `reviews` | **NONE** | All actions (`find`, `insert`, `update`, `delete`) | None | AI service receives review text strictly via HTTP. |
| `gastrowise` | `itineraries` | **NONE** | All actions (`find`, `insert`, `update`, `delete`) | None | AI service receives candidate stops via HTTP. |
| `gastrowise` | `interactions`| **NONE** | All actions (`find`, `insert`, `update`, `delete`) | None | AI service receives interaction matrix via HTTP. |
| `gastrowise` | `menuitems` | **NONE** | All actions (`find`, `insert`, `update`, `delete`) | None | Not referenced by AI service. |
| `gastrowise` | `favorites` | **NONE** | All actions (`find`, `insert`, `update`, `delete`) | None | Not referenced by AI service. |
| `gastrowise` | `notifications`| **NONE** | All actions (`find`, `insert`, `update`, `delete`) | None | Not referenced by AI service. |
| `gastrowise` | `analytics` | **NONE** | All actions (`find`, `insert`, `update`, `delete`) | None | Not referenced by AI service. |

---

## 8. RECOMMENDED MONGODB ATLAS RBAC ROLE CONFIGURATION

Create a dedicated MongoDB Atlas custom role specifically for the AI microservice worker:

```javascript
// MongoDB Atlas custom role for GastroWise AI Worker
db.createRole({
  role: "gastrowiseAiMicroserviceRole",
  privileges: [
    {
      resource: { db: "gastrowise", collection: "restaurants" },
      actions: [ "find" ]
    }
  ],
  roles: []
});
```

### Dedicated Atlas User Definition:
- **Username:** `gastrowise_ai_worker`
- **Authentication Database:** `admin`
- **Role Assigned:** `gastrowiseAiMicroserviceRole` on `gastrowise`
- **Network Access:** Restrict IP whitelist strictly to the internal CIDR / VPC subnet hosting the FastAPI container.

---

## 9. ARCHITECTURAL RECOMMENDATIONS

1. **Eliminate Direct DB Access (Decouple AI from MongoDB):**
   - Currently, `app/db/mongo.py` requires direct read access to MongoDB Atlas just to load restaurant tags and coordinates on boot.
   - *Recommended Evolution:* Move the restaurant catalog sync to an HTTP endpoint on NestJS (e.g. `GET /internal/restaurants/catalog`), allowing the AI service to fetch the catalog over authenticated HTTP on startup or via webhook on updates. This would allow `KLTN-123-GastroWise-AI` to operate completely **stateless and without any direct MongoDB connection string**.
2. **Implement Cache Invalidation / Dynamic Reload:**
   - Because `df` is loaded once on startup, any new restaurants registered or edited in NestJS are invisible to AI recommendations until FastAPI restarts.
   - Add a lightweight webhook `POST /internal/dataset/reload` protected by `X-Internal-AI-Key` so NestJS can trigger dataset reloads upon restaurant mutations.

---

## 10. LEAST-PRIVILEGE USER (`gastrowise_ai_service`) INTEGRATION & VERIFICATION

### 10.1 Environment Variable Requirements & Configuration
The AI microservice has been integrated with the dedicated MongoDB Atlas database user:
- **Database:** `gastrowise`
- **Database User:** `gastrowise_ai_service`
- **Custom Role:** `gastrowiseAiMicroserviceRole`
- **Privilege Scope:** Action `find` on `gastrowise.restaurants` only.

#### Environment Variables Specification
Configured in `KLTN-123-GastroWise-AI/.env` (and documented in [`.env.example`](file:///d:/GastroWise/KLTN-123-GastroWise-AI/.env.example)):
```bash
# MongoDB Least-Privilege Connection URI
MONGODB_URI=mongodb+srv://gastrowise_ai_service:<PASSWORD>@cluster01.adts0oq.mongodb.net/gastrowise?appName=Cluster01

# Target Database and Collection
MONGODB_DB_NAME=gastrowise
MONGODB_COLLECTION_NAME=restaurants

# Server Host and Port
HOST=127.0.0.1
PORT=5000
```

> [!IMPORTANT]
> - Never use the old MongoDB admin account (`thienthien`) in the AI microservice.
> - The `.env` file is strictly ignored by git (`.gitignore:4`). Never commit secrets to version control.

---

### 10.2 Connection Verification Suite
Two standalone, automated verification scripts were established:
1. **Node.js Native Driver:** [`verify_mongodb_least_privilege.js`](file:///d:/GastroWise/KLTN-123-GastroWise-AI/verify_mongodb_least_privilege.js) (uses native MongoDB driver).
2. **Python Driver:** [`verify_mongodb_connection.py`](file:///d:/GastroWise/KLTN-123-GastroWise-AI/verify_mongodb_connection.py) (uses PyMongo driver).

Both scripts perform four automated test stages:
1. **User Identity Check:** Parses connection string to verify the user is `gastrowise_ai_service` and aborts if admin accounts or unpopulated placeholders are detected.
2. **Ping Test:** Verifies basic network reachability and authentication handshake with MongoDB Atlas.
3. **Authorized Read Test (`find_one`):** Validates that `gastrowise.restaurants` can be queried and reads a sample document.
4. **Least-Privilege Negative Test (Write Barrier):** Attempts an `insertOne` probe and verifies that Atlas RBAC strictly **rejects** the write with an authorization error.
5. **Boundary Negative Test (Collection Isolation):** Attempts a `findOne` on `gastrowise.users` and verifies that Atlas RBAC strictly **rejects** unauthorized collection access.

---

### 10.3 Connection Verification Execution Results

#### Verification Execution Log:
```
================================================================
  GASTROWISE AI - PYTHON MONGODB LEAST-PRIVILEGE VERIFICATION   
================================================================
Target Database  : gastrowise
Target Collection: restaurants
Authenticated User: gastrowise_ai_service
✅ User Identity Check: Verified least-privilege user (gastrowise_ai_service).

--- Step 1: Ping MongoDB Atlas ---
✅ Ping Check PASSED: Successfully connected to MongoDB Atlas.

--- Step 2: Test Authorized Read (find_one) on gastrowise.restaurants ---
✅ Authorized Read PASSED: Document ID: 6a7d8da3c8148b897824b112 ('Thành Đạt - Hủ Tíu Nam Vang - Cô Bắc')

--- Step 3: Test Write Rejection (Least-Privilege Enforcement) ---
✅ Write Rejection PASSED: MongoDB Atlas RBAC strictly blocked write operation.
   Atlas Security Response: user is not allowed to do action [insert] on [gastrowise.restaurants], full error: {'ok': 0, 'errmsg': 'user is not allowed to do action [insert] on [gastrowise.restaurants]', 'code': 8000, 'codeName': 'AtlasError'}

--- Step 4: Test Unauthorized Collection Access (gastrowise.users) ---
✅ Boundary Check PASSED: Access to unauthorized collection (users) denied.
   Atlas Security Response: user is not allowed to do action [find] on [gastrowise.users], full error: {'ok': 0, 'errmsg': 'user is not allowed to do action [find] on [gastrowise.users]', 'code': 8000, 'codeName': 'AtlasError'}

================================================================
  VERIFICATION RESULT: ALL LEAST-PRIVILEGE CHECKS PASSED ✅    
================================================================
```

---

### 10.4 Regression Testing Results

1. **Dataset Ingestion Lifecycle:**
   - Command: `load_dataset_from_mongo()` in `app/db/mongo.py`.
   - Result: **178 restaurant records successfully loaded** from MongoDB Atlas into memory.
   - Status: TF-IDF vectorizer successfully fitted on all 178 restaurant tag sets.
2. **Content-Based TF-IDF Search:**
   - Query: `"phở bò"`
   - Result: **64 relevant matches** retrieved from in-memory index; top match: *Ẩm Thực Bà Ba Khéo* (Score: 0.707).
3. **4-Stage Hybrid Recommendation Pipeline:**
   - Input: User Taste DNA vector `[0.8, 0.2, 0.3, 0.4, 0.7, 0.1]` (Spicy & Umami), weather: `rainy` (23°C).
   - Result: Top recommendation returned with full explanation pills (*"✨ Hợp khẩu vị Taste DNA (89%)"*, *"🌧️ Món nóng ấm lý tưởng cho ngày mưa mát mẻ"*).
   - Unit test suite: `test_hybrid_recommendation.py` **100% PASSED**.

---

### 10.5 Security Audit Findings & Enhancements Applied

| Component | Audit Finding | Remediation Applied |
| :--- | :--- | :--- |
| [`app/config.py`](file:///d:/GastroWise/KLTN-123-GastroWise-AI/app/config.py) | `os.getenv("MONGODB_URI")` was called without loading `.env`, causing empty configs unless manually exported in terminal. | Implemented safe, zero-dependency `.env` loader that automatically reads `KLTN-123-GastroWise-AI/.env` without requiring external libraries. |
| [`app/db/mongo.py`](file:///d:/GastroWise/KLTN-123-GastroWise-AI/app/db/mongo.py) | Raw exception strings `{e}` were printed on connection failure, creating a risk of credential echoing in server logs. | Implemented `sanitize_log_message()` using regex masking (`mongodb+srv://[REDACTED_AUTH]@...`) and added placeholder sanity checks. |
| [`.env.example`](file:///d:/GastroWise/KLTN-123-GastroWise-AI/.env.example) | Example template did not reflect the dedicated `gastrowise_ai_service` username. | Updated template to explicitly specify `gastrowise_ai_service` and document least-privilege role boundaries. |

---

### 10.6 Remaining Manual Actions & Rollback Instructions

#### Remaining Manual Actions:
1. **Container / Production Deployment:** When deploying the AI Microservice via Docker or Cloud Run, pass `MONGODB_URI` securely via container secrets or Kubernetes Secrets rather than mounting `.env` files.
2. **Atlas Network Whitelist:** Ensure that MongoDB Atlas Network Access (IP Access List) restricts inbound traffic to the specific static egress IP or VPC peering subnet of the AI microservice cluster.

#### Rollback Instructions:
If connectivity issues arise with `gastrowise_ai_service`:
1. Check MongoDB Atlas console: Database Access $\rightarrow$ `gastrowise_ai_service` $\rightarrow$ verify password and custom role privileges.
2. Verify IP whitelist in MongoDB Atlas Network Access.
3. If an emergency rollback of database permissions is needed, assign the `read` built-in role on `gastrowise` to `gastrowise_ai_service` temporarily while maintaining write protection.
4. Run `node verify_mongodb_least_privilege.js` or `python verify_mongodb_connection.py` to immediately diagnose authentication and permission states.

---
*Report certified by Principal Software Architect & Senior Database Security Auditor.*

