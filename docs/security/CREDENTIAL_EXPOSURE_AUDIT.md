# GASTROWISE – CREDENTIAL EXPOSURE & GIT HISTORY AUDIT
**Sprint 0 Credential Leakage & Historical Secret Exposure Review**  
**Role:** Senior Security Engineer & Principal Architect  
**Audit Date:** November 17, 2026  
**Status:** AUDITED ACROSS 5 REPOSITORIES

---

## 1. CREDENTIAL EXPOSURE CLASSIFICATION MATRIX

This audit examined all tracked files, active working trees, and Git commit logs across all five GastroWise repositories.

> [!IMPORTANT]
> In compliance with strict security guidelines, no plaintext passwords, secret hashes, or live authentication tokens are reproduced in this report. All locations are referenced by repository, file path, line number, and commit SHA.

| Credential Type | Working Tree Status | Git History Status | Rotation Status | Required Action |
| :--- | :---: | :---: | :---: | :--- |
| **MongoDB Atlas Admin User (`thienthien`)** | Clean in AI; **Exposed in BE `scripts/remediate-config.js`** | **Exposed in AI commit `175c94e` and BE commit `f6bc66f`** | **Requires Verification / Deletion on Atlas** | **DBA Action Required:** Verify user `thienthien` is deleted or rotated on MongoDB Atlas. Remove `scripts/remediate-config.js` from Git tracking. |
| **MongoDB AI Service User (`gastrowise_ai_service`)** | Secured in local uncommitted `.env` | **Clean** (never committed to Git) | **Active & Verified** | No action required. Least-privilege role verified. |
| **Backend JWT Secrets (`JWT_SECRET`, `JWT_REFRESH_SECRET`)** | Loaded via `.env`; hardcoded fallback in `auth.service.ts:136` | **Clean** | **Needs Hardening** | Remove hardcoded fallback `'gastrowise_jwt_secret'` from source code. |
| **External AI Secret Key (`X-Internal-AI-Key`)** | Not configured | **Clean** | **New Implementation Required** | Generate 32-byte cryptographically secure random token. |
| **Mobile API Configuration** | Tracked `.env` in Git | **Exposed in Mobile commit `d9c8251`** | **Low Risk (IPs only)** | Add `.env` to Mobile `.gitignore` to prevent future secret commits. |

---

## 2. DETAILED EXPOSURE FINDINGS

### EXPOSURE ITEM 1: Tracked Remediation Script in Backend Working Tree & HEAD
- **Repository:** `KLTN-123-GastroWise-BE`
- **Location:** [scripts/remediate-config.js:9-12](file:///D:/GastroWise/KLTN-123-GastroWise-BE/scripts/remediate-config.js#L9-L12)
- **Commit SHA:** `f6bc66f` ("feat: thien add backend modules, controllers, schemas, and migration scripts")
- **Exposure Type:** Active Working Tree & Tracked Git File.
- **Description:** A Node.js helper script created to automate `config.py` string replacement was committed into the backend repository. The script contains the raw Atlas connection string for user `thienthien`.
- **Remediation:** Remove the file from git tracking (`git rm scripts/remediate-config.js`), add `scripts/remediate*.js` to `.gitignore`, and ensure the `thienthien` Atlas account is disabled.

---

### EXPOSURE ITEM 2: Historical Commit Exposure in AI Microservice
- **Repository:** `KLTN-123-GastroWise-AI`
- **Location:** `app/config.py` in Commit `175c94e` ("feat man architect folder teamwork")
- **Commit SHA:** `175c94e` (Historical commit, child of initial commit)
- **Exposure Type:** Git History Exposure (historical commit).
- **Description:** In commit `175c94e`, line 4 of `app/config.py` initialized `MONGO_URI` with a default connection string containing user `thienthien`.
- **Status:** Remediated in working tree in commit `2a9064c` (replaced with `os.getenv("MONGODB_URI")`), but preserved in the commit log history.
- **Remediation:** Under the strict constraint not to rewrite Git history or force-push, the ONLY valid security countermeasure is **complete credential invalidation on MongoDB Atlas**: the `thienthien` database user must be deleted from Atlas User Management so the exposed secret is rendered useless.

---

### EXPOSURE ITEM 3: Mobile `.env` Tracked in Git
- **Repository:** `KLTN-123-GastroWise-Mobile`
- **Location:** [.env](file:///D:/GastroWise/KLTN-123-GastroWise-Mobile/.env)
- **Commit SHA:** `d9c8251` ("feat: thien add mobile app tabs, screens, and analytics tracker")
- **Exposure Type:** Tracked Git File.
- **Description:** `.gitignore` in `KLTN-123-GastroWise-Mobile` only specifies `.env*.local`, omitting the base `.env` file. The current `.env` contains developer IP addresses and an internal Render endpoint (`api-gastrowise.onrender.com`).
- **Remediation:** Update `KLTN-123-GastroWise-Mobile/.gitignore` to ignore `.env`, untrack `.env` (`git rm --cached .env`), and retain `.env.example` as the canonical template.

---

## 3. VERIFIED ROTATED VS. ACTION REQUIRED CREDENTIALS

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CREDENTIAL STATUS SUMMARY                       │
├────────────────────────────────────────────────────────────────────────┤
│ 1. gastrowise_ai_service:                                              │
│    STATUS: VERIFIED SECURE & LEAST-PRIVILEGE                           │
│    • Never committed to Git.                                           │
│    • Stored only in local .env.                                        │
│    • Restricted to find on gastrowise.restaurants.                     │
│                                                                        │
│ 2. thienthien (Old Admin User):                                        │
│    STATUS: EXPOSED HISTORICALLY & REQUIRING DBA VERIFICATION           │
│    • Exposed in AI commit 175c94e and BE scripts/remediate-config.js.  │
│    • MUST be verified DELETED / DISABLED on MongoDB Atlas.             │
│    • scripts/remediate-config.js must be untracked.                    │
│                                                                        │
│ 3. gastrowise_jwt_secret (Fallback Secret):                            │
│    STATUS: INSECURE HARDCODED FALLBACK                                 │
│    • Present in src/auth/auth.service.ts:136.                          │
│    • Must be removed; throw startup exception if JWT_SECRET missing.   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. FORMAL CREDENTIAL EXPOSURE FINDINGS

### FINDING SEC-EXP-01: Historical Atlas User Exposure Requiring Atlas Invalidation
- **Severity:** HIGH
- **Evidence:** `KLTN-123-GastroWise-AI` commit `175c94e`, `KLTN-123-GastroWise-BE` commit `f6bc66f`.
- **Actual Behavior:** Atlas connection string containing username `thienthien` exists in Git history and a committed script.
- **Expected Behavior:** Historical commits must not contain credentials; when leakage occurs, credentials must be immediately invalidated at the identity provider (Atlas).
- **Business Impact:** Unauthorized database read/write access if the credentials remain active on MongoDB Atlas.
- **Recommended Solution:** 
  1. Access MongoDB Atlas Console $\rightarrow$ Security $\rightarrow$ Database Access.
  2. Locate user `thienthien` and delete or rotate the password immediately.
  3. Untrack `scripts/remediate-config.js` in `KLTN-123-GastroWise-BE`.
- **Dependencies:** DBA Atlas Console permissions.
- **Acceptance Criteria:** Attempting connection with user `thienthien` fails with AuthenticationFailed (code 18).
- **Testing Requirements:** Execute connection test using old credentials and verify rejection.

---

### FINDING SEC-EXP-02: Hardcoded JWT Fallback Secret in Backend Authentication Service
- **Severity:** HIGH
- **Evidence:** [KLTN-123-GastroWise-BE/src/auth/auth.service.ts:136](file:///D:/GastroWise/KLTN-123-GastroWise-BE/src/auth/auth.service.ts#L136)
- **Actual Behavior:** If `JWT_SECRET` is unset in the environment, tokens are signed with the static fallback string `'gastrowise_jwt_secret'`.
- **Expected Behavior:** Backend should refuse to boot if `JWT_SECRET` is missing in production.
- **Business Impact:** Trivial token forging if environment variable fails to load.
- **Recommended Solution:** Throw `Error('FATAL: JWT_SECRET must be defined in environment variables')` during module initialization.
- **Dependencies:** None.
- **Acceptance Criteria:** Backend fails startup if `JWT_SECRET` is undefined.
- **Testing Requirements:** Boot NestJS without `JWT_SECRET` and verify error.

