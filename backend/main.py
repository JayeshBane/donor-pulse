from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from config import settings
from database import connect_to_mongo, close_mongo_connection
from routers import donor, hospital, auth, sms, machine, admin, appointment
from middleware.rate_limit import rate_limit_middleware

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

# CORS - Configure based on environment
if settings.environment == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=3600,
    )
    # Add trusted host middleware in production
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["your-domain.com", "api.your-domain.com"]
    )
else:
    # Development - allow all
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    # Don't expose internal error details to client
    return JSONResponse(
        status_code=500, 
        content={"detail": "An internal error occurred. Please try again later."}
    )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(), 
        "version": "1.0.0",
        "environment": settings.environment
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to DonorPulse API", 
        "docs": "/docs", 
        "health": "/health",
        "version": "1.0.0"
    }


# Include routers
app.include_router(donor.router)
app.include_router(hospital.router)
app.include_router(auth.router)
app.include_router(sms.router)
app.include_router(machine.router) 
app.include_router(admin.router)
app.include_router(appointment.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=settings.port, 
        reload=settings.environment == "development"
    )