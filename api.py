"""
FastAPI web server for CalOmr
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
from pathlib import Path

from main import CalOmrPipeline

app = FastAPI(
    title="CalOmr API",
    description="AI-powered STEM question solver with RAG",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline (singleton)
pipeline = None


@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup"""
    global pipeline
    print("🚀 Starting CalOmr API...")
    pipeline = CalOmrPipeline()
    print("✓ API ready!")


class SolveResponse(BaseModel):
    """Response model for solve endpoint"""
    answer: str
    confidence: int
    reasoning: str
    source: str
    question_data: dict
    total_time_seconds: float


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "CalOmr",
        "version": "1.0.0"
    }


@app.post("/solve", response_model=SolveResponse)
async def solve_question(
    file: UploadFile = File(...),
    verify: bool = False
):
    """
    Solve a question from an uploaded image
    
    Args:
        file: Question image (JPG, PNG)
        verify: Whether to verify answer
        
    Returns:
        Solution with answer and reasoning
    """
    if not pipeline:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save to temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Solve question
        result = pipeline.solve_question(tmp_path, verify=verify)
        
        # Clean up
        os.unlink(tmp_path)
        
        return result
        
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics():
    """Get database statistics"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        stats = pipeline.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "pipeline_initialized": pipeline is not None,
        "components": {
            "groq": True,
            "database": True,
            "embeddings": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
