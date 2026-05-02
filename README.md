# 🚀 Vera Message Engine

> **Live API Demo:** [https://veramessageengine.dssjcs01.workers.dev/](https://veramessageengine.dssjcs01.workers.dev/)

A **deterministic AI decision engine** for merchant growth automation that generates **data-driven, action-oriented messages** based on business triggers and contextual insights.

---

## 🧠 Overview

Vera Message Engine simulates a **real-world merchant engagement system** (similar to campaign automation platforms), designed to:

* Analyze merchant performance signals
* Interpret business triggers
* Select optimal growth actions
* Generate high-quality, contextual messages

The system ensures **consistent, deterministic, and production-safe outputs**.

---

## 🎯 Key Objectives

* Deliver **intelligent business recommendations**
* Maintain **deterministic outputs (same input → same output)**
* Ensure **high-quality messaging with clear actions**
* Handle **unknown categories safely**
* Pass **strict evaluation benchmarks**

---

## ⚙️ Core Features

### ✅ 1. Deterministic Decision Engine

* Rule-based + scoring-driven logic
* No randomness
* Consistent outputs across runs

---

### ✅ 2. Trigger-Based Intelligence

Supports triggers like:

* `search_spike` → capitalize demand
* `footfall_drop` → recover traffic
* `recall_due` → improve retention
* `festival` → promotional opportunity
* `research` → visibility improvement
* `compliance` → trust building

---

### ✅ 3. Action Selection System

Chooses the most impactful action:

* `push_offer`
* `retention_push`
* `improve_reviews`
* `run_campaign`
* `add_photos`

Based on merchant condition and trigger context.

---

### ✅ 4. Dynamic Message Composer

* Action-first message generation
* Context-aware insights
* Data-driven (%, trends, behavior)
* Category-aware tone (but not dependent)

---

### ✅ 5. Strict Validation Layer

Ensures:

* Single CTA enforcement
* Correct suppression logic
* No malformed outputs
* Consistent formatting

---

### ✅ 6. Category-Agnostic Design

Works for:

* Known categories (dentists, gyms, salons, etc.)
* Unknown categories (fallback-safe logic)

---

### ✅ 7. Suppression Logic

Prevents duplicate messaging using:

```
<merchant_id>_<action>_<trigger>
```

Ensures better user experience and avoids spam.

---

### ✅ 8. Distributed State Management

* Redis integration for cross-worker state sharing
* Persistent session storage
* Graceful fallback to in-memory mode for local development

---

## 🌐 Infrastructure & Scaling

The engine is designed for high-availability production environments:

* **Stateless API:** The FastAPI layer can be scaled horizontally.
* **Distributed Queuing:** Uses Redis Lists (`LPUSH`/`BRPOP`) for reliable, asynchronous task processing.
* **Persistence:** Merchant context and suppression states survive server restarts.
* **Rate Limiting:** Built-in protection against merchant-level request spikes.

---

## 🏗️ System Architecture

```
INPUT (context + trigger)
        ↓
Input Validation & Normalization
        ↓
Trigger Understanding
        ↓
Merchant Analysis
        ↓
Action Scoring Engine
        ↓
Best Action Selection
        ↓
Message Composition
        ↓
Validation & Formatting
        ↓
OUTPUT (Final JSON)
```

---

## 📂 Project Structure

```
project/
│
├── routes/           # API endpoints
├── engine/           # decision logic, composer, validator
├── store/            # in-memory context storage
├── templates/        # message templates (if used)
├── utils/            # helpers
│
├── main.py           # FastAPI app entry
├── requirements.txt
└── README.md
```

---

## 🔌 API Endpoints

### 1. Health Check

```
GET /v1/healthz
```

---

### 2. Metadata

```
GET /v1/metadata
```

---

### 3. Context Ingestion

```
POST /v1/context
```

Stores merchant + category data.

---

### 4. Core Decision Endpoint ⭐

```
POST /v1/tick
```

Triggers the engine and returns final output.

---

### 5. Reply Handling

```
POST /v1/reply
```

Handles user responses (yes / no / later).

---

## 📥 Sample Input

```json
{
  "context_id": "m_101",
  "trigger": {
    "type": "recall_due"
  }
}
```

---

## 📤 Sample Output

```json
{
  "message": "Dr. Meera Clinic, several patients are likely due for their 6-month checkups around this time. Sending a recall reminder now can help improve repeat visits by ~20–25%.",
  "cta": "Send reminder?",
  "send_as": "Vera",
  "suppression_key": "m_101_retention_push_recall_due",
  "rationale": "recall_due + repeat visit opportunity → retention_push to improve revisit rate"
}
```

---

## 🧪 Evaluation Strategy

The system is tested using a dataset with:

* Action correctness
* Trigger relevance
* Message quality
* Business impact
* CTA clarity
* Determinism

### ✅ Target Metrics

* Average Score ≥ 24/30
* Pass Rate ≥ 85%
* Zero null outputs

---

## 🔐 Design Principles

* Deterministic over probabilistic
* Action-driven decision making
* Clear business value in every message
* Fail-safe and fallback-ready
* Minimal dependencies (FastAPI only)

---

## 🛠️ Tech Stack

* Python
* FastAPI
* Redis (Session & Queue)
* Pydantic

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Run server

```bash
uvicorn main:app --reload
```

---

### 3. Test API

```bash
curl -X POST "http://localhost:8000/v1/tick" \
  -H "Content-Type: application/json" \
  -d '{"context_id":"m_101","trigger":{"type":"recall_due"}}'
```

---

### 4. Run Background Workers

For distributed event processing, start the workers in separate terminal windows:

```bash
# For decision logic
python worker_manager.py decision

# For message composition/replies
python worker_manager.py reply
```

---

## 📌 Highlights

* 💡 Smart business insights
* ⚡ Fast, lightweight API
* 🧠 Deterministic decision engine
* 🔒 Production-safe outputs
* 📈 Designed for real-world merchant growth

---

## 🏁 Conclusion

Vera Message Engine demonstrates how a **deterministic AI system** can deliver **consistent, high-impact business messaging** by combining:

* structured logic
* contextual understanding
* action-oriented design

---

## 📬 Future Improvements

* Vector Database (RAG) for deep category research
* Real-time analytics dashboard
* Multi-channel adapters (SMS, WhatsApp, Push)
* A/B testing for message variations

---

## 👨‍💻 Author

Built as part of a **merchant campaign automation challenge**, focusing on real-world system design and production-ready architecture.
