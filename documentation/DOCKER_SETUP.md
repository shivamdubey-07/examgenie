# Docker Setup Guide

## Overview

Docker containerizes all services for consistent development and production environments. This guide explains the container structure and how to manage them.

## Docker Compose Files

### Development (`docker-compose.yml`)

Used for local development with source code mounted for hot reload.

### Production (`docker-compose.prod.yml`)

Used for production with optimized images, health checks, and scaling.

## Services Overview

```
examgenie/
├── api              (FastAPI + Uvicorn)
├── worker           (Celery background tasks)
├── db               (PostgreSQL)
├── redis            (Redis cache/queue)
├── minio            (S3-compatible storage)
├── minio-init       (MinIO bucket setup)
├── frontend         (React + Vite dev server)
└── nginx            (Reverse proxy)
```

## Building Images

### Development Build

```bash
# Automatic on docker-compose up
docker-compose up -d

# Force rebuild
docker-compose up -d --build
```

### Production Build

```bash
# Build production image
docker build -t examgenie:latest .

# Build with custom tag
docker build -t examgenie:v1.0 .

# List built images
docker images | grep examgenie
```

## Container Management

### Start Services

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Build and start
docker-compose up -d --build
```

### Stop Services

```bash
# Development
docker-compose down

# Production
docker-compose -f docker-compose.prod.yml down

# Remove volumes (WARNING: deletes data!)
docker-compose down -v
```

### View Status

```bash
# List containers
docker-compose ps

# List all containers (including stopped)
docker-compose ps -a

# Inspect specific container
docker inspect examgenie_api
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100 api

# Timestamps included
docker-compose logs -f --timestamps api
```

## Container Access

### Execute Commands in Container

```bash
# Shell access
docker-compose exec api bash
docker-compose exec db bash

# Run single command
docker-compose exec api python -c "import app; print('OK')"

# Run as different user
docker-compose exec -u root api apt-get update
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U examgenie_user -d examgenie

# Run SQL query
docker-compose exec db psql -U examgenie_user -d examgenie -c "SELECT * FROM users;"

# Backup database
docker-compose exec db pg_dump -U examgenie_user examgenie > backup.sql

# Restore database
docker-compose exec -T db psql -U examgenie_user examgenie < backup.sql
```

### Cache Access

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Get value
GET exam:1

# Set value
SET exam:1 '{"id": 1}'

# Clear cache
FLUSHALL

# Monitor commands (in real-time)
MONITOR
```

### MinIO Access

MinIO Web Console:

- URL: http://localhost:9001
- Username: minioadmin
- Password: minioadmin

```bash
# MinIO CLI (via container)
docker-compose exec minio mc alias set myminio http://localhost:9000 minioadmin minioadmin

# List buckets
docker-compose exec minio mc ls myminio

# List files in bucket
docker-compose exec minio mc ls myminio/examgenie
```

## Volumes and Data Persistence

### Named Volumes

```yaml
volumes:
  examgenie_db: # PostgreSQL data
  examgenie_redis: # Redis data
  examgenie_minio: # MinIO files
  examgenie_frontend_node: # npm node_modules (dev)
```

### View Volume Information

```bash
# List volumes
docker volume ls | grep examgenie

# Inspect volume
docker volume inspect examgenie_examgenie_db

# View volume location
docker volume inspect examgenie_examgenie_db | grep Mountpoint
```

### Backup Data

```bash
# Backup PostgreSQL database
docker-compose exec db pg_dump -U examgenie_user examgenie > backup_$(date +%Y%m%d).sql

# Backup MinIO files (create tar of volume)
docker run --rm -v examgenie_examgenie_minio:/data -v $(pwd):/backup \
  alpine tar czf /backup/minio_backup.tar.gz /data

# Backup Redis data
docker run --rm -v examgenie_examgenie_redis:/data -v $(pwd):/backup \
  alpine tar czf /backup/redis_backup.tar.gz /data
```

## Network Configuration

### Default Network

Docker Compose creates a default network called `examgenie_default` that allows containers to communicate by service name.

### Service Discovery

```bash
# From inside a container
ping db        # Resolves to PostgreSQL container
ping redis     # Resolves to Redis container
ping api       # Resolves to FastAPI container
```

### Ports

**Development Ports:**

```
80    → Nginx (proxies to frontend)
8000  → FastAPI API (exposed when visiting localhost:8000)
5173  → Vite dev server (if accessed directly)
9001  → MinIO console
```

**Production Ports:**

```
80    → HTTP (redirects to HTTPS)
443   → HTTPS (with SSL certificate)
9001  → MinIO console (internal only)
```

## Environment Variables

### Load from .env file

```bash
# docker-compose automatically loads .env
docker-compose up -d

# Use different env file
docker-compose --env-file .env.prod up -d
```

### Override at Runtime

```bash
# Set variable on command line
POSTGRES_PASSWORD=newpass docker-compose up -d

# Multiple variables
POSTGRES_PASSWORD=newpass REDIS_PASSWORD=newpass docker-compose up -d
```

### View Container Environment

```bash
# View all environment variables
docker-compose exec api env

# Filter specific variables
docker-compose exec api env | grep REDIS
docker-compose exec api env | grep DATABASE
```

## Resource Management

### CPU & Memory Limits

```yaml
# Defined in docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: "1"
      memory: 1G
    reservations:
      cpus: "0.5"
      memory: 512M
```

### View Resource Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats examgenie_api

# Historical stats
docker inspect --format='{{.State}}' examgenie_api
```

### Increase Service Resources

Edit `docker-compose.yml` or `docker-compose.prod.yml`:

```yaml
  api:
    ...
    deploy:
      resources:
        limits:
          cpus: "2"           # Increase from 1
          memory: 2G          # Increase from 1G
```

Then restart:

```bash
docker-compose down
docker-compose up -d
```

## Health Checks

### Check Service Health

```bash
# API health
curl http://localhost:8000/health

# Database
docker-compose exec db pg_isready -U examgenie_user

# Redis
docker-compose exec redis redis-cli ping

# Worker
docker exec examgenie_worker celery -A app.worker.celery_app inspect active
```

### View Health Status

```bash
# Check health from docker-compose output
docker-compose ps

# The STATUS column shows health status
# Example: "Up 2 minutes (healthy)"
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs for error
docker-compose logs api

# Check if port is already in use
lsof -i :80
lsof -i :8000

# Try rebuilding
docker-compose down
docker-compose up --build -d
```

### Out of Disk Space

```bash
# Remove unused containers, images, volumes
docker system prune -a

# Remove unused volumes specifically
docker volume prune

# Check disk usage
docker system df
```

### Container Keeps Restarting

```bash
# Check restart policy
docker inspect examgenie_api | grep -A 5 RestartPolicy

# View logs for errors
docker logs examgenie_api

# Access container bash before it exits
docker run -it --entrypoint bash IMAGE_ID
```

### Network Issues

```bash
# Test container-to-container connectivity
docker exec examgenie_api ping db

# Test port accessibility
docker exec examgenie_api nc -zv redis 6379

# View network details
docker network inspect examgenie_default
```

## Development Workflows

### Hot Reload Development

**Code Changes Auto-reload:**

- Backend: FastAPI auto-reloads on file change
- Frontend: Vite hot module reload (HMR)
- No container restart needed!

```bash
# Just edit files and save
nano app/main.py  # Changes apply immediately
```

### Testing in Container

```bash
# Run tests in API container
docker-compose exec api pytest

# Run tests with coverage
docker-compose exec api pytest --cov=app

# Run specific test
docker-compose exec api pytest tests/test_auth.py::test_login
```

### Debugging in Container

```bash
# Insert breakpoint in code
import pdb; pdb.set_trace()

# Run with interactive terminal
docker-compose run --rm api python app/main.py

# Attach debugger
docker attach examgenie_api
```

## Production Considerations

### Multi-Replica API

```yaml
  api:
    ...
    deploy:
      replicas: 2  # Run 2 API instances
```

### Zero-Downtime Deployment

```yaml
  api:
    ...
    deploy:
      update_config:
        parallelism: 1      # Update one at a time
        delay: 10s          # Wait between updates
      restart_policy:
        condition: on-failure
        max_attempts: 3     # Retry if fails
```

### Logging Strategy

```yaml
  api:
    ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"     # Rotate after 10MB
        max-file: "3"       # Keep 3 old files
        labels: "service=api"
```

## Docker Compose Commands Reference

```bash
# Lifecycle
docker-compose up -d                    # Start
docker-compose down                     # Stop
docker-compose restart                  # Restart all
docker-compose restart api              # Restart specific

# Building
docker-compose build                    # Build images
docker-compose up -d --build            # Build and start

# Logs
docker-compose logs -f                  # Follow all logs
docker-compose logs -f api --tail=100   # Last 100 lines

# Execution
docker-compose exec api bash            # Run bash
docker-compose run --rm api pytest      # Run command, remove after

# Status
docker-compose ps                       # List containers
docker-compose exec api env             # View environment
docker-compose stats                    # Resource usage
```

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for docker-specific issues.
