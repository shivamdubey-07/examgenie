# ExamGenie Documentation

Welcome to the ExamGenie project documentation. This folder contains comprehensive guides for development, deployment, and maintenance.

## Quick Navigation

### Getting Started

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System overview and component architecture
- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - Quick start for local development

### Setup & Configuration

- [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Docker and docker-compose configuration
- [ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md) - Environment variables and secrets
- [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md) - Database schema and Alembic migrations

### Development

- [API_INTEGRATION.md](./API_INTEGRATION.md) - Backend API structure and endpoints
- [FRONTEND_SETUP.md](./FRONTEND_SETUP.md) - Frontend development and build process

### Deployment & Operations

- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Production deployment procedures
- [MONITORING_MAINTENANCE.md](./MONITORING_MAINTENANCE.md) - Monitoring, logging, and maintenance
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues and solutions

## Project Structure

```
examgenie/              (Backend - FastAPI)
├── app/
│   ├── main.py        (FastAPI application)
│   ├── auth/          (Authentication & JWT)
│   ├── models/        (SQLAlchemy models)
│   ├── routes/        (API endpoints)
│   ├── schemas/       (Pydantic schemas)
│   ├── services/      (Business logic)
│   │   ├── ai/        (OpenAI integration)
│   │   ├── cache/     (Redis caching)
│   │   ├── pdf/       (PDF generation)
│   │   └── storage/   (S3/MinIO storage)
│   └── worker/        (Celery tasks)
├── alembic/           (Database migrations)
├── docker-compose.yml (Development)
├── docker-compose.prod.yml (Production)
└── Dockerfile

examgenie_frontend/    (Frontend - React + Vite)
├── src/
│   ├── pages/         (React pages)
│   ├── services/      (API clients)
│   └── assets/        (Static assets)
├── Dockerfile         (Dev server)
└── package.json
```

## Technology Stack

### Backend

- **Framework:** FastAPI (Python 3.12)
- **Database:** PostgreSQL 16
- **Cache:** Redis 7
- **Storage:** MinIO (S3-compatible)
- **Task Queue:** Celery
- **ORM:** SQLAlchemy 2.0

### Frontend

- **Framework:** React 19
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **Router:** React Router v7

### DevOps

- **Containerization:** Docker
- **Orchestration:** Docker Compose
- **Reverse Proxy:** Nginx
- **SSL/TLS:** Let's Encrypt (production)

## Key Features

- ✅ AI-powered exam generation (OpenAI integration)
- ✅ Exam attempt tracking with analytics
- ✅ PDF export functionality
- ✅ S3/MinIO file storage
- ✅ JWT authentication
- ✅ Async task processing (Celery)
- ✅ Redis caching layer
- ✅ Database migrations (Alembic)

## Development Workflow

### 1. Setup Development Environment

```bash
cd examgenie
docker-compose up -d
# Access: http://localhost
```

### 2. Make Changes

- Backend: `app/` folder (FastAPI reloads automatically)
- Frontend: `examgenie_frontend/src/` (Vite HMR enabled)

### 3. Database Migrations

```bash
docker exec examgenie_api alembic revision --autogenerate -m "Description"
docker exec examgenie_api alembic upgrade head
```

### 4. Test & Deploy

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

## Common Commands

### Docker Compose (Development)

```bash
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose logs -f api    # View API logs
docker-compose exec api bash  # Access API container
```

### Docker Compose (Production)

```bash
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
```

### Database

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Backup database
docker-compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql

# Restore database
docker-compose exec -T db psql -U $POSTGRES_USER $POSTGRES_DB < backup.sql
```

### Celery Worker

```bash
# View active tasks
docker exec examgenie_worker celery -A app.worker.celery_app inspect active

# Monitor tasks
docker exec examgenie_worker celery -A app.worker.celery_app events
```

## Environment

### Development (.env)

```env
DEBUG=true
ENVIRONMENT=development
POSTGRES_USER=examgenie_user
POSTGRES_PASSWORD=dev_password
REDIS_PASSWORD=redis_password
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minio_password
SECRET_KEY=dev_secret_key
```

### Production (.env.prod)

See [ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md)

## Contributing

1. Create a feature branch
2. Make changes and test locally
3. Create database migrations if needed
4. Submit pull request

See [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) for detailed workflow.

## Support

- **Issues:** Report in GitHub Issues
- **Questions:** Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Documentation:** Refer to specific guides above

## License

[Insert your license here]

## Last Updated

March 18, 2026
