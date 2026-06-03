from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.student_routes import router as student_router
from backend.api.hr_routes import router as hr_router
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env from parent directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

app = FastAPI(title="ProCareer Platform API", description="API for Resume Screening and Student Career Tools")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(student_router, prefix="/api/student", tags=["Student Portal"])
app.include_router(hr_router, prefix="/api/hr", tags=["HR Portal"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the ProCareer API"}
