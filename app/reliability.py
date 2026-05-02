import uuid
import time
import json
import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Callable

logger = logging.getLogger("vera")

# Global metrics store
metrics_store: dict = {
    "total_requests": 0,
    "successful_responses": 0,
    "failed_responses": 0,
    "no_action_count": 0,
    "suppression_count": 0,
    "start_time": time.time()
}


def generate_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:8]}"


def log_event(event_type: str, data: dict) -> None:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        **data
    }
    logger.info(json.dumps(event))


def increment_metric(name: str) -> None:
    metrics_store[name] = metrics_store.get(name, 0) + 1


def record_latency(endpoint: str, latency_ms: float) -> None:
    metrics_store[f"{endpoint}_latency_ms"] = latency_ms


def get_metrics() -> dict:
    uptime = time.time() - metrics_store.get("start_time", time.time())
    return {
        "total_requests": metrics_store.get("total_requests", 0),
        "successful_responses": metrics_store.get("successful_responses", 0),
        "failed_responses": metrics_store.get("failed_responses", 0),
        "no_action_count": metrics_store.get("no_action_count", 0),
        "suppression_count": metrics_store.get("suppression_count", 0),
        "uptime_seconds": round(uptime, 2)
    }


def log_request(request_id: str, endpoint: str, data: dict) -> None:
    log_event("request_start", {
        "request_id": request_id,
        "endpoint": endpoint,
        **{k: v for k, v in data.items() if k in ["context_id", "trigger_type", "decision", "status"]}
    })


def log_response(request_id: str, endpoint: str, status: str, latency_ms: float, decision: str = None) -> None:
    log_event("request_end", {
        "request_id": request_id,
        "endpoint": endpoint,
        "status": status,
        "latency_ms": latency_ms,
        "decision": decision
    })


def log_error(request_id: str, endpoint: str, error: Exception, stack_trace: str = None) -> None:
    log_event("error", {
        "request_id": request_id,
        "endpoint": endpoint,
        "error": str(error),
        "stack_trace": stack_trace
    })


class ReliabilityLayer:
    def __init__(self):
        self.request_counts: dict = {}
        self.rate_limit = 10  # requests per second per merchant_id

    def check_rate_limit(self, merchant_id: str) -> bool:
        now = time.time()
        key = f"{merchant_id}"
        
        if key not in self.request_counts:
            self.request_counts[key] = []
        
        # Keep only requests from last second
        self.request_counts[key] = [t for t in self.request_counts[key] if now - t < 1]
        
        if len(self.request_counts[key]) >= self.rate_limit:
            return False
        
        self.request_counts[key].append(now)
        return True

    def with_reliability(self, endpoint: str):
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                request_id = generate_request_id()
                
                increment_metric("total_requests")
                
                try:
                    log_request(request_id, endpoint, {"context_id": kwargs.get("context_id", "")})
                    
                    result = func(*args, **kwargs)
                    
                    latency_ms = round((time.time() - start_time) * 1000, 2)
                    record_latency(endpoint, latency_ms)
                    
                    status = "success"
                    if result.get("message") is None:
                        status = "no_action"
                        increment_metric("no_action_count")
                    elif result.get("suppression_key") and "suppressed" in result.get("rationale", "").lower():
                        increment_metric("suppression_count")
                    
                    increment_metric("successful_responses")
                    log_response(request_id, endpoint, status, latency_ms, result.get("rationale"))
                    
                    return result
                    
                except Exception as e:
                    increment_metric("failed_responses")
                    log_error(request_id, endpoint, e, str(e.__traceback__))
                    
                    return {
                        "message": None,
                        "cta": None,
                        "send_as": "Vera",
                        "suppression_key": "error",
                        "rationale": "Internal error occurred"
                    }
            return wrapper
        return decorator

    def rate_limit_response(self) -> dict:
        return {
            "message": None,
            "cta": None,
            "send_as": "Vera",
            "suppression_key": "rate_limited",
            "rationale": "Too many requests"
        }


reliability = ReliabilityLayer()