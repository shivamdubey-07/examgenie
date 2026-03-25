# ExamGenie Documentation

Complete guides for developing and deploying ExamGenie.

## Quick Start

New to the project?

1. **[DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)** - Get running in 5 minutes
2. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Understand the system design

## Development

### Frontend Development

- [FRONTEND_SETUP.md](./FRONTEND_SETUP.md) - React + Vite setup and development workflow
- **Note:** Frontend also lives in `examgenie_frontend/` with its own README

### Backend Development

- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - Local setup and debugging
- [API_INTEGRATION.md](./API_INTEGRATION.md) - API endpoints and authentication
- [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md) - Managing database schema changes

## Deployment & Operations

### Getting Ready for Production

1. [ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md) - Configure environment variables
2. [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Docker and docker-compose reference
3. [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Deploy to production

### Running in Production

- [MONITORING_MAINTENANCE.md](./MONITORING_MAINTENANCE.md) - Health checks, logs, and routine maintenance
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues and solutions

## Architecture Overview

**Frontend:** React 19 + Vite + Tailwind CSS

**Backend:** FastAPI + SQLAlchemy + PostgreSQL

**Infrastructure:** Docker Compose + Nginx + Redis + MinIO

**AI:** OpenAI integration for exam generation

**Async:** Celery for background tasks

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

## Technologies

| Component         | Tech                                       |
| ----------------- | ------------------------------------------ |
| **Frontend**      | React 19, Vite, React Router, Tailwind CSS |
| **Backend**       | FastAPI, SQLAlchemy 2.0, Pydantic          |
| **Database**      | PostgreSQL 16                              |
| **Cache**         | Redis 7                                    |
| **Storage**       | MinIO (S3-compatible)                      |
| **Queue**         | Celery + Redis                             |
| **Reverse Proxy** | Nginx                                      |
| **Containers**    | Docker, Docker Compose                     |
| **AI**            | OpenAI API                                 |

## Project Structure

```
Exam Genie/
├── examgenie/                  (Backend - FastAPI)
│   ├── app/
│   │   ├── main.py            (FastAPI app entry point)
│   │   ├── auth/              (JWT authentication)
│   │   ├── models/            (SQLAlchemy ORM models)
│   │   ├── routes/            (API endpoints)
│   │   ├── schemas/           (Pydantic request/response)
│   │   ├── services/          (Business logic)
│   │   │   ├── ai/            (OpenAI integration)
│   │   │   ├── auth/          (Auth service)
│   │   │   ├── cache/         (Redis caching)
│   │   │   ├── pdf/           (PDF generation)
│   │   │   └── storage/       (S3/MinIO)
│   │   ├── database/          (SQLAlchemy session)
│   │   ├── worker/            (Celery tasks)
│   │   └── common/            (Enums, config)
│   ├── alembic/               (Database migrations)
│   ├── docker-compose.yml     (Dev environment)
│   ├── docker-compose.prod.yml (Prod environment)
│   ├── Dockerfile             (API container)
│   ├── nginx.conf             (Dev reverse proxy)
│   └── nginx.prod.conf        (Prod reverse proxy)
│
├── examgenie_frontend/         (Frontend - React + Vite)
│   ├── src/
│   │   ├── pages/             (Page components)
│   │   ├── components/        (Reusable components)
│   │   ├── contexts/          (React Context)
│   │   ├── hooks/             (Custom hooks)
│   │   ├── services/          (API client)
│   │   └── assets/            (Images, fonts)
│   ├── Dockerfile             (Frontend dev server)
│   ├── vite.config.js         (Vite configuration)
│   └── package.json           (Dependencies)
│
└── documentation/             (These guides)
```

## Common Tasks

### Start Development

```bash
cd examgenie
docker-compose up -d

# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Create Database Migration

```bash
docker-compose exec api alembic revision --autogenerate -m "Description of change"
docker-compose exec api alembic upgrade head
```

### Review API Endpoints

Visit [http://localhost:8000/docs](http://localhost:8000/docs) when running locally.

Or see [API_INTEGRATION.md](./API_INTEGRATION.md) for detailed endpoint documentation.

### Deploy to Production

Follow [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for step-by-step instructions.

### Troubleshoot Issues

Start with [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common problems and solutions.

## Support

For issues or questions:

1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) first
2. Review relevant doc in this folder
3. Check application logs: `docker-compose logs -f`
   cd examgenie
   docker-compose up -d

# Access: http://localhost

````

### 2. Make Changes

- Backend: `app/` folder (FastAPI reloads automatically)
- Frontend: `examgenie_frontend/src/` (Vite HMR enabled)

### 3. Database Migrations

```bash
docker exec examgenie_api alembic revision --autogenerate -m "Description"
docker exec examgenie_api alembic upgrade head
````

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
