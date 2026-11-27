from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.db.mongo import (
    DATA_STATUS_DB_UNAVAILABLE,
    DATA_STATUS_EMPTY,
    DATA_STATUS_READY,
    DATA_STATUS_VALIDATION_FAILED,
    DatabaseLoadError,
    DatasetValidationError,
    get_dataset,
    get_validation_summary,
    load_dataset_from_mongo,
)
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- KHỞI ĐỘNG GASTROWISE AI MICROSERVICE (ENTERPRISE TREE) ---")
    try:
        load_dataset_from_mongo()
    except (DatabaseLoadError, DatasetValidationError) as exc:
        print(f"!!! [Startup Diagnostics] Dataset not ready during startup: {exc}")
    yield


app = FastAPI(
    title="GastroWise AI Microservice",
    description="Enterprise Production-Grade AI Microservice for GastroWise Platform",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(DatabaseLoadError)
async def database_load_error_handler(_request: Request, exc: DatabaseLoadError):
    return JSONResponse(
        status_code=503,
        content={
            "status": "GastroWise AI Microservice Unavailable",
            "data_status": DATA_STATUS_DB_UNAVAILABLE,
            "restaurants_loaded": 0,
            "validation": get_validation_summary(),
            "detail": str(exc),
        },
    )


@app.exception_handler(DatasetValidationError)
async def dataset_validation_error_handler(_request: Request, exc: DatasetValidationError):
    return JSONResponse(
        status_code=503,
        content={
            "status": "GastroWise AI Microservice Data Validation Failed",
            "data_status": DATA_STATUS_VALIDATION_FAILED,
            "restaurants_loaded": 0,
            "validation": get_validation_summary(),
            "detail": str(exc),
        },
    )


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 router
app.include_router(api_v1_router)


@app.get("/")
async def root():
    loaded_df = get_dataset()
    status = DATA_STATUS_READY if loaded_df is not None and not loaded_df.empty else DATA_STATUS_EMPTY
    count = len(loaded_df) if loaded_df is not None else 0
    return {
        "status": "GastroWise AI Microservice Running",
        "architecture": "Enterprise Modular Tree (Clean Architecture)",
        "data_status": status,
        "restaurants_loaded": count,
        "validation": get_validation_summary(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=False)
