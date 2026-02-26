📬 Notification Prioritization Engine

An AI-Native backend system that intelligently decides whether a notification should be:

- 🚀 Delivered immediately (`now`)
- 📦 Batched for later (`batch`)
- 🔕 Suppressed (`suppress`)

This system combines rule-based logic, deduplication, fatigue control, and configurable YAML rules to simulate real-world notification decision engines used in production systems.

---

# 🧠 Problem Statement

Modern applications generate large volumes of notifications.  
Sending every notification immediately leads to:

- User fatigue
- Duplicate alerts
- Reduced engagement
- Poor user experience

This engine introduces intelligent decision logic to ensure users receive only meaningful, timely notifications.

---

# 🏗️ Architecture Overview
app/
│
├── main.py # FastAPI entry point
├── models.py # Request/Response schemas (Pydantic)
├── decision.py # Core decision orchestration
├── rules.py # Rule engine logic (YAML-driven)
├── dedupe.py # Duplicate detection logic
├── fatigue.py # User fatigue management
├── storage.py # SQLite interaction layer
└── ai.py # AI-style scoring logic


### Design Principles:
- Modular & extensible
- Config-driven (rules.yaml)
- Clear separation of concerns
- Easy to scale to production systems

---

# ⚙️ Decision Pipeline

When a notification request hits `/v1/decide`, the system:

1. Validates input using Pydantic models
2. Loads rules from `rules.yaml`
3. Checks duplicate notifications
4. Applies fatigue control logic
5. Calculates priority score
6. Decides final action (`now`, `batch`, or `suppress`)
7. Returns reasoning trace for transparency

---

# 🚀 API Endpoint

### POST `/v1/decide`

### Sample Request

```json
{
  "user_id": "user_123",
  "type": "promo",
  "content": "50% off on premium plan!",
  "timestamp": "2025-01-01T10:00:00"
}

{
  "action": "batch",
  "priority_score": 42,
  "reasoning": [
    "Promo type detected",
    "User received 3 notifications today",
    "Fatigue threshold nearing",
    "Batching recommended"
  ]
}

📦 Tech Stack

Python 3.12

FastAPI

SQLite

Pydantic

YAML configuration


🛠️ Installation & Run
1️⃣ Clone Repository
git clone https://github.com/SpandanaS28/AI-Native-Solution-Crafting-Test-.git
cd AI-Native-Solution-Crafting-Test-

2️⃣ Create Virtual Environment
python -m venv .venv

Activate:
Windows:
.venv\Scripts\activate

Mac/Linux:
source .venv/bin/activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Run Application
uvicorn app.main:app --reload

Open in browser:
http://127.0.0.1:8000/docs

📊 Key Features

✅ Rule-based prioritization
✅ YAML-configurable logic
✅ Duplicate detection
✅ Fatigue management
✅ Decision trace logging
✅ Modular architecture
✅ Production-style structure

🔍 Why This Is AI-Native

This system is AI-Native because:

Decision logic is separated into scoring modules

Transparent reasoning trace is returned

Rules are dynamically configurable

Architecture supports future ML model integration

Designed for adaptive prioritization

📈 Future Improvements

Replace rule scoring with ML model

Add Redis caching layer

Add rate-limiting middleware

Add user behavior analytics

Add notification delivery simulation

🎬 Demo Instructions

Start server

Open /docs

Test /v1/decide

Observe:

Action

Priority Score

Reasoning trace

👩‍💻 Author

Spandana S

📌 Submission Notes

This project demonstrates:

Clean backend architecture

Decision engine logic

Config-driven prioritization

Real-world notification management concepts

---

# ✅ After Pasting

1. Click **Commit changes**
2. Add message: `Added detailed README`
3. Commit directly to main

---

Now your repository will look polished and professional.

If you want, next I can give you a **perfect 3–5 minute walkthrough script** so you sound confident and structured in your submission video.
