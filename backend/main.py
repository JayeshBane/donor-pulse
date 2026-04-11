from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from config import settings
from database import connect_to_mongo, close_mongo_connection
from routers import donor, hospital, auth, sms

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting DonorPulse Backend...")
    await connect_to_mongo()
    logger.info(f"✅ Backend ready on port {settings.port}")
    yield
    logger.info("🛑 Shutting down...")
    await close_mongo_connection()

app = FastAPI(
    title="DonorPulse API",
    description="Blood Donation Management System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": "1.0.0"}

@app.get("/")
async def root():
    return {"message": "Welcome to DonorPulse API", "docs": "/docs", "health": "/health"}

app.include_router(donor.router)
app.include_router(hospital.router)
app.include_router(auth.router)
app.include_router(sms.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)