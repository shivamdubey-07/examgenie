# Troubleshooting Guide

Common issues and solutions for ExamGenie development and deployment.

## Docker & Container Issues

### Services won't start

**Problem:** `docker-compose up -d` fails or services crash immediately

**Solutions:**

```bash
# 1. Check logs for errors
docker-compose logs

# 2. Check specific service
docker-compose logs api

# 3. Check if ports are already in use
lsof -i :80
lsof -i :8000
lsof -i :5432

# 4. Clean and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Out of memory

**Problem:** Services crash with "OOMKilled" status

**Solutions:**

```bash
# Check resource limits
docker stats

# Increase Docker memory allocation
# (Docker Desktop settings or docker daemon config)

# Reduce concurrency in compose file
# Change api.deploy.resources.limits.memory to 2G
```

### Port already in use

**Problem:** `Error: bind: address already in use`

**Solutions:**

```bash
# Find process using port
lsof -i :8000

# Kill the process
kill PID

# Or use different port
docker-compose down
# Edit docker-compose.yml ports: [8001:8000]
docker-compose up -d
```

## Database Issues

### Can't connect to database

**Problem:** `psycopg2.OperationalError: could not connect to server: Connection refused`

**Solutions:**

```bash
# Check if database container is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify database is ready
docker-compose exec db pg_isready -U examgenie_user

# Check environment variables
docker-compose exec api env | grep POSTGRES
```

### Migrations fail

**Problem:** `alembic upgrade head` fails with error

**Solutions:**

```bash
# Check current migration
docker-compose exec api alembic current

# View migration history
docker-compose exec api alembic history

# Try reverting one step
docker-compose exec api alembic downgrade -1

# Check database directly
docker-compose exec db psql -U examgenie_user -d examgenie -c "SELECT * FROM alembic_version;"
```

### Database locked

**Problem:** `database is locked` error

**Solutions:**

```bash
# Check active connections
docker-compose exec db psql -U examgenie_user -d examgenie -c "SELECT * FROM pg_stat_activity;"

# Kill blocking query
docker-compose exec db psql -U examgenie_user -d examgenie -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid();"
```

## Backend API Issues

### API not responding

**Problem:** `curl: (7) Failed to connect to localhost port 8000`

**Solutions:**

```bash
# Check if container is running
docker-compose ps api

# Check API logs
docker-compose logs api

# Check if port is listening
docker-compose exec api netstat -an | grep 8000

# Try accessing directly
docker-compose exec api curl http://localhost:8000/health
```

### "ModuleNotFoundError" on startup

**Problem:** `ModuleNotFoundError: No module named 'app'`

**Solutions:**

```bash
# Rebuild Docker image
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check requirements.txt is valid
docker-compose exec api pip list | grep fastapi

# Verify PYTHONPATH
docker-compose exec api echo $PYTHONPATH
```

### Health check fails

**Problem:** Container marks as unhealthy

**Solutions:**

```bash
# Check health directly
docker-compose exec api curl http://localhost:8000/health

# View healthcheck logs
docker inspect examgenie_api | grep -A 5 Health

# Check required services are up
docker-compose exec api curl http://db:5432
docker-compose exec api redis-cli ping
```

## Frontend Issues

### Frontend not loading

**Problem:** Blank page or 404 at http://localhost

**Solutions:**

```bash
# Check frontend container is running
docker-compose ps frontend

# Check frontend logs
docker-compose logs frontend

# Access Vite dev server directly
curl http://localhost:5173

# Check nginx is proxying correctly
docker-compose logs nginx
```

### Hot reload not working

**Problem:** Changes to React code don't appear in browser

**Solutions:**

```bash
# Check Vite is running
docker-compose logs frontend

# Verify WebSocket connection in browser Network tab
# Look for /ws or upgrade connections

# Restart frontend service
docker-compose restart frontend

# Clear browser cache and refresh
# Hard refresh: Ctrl+Shift+R or Cmd+Shift+R
```

### API requests fail with CORS error

**Problem:** `Access to XMLHttpRequest has been blocked by CORS policy`

**Solutions:**

```bash
# Check CORS config in .env
docker-compose exec api env | grep CORS

# Verify frontend origin matches CORS_ORIGINS
# CORS_ORIGINS should include your frontend URL

# Check nginx is proxying /api correctly
docker-compose logs nginx

# Test API directly
curl http://localhost:8000/api/exams
```

## Redis Issues

### Can't connect to Redis

**Problem:** `ConnectionError: Error 111 connecting to redis:6379`

**Solutions:**

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check Redis logs
docker-compose logs redis

# Check Redis password
docker-compose exec redis redis-cli -a YOUR_PASSWORD ping
```

### Redis out of memory

**Problem:** `OOM command not allowed when used memory > 'maxmemory'`

**Solutions:**

```bash
# Check memory usage
docker-compose exec redis redis-cli INFO stats

# Clear cache
docker-compose exec redis redis-cli FLUSHALL

# Set max memory policy in docker-compose.yml
# command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

# Restart Redis
docker-compose restart redis
```

## MinIO Issues

### MinIO console not accessible

**Problem:** Can't access http://localhost:9001

**Solutions:**

```bash
# Check MinIO container is running
docker-compose ps minio

# Check MinIO logs
docker-compose logs minio

# Check password is correct
# Default: minioadmin / minioadmin

# Test MinIO CLI
docker-compose exec minio mc ls myminio
```

### Bucket not created

**Problem:** minio-init service doesn't create bucket

**Solutions:**

```bash
# Check minio-init logs
docker-compose logs minio-init

# Manually create bucket
docker-compose exec minio mc alias set myminio http://localhost:9000 minioadmin minioadmin
docker-compose exec minio mc mb myminio/examgenie

# Check if bucket exists
docker-compose exec minio mc ls myminio
```

## Celery Worker Issues

### Tasks not processing

**Problem:** Celery tasks queued but never executed

**Solutions:**

```bash
# Check worker is running
docker-compose ps worker

# Check worker logs
docker-compose logs worker

# Check active tasks
docker-compose exec worker celery -A app.worker.celery_app inspect active

# Check task queue
docker-compose exec redis redis-cli LLEN celery

# Restart worker
docker-compose restart worker
```

### Worker keeps crashing

**Problem:** Worker container restarts constantly

**Solutions:**

```bash
# Check logs for error
docker-compose logs worker

# Check task for syntax errors
docker-compose exec api python -c "from app.worker import tasks; print('OK')"

# Verify Celery config
docker-compose exec worker celery -A app.worker.celery_app inspect ping

# Reduce concurrency if memory issue
# Change docker-compose.yml: command: celery -A app.worker.celery_app worker -l info --concurrency=2
```

## Authentication Issues

### "Invalid token" error on every request

**Problem:** JWT token always rejected

**Solutions:**

```bash
# Check SECRET_KEY is same everywhere
docker-compose exec api env | grep SECRET_KEY

# Verify token format
# Should be: Authorization: Bearer ACTUAL_TOKEN

# Check token expiration
# JWT tokens have exp claim

# View token claims (decode)
docker-compose exec api python -c "
import jwt
token = 'YOUR_TOKEN'
decoded = jwt.decode(token, options={'verify_signature': False})
print(decoded)
"
```

### CORS blocked login request

**Problem:** Login works in Swagger but not from frontend

**Solutions:**

```bash
# Check CORS headers in nginx.conf
# Verify X-Forwarded-Proto is set correctly

# Check Content-Type header
# POST requests need: Content-Type: application/json

# Verify credentials format
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'
```

## Performance Issues

### API responses slow

**Problem:** Endpoint takes >5 seconds to respond

**Solutions:**

```bash
# Check slow queries
docker-compose exec db psql -U examgenie_user -d examgenie -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Enable SQL logging
# Add to app/main.py:
# import logging
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Check API logs for slow routes
docker-compose logs api | grep duration

# Optimize database queries
# Use indexes, eager loading, pagination

# Check worker queue
docker-compose exec redis redis-cli LLEN celery
```

### High memory usage

**Problem:** Docker containers using >80% available memory

**Solutions:**

```bash
# Check what's using memory
docker stats

# Clear cache
docker-compose exec redis redis-cli FLUSHALL

# Identify memory leak
docker-compose logs api | grep memory

# Reduce workers
docker-compose down
# Edit: API: api.deploy.replicas = 1, workers = 2
docker-compose up -d
```

## Nginx Issues

### "502 Bad Gateway"

**Problem:** Nginx can't reach backend

**Solutions:**

```bash
# Check backend is running
docker-compose ps api

# Check nginx can reach backend
docker-compose exec nginx ping api

# Check nginx logs
docker-compose logs nginx

# Verify nginx config
docker-compose exec nginx nginx -t

# Check upstream connection
docker-compose exec nginx curl http://api:8000/health
```

### Static files return 404

**Problem:** Images, CSS, JS return 404 in production

**Solutions:**

```bash
# Check files exist in dist/
docker-compose exec nginx ls /app/examgenie_frontend/dist

# Check nginx root is correct
# Should be: root /app/examgenie_frontend/dist;

# Check try_files config
# Should be: try_files $uri $uri/ /index.html;

# Verify permissions
docker-compose exec nginx ls -la /app/examgenie_frontend/dist
```

## General Debugging

### Enable verbose logging

```python
# app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('sqlalchemy').setLevel(logging.DEBUG)
logging.getLogger('celery').setLevel(logging.DEBUG)
```

### Monitor all containers in real-time

```bash
# Terminal 1
docker-compose logs -f

# Terminal 2
watch -n 1 'docker-compose ps'

# Terminal 3
watch -n 1 'docker stats'
```

### Collect diagnostic info

```bash
# Save debug info to file
{
  echo "=== Docker Compose Status ==="
  docker-compose ps

  echo -e "\n=== Recent Logs ==="
  docker-compose logs --tail=50

  echo -e "\n=== Environment ==="
  docker-compose exec api env | grep -v PASSWORD

  echo -e "\n=== Database Status ==="
  docker-compose exec db pg_isready -v

  echo -e "\n=== Disk Usage ==="
  docker system df
} > debug_info.txt

# Share debug_info.txt to get help
```

## Getting Help

1. **Check logs first**: `docker-compose logs`
2. **Search documentation**: [README.md](./documentation/README.md)
3. **Check related docs**:
   - [DOCKER_SETUP.md](./documentation/DOCKER_SETUP.md)
   - [DEVELOPMENT_GUIDE.md](./documentation/DEVELOPMENT_GUIDE.md)
   - [ENVIRONMENT_SETUP.md](./documentation/ENVIRONMENT_SETUP.md)
4. **Create GitHub issue** with:
   - Error message (full text)
   - Steps to reproduce
   - Output of `docker-compose ps`
   - Relevant logs
   - Environment (OS, Docker version, etc.)

## Quick Commands

```bash
# Start fresh
docker-compose down -v && docker-compose up -d

# View all logs
docker-compose logs -f --tail=100

# Connect to database
docker-compose exec db psql -U examgenie_user -d examgenie

# Check health
docker-compose exec api curl http://localhost:8000/health &&
docker-compose exec redis redis-cli ping &&
docker-compose exec db pg_isready

# Restart everything
docker-compose restart

# Clean up unused resources
docker system prune -a --volumes
```
