from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from .routes import assets, data_sources, time_series, ingestion

# Configure logging
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    try:
        # Import here to delay database connection until needed
        from connect_database import get_session
        # Test database connection
        session = get_session()
        session.execute("SELECT now() FROM system.local")
        logger.info("Successfully connected to database")
    except Exception as e:
        logger.warning(f"Database connection failed during startup: {str(e)}")
        logger.info("Application will start but database operations may fail")
    
    yield


app = FastAPI(
    title="Acme Ltd Financial Data Warehouse API",
    description="API for managing financial data from various sources",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log the incoming request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process the request
    response = await call_next(request)
    
    # Calculate request duration
    process_time = time.time() - start_time
    
    # Log the response
    logger.info(f"Response: {request.method} {request.url} - Status: {response.status_code} - Duration: {process_time:.3f}s")
    
    return response

# Include routers
app.include_router(assets.router)
app.include_router(data_sources.router)
app.include_router(time_series.router)
app.include_router(ingestion.router)

@app.get("/health")
async def health_check():
    """Health check endpoint with database connectivity test"""
    logger.info("Health check requested")
    try:
        from connect_database import get_session
        session = get_session()
        result = session.execute("SELECT now() FROM system.local").one()
        logger.info("Health check passed - database connection successful")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": str(result[0]) if result else None
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to Acme Ltd Financial Data Warehouse API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception for {request.method} {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )