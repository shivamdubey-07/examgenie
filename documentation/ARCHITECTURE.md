# System Architecture

## Overview

ExamGenie is a full-stack web application for AI-powered exam generation and tracking. It uses a modern microservices-like architecture with clear separation of concerns.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Nginx Reverse Proxy                      │
│  (SSL/TLS, Caching, Rate Limiting, Static Files)           │
└─────────────────────────────────────────────────────────────┘
         │                                      │
         ▼                                      ▼
┌──────────────────────────────┐    ┌──────────────────────┐
│   React Frontend (Vite)      │    │   FastAPI Backend    │
│   - Pages                    │    │   - API Routes       │
│   - Components               │    │   - Business Logic   │
│   - State Management         │    │   - Data Validation  │
└──────────────────────────────┘    └──────────────────────┘
         │                                      │
         │                        ┌─────────────┼─────────────┐
         │                        │             │             │
         ▼                        ▼             ▼             ▼
    (HTTP API)          ┌──────────────┐ ┌──────────┐ ┌──────────┐
                        │ PostgreSQL   │ │  Redis   │ │  MinIO   │
                        │  Database    │ │  Cache   │ │ Storage  │
                        └──────────────┘ └──────────┘ └──────────┘

                        ┌──────────────┐
                        │ Celery Worker│
                        │ Task Queue   │
                        └──────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │ OpenAI API   │
                        │ (External)   │
                        └──────────────┘
```

## Component Architecture

### Frontend Layer (React + Vite)

**Responsibilities:**

- User interface rendering
- Client-side routing
- Form validation and submission
- State management
- API integration

**Key Components:**

```
examgenie_frontend/
├── src/
│   ├── pages/
│   │   ├── Landing.jsx      (Home/intro page)
│   │   ├── Register.jsx     (User registration)
│   │   ├── Login.jsx        (Authentication)
│   │   ├── Dashboard.jsx    (Main dashboard)
│   │   ├── Generate.jsx     (Exam generation)
│   │   ├── Exam.jsx         (Exam taking)
│   │   └── Results.jsx      (Results/analytics)
│   ├── services/
│   │   └── api.js           (Axios client)
│   └── assets/              (Images, fonts, etc)
```

**Technologies:**

- React 19 - UI framework
- Vite - Build tool & dev server
- React Router v7 - Client-side routing
- Axios - HTTP client
- Tailwind CSS - Styling

### API Layer (FastAPI)

**Responsibilities:**

- REST API endpoints
- Request validation (Pydantic)
- Authentication/Authorization
- Business logic orchestration
- Data persistence

**Key Modules:**

```
app/
├── main.py              (FastAPI app setup)
├── auth/
│   ├── jwt_handler.py   (Token generation/verification)
│   └── password.py      (Hashing and verification)
├── routes/              (API endpoints)
│   ├── users.py
│   ├── exams.py
│   ├── attempts.py
│   └── ...
├── models/              (SQLAlchemy ORM models)
│   ├── user.py
│   ├── exam.py
│   ├── question.py
│   ├── attempt.py
│   └── ...
├── schemas/             (Pydantic request/response models)
│   └── models.py
├── services/            (Business logic)
│   ├── ai/              (OpenAI integration)
│   ├── cache/           (Redis operations)
│   ├── pdf/             (PDF generation)
│   └── storage/         (S3/MinIO operations)
└── worker/              (Celery tasks)
    ├── celery_app.py    (Celery configuration)
    └── tasks.py         (Async tasks)
```

**Key Technologies:**

- FastAPI - Web framework
- SQLAlchemy 2.0 - ORM
- Pydantic 2.0 - Data validation
- Alembic - Database migrations
- Celery - Task queue
- Passlib - Password hashing
- PyJWT - JWT tokens

### Data Layer

#### PostgreSQL Database

- **Primary datastore** for application data
- **Schema versioning** via Alembic migrations
- **Persistence** for users, exams, questions, attempts, etc.

**Key Tables:**

```sql
users              -- User accounts
exams              -- Exam metadata
questions          -- Individual questions
question_options   -- Multiple choice options
exams_attempts     -- Exam attempts by users
attempt_answers    -- User's answers during attempt
exam_questions     -- Question-to-exam mapping
question_statistics -- Analytics per question
ai_generation_logs  -- AI generation history
```

#### Redis Cache

- **Session storage** for active connections
- **Task queue** for Celery workers
- **Caching layer** for frequently accessed data

**Uses:**

- User session tokens
- Celery task queue
- Cache invalidation on data updates

#### MinIO (S3-Compatible Storage)

- **File storage** for PDFs, exports
- **Backup storage** for generated content
- **Multi-part upload** support for large files

### Service Layer

#### Authentication Service (`auth/`)

- JWT token generation and validation
- Password hashing with Passlib
- User session management
- Token refresh mechanism

#### AI Service (`services/ai/`)

- OpenAI API integration
- Prompt engineering for exam generation
- Streaming responses for long-running operations
- Error handling and retry logic

#### Cache Service (`services/cache/`)

- Redis connection pooling
- Key-value operations
- Cache invalidation strategies
- TTL management

#### Storage Service (`services/storage/`)

- S3/MinIO file uploads
- Signed URL generation
- File deletion and management
- Bucket operations

#### PDF Service (`services/pdf/`)

- Report generation
- Answer sheet creation
- Statistics visualization
- Batch PDF creation

### Background Processing

#### Celery Worker

- **Async task execution** for long-running operations
- **Task retries** with exponential backoff
- **Task scheduling** for periodic jobs
- **Failure handling** and dead-letter queues

**Task Types:**

- PDF generation
- Email notifications
- Bulk data processing
- Analytics calculation

## Data Flow

### Exam Generation Flow

```
1. User submits exam request (Topic, Questions, Difficulty)
                ↓
2. Frontend → API /exams/generate (POST)
                ↓
3. API validates request (Pydantic schema)
                ↓
4. Create exam record in PostgreSQL (status: pending)
                ↓
5. Queue Celery task for AI generation
                ↓
6. Return exam ID to frontend (Polling begins)
                ↓
7. Celery Worker receives task
                ↓
8. Celery → OpenAI API (Generate questions)
                ↓
9. Process and store questions in PostgreSQL
                ↓
10. Update exam status to 'ready'
                ↓
11. Cache exam data in Redis
                ↓
12. Frontend detects status change, loads exam
```

### Exam Attempt Flow

```
1. User clicks "Start Exam"
                ↓
2. Frontend → API /attempts (POST)
                ↓
3. API creates attempt record (status: in_progress)
                ↓
4. Frontend loads questions from cache/API
                ↓
5. User answers questions (stored in session/state)
                ↓
6. User submits answers → API /attempts/{id}/submit
                ↓
7. API validates and stores answers in PostgreSQL
                ↓
8. Celery task: Calculate statistics and analytics
                ↓
9. API returns results (Score, breakdown, explanation)
                ↓
10. Frontend displays results page
                ↓
11. Optional: Generate PDF report (Async Celery task)
```

## API Design

### REST Endpoints Structure

```
/auth/              -- Authentication
  POST /register              (User registration)
  POST /login                 (User login)
  POST /refresh               (Token refresh)
  POST /logout                (User logout)

/users/{id}         -- User management
  GET    /                    (Get profile)
  PUT    /                    (Update profile)

/exams              -- Exam management
  GET    /                    (List exams)
  POST   /                    (Create exam)
  GET    /{id}                (Get exam details)
  POST   /{id}/generate       (Generate with AI)
  DELETE /{id}                (Delete exam)

/questions/{id}     -- Question management
  GET    /                    (List questions)
  GET    /{id}                (Get question details)
  GET    /{id}/explanation    (Get explanation)

/attempts           -- Exam attempts
  GET    /                    (List user's attempts)
  POST   /                    (Start new attempt)
  GET    /{id}                (Get attempt details)
  POST   /{id}/answer         (Submit answer)
  POST   /{id}/submit         (Complete attempt)

/analytics          -- Analytics & statistics
  GET    /exams/{id}          (Exam statistics)
  GET    /questions/{id}      (Question statistics)
```

## Authentication & Authorization

### JWT Authentication Flow

```
1. User POST /auth/login {email, password}
                ↓
2. API validates credentials
                ↓
3. API generates JWT token (header.payload.signature)
                ↓
4. Frontend stores token (localStorage/sessionStorage)
                ↓
5. Subsequent requests include Authorization header
                ↓
6. API validates token signature
                ↓
7. Extract user info from token claims
                ↓
8. Verify token expiration
                ↓
9. Grant/deny access based on user permissions
```

### Token Structure

```javascript
{
  "sub": "user_id",
  "email": "user@example.com",
  "exp": 1234567890,
  "iat": 1234567200,
  "type": "access"  // or "refresh"
}
```

## Deployment Architecture

### Development Environment

```
Docker Host Machine
├── Container: postgres:16
├── Container: redis:7-alpine
├── Container: minio (S3-compatible)
├── Container: fastapi (uvicorn)
├── Container: celery-worker
├── Container: frontend (Vite dev)
└── Container: nginx (reverse proxy)
```

### Production Environment

```
Nginx (SSL/TLS, Rate Limiting, Caching)
    ├── API Service (Multiple replicas)
    │   ├── FastAPI instances (load balanced)
    │   └── SQLAlchemy connection pool
    │
    ├── Celery Workers (Distributed task processing)
    │
    └── Static Files (React build)

PostgreSQL (Primary datastore)
Redis (Cache & task queue)
MinIO/S3 (File storage)
```

## Scalability Considerations

### Horizontal Scaling

- **API Service:** Multiple FastAPI instances behind load balancer
- **Celery Workers:** Scale workers based on task queue depth
- **Database:** Connection pooling for efficient resource usage
- **Redis:** Cluster mode for high availability

### Performance Optimization

```python
# Caching strategies
- Cache exam data (30 min TTL)
- Cache user sessions (1 hour TTL)
- Cache frequently accessed questions
- Invalidate on updates

# Database optimization
- Connection pooling (SQLAlchemy)
- Query optimization with indexes
- Read replicas for analytics queries
- Batch operations for bulk updates

# Frontend optimization
- Code splitting with Vite
- Lazy-load routes
- Image optimization
- Gzip compression (nginx)
```

## Security Architecture

```
User Request
    ↓
Nginx SSL/TLS → Decrypt HTTPS
    ↓
Rate Limiting (prevents brute force)
    ↓
Input Validation (Pydantic schemas)
    ↓
JWT Authentication (verify token)
    ↓
Authorization Checks (user permissions)
    ↓
SQL Injection Prevention (SQLAlchemy ORM)
    ↓
CORS Headers (origin validation)
    ↓
Secure Response (no sensitive data leaks)
```

## Monitoring & Observability

### Logging

- Nginx access/error logs
- FastAPI application logs
- Celery task logs
- Database query logs (slow query log)

### Metrics

- Request latency (API endpoints)
- Error rate (5xx, 4xx by endpoint)
- Queue depth (Celery tasks)
- Cache hit ratio (Redis)
- Database connection pool usage

### Health Checks

```
GET /health → 200 OK
GET /readiness → 200 (checks: DB, Redis, MinIO)
GET /live → 200 (container orchestration)
```

## Disaster Recovery

### Backup Strategy

- **Database:** Daily backups to S3/MinIO
- **Files:** Versioning enabled in MinIO
- **Configuration:** Infrastructure as Code (docker-compose)

### Recovery Procedures

1. Spin up fresh containers
2. Restore database from backup
3. Restore files from MinIO
4. Run migrations to latest version
5. Verify health checks pass

## Technology Decisions

| Component     | Choice       | Reason                        |
| ------------- | ------------ | ----------------------------- |
| Backend       | FastAPI      | Modern, fast, auto-docs       |
| Frontend      | React + Vite | Hot reload, ecosystem         |
| Database      | PostgreSQL   | Reliable, feature-rich RDBMS  |
| Cache         | Redis        | In-memory, atomic ops         |
| Task Queue    | Celery       | Distributed, Django ecosystem |
| Storage       | MinIO        | S3-compatible, self-hosted    |
| Container     | Docker       | Reproducible environments     |
| Reverse Proxy | Nginx        | Performance, flexibility      |
| Auth          | JWT          | Stateless, scalable           |

## Future Improvements

- [ ] WebSocket support for real-time notifications
- [ ] GraphQL API for optimized queries
- [ ] Kubernetes deployment
- [ ] Multi-region database replication
- [ ] Advanced analytics dashboard
- [ ] Role-based access control (RBAC)
- [ ] Audit logging
- [ ] API rate limiting per user
