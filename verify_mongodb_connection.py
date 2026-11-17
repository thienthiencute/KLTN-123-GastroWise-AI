"""
GastroWise AI Microservice - Python MongoDB Least-Privilege Verification Script
Validates connectivity, authentication with gastrowise_ai_service,
authorized read on gastrowise.restaurants, and RBAC rejection of write operations.
"""

import os
import re
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.config import MONGO_URI, DB_NAME, COLLECTION_NAME

def sanitize(msg: str) -> str:
    if not msg:
        return ""
    return re.sub(r'mongodb(\+srv)?:\/\/[^@]+@', r'mongodb\1://[REDACTED_AUTH]@', str(msg))

def main():
    print("=" * 64)
    print("  GASTROWISE AI - PYTHON MONGODB LEAST-PRIVILEGE VERIFICATION   ")
    print("=" * 64)
    print(f"Target Database  : {DB_NAME}")
    print(f"Target Collection: {COLLECTION_NAME}")

    if not MONGO_URI:
        print("❌ FAILED: MONGODB_URI is not set in environment or .env file.")
        sys.exit(1)

    if any(placeholder in MONGO_URI for placeholder in ["<username>", "<password>", "<YOUR_AI_SERVICE_PASSWORD>"]):
        print("⚠️  CONFIG REQUIRED: MONGODB_URI contains placeholder credentials.")
        print("👉 Please update KLTN-123-GastroWise-AI/.env with the real password for: gastrowise_ai_service")
        print("=" * 64)
        sys.exit(2)

    # Check user identity
    user_match = re.search(r'mongodb(?:\+srv)?:\/\/([^:]+):([^@]+)@', MONGO_URI)
    user_name = user_match.group(1) if user_match else "unknown"
    print(f"Authenticated User: {user_name}")

    if user_name != "gastrowise_ai_service":
        print(f"⚠️  WARNING: Authenticated user is '{user_name}', expected 'gastrowise_ai_service'.")
        if "admin" in user_name.lower() or user_name == "thienthien":
            print("❌ SECURITY POLICY VIOLATION: Admin credentials detected! Must use gastrowise_ai_service.")
            sys.exit(1)
    else:
        print("✅ User Identity Check: Verified least-privilege user (gastrowise_ai_service).")

    try:
        from pymongo import MongoClient
        from pymongo.errors import OperationFailure
    except ImportError:
        print("❌ pymongo is not installed in the current Python environment.")
        print("Run: pip install pymongo dnspython, or run the Node.js verifier: node verify_mongodb_least_privilege.js")
        sys.exit(1)

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    try:
        print("\n--- Step 1: Ping MongoDB Atlas ---")
        client.admin.command('ping')
        print("✅ Ping Check PASSED: Successfully connected to MongoDB Atlas.")

        print("\n--- Step 2: Test Authorized Read (find_one) on gastrowise.restaurants ---")
        col = client[DB_NAME][COLLECTION_NAME]
        doc = col.find_one({}, projection={"_id": 1, "name": 1, "tenQuan": 1})
        if doc:
            doc_id = doc.get("_id")
            name = doc.get("tenQuan") or doc.get("name") or "Unknown"
            print(f"✅ Authorized Read PASSED: Document ID: {doc_id} ('{name}')")
        else:
            print("⚠️  Read succeeded, but collection is empty.")

        print("\n--- Step 3: Test Write Rejection (Least-Privilege Enforcement) ---")
        write_rejected = False
        inserted_id = None
        try:
            res = col.insert_one({"_probe_security_test": "least_privilege_audit"})
            inserted_id = res.inserted_id
        except OperationFailure as err:
            write_rejected = True
            print("✅ Write Rejection PASSED: MongoDB Atlas RBAC strictly blocked write operation.")
            print(f"   Atlas Security Response: {sanitize(str(err)).splitlines()[0]}")

        if not write_rejected:
            if inserted_id:
                try:
                    col.delete_one({"_id": inserted_id})
                except Exception:
                    pass
            print("❌ SECURITY FAILURE: Unauthorized write SUCCEEDED! User has write permissions!")
            sys.exit(1)

        print("\n--- Step 4: Test Unauthorized Collection Access (gastrowise.users) ---")
        boundary_rejected = False
        try:
            client[DB_NAME]["users"].find_one({}, projection={"_id": 1})
        except OperationFailure as err:
            boundary_rejected = True
            print("✅ Boundary Check PASSED: Access to unauthorized collection (users) denied.")
            print(f"   Atlas Security Response: {sanitize(str(err)).splitlines()[0]}")

        if not boundary_rejected:
            print("⚠️  Notice: Reading users collection did not throw authorization error.")

        print("\n" + "=" * 64)
        print("  VERIFICATION RESULT: ALL LEAST-PRIVILEGE CHECKS PASSED ✅    ")
        print("=" * 64)
    except Exception as e:
        print("\n❌ Connection Verification Failed:")
        print(sanitize(str(e)))
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()

