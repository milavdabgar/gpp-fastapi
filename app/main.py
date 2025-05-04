from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION, CORS_ORIGINS, DATABASE_URL
from app.api import api_router
from app.database import Base, engine
from app.services.init import initialize_database
from app.middleware.error import error_handler

# Create FastAPI app
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    # Set the correct paths for the documentation
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root path handler - redirect to API docs
@app.get("/", tags=["root"], include_in_schema=False)
async def root_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/docs")

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "success", "message": "Server is running"}

# Include API routes
app.include_router(api_router)

# Add error handler middleware
app.middleware("http")(error_handler)

# Create database tables at startup
@app.on_event("startup")
async def startup_event():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize database with default data
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        initialize_database(db)
    finally:
        db.close()