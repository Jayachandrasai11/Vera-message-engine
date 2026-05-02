from fastapi import FastAPI

import logging
import sys
from .routes import health, metadata, context, tick, reply
from .store.memory import USE_REDIS

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("vera")

app = FastAPI()

app.include_router(health.router, prefix="/v1")
app.include_router(metadata.router, prefix="/v1")
app.include_router(context.router, prefix="/v1")
app.include_router(tick.router, prefix="/v1")
app.include_router(reply.router, prefix="/v1")


@app.on_event("startup")
async def startup_event():
    mode = "DISTRIBUTED (Redis)" if USE_REDIS else "EPHEMERAL (In-Memory)"
    logger.info(f"Vera Engine starting in {mode} mode.")

@app.get("/")
def root():
    return {
        "message": "Vera Engine is running",
        "mode": "distributed" if USE_REDIS else "ephemeral"
    }