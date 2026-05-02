import os
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Configuration & Infrastructure Setup
# -----------------------------------------------------------------------------

REDIS_URL = os.environ.get("REDIS_URL")
USE_REDIS = False
redis_client = None

if REDIS_URL:
    try:
        import redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        USE_REDIS = True
        logger.info("Successfully connected to Redis. Distributed state is ACTIVE.")
    except Exception as e:
        logger.warning(f"Redis connection failed. Falling back to in-memory store. Error: {e}")
else:
    logger.info("No REDIS_URL found in environment. Using ephemeral in-memory store.")

# Ephemeral in-memory fallbacks (legacy mode)
context_store: dict = {}
suppression_store: dict = {}

ACTION_VARIANTS = {
    "push_offer": [
        "1. {count} people searched for '{keyword}' near you — ready to convert? Your {offer} offer is live now.",
        "2. Rising search demand ({count}+) — your {offer} offer taps high-intent traffic.",
        "3. Missing out? {count} searches for '{keyword}' = easy conversions waiting."
    ],
    "improve_reviews": [
        "1. Rating needs attention — want me to help recover your reputation?",
        "2. Low rating = lost customers. Should I trigger a recovery plan?",
        "3. Your score affects visibility — let's fix reviews together."
    ],
    "run_campaign": [
        "1. General campaign boost — should I activate visibility for you?",
        "2. Business growth opportunity — launch campaign now?",
        "3. Ready to expand reach? Campaign can drive new customers."
    ]
}

PIVOT_ACTIONS = {
    "push_offer": "improve_reviews",
    "improve_reviews": "push_offer",
    "run_campaign": "push_offer",
    "retention_push": "run_campaign",
    "expand_capacity": "run_campaign"
}

SUPPRESSION_TTL_SECONDS = 60
DEFAULT_CONTEXT_TTL = 86400 * 7  # 7 days to prevent memory leaks in production

# -----------------------------------------------------------------------------
# Core State Management Functions
# -----------------------------------------------------------------------------

def _get_redis_json(key: str) -> dict | None:
    data = redis_client.get(key)
    return json.loads(data) if data else None

def _set_redis_json(key: str, data: dict, ttl: int = None):
    serialized = json.dumps(data)
    if ttl:
        redis_client.setex(key, ttl, serialized)
    else:
        redis_client.setex(key, DEFAULT_CONTEXT_TTL, serialized)

def store_context(scope: str, context_id: str, version: int, payload: dict) -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()
    ack_id = f"ack_{uuid.uuid4().hex[:8]}"
    
    if USE_REDIS:
        key = f"context:{context_id}"
        existing = _get_redis_json(key)
        
        if existing:
            if version <= existing.get("version", 0):
                return {"accepted": True, "ack_id": ack_id, "stored_at": now_iso}
            
        new_data = {
            "version": version,
            "payload": payload,
            "scope": scope,
            "last_action": existing.get("last_action") if existing else None,
            "interactions": existing.get("interactions", []) if existing else [],
            "updated_at": now_iso,
            "status": existing.get("status", "active") if existing else "active",
            "last_message": existing.get("last_message") if existing else None,
            "last_intent": existing.get("last_intent") if existing else None
        }
        _set_redis_json(key, new_data)
    else:
        existing = context_store.get(context_id)
        if existing and version <= existing.get("version", 0):
            return {"accepted": True, "ack_id": ack_id, "stored_at": now_iso}
            
        context_store[context_id] = {
            "version": version,
            "payload": payload,
            "scope": scope,
            "last_action": existing.get("last_action") if existing else None,
            "interactions": existing.get("interactions", []) if existing else [],
            "updated_at": now_iso,
            "status": existing.get("status", "active") if existing else "active",
            "last_message": existing.get("last_message") if existing else None,
            "last_intent": existing.get("last_intent") if existing else None
        }
        
    return {"accepted": True, "ack_id": ack_id, "stored_at": now_iso}


def get_context(context_id: str) -> dict | None:
    if USE_REDIS:
        return _get_redis_json(f"context:{context_id}")
    return context_store.get(context_id)


def save_last_action(context_id: str, action: str, trigger: dict = None, message: str = None) -> None:
    interaction = {
        "action": action,
        "trigger": trigger.get("type", "unknown") if trigger else "unknown",
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_status": "pending"
    }
    
    if USE_REDIS:
        key = f"context:{context_id}"
        ctx = _get_redis_json(key)
        if ctx:
            ctx["last_action"] = action
            ctx.setdefault("interactions", []).append(interaction)
            _set_redis_json(key, ctx)
    else:
        if context_id in context_store:
            context_store[context_id]["last_action"] = action
            context_store[context_id].setdefault("interactions", []).append(interaction)


def update_user_status(context_id: str, status: str) -> None:
    if USE_REDIS:
        key = f"context:{context_id}"
        ctx = _get_redis_json(key)
        if ctx and ctx.get("interactions"):
            ctx["interactions"][-1]["user_status"] = status
            _set_redis_json(key, ctx)
    else:
        if context_id in context_store:
            interactions = context_store[context_id].get("interactions", [])
            if interactions:
                interactions[-1]["user_status"] = status


def is_recently_sent(context_id: str, min_hours: int = 2) -> bool:
    ctx = get_context(context_id)
    if not ctx:
        return False
        
    interactions = ctx.get("interactions", [])
    if not interactions:
        return False
        
    last = interactions[-1]
    last_time = datetime.fromisoformat(last["timestamp"])
    return datetime.now(timezone.utc) - last_time < timedelta(hours=min_hours)


def get_last_interaction(context_id: str) -> dict | None:
    ctx = get_context(context_id)
    if not ctx:
        return None
    interactions = ctx.get("interactions", [])
    return interactions[-1] if interactions else None


def get_message_variant(action: str, variant_index: int = 0) -> str:
    variants = ACTION_VARIANTS.get(action, [])
    if variants:
        return variants[variant_index % len(variants)]
    return ""


# -----------------------------------------------------------------------------
# Suppression Management
# -----------------------------------------------------------------------------

def is_suppressed(merchant_id: str, suppression_key: str) -> bool:
    """Check if message is suppressed for this merchant + suppression key."""
    key = f"suppress:{merchant_id}:{suppression_key}"
    
    if USE_REDIS:
        # Redis natively handles expiration TTLs
        return bool(redis_client.exists(key))
    else:
        entry = suppression_store.get(key)
        if not entry:
            return False
        expires_at = entry.get("expires_at")
        if expires_at and datetime.now(timezone.utc) > datetime.fromisoformat(expires_at):
            del suppression_store[key]
            return False
        return True


def set_suppression(merchant_id: str, suppression_key: str, ttl_seconds: int = SUPPRESSION_TTL_SECONDS) -> None:
    """Set suppression for merchant + suppression key with TTL."""
    key = f"suppress:{merchant_id}:{suppression_key}"
    now_iso = datetime.now(timezone.utc)
    
    if USE_REDIS:
        data = {
            "merchant_id": merchant_id,
            "suppression_key": suppression_key,
            "set_at": now_iso.isoformat()
        }
        _set_redis_json(key, data, ttl=ttl_seconds)
    else:
        expires_at = now_iso + timedelta(seconds=ttl_seconds)
        suppression_store[key] = {
            "merchant_id": merchant_id,
            "suppression_key": suppression_key,
            "expires_at": expires_at.isoformat(),
            "set_at": now_iso.isoformat()
        }


# -----------------------------------------------------------------------------
# Conversation State
# -----------------------------------------------------------------------------

def get_conversation_state(context_id: str) -> dict:
    """Get conversation state for context."""
    stored = get_context(context_id)
    if not stored:
        return {"status": "unknown", "last_message": None, "last_intent": None}
    return {
        "status": stored.get("status", "active"),
        "last_message": stored.get("last_message"),
        "last_intent": stored.get("last_intent"),
        "last_updated": stored.get("updated_at")
    }


def update_conversation_state(context_id: str, status: str = None, last_message: str = None, last_intent: str = None) -> None:
    """Update conversation state."""
    now_iso = datetime.now(timezone.utc).isoformat()
    
    if USE_REDIS:
        key = f"context:{context_id}"
        ctx = _get_redis_json(key)
        if ctx:
            if status: ctx["status"] = status
            if last_message: ctx["last_message"] = last_message
            if last_intent: ctx["last_intent"] = last_intent
            ctx["updated_at"] = now_iso
            _set_redis_json(key, ctx)
    else:
        if context_id in context_store:
            if status: context_store[context_id]["status"] = status
            if last_message: context_store[context_id]["last_message"] = last_message
            if last_intent: context_store[context_id]["last_intent"] = last_intent
            context_store[context_id]["updated_at"] = now_iso