from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import time
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Set
from .routes import assets, data_sources, time_series, ingestion

# Configure logging
logger = logging.getLogger(__name__)

# WebSocket connection manager for progress updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.progress_data: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_progress_update(self, session_id: str, progress_data: dict):
        """Send progress update to all connected clients"""
        logger.info(f"Sending progress update for session {session_id}: {progress_data}")
        
        if not self.active_connections:
            logger.warning("No active WebSocket connections to send progress to")
            return
            
        message = {
            "type": "progress_update",
            "session_id": session_id,
            "data": progress_data
        }
        
        # Store latest progress data
        self.progress_data[session_id] = progress_data
        
        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
                logger.debug("Sent progress update to WebSocket connection")
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        if disconnected:
            logger.info(f"Removing {len(disconnected)} disconnected WebSocket connections")
            self.active_connections -= disconnected

manager = ConnectionManager()

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

# Mount static files for the web interface
web_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web")
if os.path.exists(web_directory):
    app.mount("/web", StaticFiles(directory=web_directory, html=True), name="web")
    logger.info(f"Web interface mounted at /web from {web_directory}")

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates with improved timeout handling"""
    await manager.connect(websocket)
    try:
        while True:
            try:
                # Reduced timeout to improve responsiveness
                await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
            except asyncio.TimeoutError:
                # Send keepalive ping to maintain connection
                try:
                    await websocket.send_json({"type": "ping", "timestamp": datetime.now().isoformat()})
                except (WebSocketDisconnect, ConnectionError):
                    # If ping fails, connection is likely dead
                    break
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    """Root endpoint redirects to web interface"""
    logger.info("Root endpoint accessed - redirecting to web interface")
    return RedirectResponse(url="/web/")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception for {request.method} {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )