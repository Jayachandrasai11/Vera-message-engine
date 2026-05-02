KAFKA_TOPICS = {
    "context_events": {
        "partitions": 6,
        "replication": 3,
        "description": "Context created/updated events"
    },
    "trigger_events": {
        "partitions": 12,
        "replication": 3,
        "description": "Trigger/alert events from external sources"
    },
    "reply_events": {
        "partitions": 6,
        "replication": 3,
        "description": "User conversation replies"
    },
    "action_events": {
        "partitions": 12,
        "replication": 3,
        "description": "Executed actions ready for delivery"
    },
    "message_events": {
        "partitions": 6,
        "replication": 3,
        "description": "Generated messages for delivery"
    },
    "dead_letter_events": {
        "partitions": 3,
        "replication": 3,
        "description": "Failed events after max retries"
    }
}

WORKER_CONFIG = {
    "context_worker": {
        "topics": ["context_events"],
        "group_id": "context-processors",
        "concurrency": 4
    },
    "decision_worker": {
        "topics": ["trigger_events"],
        "group_id": "decision-processors",
        "concurrency": 8
    },
    "reply_worker": {
        "topics": ["reply_events"],
        "group_id": "reply-processors",
        "concurrency": 4
    },
    "message_worker": {
        "topics": ["action_events"],
        "group_id": "message-processors",
        "concurrency": 6
    }
}