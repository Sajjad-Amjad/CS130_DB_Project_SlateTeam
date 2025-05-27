from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api import api_router
from app.core.config import PROJECT_NAME, API_V1_STR
from app.database.session import get_db

app = FastAPI(title=PROJECT_NAME)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": f"Welcome to {PROJECT_NAME} API"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Include API router
app.include_router(api_router, prefix=API_V1_STR)