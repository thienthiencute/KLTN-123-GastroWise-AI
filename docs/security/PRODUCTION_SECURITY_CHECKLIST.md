# GASTROWISE – PRODUCTION ZERO-TRUST SECURITY AUDIT & CHECKLIST
**Sprint 2 Security & Compliance Verification**  
**Role:** Principal Software Architect & QA Technical Lead  
**Audit Date:** November 2026  
**Standard:** OWASP Top 10 (2021), CIS Benchmarks, Zero-Trust Architecture (NIST SP 800-207)  
**Status:** AUDITED AGAINST CODEBASE

---

## 1. EXECUTIVE SECURITY SUMMARY

A comprehensive zero-trust security review of the GastroWise multi-tier ecosystem (`KLTN-123-GastroWise-BE`, `KLTN-123-GastroWise-AI`, `KLTN-123-GastroWise-Mobile`, and MongoDB Atlas) was conducted.

| Total Security Items | PASS (Compliant) | WARN (Moderate Risk) | FAIL (Critical/High Vulnerability) |
| :---: | :---: | :---: | :---: |
| **16** | **8** | **4** | **4** |

### Critical Action Items (P0 Blockers for Production):
1. **SEC-VULN-01 (OWASP A01 - Broken Access Control):** `DELETE /reviews/:id`, `PATCH /reviews/:id`, and `POST /reviews/migrate-sentiment` in `reviews.controller.ts` completely lack authentication guards and ownership validation. Any anonymous client can delete or overwrite reviews.
2. **SEC-VULN-02 (OWASP A01 - Unauthenticated Data Leakage):** `GET /interactions/matrix` in `interactions.controller.ts` is publicly accessible without authentication, exposing complete user IDs, restaurant IDs, and behavioral data.
3. **SEC-VULN-03 (OWASP A07 - Missing Service-to-Service Authentication):** The Python FastAPI AI Microservice has zero authentication. Neither NestJS attaches an internal API key, nor does FastAPI validate `X-Internal-AI-Key`. Anyone reaching port 5000 can invoke heavy AI models or trigger SVD retraining.
4. **SEC-VULN-04 (OWASP A05 - Security Misconfiguration / DoS):** `POST /restaurants/search-by-image` accepts raw file uploads without file size limits, MIME type filtering, or magic byte verification, opening the backend and AI service to memory exhaustion and malicious file processing.

---

## 2. ZERO-TRUST DOMAIN AUDIT MATRIX

### DOMAIN 1: JWT SECURITY & SESSION MANAGEMENT

| Item ID | Check Description | Verified Code Location | Severity | Status | Technical Finding & Remediation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **SEC-JWT-01** | JWT Signing Secret & Fallback | `src/auth/auth.service.ts:136` | **HIGH** | <span style="color:red">**WARN**</span> | **Finding:** `JWT_SECRET` falls back to `'gastrowise_jwt_secret'`. If environment variable fails to load in production, tokens will be signed with a known weak secret.<br/>**Remediation:** Enforce strict startup exception if `process.env.JWT_SECRET` is unset or less than 32 characters (similar to `jwt.strategy.ts:13`). |
| **SEC-JWT-02** | Token Expiration Discrepancy | `src/auth/auth.module.ts:22`<br/>`src/auth/auth.service.ts:142` | **MEDIUM** | <span style="color:orange">**WARN**</span> | **Finding:** `auth.module.ts` configures `expiresIn: '15m'`, but `auth.service.ts` overrides it with `expiresIn: '1d'`. Access tokens remain valid for 24 hours, increasing the exposure window upon credential compromise.<br/>**Remediation:** Standardize Access Token lifetime to 15 minutes (`15m`) and rely on Refresh Token (`7d`) rotation. |
| **SEC-JWT-03** | Refresh Token Hashing & Storage | `src/auth/auth.service.ts:43, 81, 106`<br/>`src/users/users.service.ts` | **HIGH** | <span style="color:green">**PASS**</span> | **Finding:** Refresh tokens are hashed using `bcrypt` before storage in `user.hashedRefreshToken`. Token rotation is enforced upon each refresh request. |
| **SEC-JWT-04** | Token Revocation & Banned User Invalidation | `src/auth/jwt.strategy.ts:23-33` | **MEDIUM** | <span style="color:orange">**WARN**</span> | **Finding:** `jwt.strategy.ts` validates token signature and claims (`sub`), but does not query database or cache to verify whether the user account was banned or deleted after token issuance.<br/>**Remediation:** Implement Redis blacklist or check `user.status !== 'banned'` in `jwt.strategy.ts` or a lightweight user state cache. |

---

### DOMAIN 2: ROLE-BASED ACCESS CONTROL (RBAC) & PERMISSIONS

| Item ID | Check Description | Verified Code Location | Severity | Status | Technical Finding & Remediation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **SEC-RBAC-01** | RolesGuard Implementation | `src/auth/roles.guard.ts`<br/>`src/auth/roles.decorator.ts` | **CRITICAL** | <span style="color:green">**PASS**</span> | **Finding:** `RolesGuard` correctly checks `requiredRoles` against `request.user.role`, throws `ForbiddenException` on mismatch, and handles missing roles gracefully. Unit tests verified passing. |
| **SEC-RBAC-02** | Admin & Owner Route Protection | `src/restaurants/restaurants.controller.ts`<br/>`src/users/users.controller.ts`<br/>`src/itineraries/itineraries.controller.ts` | **CRITICAL** | <span style="color:green">**PASS**</span> | **Finding:** Sensitive administrative endpoints (`POST /restaurants`, `GET /users`, `PATCH /users/:id/role`, `GET /itineraries/all`, `POST /restaurants/recommender/sync-cf`) are secured with `@UseGuards(JwtAuthGuard, RolesGuard)` and `@Roles('admin', 'owner')`. |
| **SEC-RBAC-03** | Missing Guards on Review Mutation | `src/reviews/reviews.controller.ts:48-61` | **CRITICAL** | <span style="color:red">**FAIL**</span> | **Finding:** `DELETE /reviews/:id`, `PATCH /reviews/:id`, and `POST /reviews/migrate-sentiment` have NO `JwtAuthGuard` and NO `RolesGuard`. Unauthenticated anonymous clients can delete/alter any review.<br/>**Remediation:** Add `@UseGuards(JwtAuthGuard)` to all mutation endpoints and enforce user ownership or admin role. |
| **SEC-RBAC-04** | Unauthenticated Behavioral Matrix Export | `src/interactions/interactions.controller.ts:67` | **HIGH** | <span style="color:red">**FAIL**</span> | **Finding:** `GET /interactions/matrix` has no guards. Any client can extract up to 5,000 raw user interaction logs.<br/>**Remediation:** Add `@UseGuards(JwtAuthGuard, RolesGuard)` and `@Roles('admin')` to `GET /interactions/matrix`. |

---

### DOMAIN 3: RESOURCE OWNERSHIP & MULTI-TENANCY

| Item ID | Check Description | Verified Code Location | Severity | Status | Technical Finding & Remediation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **SEC-OWN-01** | Itinerary Ownership Validation | `src/itineraries/itineraries.service.ts:480-484, 532, 590, 680` | **CRITICAL** | <span style="color:green">**PASS**</span> | **Finding:** All itinerary mutations (`reorderStops`, `addStop`, `removeStop`, `recalculateItinerary`, `updateStatus`, `remove`) verify that `itinerary.user_id === actorId` or `actorRole === 'admin'`, throwing `ForbiddenException` on violation. |
| **SEC-OWN-02** | Taste DNA Profile Ownership | `src/taste-dna/taste-dna.controller.ts:25-50` | **HIGH** | <span style="color:green">**PASS**</span> | **Finding:** Taste DNA endpoints (`GET /taste-dna/me`, `PATCH /taste-dna/me`, `POST /taste-dna/quiz`) extract `userId` strictly from `req.user.sub` populated by `JwtStrategy`. Cross-tenant profile manipulation is impossible. |
| **SEC-OWN-03** | User Profile & Interaction Isolation | `src/users/users.controller.ts`<br/>`src/interactions/interactions.controller.ts:44` | **HIGH** | <span style="color:green">**PASS**</span> | **Finding:** User updates and interaction history querying (`GET /interactions/me`) bind strictly to `req.user.sub`. |

---

### DOMAIN 4: INTERNAL AI MICROSERVICE MUTUAL AUTHENTICATION

| Item ID | Check Description | Verified Code Location | Severity | Status | Technical Finding & Remediation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **SEC-AI-01** | AI Service Inbound Authentication | `KLTN-123-GastroWise-AI/main.py`<br/>`app/api/v1/router.py` | **CRITICAL** | <span style="color:red">**FAIL**</span> | **Finding:** FastAPI exposes all endpoints without verifying any API key or token. No FastAPI dependency (`Depends(verify_internal_key)`) exists.<br/>**Remediation:** Implement `verify_internal_key` dependency verifying `X-Internal-AI-Key` header with timing-safe comparison (`hmac.compare_digest`). |
| **SEC-AI-02** | NestJS Outbound Internal Header | `KLTN-123-GastroWise-BE/src/restaurants/restaurants.service.ts`<br/>`src/itineraries/itineraries.service.ts` | **CRITICAL** | <span style="color:red">**FAIL**</span> | **Finding:** `HttpService.post()` calls to FastAPI (`/recommend/hybrid`, `/routes/optimize`, `/copilot/message`) send no authorization or secret key headers.<br/>**Remediation:** Configure `HttpModule` or interceptor in NestJS to automatically inject `headers: { 'X-Internal-AI-Key': process.env.AI_SECRET_KEY }`. |

---

### DOMAIN 5: MONGODB LEAST-PRIVILEGE & CREDENTIAL INTEGRITY

| Item ID | Check Description | Verified Code Location | Severity | Status | Technical Finding & Remediation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **SEC-DB-01** | AI Service MongoDB Least-Privilege | `KLTN-123-GastroWise-AI/app/db/mongo.py`<br/>`verify_mongodb_least_privilege.js` | **CRITICAL** | <span style="color:green">**PASS**</span> | **Finding:** Live Atlas integration verified with user `gastrowise_ai_service`. Read on `gastrowise.restaurants` succeeded. Write on `restaurants` rejected (AtlasError 8000). Read on `users` rejected (AtlasError 8000). Zero hardcoded credentials in source code. |
| **SEC-DB-02** | Connection Credential Log Scrubbing | `KLTN-123-GastroWise-AI/app/db/mongo.py:12-16` | **HIGH** | <span style="color:green">**PASS**</span> | **Finding:** `sanitize_log_message()` uses regex `(mongodb(?:\+srv)?:\/\/[^:]+:)[^@]+(@.+)` to scrub database passwords from all initialization and error logs. |

---

### DOMAIN 6: CORS & NETWORK BOUNDARY DEFENSE

| Item ID | Check Description | Verified Code Location | Severity | Status | Technical Finding & Remediation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **SEC-NET-01** | Backend Gateway CORS Policy | `KLTN-123-GastroWise-BE/src/main.ts:23-49` | **HIGH** | <span style="color:green">**PASS**</span> | **Finding:** NestJS implements dynamic whitelist combining `FRONTEND_URL`, `ALLOWED_ORIGINS`, and localhost dev ports. Allows originless requests for native mobile apps. |
| **SEC-NET-02** | AI Microservice CORS Misconfiguration | `KLTN-123-GastroWise-AI/main.py:23-29` | **MEDIUM** | <span style="color:orange">**WARN**</span> | **Finding:** FastAPI uses `allow_origins=["*"]` with `allow_credentials=True`. In production, this violates W3C CORS standards and allows arbitrary web clients to cross-origin probe the AI service.<br/>**Remediation:** Restrict `allow_origins` to NestJS gateway internal IP/hostname and local development hosts. |

---

### DOMAIN 7: SECURE FILE UPLOAD & MULTIMEDIA PROCESSING

| Item ID | Check Description | Verified Code Location | Severity | Status | Technical Finding & Remediation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **SEC-UPL-01** | File Size & MIME Whitelist | `src/restaurants/restaurants.controller.ts:39-43` | **HIGH** | <span style="color:red">**FAIL**</span> | **Finding:** `FileInterceptor('file')` lacks `limits: { fileSize: 5 * 1024 * 1024 }` and lacks `fileFilter` validating MIME types (`image/jpeg`, `image/png`, `image/webp`).<br/>**Remediation:** Configure `FileInterceptor` options with 5MB limit and MIME type regex. |
| **SEC-UPL-02** | Pillow Image Decompression Bomb Protection | `KLTN-123-GastroWise-AI/app/core/vision_service.py:105` | **MEDIUM** | <span style="color:orange">**WARN**</span> | **Finding:** `Image.open(io.BytesIO(contents))` opens uploaded bytes directly without setting `Image.MAX_IMAGE_PIXELS` or calling `raw_image.verify()` prior to decompression.<br/>**Remediation:** Enforce `Image.MAX_IMAGE_PIXELS = 10_000_000` and catch decompression bomb exceptions. |

---

### DOMAIN 8: LOG SANITIZATION & SENSITIVE DATA EXPOSURE

| Item ID | Check Description | Verified Code Location | Severity | Status | Technical Finding & Remediation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **SEC-LOG-01** | Secret & PII Logging Audit | `KLTN-123-GastroWise-BE/src/` | **HIGH** | <span style="color:green">**PASS**</span> | **Finding:** Grep audit confirmed zero instances of passwords, JWT secrets, reset tokens, or user PII being printed to console or standard logs. |
| **SEC-LOG-02** | Reset OTP Generation & Plaintext Storage | `src/auth/auth.service.ts` | **MEDIUM** | <span style="color:orange">**WARN**</span> | **Finding:** Password reset OTP is generated as a raw 6-digit string without an expiration timestamp (`otpExpiresAt`) or attempt rate-limiter in `user.schema.ts`.<br/>**Remediation:** Hash the OTP with bcrypt or SHA-256 before storing in DB, add a 10-minute expiry timestamp, and enforce maximum 3 failed attempts. |

---

## 3. VERIFIED SECURITY REMEDIATION PLAN

```mermaid
graph TD
    subgraph P0: Immediate Pre-Production Fixes (Sprint 2 Stabilization)
        R1["SEC-VULN-01: Secure reviews.controller.ts<br/>(Add JwtAuthGuard, RolesGuard, and ownership check)"]
        R2["SEC-VULN-02: Protect GET /interactions/matrix<br/>(Add RolesGuard with 'admin' role)"]
        R3["SEC-VULN-03: Implement Mutual AI Authentication<br/>(Add X-Internal-AI-Key header validation)"]
        R4["SEC-VULN-04: Secure File Uploads<br/>(Add 5MB limit & MIME filter to search-by-image)"]
    end

    subgraph P1: Defense-in-Depth Enhancements
        R5["SEC-JWT-01/02: Remove hardcoded fallback & set 15m access token expiry"]
        R6["SEC-NET-02: Restrict FastAPI CORS origins"]
        R7["SEC-LOG-02: Hash password reset OTP & add 10m TTL"]
    end

    R1 --> R5
    R2 --> R6
    R3 --> R7
    R4 --> R7
```

