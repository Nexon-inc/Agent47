from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from ..config import settings

def setup_cors(app: FastAPI):
    """Setup CORS middleware"""
    app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
