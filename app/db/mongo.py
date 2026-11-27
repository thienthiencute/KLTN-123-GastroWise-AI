import math
import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, OperationFailure, PyMongoError
from sklearn.feature_extraction.text import TfidfVectorizer
from app.config import MONGO_URI, DB_NAME, COLLECTION_NAME
from app.core.text_utils import clean_coordinate, clean_price, extract_district_from_address
from app.core.rating_normalizer import detect_restaurant_rating_scale, normalize_rating

DATA_STATUS_DB_UNAVAILABLE = "DATABASE_UNAVAILABLE"
DATA_STATUS_EMPTY = "EMPTY_DATASET"
DATA_STATUS_VALIDATION_FAILED = "DATA_VALIDATION_FAILED"
DATA_STATUS_READY = "DATA_READY"

EXPECTED_COLUMNS = [
    "id",
    "name",
    "tags",
    "rating",
    "raw_rating",
    "raw_rating_scale",
    "_rating_normalized",
    "price",
    "lat",
    "lon",
    "coords_valid",
    "district",
    "address",
]


class DatabaseLoadError(RuntimeError):
    """Raised when MongoDB authentication, authorization, or connection fails."""


class DatasetValidationError(RuntimeError):
    """Raised when documents exist in MongoDB but none satisfy required AI schema."""


# Global dataset & model state
df = None
tfidf_vectorizer = None
_last_db_error: Optional[str] = None
_dataset_status: str = DATA_STATUS_DB_UNAVAILABLE
_validation_summary: Dict[str, Any] = {
    "database": DB_NAME,
    "collection": COLLECTION_NAME,
    "raw_count": 0,
    "loaded_count": 0,
    "rejected_count": 0,
    "duplicates_skipped": 0,
    "invalid_coordinates_count": 0,
    "missing_tags_count": 0,
    "missing_address_count": 0,
}


def sanitize_log_message(msg: str) -> str:
    """Mask credentials and connection strings in log output."""
    if not msg:
        return ""
    masked = re.sub(
        r"mongodb(\+srv)?:\/\/[^@/\s]+@",
        r"mongodb\1://[REDACTED_AUTH]@",
        str(msg),
    )
    masked = re.sub(
        r"(password|passwd|pwd|secret|token)=[^\s&;,\"']+",
        r"\1=[REDACTED]",
        masked,
        flags=re.IGNORECASE,
    )
    return masked


def get_dataset_status() -> str:
    return _dataset_status


def get_validation_summary() -> Dict[str, Any]:
    return dict(_validation_summary)


def _is_valid_lat_lon(lat: float, lon: float) -> bool:
    if any(math.isnan(v) or math.isinf(v) for v in (lat, lon)):
        return False
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return False
    if lat == 0.0 and lon == 0.0:
        return False
    return True


def extract_coords_from_row(row: Dict[str, Any]) -> Tuple[float, float, bool]:
    """
    [TASK-P0-01 / M10.0] Extract GeoJSON `location: { type: 'Point', coordinates: [lon, lat] }`
    or flat `lat`/`lon`, validating geographic bounds and rejecting (0, 0).
    Returns (lat, lon, coords_valid).
    """
    loc = row.get("location")
    if (
        isinstance(loc, dict)
        and isinstance(loc.get("coordinates"), (list, tuple))
        and len(loc["coordinates"]) >= 2
    ):
        lon_candidate = clean_coordinate(loc["coordinates"][0])
        lat_candidate = clean_coordinate(loc["coordinates"][1])
        if _is_valid_lat_lon(lat_candidate, lon_candidate):
            return lat_candidate, lon_candidate, True

    lat = clean_coordinate(row.get("lat", 0.0))
    lon = clean_coordinate(row.get("lon", 0.0))
    if _is_valid_lat_lon(lat, lon):
        return lat, lon, True
    return 0.0, 0.0, False


def _clean_tags(raw_tags: Any) -> Tuple[str, bool]:
    if raw_tags is None or (isinstance(raw_tags, float) and math.isnan(raw_tags)):
        return "", True
    if isinstance(raw_tags, list):
        parts = [str(item).strip() for item in raw_tags if item is not None and str(item).strip()]
        joined = " ".join(parts).strip()
        return joined, len(joined) == 0
    if isinstance(raw_tags, str):
        cleaned = raw_tags.strip()
        if cleaned.lower() in ("none", "nan", "null"):
            return "", True
        return cleaned, len(cleaned) == 0
    return str(raw_tags).strip(), False


def _clean_text(val: Any) -> str:
    if val is None or isinstance(val, bool):
        return ""
    if isinstance(val, float) and math.isnan(val):
        return ""
    s = str(val).strip()
    if s.lower() in ("none", "nan", "null"):
        return ""
    return s


def normalize_and_validate_documents(
    raw_docs: List[Dict[str, Any]],
    db_name: str = DB_NAME,
    collection_name: str = COLLECTION_NAME,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate and normalize raw MongoDB restaurant documents into a clean AI DataFrame.
    - Enforces non-empty ID and restaurant name.
    - Deduplicates by ID and normalized (name, address).
    - Prevents double rating normalization across 10-point Foody and 5-point scales.
    - Coerces invalid/null coordinates safely without crashing.
    """
    seen_ids = set()
    seen_name_addr = set()
    rows: List[Dict[str, Any]] = []

    rejected_count = 0
    duplicates_skipped = 0
    invalid_coordinates_count = 0
    missing_tags_count = 0
    missing_address_count = 0

    for doc in raw_docs:
        if not isinstance(doc, dict):
            rejected_count += 1
            continue

        raw_id = doc.get("_id") if doc.get("_id") is not None else doc.get("id")
        doc_id = _clean_text(raw_id)
        if not doc_id:
            rejected_count += 1
            continue

        if doc_id in seen_ids:
            duplicates_skipped += 1
            continue

        name = _clean_text(doc.get("tenQuan") or doc.get("name"))
        if not name:
            rejected_count += 1
            continue

        address = _clean_text(doc.get("diaChi") or doc.get("address"))
        dedup_key = (name.lower(), address.lower())
        if address and dedup_key in seen_name_addr:
            duplicates_skipped += 1
            continue

        seen_ids.add(doc_id)
        if address:
            seen_name_addr.add(dedup_key)
        else:
            missing_address_count += 1

        scale, raw_rating = detect_restaurant_rating_scale(doc)
        is_already_norm = doc.get("_rating_normalized") is True
        norm_rating = normalize_rating(
            raw_rating,
            scale=scale,
            is_already_normalized=is_already_norm,
        )

        tags, tags_missing = _clean_tags(doc.get("tags"))
        if tags_missing:
            missing_tags_count += 1

        lat, lon, coords_valid = extract_coords_from_row(doc)
        if not coords_valid:
            invalid_coordinates_count += 1

        raw_price = doc.get("giaCa")
        if raw_price is None or (isinstance(raw_price, float) and math.isnan(raw_price)):
            raw_price = doc.get("price")
        if raw_price is None or (isinstance(raw_price, float) and math.isnan(raw_price)):
            raw_price = doc.get("avgPrice")
        price = clean_price(raw_price)

        district = extract_district_from_address(address)

        rows.append(
            {
                "id": doc_id,
                "name": name,
                "tags": tags,
                "rating": norm_rating,
                "raw_rating": raw_rating,
                "raw_rating_scale": scale.value,
                "_rating_normalized": True,
                "price": price,
                "lat": lat,
                "lon": lon,
                "coords_valid": coords_valid,
                "district": district,
                "address": address,
            }
        )

    summary = {
        "database": db_name,
        "collection": collection_name,
        "raw_count": len(raw_docs),
        "loaded_count": len(rows),
        "rejected_count": rejected_count,
        "duplicates_skipped": duplicates_skipped,
        "invalid_coordinates_count": invalid_coordinates_count,
        "missing_tags_count": missing_tags_count,
        "missing_address_count": missing_address_count,
    }

    normalized_df = (
        pd.DataFrame(rows, columns=EXPECTED_COLUMNS)
        if rows
        else pd.DataFrame(columns=EXPECTED_COLUMNS)
    )
    return normalized_df, summary


def _fit_vectorizer(dataset: pd.DataFrame) -> TfidfVectorizer:
    vec = TfidfVectorizer()
    corpus = [t for t in dataset["tags"].astype(str).tolist() if t.strip()]
    if not corpus:
        corpus = dataset["name"].astype(str).tolist()
    if not corpus:
        return vec
    try:
        vec.fit(corpus)
    except ValueError:
        # Fallback if vocabulary contains only 1-char tokens/stopwords
        fallback_vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        try:
            fallback_vec.fit(corpus)
            return fallback_vec
        except ValueError:
            vec.fit(["food restaurant"])
    return vec


def load_dataset_from_mongo():
    global df, tfidf_vectorizer, _last_db_error, _dataset_status, _validation_summary
    print(f"-> [MongoDB Loader] Connecting to MongoDB database='{DB_NAME}', collection='{COLLECTION_NAME}'...")
    if not MONGO_URI or "<username>" in MONGO_URI or "<password>" in MONGO_URI:
        msg = "MONGODB_URI / AI credentials are unset or contain placeholder values."
        print(f"!!! [MongoDB Loader] {msg}")
        _last_db_error = msg
        _dataset_status = DATA_STATUS_DB_UNAVAILABLE
        _validation_summary = {
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "raw_count": 0,
            "loaded_count": 0,
            "rejected_count": 0,
            "duplicates_skipped": 0,
            "invalid_coordinates_count": 0,
            "missing_tags_count": 0,
            "missing_address_count": 0,
        }
        df = None
        tfidf_vectorizer = None
        raise DatabaseLoadError(msg)

    client = None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        client.admin.command("ping")
        collection = client[DB_NAME][COLLECTION_NAME]
        data_list = list(collection.find({}))
        _last_db_error = None

        if not data_list:
            df = pd.DataFrame(columns=EXPECTED_COLUMNS)
            tfidf_vectorizer = TfidfVectorizer()
            _dataset_status = DATA_STATUS_EMPTY
            _validation_summary = {
                "database": DB_NAME,
                "collection": COLLECTION_NAME,
                "raw_count": 0,
                "loaded_count": 0,
                "rejected_count": 0,
                "duplicates_skipped": 0,
                "invalid_coordinates_count": 0,
                "missing_tags_count": 0,
                "missing_address_count": 0,
            }
            print(f"-> [MongoDB Loader] Authenticated cleanly to '{DB_NAME}.{COLLECTION_NAME}', loaded 0 documents ({DATA_STATUS_EMPTY}).")
            return False

        temp_df, summary = normalize_and_validate_documents(
            data_list,
            db_name=DB_NAME,
            collection_name=COLLECTION_NAME,
        )
        _validation_summary = summary

        if temp_df.empty:
            err_msg = (
                f"All {summary['raw_count']} documents in '{DB_NAME}.{COLLECTION_NAME}' failed schema validation "
                f"(rejected={summary['rejected_count']})."
            )
            _last_db_error = err_msg
            _dataset_status = DATA_STATUS_VALIDATION_FAILED
            df = None
            tfidf_vectorizer = None
            print(f"!!! [MongoDB Loader] {err_msg}")
            raise DatasetValidationError(err_msg)

        df = temp_df
        tfidf_vectorizer = _fit_vectorizer(df)
        _dataset_status = DATA_STATUS_READY
        print(
            f"-> [MongoDB Loader] {DATA_STATUS_READY}: loaded {len(df)}/{summary['raw_count']} restaurants "
            f"from '{DB_NAME}.{COLLECTION_NAME}' (rejected={summary['rejected_count']}, duplicates={summary['duplicates_skipped']})."
        )
        return True
    except DatasetValidationError:
        raise
    except (OperationFailure, ConfigurationError, PyMongoError, Exception) as e:
        safe_err = sanitize_log_message(str(e))
        _last_db_error = safe_err
        _dataset_status = DATA_STATUS_DB_UNAVAILABLE
        df = None
        tfidf_vectorizer = None
        print(f"!!! [MongoDB Loader] Critical DB error on '{DB_NAME}.{COLLECTION_NAME}': {safe_err}")
        raise DatabaseLoadError(f"MongoDB database load failed for '{DB_NAME}.{COLLECTION_NAME}': {safe_err}") from e
    finally:
        if client is not None:
            client.close()


def get_dataset():
    global df
    if _last_db_error is not None or df is None or df.empty:
        load_dataset_from_mongo()
    return df


def get_vectorizer():
    global tfidf_vectorizer
    if _last_db_error is not None or tfidf_vectorizer is None:
        load_dataset_from_mongo()
    return tfidf_vectorizer
