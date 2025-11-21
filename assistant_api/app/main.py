"""
Assistant API
=============
FastAPI application for unified assistant item management
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import engine, Base
from .routers import items, stats

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Unified API for managing appointments, meetings, tasks, and goals"
)

# CORS middleware for Streamlit integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(items.router)
app.include_router(stats.router)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": settings.api_version}
