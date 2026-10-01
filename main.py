from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongo import load_dataset_from_mongo, get_dataset
from app.api.v1.router import api_v1_router
from app.core.sentiment_service import get_sentiment_pipeline
from app.core.vision_service import get_yolo_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- KHỞI ĐỘNG GASTROWISE AI MICROSERVICE (ENTERPRISE TREE) ---")
    load_dataset_from_mongo()
    yield

app = FastAPI(
    title="GastroWise AI Microservice",
    description="Enterprise Production-Grade AI Microservice for GastroWise Platform",
    version="1.0.0",
    lifespan=lifespan
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
    df = get_dataset()
    status = "Active" if df is not None and not df.empty else "Empty Data"
    count = len(df) if df is not None else 0
    return {
        "status": "GastroWise AI Microservice Running",
        "architecture": "Enterprise Modular Tree (Clean Architecture)",
        "data_status": status,
        "restaurants_loaded": count
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=False)
