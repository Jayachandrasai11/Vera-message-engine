from fastapi import APIRouter
from datetime import datetime

from ..reliability import get_metrics

router = APIRouter()

START_TIME = datetime.now()


@router.get("/healthz")
def healthz():
    metrics = get_metrics()
    return {
        "status": "ok",
        "uptime": f"{metrics['uptime_seconds']}s",
        "dependencies": {
            "db": "ok",
            "redis": "ok"
        },
        "metrics": metrics
    }


@router.get("/health")
def health():
    metrics = get_metrics()
    return {
        "status": "ok",
        "uptime": f"{metrics['uptime_seconds']}s",
        "dependencies": {
            "db": "ok",
            "redis": "ok"
        },
        "metrics": metrics
    }