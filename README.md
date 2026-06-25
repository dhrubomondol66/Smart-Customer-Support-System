# Smart Customer Support Inbox Engine

A backend API system for managing customer support conversations — similar to Intercom or Zendesk. Built with Python, Django, Django REST Framework, Celery, Redis, and Django Channels.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | Django 4.2+, Django REST Framework |
| Authentication | JWT (djangorestframework-simplejwt) |
| Async Tasks | Celery + Redis |
| Real-Time | Django Channels (WebSocket) |
| Database | PostgreSQL |
| Cache / Lock | Redis (django-redis) |
| API Docs | drf-yasg (Swagger) |

---____

## Project Structure

```
smart_customer_support/
├── apps/
│   ├── accounts/                   # Agent authentication
│   │   ├── models.py               # Custom Agent user model
│   │   ├── serializers.py
│   │   ├── views.py                # Login endpoint
│   │   ├── urls.py
│   │   └── management/
│   │       └── commands/
│   │           └── seed.py         # Creates default admin agent
│   │
│   └── conversations/              # Core support inbox logic
│       ├── models.py               # Conversation, Message models
│       ├── serializers.py
│       ├── views.py                # All API endpoints
│       ├── urls.py
│       ├── tasks.py                # Celery background tasks
│       ├── consumers.py            # WebSocket consumer
│       ├── routing.py              # WebSocket URL routing
│       ├── services/
│       │   ├── suggestion_engine.py  # Mock AI reply suggestions
│       │   └── lock_service.py       # Redis distributed locking
│       └── tests/
│           ├── test_models.py
│           ├── test_api.py
│           └── test_services.py
│
├── config/
│   ├── settings.py
│   ├── celery.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── urls.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Features

### Core Features
- JWT Authentication — stateless, secure agent login
- Conversation Management — list, search, and filter by status
- Message Threading — full chronological chat history
- Agent Reply — send messages with instant HTTP response
- Mock AI Suggestions — keyword-based reply recommendations (no external API)

### Advanced Features
- Background Sentiment Analysis — Celery task fires after every agent reply, computes Positive/Neutral/Negative and stores on conversation
- Distributed Locking — Redis-based conversation lock with 5-minute auto-expiry, prevents two agents replying simultaneously
- Real-Time Broadcasting — Django Channels WebSocket pushes new messages to all connected agents instantly

---

## Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis

### Step 1 — Clone the Repository
```bash
git clone https://github.com/yourusername/smart-customer-support-inbox.git
cd smart-customer-support-inbox
```

### Step 2 — Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env`:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=*

DB_NAME=support_inbox
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379
```

### Step 5 — Run Migrations
```bash
python manage.py migrate
```

### Step 6 — Seed Database
```bash
python manage.py seed
```

Creates default agent:
```
Email    : admin@test.com
Password : admin123
```

### Step 7 — Start Redis
Make sure Redis is running on `localhost:6379`

```bash
# Windows (if Redis installed as service)
redis-cli ping   # should return PONG

# Linux/Mac
sudo service redis-server start
```

### Step 8 — Start Celery Worker
Open a new terminal:
```bash
# Windows
celery -A config worker --loglevel=info --pool=solo

# Linux/Mac
celery -A config worker --loglevel=info
```

### Step 9 — Start Django Server
```bash
python manage.py runserver
```

Server runs at: `http://127.0.0.1:8000`

---

## Docker Setup

### Start with Docker Compose
```bash
# Build and start all services
docker compose up --build

# Start in background
docker compose up -d --build

# Check running containers
docker compose ps
```

### Docker Services
| Service | Description | Port |
|---|---|---|
| web | Django app (Daphne ASGI) | 8000 |
| db | PostgreSQL | 5432 |
| redis | Redis | 6379 |
| celery | Celery worker | — |
| celery-beat | Periodic tasks | — |

### Useful Docker Commands
```bash
# View logs
docker compose logs web
docker compose logs celery

# Run management commands
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed

# Run tests
docker compose exec web pytest

# Stop everything
docker compose down

# Stop and delete volumes (fresh DB)
docker compose down -v
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login/` | Get JWT access + refresh token |
| POST | `/api/auth/refresh/` | Refresh access token |

### Conversations

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/conversations/` | List all conversations |
| GET | `/api/conversations/?search=John` | Search by customer name |
| GET | `/api/conversations/?status=open` | Filter by status |
| GET | `/api/conversations/{id}/messages/` | Get message thread |
| POST | `/api/conversations/{id}/messages/send/` | Send agent reply |
| POST | `/api/conversations/{id}/suggest-reply/` | Get AI suggestion |

### Locks

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/conversations/{id}/lock/` | Acquire conversation lock |
| DELETE | `/api/conversations/{id}/lock/release/` | Release lock |
| GET | `/api/conversations/{id}/lock/status/` | Check lock status + TTL |

### API Documentation
```
Swagger UI : http://127.0.0.1:8000/swagger/
Redoc      : http://127.0.0.1:8000/redoc/
```

---

## Request Examples

### Login
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "admin123"}'
```

Response:
```json
{
    "access": "eyJhbGciOiJIUzI1NiIs...",
    "refresh": "eyJhbGciOiJIUzI1NiIs...",
    "agent_id": 1,
    "email": "admin@test.com"
}
```

### List Conversations
```bash
curl -X GET http://127.0.0.1:8000/api/conversations/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Send Message
```bash
curl -X POST http://127.0.0.1:8000/api/conversations/1/messages/send/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "We will resolve this shortly!"}'
```

### Get AI Suggestion
```bash
curl -X POST http://127.0.0.1:8000/api/conversations/1/suggest-reply/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Customer wants refund"}'
```

Response:
```json
{
    "suggestion": "We are sorry for the inconvenience. We have initiated your refund and it will reflect within 5-7 business days."
}
```

### Acquire Lock
```bash
curl -X POST http://127.0.0.1:8000/api/conversations/1/lock/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Architecture Overview

### Non-Blocking Background Processing (Task 1)
When an agent sends a reply the HTTP thread is never blocked:

```
Agent sends message
        │
        ├── Message saved to DB
        ├── HTTP 201 returned instantly
        └── Celery task fires in background
                  │
                  └── Sentiment analyzed → Positive / Neutral / Negative
                            │
                            └── Conversation updated
```

### Distributed Locking (Task 2)
Prevents two agents replying to the same conversation simultaneously:

```
Agent 1 acquires lock
        │
Redis: conversation_lock:1 = "agent_1_id"  TTL = 300 seconds
        │
Agent 2 tries to send message
        │
System checks Redis → lock owned by Agent 1
        │
Agent 2 receives 423 Locked
        │
Lock auto-expires after 5 minutes OR Agent 1 releases manually
```

### Real-Time WebSocket Flow
```
Agent connects to ws://localhost:8000/ws/conversations/1/
        │
Joins room "conversation_1"
        │
Agent 2 also joins same room
        │
Agent 1 sends HTTP POST message
        │
views.py broadcasts to room via channel_layer
        │
Agent 2 receives message instantly — no refresh needed
```

---

## Running Tests

```bash
# Run all tests
python manage.py test apps

# Run with verbosity
python manage.py test apps --verbosity=2

# Using pytest
pytest

# Run specific test files
pytest apps/conversations/tests/test_models.py -v
pytest apps/conversations/tests/test_api.py -v
```

### Test Coverage
- Unit Test 1 — `Conversation.get_last_message()` model method
- Unit Test 2 — `LockService.calculate_ttl()` TTL helper
- Unit Test 3 — `SuggestionEngine.get_suggestion()` keyword mapping
- Integration Test 1 — JWT authentication header validation
- Integration Test 2 — Lock blocking other agents (423 response)

---

## AI Suggestion Keywords

The mock AI engine matches these keywords to generate suggestions:

| Keyword | Response Type |
|---|---|
| refund | Refund apology + timeline |
| cancel | Cancellation processing |
| shipping | Tracking information |
| delay | Delay apology |
| password | Reset instructions |
| payment | Payment issue help |
| damaged | Damaged item response |
| wrong | Wrong item response |
| broken / not working | Issue investigation |
| talk to human | Connect to agent |
| thank / thanks | Welcome response |

---

## Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| SECRET_KEY | Django secret key | — |
| DEBUG | Debug mode | True |
| ALLOWED_HOSTS | Allowed hosts | * |
| DB_NAME | Database name | support_inbox |
| DB_USER | Database user | postgres |
| DB_PASSWORD | Database password | postgres |
| DB_HOST | Database host | localhost |
| DB_PORT | Database port | 5432 |
| REDIS_URL | Redis connection URL | redis://localhost:6379 |

---

## License

This project was built as a technical assessment for a Mid-Level Backend Developer position.