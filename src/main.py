from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.api.v1.router import api_router
from src.api.v1.endpoints.iclock import router as iclock_router

# Initialize FastAPI application
app = FastAPI(
    title="Scoto ERP Backend API",
    version="1.0.0",
    description="Multi-tenant ERP backend integrating eSSL biometric face devices and core services.",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Configure Cross-Origin Resource Sharing (CORS) for Mobile/Web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 unified router (/api/v1/...)
app.include_router(api_router, prefix="/api/v1")

# Register hardware biometric push protocol endpoints (ADMS / iclock listeners)
app.include_router(iclock_router, prefix="/iclock")
app.include_router(iclock_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Simple ping-pong health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database_tenants_available": list(settings.databases_map.keys()),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=2015, reload=True)
