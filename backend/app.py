"""
Main FastAPI application with Azure AD authentication.
Implements secure SSO solution following Azure best practices.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import structlog
import uvicorn

from config import settings
from auth.routes import router as auth_router
from auth.middleware import AuthenticationMiddleware, SecurityHeaders, get_current_user



# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# Create FastAPI application
app = FastAPI(
    title="SSO Authentication Service",
    description="Secure Single Sign-On service with Azure AD and Dataverse integration",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add security headers middleware
app.add_middleware(SecurityHeaders)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware with exempted paths
app.add_middleware(
    AuthenticationMiddleware,
    exempt_paths=[
        "/",
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/auth/login",
        "/auth/callback",
        "/health",
        "/auth/refresh",
        "/auth/logout",
        "/auth/login-url"
    ]
)

# Include authentication routes
app.include_router(auth_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "sso-auth-service",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SSO Authentication Service",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Not available in production"
    }


# Protected API routes
@app.get("/api/profile")
async def get_user_profile(request: Request, current_user: dict = Depends(get_current_user)):
    """Get authenticated user profile."""
    return {
        "user": current_user,
        "message": "Profile retrieved successfully"
    }


@app.get("/api/protected")
async def protected_endpoint(request: Request, current_user: dict = Depends(get_current_user)):
    """Example protected endpoint."""
    return {
        "message": "This is a protected endpoint",
        "user": current_user["email"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(
        "Unexpected error occurred",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
