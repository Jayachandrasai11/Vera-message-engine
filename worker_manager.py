#!/usr/bin/env python
"""Worker manager for distributed event processing with Redis support."""
import os
import json
import time
import signal
import sys
import logging

from app.workers.context_worker import process_context_event
from app.workers.decision_worker import process_trigger_event
from app.workers.reply_worker import process_reply_event
from app.events.producer import producer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("worker_manager")

# Worker registry
WORKERS = {
    "context": {
        "topic": "context_events",
        "handler": process_context_event
    },
    "decision": {
        "topic": "trigger_events", 
        "handler": process_trigger_event
    },
    "reply": {
        "topic": "reply_events",
        "handler": process_reply_event
    }
}

def run_worker(worker_name: str, max_messages: int = None):
    """Run a single worker polling from Redis or local mock producer."""
    worker_config = WORKERS.get(worker_name)
    if not worker_config:
        logger.error(f"Unknown worker: {worker_name}")
        return
    
    topic = worker_config["topic"]
    handler = worker_config["handler"]
    
    logger.info(f"Starting {worker_name} worker on topic: {topic}")
    
    processed_count = 0
    
    # Graceful shutdown handling
    running = True
    def stop_worker(signum, frame):
        nonlocal running
        logger.info(f"Shutdown signal received. Stopping {worker_name}...")
        running = False
    
    signal.signal(signal.SIGINT, stop_worker)
    signal.signal(signal.SIGTERM, stop_worker)

    while running:
        if max_messages and processed_count >= max_messages:
            logger.info(f"Reached max_messages ({max_messages}). Exiting.")
            break
            
        message_data = None
        
        if producer.use_redis:
            # BRPOP (Blocking Right Pop) - Wait for 1 second for a new message
            # This is the industry standard for lightweight distributed workers
            msg = producer.redis_client.brpop(f"queue:{topic}", timeout=1)
            if msg:
                # msg is a tuple (key, value)
                message_data = json.loads(msg[1])
        else:
            # Fallback to local memory list (non-blocking)
            if producer.topics.get(topic):
                msg_obj = producer.topics[topic].pop(0)
                message_data = json.loads(msg_obj["value"])
            else:
                time.sleep(0.5) # Prevent CPU spinning in mock mode
        
        if message_data:
            try:
                result = handler(message_data)
                processed_count += 1
                logger.info(f"[{worker_name}] Result: {result.get('status', 'ok')}")
            except Exception as e:
                logger.error(f"[{worker_name}] Fatal handler error: {e}")
                time.sleep(1)

    logger.info(f"Worker {worker_name} stopped. Total processed: {processed_count}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python worker_manager.py <worker_name> [max_messages]")
        print(f"Available workers: {list(WORKERS.keys())}")
        sys.exit(1)
    
    name = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run_worker(name, limit)