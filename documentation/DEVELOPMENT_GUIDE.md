# Development Guide

## Prerequisites

- Docker & Docker Compose installed
- Git for version control
- IDE: VS Code recommended

## Quick Start (5 minutes)

### 1. Clone and Navigate

```bash
cd /home/noel2105/Desktop/Projects/Exam\ Genie/examgenie
```

### 2. Start Development Environment

```bash
docker-compose up -d
```

### 3. Access Services

- Frontend: http://localhost (or http://localhost:5173)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001
  - Login: minioadmin / minioadmin

### 4. Stop Environment

```bash
docker-compose down
```

## Development Setup

### Environment Variables

Copy `.env.example` to `.env` with dev values:

```bash
cp .env.example .env
```

Required variables for development:

```env
# Database
POSTGRES_USER=examgenie_user
POSTGRES_PASSWORD=dev_password
POSTGRES_DB=examgenie
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_PASSWORD=redis_password

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
S3_BUCKET=examgenie

# Application
SECRET_KEY=dev_secret_key_at_least_32_chars
DEBUG=true
ENVIRONMENT=development

# OpenAI (optional for testing)
OPENAI_API_KEY=sk-...
```

### Initial Setup

```bash
# Start services
docker-compose up -d

# Check services are running
docker-compose ps

# Verify database migrations ran
docker logs examgenie_api | grep "running existing migrations"

# View logs
docker-compose logs -f
```

## Project Structure for Development

```
examgenie/
├── app/
│   ├── main.py              ← Start here (FastAPI app)
│   ├── routes/              ← Add new endpoints
│   │   └── exams.py         ← Exam endpoints
│   ├── models/              ← Database models
│   │   └── exam.py          ← Exam model
│   ├── schemas/             ← Request/response validation
│   │   └── models.py        ← Pydantic schemas
│   ├── services/            ← Business logic
│   │   ├── ai/              ← OpenAI integration
│   │   ├── cache/           ← Redis operations
│   │   └── storage/         ← MinIO/S3 operations
│   ├── auth/                ← Authentication
│   └── worker/              ← Celery async tasks
│
├── alembic/                 ← Database migrations
│   └── versions/            ← Migration scripts
│
├── tests/                   ← Unit & integration tests
├── Dockerfile               ← Container definition
├── docker-compose.yml       ← Dev services
├── requirements.txt         ← Python dependencies
└── app/start.sh             ← Entry script
```

## Backend Development Workflow

### 1. Make Changes to FastAPI Code

All changes to `app/` folder are automatically reloaded:

```bash
# Edit app/routes/exams.py
nano app/routes/exams.py
```

Changes appear immediately - no restart needed!

### 2. Test API Changes

#### Using Interactive API Docs

```
http://localhost:8000/docs          ← Swagger UI (Try it out!)
http://localhost:8000/redoc         ← ReDoc
```

#### Using curl

```bash
curl http://localhost:8000/health

curl -X GET http://localhost:8000/api/exams \
  -H "Authorization: Bearer YOUR_TOKEN"

curl -X POST http://localhost:8000/api/exams \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python", "num_questions": 5}'
```

#### Using Python

```python
import requests

response = requests.get('http://localhost:8000/api/exams')
print(response.json())
```

### 3. Database Changes

#### Check Database Schema

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U examgenie_user -d examgenie

# List tables
\dt

# View table schema
\d exams

# Exit
\q
```

#### Create Database Migration

```bash
# After modifying models/
docker exec examgenie_api alembic revision --autogenerate -m "Add new field to exams"

# This creates: alembic/versions/001_add_new_field_to_exams.py

# Review the migration file
nano alembic/versions/001_add_new_field_to_exams.py

# Apply migration
docker exec examgenie_api alembic upgrade head

# View migration history
docker exec examgenie_api alembic history
```

#### Example: Add New Column to Exam Table

1. **Update Model** (`app/models/exam.py`):

```python
from sqlalchemy import Column, String, DateTime
from datetime import datetime

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    # New column
    difficulty_level = Column(String, default="intermediate")
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. **Create Migration**:

```bash
docker exec examgenie_api alembic revision --autogenerate -m "Add difficulty_level to exams"
```

3. **Apply Migration**:

```bash
docker exec examgenie_api alembic upgrade head
```

4. **Update Schema** (`app/schemas/models.py`):

```python
from pydantic import BaseModel

class ExamCreate(BaseModel):
    title: str
    difficulty_level: str = "intermediate"

class ExamResponse(BaseModel):
    id: int
    title: str
    difficulty_level: str
```

5. **Update Routes** (`app/routes/exams.py`):

```python
@router.post("/exams")
async def create_exam(exam: ExamCreate, db: Session = Depends(get_db)):
    new_exam = Exam(**exam.dict())
    db.add(new_exam)
    db.commit()
    return new_exam
```

### 4. Working with Celery Tasks

#### View Active Tasks

```bash
docker exec examgenie_worker celery -A app.worker.celery_app inspect active
```

#### View Task Results

```bash
docker exec examgenie_worker celery -A app.worker.celery_app inspect result
```

#### Manually Trigger Task

```python
# From Python shell
from app.worker.celery_app import app
from app.worker.tasks import generate_questions_task

task = generate_questions_task.delay(exam_id=1)
print(task.id)
print(task.status)
print(task.result)
```

## Frontend Development Workflow

### 1. Make Changes to React Code

All changes to `examgenie_frontend/src/` are hot-reloaded:

```bash
# Edit page
nano examgenie_frontend/src/pages/Dashboard.jsx

# Changes appear immediately in browser!
```

### 2. API Integration Example

**Create API Client** (`examgenie_frontend/src/services/api.js`):

```javascript
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost/api",
  withCredentials: true,
});

export const getExams = () => api.get("/exams");
export const createExam = (data) => api.post("/exams", data);
export default api;
```

**Use in Component**:

```javascript
import { useEffect, useState } from "react";
import { getExams } from "../services/api";

export default function Dashboard() {
  const [exams, setExams] = useState([]);

  useEffect(() => {
    getExams()
      .then((res) => setExams(res.data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div>
      {exams.map((exam) => (
        <h2 key={exam.id}>{exam.title}</h2>
      ))}
    </div>
  );
}
```

### 3. Build Frontend for Testing

```bash
cd examgenie_frontend

# Development server (hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### 4. Debug in Browser

```bash
# Open DevTools F12 in browser

# Check Network tab for API calls
# Check Console for errors
# Use React DevTools extension (Chrome/Firefox)
```

## Testing

### Backend Unit Tests

```bash
# Run pytest
docker exec examgenie_api pytest

# Run specific test file
docker exec examgenie_api pytest tests/test_auth.py

# Run with verbose output
docker exec examgenie_api pytest -v

# Run with coverage
docker exec examgenie_api pytest --cov=app
```

### Manual Testing Checklist

- [ ] Database migrations run without errors
- [ ] API docs load at `/docs`
- [ ] Health check passes: `GET /health`
- [ ] User registration works
- [ ] User login returns valid JWT token
- [ ] Protected endpoints reject requests without token
- [ ] Exam generation queues task in Celery
- [ ] Attempt submission stores answers
- [ ] PDF export generates file

## Common Development Tasks

### Add New API Endpoint

1. **Create route** (`app/routes/new_feature.py`):

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.get("/")
async def list_items(db: Session = Depends(get_db)):
    return {"items": []}

@router.post("/")
async def create_item(data: dict, db: Session = Depends(get_db)):
    return {"created": True}
```

2. **Register route** (`app/main.py`):

```python
from app.routes import new_feature

app.include_router(new_feature.router)
```

3. **Test in Swagger UI**: http://localhost:8000/docs

### Add New Model

1. **Create model** (`app/models/new_model.py`):

```python
from sqlalchemy import Column, Integer, String
from app.database import Base

class NewModel(Base):
    __tablename__ = "new_models"
    id = Column(Integer, primary_key=True)
    name = Column(String)
```

2. **Create migration**:

```bash
docker exec examgenie_api alembic revision --autogenerate -m "Add NewModel"
docker exec examgenie_api alembic upgrade head
```

3. **Create schema** (`app/schemas/models.py`):

```python
class NewModelResponse(BaseModel):
    id: int
    name: str
```

### Debug API Request

```bash
# View request/response in logs
docker-compose logs api | grep "POST /api/exams"

# Enable SQL logging (add to app/main.py for debugging)
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Cache Data for Testing

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Set test value
SET exam:1 "{\"id\": 1, \"title\": \"Test Exam\"}"

# Get value
GET exam:1

# Clear all
FLUSHALL
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs api

# Restart services
docker-compose down
docker-compose up -d
```

### Database Connection Error

```bash
# Test database connection
docker-compose exec db psql -U examgenie_user -d examgenie -c "SELECT 1"

# Check environment variables
docker-compose exec api env | grep POSTGRES
```

### API Not Responding

```bash
# Check if container is running
docker-compose ps api

# View API logs
docker-compose logs api

# Check port is listening
docker-compose exec api netstat -an | grep 8000
```

### Migrations Failed

```bash
# View current migration version
docker exec examgenie_api alembic current

# View migration history
docker exec examgenie_api alembic history

# Downgrade one version (if needed)
docker exec examgenie_api alembic downgrade -1

# Re-apply migrations
docker exec examgenie_api alembic upgrade head
```

## Performance Tips

1. **Use connection pooling** - SQLAlchemy handles this
2. **Cache frequently accessed data** - Use Redis with TTL
3. **Optimize database queries** - Use `select()` instead of `query()`
4. **Async operations** - Use Celery for long-running tasks
5. **Monitor logs** - Check for slow queries and errors
6. **Profile code** - Use Python profilers to identify bottlenecks

## Code Style

- **Backend**: Follow PEP 8, use Black for formatting
- **Frontend**: Use ESLint config provided in project
- **Commit messages**: Use conventional commits

Example:

```
feat: add exam generation endpoint
fix: correct answer validation logic
docs: update API documentation
style: format code with black
test: add unit tests for auth
```

## Getting Help

1. Check logs: `docker-compose logs`
2. Review documentation in `documentation/` folder
3. Check API docs: http://localhost:8000/docs
4. Review existing code patterns
5. Ask team members or create issue

## Next Steps

- Read [DOCKER_SETUP.md](./DOCKER_SETUP.md) for Docker details
- Read [API_INTEGRATION.md](./API_INTEGRATION.md) for API structure
- Read [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md) for migrations
