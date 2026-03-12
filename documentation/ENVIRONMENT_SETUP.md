# Environment Setup Guide

## Environment Variables

All configuration is managed through environment variables stored in `.env` file. This allows different configs for dev/prod without code changes.

## .env File Structure

Create `.env` in the `examgenie/` root directory:

```bash
cp .env.example .env
```

## Required Variables

### Database Configuration

```env
POSTGRES_USER=examgenie_user              # Database user
POSTGRES_PASSWORD=strong_password_123     # Database password (change in prod!)
POSTGRES_DB=examgenie                     # Database name
DB_HOST=db                                # Container name (or IP in production)
DB_PORT=5432                              # PostgreSQL port
DB_URL=postgresql://user:pass@db:5432/examgenie  # Full connection string (optional)
```

### Redis Configuration

```env
REDIS_PASSWORD=redis_password_123         # Redis password
REDIS_URL=redis://:password@redis:6379/0  # Full connection string (optional)
```

### MinIO (S3-Compatible Storage)

```env
MINIO_ROOT_USER=minioadmin                # MinIO root username
MINIO_ROOT_PASSWORD=minoadmin_pass_123    # MinIO root password
S3_BUCKET=examgenie                       # S3 bucket name
S3_REGION=us-east-1                       # S3 region
S3_ENDPOINT_URL=http://minio:9000        # MinIO endpoint (dev)
S3_ACCESS_KEY_ID=minioadmin               # Access key (should match root user)
S3_SECRET_ACCESS_KEY=minioadmin_pass_123  # Secret key (should match root password)
```

### Application Configuration

```env
# Security & Debug
DEBUG=true                                # Enable debug mode (false in production!)
ENVIRONMENT=development                   # development, staging, production
SECRET_KEY=dev_secret_key_at_least_32_chars  # JWT signing key (generate with secrets.token_urlsafe(32))

# CORS (Cross-Origin Resource Sharing)
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# API Configuration
API_HOST=0.0.0.0                         # API bind address
API_PORT=8000                            # API bind port
API_WORKERS=1                            # Number of uvicorn workers (>1 for production)
```

### External Services

```env
# OpenAI
OPENAI_API_KEY=sk-...your_key_here...    # OpenAI API key
OPENAI_MODEL=gpt-4                       # Model to use
OPENAI_ORG_ID=org-...                    # Organization ID (optional)

# Email (if sending notifications)
SMTP_HOST=smtp.gmail.com                 # Email server
SMTP_PORT=587                            # Email port
SMTP_USER=your_email@gmail.com           # Email username
SMTP_PASSWORD=your_app_password          # Email password
SMTP_FROM=noreply@examgenie.com          # From email address
```

### Logging

```env
LOG_LEVEL=INFO                           # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=/var/log/examgenie/app.log     # Log file path (optional)
```

## Development Environment (.env)

Minimal setup for local development:

```env
# Database
POSTGRES_USER=examgenie_user
POSTGRES_PASSWORD=dev_password123
POSTGRES_DB=examgenie
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_PASSWORD=redis_password123

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
S3_BUCKET=examgenie

# App
DEBUG=true
ENVIRONMENT=development
SECRET_KEY=dev_secret_key_must_be_at_least_32_characters_long!!!
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:80"]
API_WORKERS=1

# OpenAI (optional)
OPENAI_API_KEY=sk-...test_key_if_testing_ai...

LOG_LEVEL=INFO
```

## Production Environment (.env.prod)

Secure configuration for production deployment:

```env
# Database (use strong passwords!)
POSTGRES_USER=examgenie_prod
POSTGRES_PASSWORD=p@ssw0rd_very_strong_random_string_here_minimum_16_chars
POSTGRES_DB=examgenie
DB_HOST=db-prod.mydomain.com  # Or internal IP
DB_PORT=5432

# Redis (with password!)
REDIS_PASSWORD=redis_very_strong_password_minimum_16_chars

# MinIO
MINIO_ROOT_USER=minioadmin_prod
MINIO_ROOT_PASSWORD=minio_very_strong_password_minimum_16_chars
S3_BUCKET=examgenie

# App (production!)
DEBUG=false                                 # NEVER debug in production!
ENVIRONMENT=production
SECRET_KEY=generate_with_python_random_32_chars_or_more  # Must be random!
CORS_ORIGINS=["https://examgenie.com","https://www.examgenie.com"]
API_WORKERS=4                              # Multiple workers for production

# OpenAI (required for AI features)
OPENAI_API_KEY=sk-...your_real_production_key...
OPENAI_MODEL=gpt-4

# Email notifications
SMTP_HOST=mail.yourdomain.com
SMTP_PORT=587
SMTP_USER=noreply@examgenie.com
SMTP_PASSWORD=email_password
SMTP_FROM=ExamGenie <noreply@examgenie.com>

LOG_LEVEL=WARNING                         # Less logging in production
```

## Generating Secret Keys

### Python Method

```python
import secrets

# Generate 32-character secret key
secret_key = secrets.token_urlsafe(32)
print(secret_key)
```

### Shell Method

```bash
# Using openssl
openssl rand -base64 32

# Using python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Using /dev/urandom
head -c 32 /dev/urandom | base64
```

## Loading Environment Variables

### Automatic (Docker)

Docker-compose automatically reads `.env` file:

```bash
docker-compose up -d  # Loads .env automatically
```

### Manual (Python)

```python
from dotenv import load_dotenv
import os

# Load from .env
load_dotenv()

# Access variables
db_user = os.getenv('POSTGRES_USER')
db_pass = os.getenv('POSTGRES_PASSWORD')
```

### In Application (FastAPI)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    debug: bool = False
    environment: str = "development"
    secret_key: str
    postgres_user: str
    postgres_password: str
    redis_password: str
    openai_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
```

## Environment-Specific Behavior

### Development

- Debug enabled
- Hot reload enabled
- Verbose logging
- CORS open to localhost
- No SSL required
- Single worker process

### Production

- Debug disabled
- Static files served
- JSON logging
- CORS restricted to domain
- SSL/TLS required
- Multiple worker processes
- Health checks enabled
- Monitoring instrumented

## Secrets Management Best Practices

### Do ✅

- Generate strong random keys
- Store secrets in `.env` (not in repo!)
- Use different secrets per environment
- Rotate secrets periodically
- Store `.env` in secure vault (production)
- Use environment variables for all sensitive data

### Don't ❌

- Commit `.env` to git (add to `.gitignore`)
- Use default/weak passwords
- Put secrets in code
- Share secrets in chat/email
- Use same secrets for dev and prod
- Log sensitive environment variables

## .env in .gitignore

Ensure `.env` is not committed to version control:

```
# .gitignore
.env
.env.local
.env.*.local
.env.prod
```

Then create `.env.example` with dummy values for documentation:

```bash
cp .env .env.example
# Edit .env.example to remove actual values
# Commit .env.example to git
```

## Docker Secrets (Advanced)

For production Kubernetes/Swarm deployments:

```yaml
services:
  api:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password

secrets:
  db_password:
    external: true
```

## Verifying Configuration

### Check Variables are Loaded

```bash
# From container
docker-compose exec api env | grep POSTGRES
docker-compose exec api env | grep REDIS
docker-compose exec api env | grep OPENAI

# From Python
docker-compose exec api python -c "from app.config import settings; print(settings.postgres_user)"
```

### Test Database Connection

```bash
# Via docker-compose
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"

# Via Python
docker-compose exec api python -c "import sqlalchemy; print('DB OK')"
```

### Test Redis Connection

```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Test OpenAI Connection

```bash
docker-compose exec api python -c "
import openai
openai.api_key = os.getenv('OPENAI_API_KEY')
models = openai.Model.list()
print(f'Connected! Available models: {len(models.data)}')"
```

## Changing Environment Variables

### For Development

1. Edit `.env`:

```bash
nano .env
```

2. Restart affected services:

```bash
docker-compose restart api
# Or restart all
docker-compose down && docker-compose up -d
```

### For Production

1. Update `.env.prod` on server
2. Use secrets management (Vault, AWS Secrets Manager)
3. Restart only affected services to minimize downtime
4. Monitor logs for errors

```bash
docker-compose -f docker-compose.prod.yml restart api
```

## Common Configuration Issues

### "DEBUG must be False in production"

```env
# ❌ Wrong
DEBUG=true

# ✅ Correct
DEBUG=false
```

### "CORS origin mismatch"

```env
# ❌ Wrong
CORS_ORIGINS=["*"]  # Too permissive!

# ✅ Correct
CORS_ORIGINS=["https://yourdomain.com"]
```

### "Secret key too short"

```env
# ❌ Wrong (too short)
SECRET_KEY=mykey

# ✅ Correct (32+ characters)
SECRET_KEY=aB3xC9mK2pL4qR7sT1uV5wX8yZ0jH6nM
```

### "Database password has special characters"

```env
# ❌ Wrong (special char not escaped)
POSTGRES_PASSWORD=p@ss&word

# ✅ Correct (quoted)
POSTGRES_PASSWORD="p@ss&word"
```

## Reference

For complete configuration options, see:

- `.env.example` in project root
- `app/common/config.py` for application settings
- `docker-compose.yml` for service variables
