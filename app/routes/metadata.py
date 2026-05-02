from fastapi import APIRouter

router = APIRouter()


@router.get("/metadata")
def metadata():
    return {
        "name": "Vera Engine",
        "version": "1.0",
        "strategy": "deterministic rule-based decision engine"
    }