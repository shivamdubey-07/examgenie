# Monitoring & Maintenance Guide

## Overview

Proactive monitoring and regular maintenance keep ExamGenie running smoothly in production.

## Health Checks

### Basic Health Endpoint

```bash
# Check API health
curl https://yourdomain.com/health

# Response (200 OK):
# {"status": "healthy"}

# Should return 200 status code
curl -I https://yourdomain.com/health
# HTTP/2 200
```

### Readiness Check

```bash
# Checks if all dependencies are available
curl https://yourdomain.com/readiness

# Response (200 OK):
{
  "status": "ready",
  "database": "connected",
  "redis": "connected",
  "storage": "connected"
}
```

### Liveness Check

```bash
# For container orchestration (Kubernetes, Docker Swarm)
curl https://yourdomain.com/live

# Response (200 OK):
# {"status": "alive"}
```

## Monitoring Setup

### Prometheus Metrics

Export metrics from FastAPI:

```bash
# Install prometheus client
pip install prometheus-client

# Add to app/main.py
from prometheus_client import Counter, Histogram, make_wsgi_app
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)

# Metrics available at: http://localhost:8000/metrics
```

### Datadog Integration

```python
# In app/main.py
from datadog import initialize, api

options = {
    'api_key': 'YOUR_API_KEY',
    'app_key': 'YOUR_APP_KEY'
}

initialize(**options)

# Send custom metrics
from datadog import statsd

statsd.gauge('exam.generation.time', elapsed_seconds, tags=['difficulty:intermediate'])
statsd.increment('api.request.count', tags=[f'endpoint:{request.url.path}'])
```

### New Relic Integration

```python
# In requirements.txt
newrelic

# In app/main.py
import newrelic.agent
newrelic.agent.initialize('newrelic.ini')

# Add to startup
app.add_middleware(NewRelicMiddleware)
```

## Key Metrics to Monitor

### API Performance

```bash
# Check response times
docker-compose logs api | grep "duration"

# Average response time should be < 200ms
# 95th percentile < 1 second
```

### Database Performance

```bash
# Connect and check queries
docker-compose exec db psql -U examgenie -d examgenie

# Find slow queries
SELECT query, calls, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

# Check connections
SELECT * FROM pg_stat_activity;

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname != 'pg_catalog'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Redis Performance

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check memory usage
INFO memory

# Check commands (real-time)
MONITOR

# Check slow commands
SLOWLOG GET 10

# Set slowlog threshold
CONFIG SET slowlog-log-microseconds 10000
```

### Celery Tasks

```bash
# Active tasks
docker-compose exec worker celery -A app.worker.celery_app inspect active

# Task stats
docker-compose exec worker celery -A app.worker.celery_app inspect stats

# Monitor in real-time
docker-compose exec worker celery -A app.worker.celery_app events

# Check task queue
docker-compose exec redis redis-cli LLEN celery
docker-compose exec redis redis-cli LRANGE celery 0 -1
```

## Logging Strategy

### Log Levels

```env
# Development
LOG_LEVEL=DEBUG

# Staging
LOG_LEVEL=INFO

# Production
LOG_LEVEL=WARNING
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f db

# Last N lines
docker-compose logs --tail=500 api

# With timestamps
docker-compose logs -f --timestamps api

# Filter logs
docker-compose logs api | grep "error"
docker-compose logs api | grep "POST /auth/login"
```

### Log Aggregation

Send logs to external service:

```bash
# With docker-compose
logging:
  driver: "splunk"  # or awslogs, awsfirelens, etc.
  options:
    splunk-token: "YOUR_TOKEN"
    splunk-url: "https://your-instance.splunkcloud.com"
```

## Backup & Recovery

### Database Backup

```bash
# Manual backup
docker-compose exec db pg_dump -U examgenie examgenie > backup.sql

# Backup with timestamp
docker-compose exec db pg_dump -U examgenie examgenie > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker-compose exec db pg_dump -U examgenie examgenie | gzip > backup.sql.gz
```

### Restore Database

```bash
# From backup file
docker-compose exec -T db psql -U examgenie examgenie < backup.sql

# From compressed backup
gunzip -c backup.sql.gz | docker-compose exec -T db psql -U examgenie examgenie
```

### Automated Backups (Cron)

```bash
#!/bin/bash
# /opt/examgenie/backup.sh

BACKUP_DIR=/backups/examgenie
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database
docker-compose -f /opt/examgenie/docker-compose.prod.yml exec db \
  pg_dump -U examgenie examgenie | gzip > \
  $BACKUP_DIR/db_${DATE}.sql.gz

# MinIO files (if needed)
# docker-compose exec minio mc cp -r minio/examgenie /backups/examgenie/minio_${DATE}

# Keep only last 7 days
find $BACKUP_DIR -mtime +7 -delete

# Optional: Upload to S3
# aws s3 cp $BACKUP_DIR/ s3://backups/examgenie/ --recursive --sse AES256
```

Add to crontab:

```bash
# Daily at 2 AM
0 2 * * * /opt/examgenie/backup.sh
```

## Resource Management

### Monitor Resource Usage

```bash
# Real-time stats
docker stats

# Check specific containers
docker stats examgenie_api examgenie_db examgenie_worker

# Historical usage
docker inspect examgenie_api | grep -A 5 HostConfig
```

### Set Resource Limits

Update `docker-compose.prod.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: "1.5" # Max CPU
          memory: 1.5G # Max memory
        reservations:
          cpus: "0.5" # Guaranteed CPU
          memory: 512M # Guaranteed memory
```

Restart:

```bash
docker-compose down
docker-compose up -d
```

### Disk Usage

```bash
# Check disk space
df -h /

# Docker image size
docker images | grep examgenie

# Container size
docker ps -a --format "table {{.Names}}\t{{.Size}}"

# Volume size
docker volume ls
docker inspect examgenie_examgenie_db

# Cleanup unused resources
docker system prune -a --volumes    # WARNING: removes everything
docker volume prune                  # Remove unused volumes
docker image prune -a                # Remove unused images
```

## Regular Maintenance Tasks

### Daily

- [ ] Check API health endpoint
- [ ] Monitor error logs
- [ ] Verify database connectivity

### Weekly

- [ ] Review performance metrics
- [ ] Check disk space usage
- [ ] Update dependencies
- [ ] Test backup/restore

### Monthly

- [ ] Analyze slow queries
- [ ] Optimize hot tables (add indexes)
- [ ] Review security logs
- [ ] Update SSL certificate status

### Quarterly

- [ ] Full disaster recovery test
- [ ] Review and update documentation
- [ ] Capacity planning
- [ ] Security audit

## Optimization Guidelines

### Database Optimization

```sql
-- Analyze table for optimizer
ANALYZE exams;

-- Add index for frequent queries
CREATE INDEX idx_exams_user_id ON exams(user_id);
CREATE INDEX idx_attempts_exam_id ON exam_attempts(exam_id);

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Check unused indexes
SELECT schemaname, tablename, indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexrelname NOT LIKE 'pg_toast%';
```

### Query Optimization

```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1 second
SELECT pg_reload_conf();

-- View slow queries
SELECT query, calls, mean_time, max_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC;
```

### Cache Optimization

```bash
# Check Redis memory usage
docker-compose exec redis redis-cli INFO memory

# Monitor key counts
docker-compose exec redis redis-cli DBSIZE

# Find large keys
docker-compose exec redis redis-cli --bigkeys

# Set eviction policy
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Alerting

### Create Alerts

Example with Prometheus/AlertManager:

```yaml
groups:
  - name: examgenie
    rules:
      - alert: APIDown
        expr: up{job="api"} == 0
        for: 5m
        actions:
          - send_email: ops@examgenie.com

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        actions:
          - send_slack: #alerts

      - alert: DatabaseSlow
        expr: pg_slow_queries > 10
        for: 10m
        actions:
          - send_pagerduty: ops@examgenie.com
```

### Manual Health Check Script

```bash
#!/bin/bash
# /opt/examgenie/health-check.sh

echo "=== ExamGenie Health Check ==="
echo ""

# API
if curl -s -f https://yourdomain.com/health > /dev/null; then
  echo "✓ API: Healthy"
else
  echo "✗ API: Down"
  exit 1
fi

# Database
if docker-compose exec db pg_isready -U examgenie > /dev/null 2>&1; then
  echo "✓ Database: Connected"
else
  echo "✗ Database: Not responding"
  exit 1
fi

# Redis
if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
  echo "✓ Redis: Connected"
else
  echo "✗ Redis: Not responding"
  exit 1
fi

# MinIO
if docker-compose exec minio mc alias list myminio > /dev/null 2>&1; then
  echo "✓ MinIO: Connected"
else
  echo "✗ MinIO: Not accessible"
  exit 1
fi

echo ""
echo "✓ All systems operational"
```

Run periodically:

```bash
chmod +x /opt/examgenie/health-check.sh
# Add to crontab: */5 * * * * /opt/examgenie/health-check.sh
```

## Performance Baseline

Document baseline metrics:

```
System Baseline
Date: 2024-03-18
Environment: Production

API Performance
- Response time (avg):       120ms
- Response time (p95):       500ms
- Error rate:                <0.1%
- Requests/sec:              100

Database
- Connections:               10/100
- Cache hit ratio:           95%
- Slow queries:              0
- Replication lag:           0s

Infrastructure
- CPU usage:                 30%
- Memory usage:              45%
- Disk usage:                40%

Update these monthly for trend analysis.
```

## Documentation

Keep runbooks for common scenarios:

- Restart API service
- Failover database
- Scale workers
- Emergency data restore
- SSL certificate renewal
- Database migration
- Feature deployment
- Rollback procedure

## Support & Escalation

```
Severity  |  Response Time  |  Resolution Time
--------  |  --------       |  ----------
Critical  |  15 minutes     |  1 hour
High      |  1 hour         |  4 hours
Medium    |  4 hours        |  24 hours
Low       |  24 hours       |  1 week
```

## Related Documentation

- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Deployment procedures
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues
- [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Docker management
