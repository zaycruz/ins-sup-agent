from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "components": {
            "api": "healthy",
            "job_store": "healthy",
            "vision_model": "available",
            "text_model": "available",
        },
    }


@router.get("/ready")
async def readiness_check() -> dict:
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
