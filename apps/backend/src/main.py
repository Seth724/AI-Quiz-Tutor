"""
AI Quiz Tutor - Backend (ML Service)

FastAPI backend for:
- Document upload & processing (PDF, images)
- RAG with MongoDB Atlas
- Quiz generation
- Progress tracking
- Chat with AI tutor

Uses working code from tutorial-3-mongodb:
- pdf_rag_simple.py (PDF processing)
- demo_retrieval_methods.py (MongoDB retrieval)
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings

# Initialize FastAPI app
app = FastAPI(
    title="AI Quiz Tutor API",
    description="Backend for AI-powered quiz generation from documents",
    version="0.1.0"
)

frontend_origins = [
    origin.strip()
    for origin in str(settings.FRONTEND_ORIGINS or "").split(",")
    if origin.strip()
]

# CORS - Allow frontend to access
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_origin_regex=str(settings.FRONTEND_ORIGIN_REGEX or "") or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Health Check
# ============================================================================
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "AI Quiz Tutor API is running",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    """Health check for monitoring"""
    return {"status": "healthy"}

# ============================================================================
# Import Services (will create next)
# ============================================================================
from api.routes import router as api_router

# Include API routes
app.include_router(api_router, prefix="/api")

# ============================================================================
# Run Server
# ============================================================================
if __name__ == "__main__":
    print("="*60)
    print("AI Quiz Tutor - Backend (ML Service)")
    print("="*60)
    print(f"\nStarting server at: {settings.BACKEND_URL}")
    print(f"API Docs: {settings.BACKEND_URL}/docs")
    print(f"Environment: {settings.ENVIRONMENT}")
    print("\n" + "="*60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=(settings.ENVIRONMENT == "development")
    )
