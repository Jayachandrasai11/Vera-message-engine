import os
import json
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("vera")

class Producer:
    """Production-ready producer using Redis for task queuing with in-memory fallback."""
    
    def __init__(self):
        self.redis_client = None
        self.use_redis = False
        
        # Mock storage for fallback mode
        self.topics: Dict[str, list] = {
            "context_events": [],
            "trigger_events": [],
            "reply_events": [],
            "action_events": [],
            "message_events": [],
            "dead_letter_events": []
        }
        
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Producer successfully connected to Redis for distributed queuing.")
            except Exception as e:
                logger.warning(f"Producer failed to connect to Redis, using in-memory fallback: {e}")

    def send(self, topic: str, value: str | Dict[str, Any], key: str = None) -> None:
        """Send message to topic (Redis list or local list)."""
        message_dict = value if isinstance(value, dict) else json.loads(value)
        
        # Add metadata if not present
        if "metadata" not in message_dict:
            message_dict["metadata"] = {}
        
        message_dict["metadata"].update({
            "producer_id": "vera_engine_prod",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "key": key or str(uuid.uuid4())
        })
        
        message_json = json.dumps(message_dict)
        
        if self.use_redis:
            # Using Redis LIST as a simple queue (LPUSH/BRPOP pattern)
            self.redis_client.lpush(f"queue:{topic}", message_json)
        else:
            # Fallback to local memory
            if topic not in self.topics:
                self.topics[topic] = []
            self.topics[topic].append({
                "key": key or str(uuid.uuid4()),
                "value": message_json,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    def flush(self) -> None:
        """Flush pending messages (no-op for Redis lists)."""
        pass

# Global producer instance
producer = Producer()

def produce_event(topic: str, event: Dict[str, Any]) -> str:
    """Produce event to the configured message bus."""
    producer.send(topic, event)
    return event.get("event_id", "")