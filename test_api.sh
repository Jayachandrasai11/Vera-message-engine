#!/bin/bash

# Start server in background first: uvicorn app.main:app --reload

# Create context with required fields
curl -X POST http://127.0.0.1:8000/v1/context \
  -H "Content-Type: application/json" \
  -d '{"scope": "merchant", "context_id": "test_ctx", "version": 1, "payload": {"merchant": {"id": "m_101", "name": "Dr. Meera Clinic"}, "category": {"slug": "dentists"}}, "delivered_at": "2024-01-01T00:00:00Z"}'

echo ""
echo "---"

# Test customer-level recall (last_visit_days >= 150)
curl -X POST http://127.0.0.1:8000/v1/tick \
  -H "Content-Type: application/json" \
  -d '{"context_id": "test_ctx", "trigger": {"type": "recall_due", "customer": {"id": "c_1", "name": "John", "last_visit_days": 160}}}'

echo ""
echo "---"

# Test merchant-level recall nudge
curl -X POST http://127.0.0.1:8000/v1/tick \
  -H "Content-Type: application/json" \
  -d '{"context_id": "test_ctx", "trigger": {"type": "recall_due"}}'