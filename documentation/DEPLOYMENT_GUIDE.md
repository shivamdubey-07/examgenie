# Deployment Guide

## Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Backups created
- [ ] Monitoring configured
- [ ] Team notified

## Development to Production

### 1. Build Docker Image

```bash
cd examgenie

# Build production image
docker build -t examgenie:v1.0 .

# Test image locally
docker run -p 8000:8000 examgenie:v1.0

# Tag for registry
docker tag examgenie:v1.0 registry.example.com/examgenie:v1.0

# Push to registry
docker push registry.example.com/examgenie:v1.0
```

### 2. Prepare Environment

```bash
# On production server
mkdir -p /opt/examgenie
cd /opt/examgenie

# Copy docker-compose files
scp docker-compose.prod.yml user@server:/opt/examgenie/
scp nginx.prod.conf user@server:/opt/examgenie/nginx.conf

# Create environment file
cat > .env.prod << EOF
# Database
POSTGRES_USER=examgenie
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
POSTGRES_DB=examgenie
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_PASSWORD=REDIS_PASSWORD_HERE

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=MINIO_PASSWORD_HERE
S3_BUCKET=examgenie

# App
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=GENERATE_RANDOM_32_CHAR_STRING
CORS_ORIGINS=["https://yourdomain.com"]

# OpenAI
OPENAI_API_KEY=sk-...

LOG_LEVEL=WARNING
EOF

chmod 600 .env.prod
```

### 3. SSL Certificate Setup

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Creates: /etc/letsencrypt/live/yourdomain.com/

# Verify certificate
sudo certbot certificates
```

### 4. Configure Nginx

Update `nginx.prod.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### 5. Start Services

```bash
cd /opt/examgenie

# Pull latest image
docker pull registry.example.com/examgenie:v1.0

# Start with production compose
docker-compose -f docker-compose.prod.yml up -d

# Verify all services
docker-compose -f docker-compose.prod.yml ps

# Check health
curl https://yourdomain.com/health
```

### 6. Database Setup (First Time Only)

```bash
# Create database and run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Verify database
docker-compose -f docker-compose.prod.yml exec db psql -U examgenie -d examgenie -c "SELECT 1;"
```

## Zero-Downtime Deployment

### Strategy: Rolling Update

```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      replicas: 2
      update_config:
        parallelism: 1 # Update one at a time
        delay: 30s # Wait 30 seconds between updates
        failure_action: rollback # Rollback if fails
```

### Deployment Steps

```bash
# 1. Build new image
docker build -t examgenie:v1.1 .
docker push registry.example.com/examgenie:v1.1

# 2. Update compose file with new image tag
sed -i 's|examgenie:v1.0|examgenie:v1.1|' docker-compose.prod.yml

# 3. Apply update (rolling)
docker-compose -f docker-compose.prod.yml up -d

# New image pulled and services updated one at a time
# Old instances still serve traffic during update

# 4. Verify
docker-compose -f docker-compose.prod.yml ps
curl https://yourdomain.com/health

# 5. If something fails, Docker rolls back automatically
```

## Database Migrations in Production

### Safe Migration Procedure

```bash
# 1. Backup current database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U examgenie examgenie > backup_pre_deploy.sql

# 2. Test migration on staging environment first
docker-compose -f docker-compose.staging.yml exec api alembic upgrade head

# 3. After testing, run on production
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# 4. Verify migration succeeded
docker-compose -f docker-compose.prod.yml exec db psql -U examgenie -d examgenie -c "SELECT * FROM alembic_version;"

# 5. If error, rollback
docker-compose -f docker-compose.prod.yml exec api alembic downgrade -1
docker-compose -f docker-compose.prod.yml exec db psql -U examgenie -d examgenie < backup_pre_deploy.sql
```

## Monitoring & Logging

```bash
# Stream logs from all services
docker-compose -f docker-compose.prod.yml logs -f

# Stream specific service logs
docker-compose -f docker-compose.prod.yml logs -f api

# View recent logs
docker-compose -f docker-compose.prod.yml logs --tail=100 api
```

## SSL Auto-Renewal

```bash
# Create renewal script
cat > /opt/examgenie/renew-ssl.sh << 'EOF'
#!/bin/bash
certbot renew --quiet
docker-compose -f /opt/examgenie/docker-compose.prod.yml exec -T nginx nginx -s reload
EOF

chmod +x /opt/examgenie/renew-ssl.sh

# Add to crontab (runs daily at 3 AM)
(crontab -l; echo "0 3 * * * /opt/examgenie/renew-ssl.sh") | crontab -
```

## Scaling

### Increase API Replicas

```bash
# Update docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml down
# Edit: api.deploy.replicas = 3
docker-compose -f docker-compose.prod.yml up -d

# Verify 3 API instances running
docker-compose -f docker-compose.prod.yml ps | grep api
```

### Increase Worker Replicas

```bash
# Similar to API scaling
docker-compose -f docker-compose.prod.yml down
# Edit: worker.deploy.replicas = 2
docker-compose -f docker-compose.prod.yml up -d
```

## Backup & Recovery

### Automated Daily Backups

```bash
cat > /opt/examgenie/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backups/examgenie
mkdir -p $BACKUP_DIR

# Database backup
docker-compose -f /opt/examgenie/docker-compose.prod.yml exec db \
  pg_dump -U examgenie examgenie | gzip > \
  $BACKUP_DIR/db_$(date +%Y%m%d_%H%M%S).sql.gz

# Keep only last 7 backups
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

# Upload to S3 (optional)
# aws s3 cp $BACKUP_DIR s3://my-backup-bucket/examgenie/ --recursive
EOF

chmod +x /opt/examgenie/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l; echo "0 2 * * * /opt/examgenie/backup.sh") | crontab -
```

### Recovery from Backup

```bash
# 1. Find backup file
ls -la /backups/examgenie/

# 2. Restore database
gunzip -c /backups/examgenie/db_20240318_020000.sql.gz | \
  docker-compose -f docker-compose.prod.yml exec -T db \
  psql -U examgenie examgenie

# 3. Verify restoration
docker-compose -f docker-compose.prod.yml exec db \
  psql -U examgenie -d examgenie -c "SELECT COUNT(*) FROM exams;"
```

## Monitoring & Alerts

### Health Check Setup

```bash
# Monitor endpoint
curl -f https://yourdomain.com/health && echo "API healthy" || echo "API down"

# Add to monitoring system (Datadog, New Relic, etc.)
# Example with curl and cron:

cat > /opt/examgenie/health-check.sh << 'EOF'
#!/bin/bash
if ! curl -f -s https://yourdomain.com/health > /dev/null; then
  # Send alert
  curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK \
    -d '{"text":"ExamGenie API is down!"}'
fi
EOF

chmod +x /opt/examgenie/health-check.sh
# Add to crontab: */5 * * * * /opt/examgenie/health-check.sh
```

## Troubleshooting Deployment

### Services won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Common issues
# 1. Port already in use: lsof -i :80
# 2. Out of disk: df -h
# 3. Out of memory: free -h
```

### API is slow

```bash
# Check resources
docker-compose -f docker-compose.prod.yml stats

# View slow queries
docker-compose -f docker-compose.prod.yml exec db \
  psql -U examgenie -d examgenie -c \
  "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC;"
```

### Database migrations failed

```bash
# View current version
docker-compose -f docker-compose.prod.yml exec api alembic current

# View migration history
docker-compose -f docker-compose.prod.yml exec api alembic history

# Downgrade and retry
docker-compose -f docker-compose.prod.yml exec api alembic downgrade -1
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

## Post-Deployment

### Verification Checklist

- [ ] API responds on HTTPS: `curl https://yourdomain.com/health`
- [ ] Frontend loads: `curl https://yourdomain.com/`
- [ ] Database connected
- [ ] Redis connected
- [ ] MinIO connected
- [ ] SSL certificate valid: `openssl s_client -connect yourdomain.com:443`
- [ ] Logs are clean (no errors)
- [ ] Performance acceptable
- [ ] Monitoring alerts in place

### Document Deployment

```bash
# Create deployment record
cat > /opt/examgenie/deployments.log << 'EOF'
2024-03-18 10:30:00 - v1.0 deployed by admin
  - New feature: exam generation with AI
  - Database migration: add difficulty_level
  - Test results: passing
  - Rollback: none needed

2024-03-18 14:30:00 - v1.1 deployed by admin
  - Bug fix: login CORS issue
  - Rollback: successful, back to v1.0
EOF
```

## Quick Deployment Reference

```bash
# Full deployment
cd /opt/examgenie

# 1. Stop current services
docker-compose -f docker-compose.prod.yml down

# 2. Update files
git pull origin main
docker build -t examgenie:v1.1 .

# 3. Update .env.prod if needed
# nano .env.prod

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d

# 5. Run migrations if needed
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# 6. Verify
docker-compose -f docker-compose.prod.yml ps
curl https://yourdomain.com/health
```

## Rollback

If deployment fails:

```bash
# Revert image tag
docker tag examgenie:v1.0 examgenie:latest

# Restart services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Verify
curl https://yourdomain.com/health
```

## Related Documentation

- [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Docker details
- [ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md) - Configuration
- [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md) - Migrations
- [MONITORING_MAINTENANCE.md](./MONITORING_MAINTENANCE.md) - Monitoring
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Issues
